# Copyright 2024 KugelAudio
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""KugelAudio TTS plugin for LiveKit Agents."""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
from dataclasses import dataclass, replace
from typing import Any

import aiohttp
from livekit.agents import (
    APIConnectionError,
    APIConnectOptions,
    APIStatusError,
    APITimeoutError,
    tts,
    utils,
)
from livekit.agents.types import DEFAULT_API_CONNECT_OPTIONS, NOT_GIVEN, NotGivenOr
from livekit.agents.utils import is_given

from .models import (
    DEFAULT_MODEL,
    DEFAULT_SAMPLE_RATE,
    SUPPORTED_SAMPLE_RATES,
    TTSModels,
)

logger = logging.getLogger("kugelaudio.livekit")


@dataclass
class _TTSOptions:
    model: TTSModels | str
    voice_id: int | None
    sample_rate: int
    cfg_scale: float
    max_new_tokens: int
    speaker_prefix: bool
    api_key: str
    base_url: str


class TTS(tts.TTS):
    """KugelAudio Text-to-Speech plugin for LiveKit Agents.

    This plugin integrates KugelAudio's TTS API with LiveKit's agent framework,
    providing high-quality voice synthesis with streaming support.

    Example:
        ```python
        from kugelaudio.livekit import TTS

        tts = TTS(api_key="your-api-key")

        # Use with VoicePipelineAgent
        agent = VoicePipelineAgent(
            tts=tts,
            ...
        )
        ```

    Or via the livekit.plugins namespace (after registering):
        ```python
        from kugelaudio.livekit import register_plugin
        register_plugin()

        from livekit.plugins import kugelaudio
        tts = kugelaudio.TTS()
        ```
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: TTSModels | str = DEFAULT_MODEL,
        voice_id: int | None = None,
        sample_rate: int = DEFAULT_SAMPLE_RATE,
        cfg_scale: float = 2.0,
        max_new_tokens: int = 2048,
        speaker_prefix: bool = True,
        base_url: str = "https://api.kugelaudio.com",
        http_session: aiohttp.ClientSession | None = None,
    ) -> None:
        """Create a new KugelAudio TTS instance.

        Args:
            api_key: KugelAudio API key. If not provided, reads from
                KUGELAUDIO_API_KEY environment variable.
            model: TTS model to use. "kugel-1-turbo" (fast, 1.5B) or
                "kugel-1" (premium, 7B).
            voice_id: Voice ID to use. If None, uses server default.
            sample_rate: Output sample rate in Hz. Supported rates: 24000 (native),
                22050, 16000, 8000. Lower rates use server-side resampling with
                minimal latency impact (~0.1ms per 100ms of audio).
            cfg_scale: CFG scale for generation quality. Defaults to 2.0.
            max_new_tokens: Maximum tokens to generate. Defaults to 2048.
            speaker_prefix: Whether to add speaker prefix. Defaults to True.
            base_url: API base URL. Defaults to https://api.kugelaudio.com.
            http_session: Optional aiohttp session to reuse.
        """
        super().__init__(
            capabilities=tts.TTSCapabilities(
                streaming=True,
                aligned_transcript=False,
            ),
            sample_rate=sample_rate,
            num_channels=1,
        )

        kugelaudio_api_key = api_key or os.environ.get("KUGELAUDIO_API_KEY")
        if not kugelaudio_api_key:
            raise ValueError(
                "KUGELAUDIO_API_KEY must be set or api_key must be provided"
            )

        self._opts = _TTSOptions(
            model=model,
            voice_id=voice_id,
            sample_rate=sample_rate,
            cfg_scale=cfg_scale,
            max_new_tokens=max_new_tokens,
            speaker_prefix=speaker_prefix,
            api_key=kugelaudio_api_key,
            base_url=base_url.rstrip("/"),
        )

        self._session = http_session

    @property
    def model(self) -> str:
        return self._opts.model

    @property
    def provider(self) -> str:
        return "KugelAudio"

    def _ensure_session(self) -> aiohttp.ClientSession:
        if not self._session:
            self._session = utils.http_context.http_session()
        return self._session

    def update_options(
        self,
        *,
        model: NotGivenOr[TTSModels | str] = NOT_GIVEN,
        voice_id: NotGivenOr[int | None] = NOT_GIVEN,
        cfg_scale: NotGivenOr[float] = NOT_GIVEN,
        max_new_tokens: NotGivenOr[int] = NOT_GIVEN,
        speaker_prefix: NotGivenOr[bool] = NOT_GIVEN,
    ) -> None:
        """Update TTS options dynamically.

        Args:
            model: TTS model to use.
            voice_id: Voice ID to use.
            cfg_scale: CFG scale for generation.
            max_new_tokens: Maximum tokens to generate.
            speaker_prefix: Whether to add speaker prefix.
        """
        if is_given(model):
            self._opts.model = model
        if is_given(voice_id):
            self._opts.voice_id = voice_id
        if is_given(cfg_scale):
            self._opts.cfg_scale = cfg_scale
        if is_given(max_new_tokens):
            self._opts.max_new_tokens = max_new_tokens
        if is_given(speaker_prefix):
            self._opts.speaker_prefix = speaker_prefix

    def synthesize(
        self,
        text: str,
        *,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> ChunkedStream:
        """Synthesize text to speech (non-streaming).

        Args:
            text: Text to synthesize.
            conn_options: Connection options.

        Returns:
            ChunkedStream that yields audio frames.
        """
        return ChunkedStream(tts=self, input_text=text, conn_options=conn_options)

    def stream(
        self,
        *,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> "SynthesizeStream":
        """Create a streaming TTS session.

        Args:
            conn_options: Connection options.

        Returns:
            SynthesizeStream for streaming text input.
        """
        return SynthesizeStream(tts=self, conn_options=conn_options)

    async def aclose(self) -> None:
        """Close the TTS instance and release resources."""
        pass


class ChunkedStream(tts.ChunkedStream):
    """Non-streaming TTS synthesis using WebSocket."""

    def __init__(
        self,
        *,
        tts: TTS,
        input_text: str,
        conn_options: APIConnectOptions,
    ) -> None:
        super().__init__(tts=tts, input_text=input_text, conn_options=conn_options)
        self._tts = tts
        self._opts = replace(tts._opts)

    async def _run(self, output_emitter: tts.AudioEmitter) -> None:
        """Run the synthesis and emit audio frames."""
        request_id = utils.shortuuid()

        output_emitter.initialize(
            request_id=request_id,
            sample_rate=self._opts.sample_rate,
            num_channels=1,
            mime_type="audio/pcm",
        )

        ws_url = self._opts.base_url.replace("https://", "wss://").replace(
            "http://", "ws://"
        )
        ws_url = (
            f"{ws_url}/ws/tts?api_key={self._opts.api_key}&model={self._opts.model}"
        )

        request_data = {
            "text": self._input_text,
            "model": self._opts.model,
            "cfg_scale": self._opts.cfg_scale,
            "max_new_tokens": self._opts.max_new_tokens,
            "sample_rate": self._opts.sample_rate,
            "speaker_prefix": self._opts.speaker_prefix,
        }
        if self._opts.voice_id is not None:
            request_data["voice_id"] = self._opts.voice_id

        try:
            session = self._tts._ensure_session()
            async with session.ws_connect(
                ws_url,
                timeout=aiohttp.ClientTimeout(
                    total=60, sock_connect=self._conn_options.timeout
                ),
            ) as ws:
                await ws.send_str(json.dumps(request_data))

                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(msg.data)

                        if data.get("error"):
                            raise APIStatusError(
                                message=data["error"],
                                status_code=400,
                                request_id=request_id,
                                body=None,
                            )

                        if data.get("audio"):
                            audio_bytes = base64.b64decode(data["audio"])
                            output_emitter.push(audio_bytes)

                        if data.get("final"):
                            break

                    elif msg.type in (
                        aiohttp.WSMsgType.CLOSED,
                        aiohttp.WSMsgType.ERROR,
                    ):
                        break

                output_emitter.flush()

        except asyncio.TimeoutError:
            raise APITimeoutError() from None
        except aiohttp.ClientError as e:
            raise APIConnectionError() from e


class SynthesizeStream(tts.SynthesizeStream):
    """Streaming TTS synthesis using WebSocket."""

    def __init__(
        self,
        *,
        tts: TTS,
        conn_options: APIConnectOptions,
    ) -> None:
        super().__init__(tts=tts, conn_options=conn_options)
        self._tts = tts
        self._opts = replace(tts._opts)

    async def _run(self, output_emitter: tts.AudioEmitter) -> None:
        """Run the streaming synthesis."""
        request_id = utils.shortuuid()

        output_emitter.initialize(
            request_id=request_id,
            sample_rate=self._opts.sample_rate,
            num_channels=1,
            mime_type="audio/pcm",
            stream=True,
        )

        ws_url = self._opts.base_url.replace("https://", "wss://").replace(
            "http://", "ws://"
        )
        ws_url = (
            f"{ws_url}/ws/tts?api_key={self._opts.api_key}&model={self._opts.model}"
        )

        try:
            session = self._tts._ensure_session()
            async with session.ws_connect(
                ws_url,
                timeout=aiohttp.ClientTimeout(total=None, sock_connect=30),
            ) as ws:
                segment_id = utils.shortuuid()
                output_emitter.start_segment(segment_id=segment_id)

                async def send_task() -> None:
                    """Collect text and send to WebSocket."""
                    text_buffer: list[str] = []

                    async for data in self._input_ch:
                        if isinstance(data, self._FlushSentinel):
                            if text_buffer:
                                text = "".join(text_buffer)
                                await self._send_text(ws, text)
                                text_buffer.clear()
                            continue
                        text_buffer.append(data)

                    if text_buffer:
                        text = "".join(text_buffer)
                        await self._send_text(ws, text)

                async def recv_task() -> None:
                    """Receive audio from WebSocket."""
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)

                            if data.get("error"):
                                logger.error(f"KugelAudio error: {data['error']}")
                                raise APIStatusError(
                                    message=data["error"],
                                    status_code=400,
                                    request_id=request_id,
                                    body=None,
                                )

                            if data.get("audio"):
                                audio_bytes = base64.b64decode(data["audio"])
                                self._mark_started()
                                output_emitter.push(audio_bytes)

                            if data.get("final"):
                                break

                        elif msg.type in (
                            aiohttp.WSMsgType.CLOSED,
                            aiohttp.WSMsgType.ERROR,
                        ):
                            break

                send = asyncio.create_task(send_task())
                recv = asyncio.create_task(recv_task())

                try:
                    await asyncio.gather(send, recv)
                finally:
                    await utils.aio.gracefully_cancel(send, recv)
                    output_emitter.flush()
                    output_emitter.end_segment()

        except asyncio.TimeoutError:
            raise APITimeoutError() from None
        except aiohttp.ClientError as e:
            raise APIConnectionError() from e

    async def _send_text(self, ws: aiohttp.ClientWebSocketResponse, text: str) -> None:
        """Send text to WebSocket for synthesis."""
        if not text.strip():
            return

        request_data = {
            "text": text,
            "model": self._opts.model,
            "cfg_scale": self._opts.cfg_scale,
            "max_new_tokens": self._opts.max_new_tokens,
            "sample_rate": self._opts.sample_rate,
            "speaker_prefix": self._opts.speaker_prefix,
        }
        if self._opts.voice_id is not None:
            request_data["voice_id"] = self._opts.voice_id

        await ws.send_str(json.dumps(request_data))
