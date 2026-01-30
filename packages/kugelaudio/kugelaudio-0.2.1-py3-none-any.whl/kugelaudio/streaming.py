"""Streaming TTS session for text-in/audio-out streaming."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, AsyncIterator, Callable, Dict, Optional, Union

from kugelaudio.exceptions import (
    AuthenticationError,
    InsufficientCreditsError,
    KugelAudioError,
)
from kugelaudio.models import AudioChunk, StreamConfig

logger = logging.getLogger(__name__)


class StreamingSession:
    """WebSocket session for streaming text input and audio output.

    This allows streaming text (e.g., from an LLM) and receiving audio
    as it's generated. Text is buffered and processed when sentence
    boundaries are detected or when explicitly flushed.

    Example:
        async with client.tts.streaming_session(voice_id=123) as session:
            async for token in llm_stream:
                async for chunk in session.send(token):
                    play_audio(chunk)

            # Flush remaining text
            async for chunk in session.flush():
                play_audio(chunk)
    """

    def __init__(
        self,
        api_key: str,
        tts_url: str,
        config: Optional[StreamConfig] = None,
    ):
        self._api_key = api_key
        self._tts_url = tts_url
        self._config = config or StreamConfig()
        self._ws = None
        self._session_id: Optional[str] = None
        self._is_started = False

    async def __aenter__(self) -> StreamingSession:
        await self.connect()
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()

    async def connect(self) -> None:
        """Connect to the streaming WebSocket endpoint."""
        try:
            import websockets
        except ImportError:
            raise ImportError(
                "websockets required. Install with: pip install websockets"
            )

        ws_url = self._tts_url.replace("https://", "wss://").replace("http://", "ws://")
        ws_url = f"{ws_url}/ws/tts/stream?api_key={self._api_key}"

        try:
            self._ws = await websockets.connect(ws_url)
        except websockets.exceptions.InvalidStatusCode as e:
            if e.status_code == 401:
                raise AuthenticationError("Invalid API key")
            elif e.status_code == 403:
                raise InsufficientCreditsError("Insufficient credits")
            raise KugelAudioError(f"Connection failed: {e}")

    async def start(self) -> None:
        """Start the streaming session with initial config."""
        if self._is_started:
            return

        if not self._ws:
            await self.connect()

        # Send initial config
        await self._ws.send(json.dumps(self._config.to_dict()))

        # Wait for session confirmation
        msg = await self._ws.recv()
        data = json.loads(msg)

        if data.get("error"):
            raise KugelAudioError(data["error"])

        if data.get("session_started"):
            self._session_id = data.get("session_id")
            self._is_started = True
            logger.debug("Streaming session started: %s", self._session_id)

    async def send(
        self,
        text: str,
        flush: bool = False,
    ) -> AsyncIterator[AudioChunk]:
        """Send text and yield any generated audio chunks.

        Args:
            text: Text to add to buffer
            flush: Force flush the buffer

        Yields:
            AudioChunk as audio is generated
        """
        if not self._is_started:
            await self.start()

        # Send text
        await self._ws.send(json.dumps({"text": text, "flush": flush}))

        # Collect any generated audio
        async for chunk in self._receive_until_idle():
            yield chunk

    async def flush(self) -> AsyncIterator[AudioChunk]:
        """Flush the text buffer and yield remaining audio.

        Yields:
            AudioChunk as remaining audio is generated
        """
        if not self._is_started:
            return

        await self._ws.send(json.dumps({"flush": True}))

        async for chunk in self._receive_until_idle():
            yield chunk

    async def _receive_until_idle(self) -> AsyncIterator[AudioChunk]:
        """Receive messages until we get a final message."""
        while True:
            try:
                msg = await asyncio.wait_for(self._ws.recv(), timeout=0.1)
                data = json.loads(msg)

                if data.get("error"):
                    raise KugelAudioError(data["error"])

                if data.get("audio"):
                    yield AudioChunk.from_dict(data)

                if data.get("final"):
                    # Generation complete for this chunk
                    break

            except asyncio.TimeoutError:
                # No more messages waiting
                break
            except Exception as e:
                if "ConnectionClosed" in str(type(e)):
                    break
                raise

    async def close(self) -> Dict[str, Any]:
        """Close the session and return stats.

        Returns:
            Session statistics
        """
        stats = {}

        if self._ws:
            try:
                # Send close command
                await self._ws.send(json.dumps({"close": True}))

                # Wait for session stats
                msg = await asyncio.wait_for(self._ws.recv(), timeout=5.0)
                data = json.loads(msg)

                if data.get("session_closed"):
                    stats = data

            except Exception:
                pass
            finally:
                await self._ws.close()
                self._ws = None
                self._is_started = False

        return stats


class StreamingSessionSync:
    """Synchronous wrapper for StreamingSession."""

    def __init__(self, session: StreamingSession):
        self._session = session
        self._loop = asyncio.new_event_loop()

    def __enter__(self) -> StreamingSessionSync:
        self._loop.run_until_complete(self._session.connect())
        return self

    def __exit__(self, *args) -> None:
        self._loop.run_until_complete(self._session.close())
        self._loop.close()

    def send(self, text: str, flush: bool = False):
        """Send text and return generated audio chunks."""

        async def collect():
            chunks = []
            async for chunk in self._session.send(text, flush=flush):
                chunks.append(chunk)
            return chunks

        return self._loop.run_until_complete(collect())

    def flush(self):
        """Flush buffer and return remaining audio chunks."""

        async def collect():
            chunks = []
            async for chunk in self._session.flush():
                chunks.append(chunk)
            return chunks

        return self._loop.run_until_complete(collect())

    def close(self) -> Dict[str, Any]:
        """Close the session."""
        return self._loop.run_until_complete(self._session.close())


class MultiContextSession:
    """WebSocket session for multi-context TTS streaming.

    Allows managing up to 5 independent audio generation contexts over
    a single WebSocket connection. Each context has its own text buffer,
    voice settings, and generation queue.

    Use cases:
    - Multi-speaker conversations with different voices
    - Pre-buffering audio while another stream plays
    - Interleaved audio generation for dynamic conversations

    Example:
        async with client.tts.multi_context_session() as session:
            # Create contexts with different voices
            await session.create_context("narrator", voice_id=123)
            await session.create_context("character", voice_id=456)

            # Send text to different speakers
            async for chunk in session.send("narrator", "The story begins."):
                play_audio("narrator", chunk)

            async for chunk in session.send("character", "Hello!"):
                play_audio("character", chunk)

            # Close specific context
            await session.close_context("narrator")
    """

    def __init__(
        self,
        api_key: str,
        tts_url: str,
        default_voice_id: Optional[int] = None,
        sample_rate: int = 24000,
        cfg_scale: float = 2.0,
        max_new_tokens: int = 2048,
        normalize: bool = True,
        speaker_prefix: bool = True,
        inactivity_timeout: float = 20.0,
    ):
        self._api_key = api_key
        self._tts_url = tts_url
        self._default_voice_id = default_voice_id
        self._sample_rate = sample_rate
        self._cfg_scale = cfg_scale
        self._max_new_tokens = max_new_tokens
        self._normalize = normalize
        self._speaker_prefix = speaker_prefix
        self._inactivity_timeout = inactivity_timeout
        self._ws = None
        self._session_id: Optional[str] = None
        self._is_started = False
        self._contexts: set[str] = set()

    async def __aenter__(self) -> "MultiContextSession":
        await self.connect()
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()

    async def connect(self) -> None:
        """Connect to the multi-context WebSocket endpoint."""
        try:
            import websockets
        except ImportError:
            raise ImportError(
                "websockets required. Install with: pip install websockets"
            )

        ws_url = self._tts_url.replace("https://", "wss://").replace("http://", "ws://")
        ws_url = f"{ws_url}/ws/tts/multi?api_key={self._api_key}"

        try:
            self._ws = await websockets.connect(ws_url)
        except websockets.exceptions.InvalidStatusCode as e:
            if e.status_code == 401:
                raise AuthenticationError("Invalid API key")
            elif e.status_code == 403:
                raise InsufficientCreditsError("Insufficient credits")
            raise KugelAudioError(f"Connection failed: {e}")

    async def _start_session(self, context_id: str, voice_id: Optional[int] = None) -> None:
        """Start the session with first context creation."""
        if self._is_started:
            return

        if not self._ws:
            await self.connect()

        # Send first context initialization (starts session)
        init_msg = {
            "text": " ",
            "context_id": context_id,
            "sample_rate": self._sample_rate,
            "cfg_scale": self._cfg_scale,
            "max_new_tokens": self._max_new_tokens,
            "normalize": self._normalize,
            "speaker_prefix": self._speaker_prefix,
            "inactivity_timeout": self._inactivity_timeout,
        }
        if voice_id or self._default_voice_id:
            init_msg["voice_id"] = voice_id or self._default_voice_id

        await self._ws.send(json.dumps(init_msg))

        # Wait for session confirmation
        while True:
            msg = await self._ws.recv()
            data = json.loads(msg)

            if data.get("error"):
                raise KugelAudioError(data["error"])

            if data.get("session_started"):
                self._session_id = data.get("session_id")
                self._is_started = True
                logger.debug("Multi-context session started: %s", self._session_id)

            if data.get("context_created"):
                self._contexts.add(data["context_id"])
                logger.debug("Context created: %s", data["context_id"])
                break

    async def create_context(
        self,
        context_id: str,
        voice_id: Optional[int] = None,
    ) -> None:
        """Create a new context with optional voice override.

        Args:
            context_id: Unique identifier for this context
            voice_id: Optional voice ID (uses default if not specified)
        """
        if not self._is_started:
            await self._start_session(context_id, voice_id)
            return

        if context_id in self._contexts:
            return  # Already exists

        # Send context initialization
        msg = {"text": " ", "context_id": context_id}
        if voice_id:
            msg["voice_id"] = voice_id

        await self._ws.send(json.dumps(msg))

        # Wait for confirmation
        while True:
            response = await self._ws.recv()
            data = json.loads(response)

            if data.get("error"):
                raise KugelAudioError(data["error"])

            if data.get("context_created") and data.get("context_id") == context_id:
                self._contexts.add(context_id)
                break

    async def send(
        self,
        context_id: str,
        text: str,
        flush: bool = False,
    ) -> AsyncIterator[AudioChunk]:
        """Send text to a specific context and yield audio chunks.

        Args:
            context_id: Context to send text to
            text: Text to synthesize
            flush: Force flush the buffer

        Yields:
            AudioChunk as audio is generated
        """
        if not self._is_started:
            await self._start_session(context_id)

        if context_id not in self._contexts:
            await self.create_context(context_id)

        await self._ws.send(json.dumps({
            "text": text,
            "context_id": context_id,
            "flush": flush,
        }))

        # Collect audio for this context
        async for chunk in self._receive_audio(context_id, wait_for_final=flush):
            yield chunk

    async def flush(self, context_id: str) -> AsyncIterator[AudioChunk]:
        """Flush a specific context's buffer.

        Args:
            context_id: Context to flush

        Yields:
            AudioChunk as remaining audio is generated
        """
        if not self._is_started or context_id not in self._contexts:
            return

        await self._ws.send(json.dumps({
            "flush": True,
            "context_id": context_id,
        }))

        async for chunk in self._receive_audio(context_id, wait_for_final=True):
            yield chunk

    async def close_context(self, context_id: str) -> AsyncIterator[AudioChunk]:
        """Close a specific context and get remaining audio.

        Args:
            context_id: Context to close

        Yields:
            AudioChunk for any remaining buffered text
        """
        if not self._is_started or context_id not in self._contexts:
            return

        await self._ws.send(json.dumps({
            "close_context": True,
            "context_id": context_id,
        }))

        async for chunk in self._receive_audio(context_id, wait_for_close=True):
            yield chunk

        self._contexts.discard(context_id)

    async def keep_alive(self, context_id: str) -> None:
        """Reset inactivity timeout for a context.

        Args:
            context_id: Context to keep alive
        """
        if self._is_started and context_id in self._contexts:
            await self._ws.send(json.dumps({
                "text": "",
                "context_id": context_id,
            }))

    async def _receive_audio(
        self,
        context_id: str,
        wait_for_final: bool = False,
        wait_for_close: bool = False,
    ) -> AsyncIterator[AudioChunk]:
        """Receive audio messages for a specific context."""
        while True:
            try:
                msg = await asyncio.wait_for(self._ws.recv(), timeout=0.1)
                data = json.loads(msg)

                if data.get("error"):
                    raise KugelAudioError(data["error"])

                # Only yield audio for matching context
                if data.get("audio") and data.get("context_id") == context_id:
                    yield AudioChunk.from_dict(data)

                # Check for completion signals
                if data.get("context_id") == context_id:
                    if wait_for_final and data.get("is_final"):
                        break
                    if wait_for_close and data.get("context_closed"):
                        break

            except asyncio.TimeoutError:
                # No more messages waiting
                if not wait_for_final and not wait_for_close:
                    break
            except Exception as e:
                if "ConnectionClosed" in str(type(e)):
                    break
                raise

    async def close(self) -> Dict[str, Any]:
        """Close the session and return stats.

        Returns:
            Session statistics including total audio generated
        """
        stats = {}

        if self._ws:
            try:
                await self._ws.send(json.dumps({"close_socket": True}))

                # Wait for session stats
                msg = await asyncio.wait_for(self._ws.recv(), timeout=5.0)
                data = json.loads(msg)

                if data.get("session_closed"):
                    stats = data

            except Exception:
                pass
            finally:
                await self._ws.close()
                self._ws = None
                self._is_started = False
                self._contexts.clear()

        return stats

    @property
    def active_contexts(self) -> set[str]:
        """Get the set of active context IDs."""
        return self._contexts.copy()

    @property
    def session_id(self) -> Optional[str]:
        """Get the session ID."""
        return self._session_id

