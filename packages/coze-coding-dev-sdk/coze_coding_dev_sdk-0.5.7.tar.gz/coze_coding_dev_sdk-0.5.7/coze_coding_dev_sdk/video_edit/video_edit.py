import asyncio
import requests
from typing import Dict, List, Optional

from cozeloop.decorator import observe
from coze_coding_utils.runtime_ctx.context import Context

from ..core.client import BaseClient
from ..core.config import Config
from ..core.exceptions import APIError
from .models import (
    AddSubtitlesRequest,
    AudioExtractRequest,
    AudioToSubtitleRequest,
    CompileVideoAudioRequest,
    ConcatVideosRequest,
    OutputSync,
    SubtitleConfig,
    TextItem,
    VideoEditResponse,
    VideoTrimRequest,
)


class VideoEditClient(BaseClient):
    def __init__(
            self,
            config: Optional[Config] = None,
            ctx: Optional[Context] = None,
            custom_headers: Optional[Dict[str, str]] = None,
            verbose: bool = False,
    ):
        super().__init__(config, ctx, custom_headers, verbose)
        self.base_url = self.config.base_url

    @observe
    def add_subtitles(
            self,
            video: str,
            subtitle_config: SubtitleConfig,
            subtitle_url: Optional[str] = None,
            text_list: Optional[List[TextItem]] = None,
            url_expire: Optional[int] = None,
    ) -> VideoEditResponse:
        """
       视频添加字幕：为视频添加字幕，视频支持MP4、AVI、MKV、MOV等常见格式，字幕文件支持SRT、VTT、ASS 等格式。
       支持指定字幕样式的配置，包括字体大小、字体 ID、字体颜色及字幕显示位置和尺寸等。

        Args:
            video: 视频输入地址
            subtitle_config: 字幕配置（字体、位置、颜色等）
            subtitle_url: 字幕文件 url（可选）
            text_list: 文本序列（可选）
            url_expire: 产物url有效时间，单位秒，默认一天，最大30天

        Returns:
            VideoEditResponse: 视频编辑结果响应

        Raises:
            APIError: 当添加字幕失败时
        """
        request_params = {
            "video": video,
            "subtitle_config": subtitle_config,
        }
        if subtitle_url is not None:
            request_params["subtitle_url"] = subtitle_url
        if text_list is not None:
            request_params["text_list"] = text_list
        if url_expire is not None:
            request_params["url_expire"] = url_expire

        request = AddSubtitlesRequest(**request_params)

        response = self._request_with_response(
            method="POST",
            url=f"{self.base_url}/api/v1/integration/video_editing_utils?tool_name=add_subtitles",
            json=request.to_api_request(),
        )

        status_code = response.headers.get("X-Api-Status-Code", "0")
        message = response.headers.get("X-Api-Message", "")

        if status_code != "0":
            raise APIError(
                f"添加字幕失败，状态码: {status_code}, 错误信息: {message}",
                code=status_code,
                status_code=response.status_code,
            )

        response.raise_for_status()

        try:
            data = response.json()
        except Exception as e:
            raise APIError(
                f"响应解析失败: {str(e)}",
                status_code=response.status_code,
            )

        result = VideoEditResponse(**data)
        if not result.url:
            raise APIError(
                f"添加字幕失败: 返回的 URL 为空",
                status_code=response.status_code,
            )
        return result

    @observe
    def concat_videos(
            self,
            videos: List[str],
            transitions: Optional[List[str]] = None,
            url_expire: Optional[int] = None,
    ) -> VideoEditResponse:
        """
        视频拼接/音频拼接，支持：
        （1）对输入的多个视频片段进行拼接，并支持添加转场。
        （2）对输入的多个音频片段进行拼接。

        Args:
            videos: 音视频列表，每个元素为视频 URL 地址
            transitions: 转场ID列表（可选），仅支持非交叠转场
            url_expire: 产物有效时间，单位秒，默认一天，最长30天

        Returns:
            VideoEditResponse: 视频编辑结果响应

        Raises:
            APIError: 当视频拼接失败时
        """
        request_params = {"videos": videos}
        if transitions is not None:
            request_params["transitions"] = transitions
        if url_expire is not None:
            request_params["url_expire"] = url_expire

        request = ConcatVideosRequest(**request_params)

        response = self._request_with_response(
            method="POST",
            url=f"{self.base_url}/api/v1/integration/video_editing_utils?tool_name=concat_videos",
            json=request.to_api_request(),
        )

        status_code = response.headers.get("X-Api-Status-Code", "0")
        message = response.headers.get("X-Api-Message", "")

        if status_code != "0":
            raise APIError(
                f"视频拼接失败，状态码: {status_code}, 错误信息: {message}",
                code=status_code,
                status_code=response.status_code,
            )

        response.raise_for_status()

        try:
            data = response.json()
        except Exception as e:
            raise APIError(
                f"响应解析失败: {str(e)}",
                status_code=response.status_code,
            )

        result = VideoEditResponse(**data)
        if not result.url:
            raise APIError(
                f"视频拼接失败: 返回的 URL 为空",
                status_code=response.status_code,
            )
        return result

    @observe
    def compile_video_audio(
            self,
            video: str,
            audio: str,
            is_video_audio_sync: Optional[bool] = None,
            output_sync: Optional[OutputSync] = None,
            is_audio_reserve: Optional[bool] = None,
            url_expire: Optional[int] = None,
    ) -> VideoEditResponse:
        """
        音视频合成：将视频、音频叠加合成视频。

        Args:
            video: 输入视频 URL
            audio: 输入音频 URL
            is_video_audio_sync: 是否执行音频视频对齐，默认保持原样输出，不做音视频对齐
            output_sync: 输出模式配置（对齐方式和基准），与 is_video_audio_sync 配合使用
            is_audio_reserve: 是否保留原视频流中的音频
            url_expire: 产物有效时间，单位秒，默认一天，最大30天

        Returns:
            VideoEditResponse: 视频编辑结果响应

        Raises:
            APIError: 当视频音频合成失败时
        """
        request_params = {
            "video": video,
            "audio": audio,
        }
        if is_video_audio_sync is not None:
            request_params["is_video_audio_sync"] = is_video_audio_sync
        if output_sync is not None:
            request_params["output_sync"] = output_sync
        if is_audio_reserve is not None:
            request_params["is_audio_reserve"] = is_audio_reserve
        if url_expire is not None:
            request_params["url_expire"] = url_expire

        request = CompileVideoAudioRequest(**request_params)

        response = self._request_with_response(
            method="POST",
            url=f"{self.base_url}/api/v1/integration/video_editing_utils?tool_name=compile_video_audio",
            json=request.to_api_request(),
        )

        status_code = response.headers.get("X-Api-Status-Code", "0")
        message = response.headers.get("X-Api-Message", "")

        if status_code != "0":
            raise APIError(
                f"视频音频合成失败，状态码: {status_code}, 错误信息: {message}",
                code=status_code,
                status_code=response.status_code,
            )

        response.raise_for_status()

        try:
            data = response.json()
        except Exception as e:
            raise APIError(
                f"响应解析失败: {str(e)}",
                status_code=response.status_code,
            )

        result = VideoEditResponse(**data)
        if not result.url:
            raise APIError(
                f"音视频合成失败: 返回的 URL 为空",
                status_code=response.status_code,
            )
        return result

    @observe
    def audio_to_subtitle(
            self,
            source: str,
            subtitle_type: Optional[str] = None,
            url_expire: Optional[int] = None,
    ) -> VideoEditResponse:
        """
        语音转写字幕：将视频或音频中的语音内容转换为字幕文件。
        可以组合 add_subtitles（视频添加字幕）工具使用，将字幕合成到视频中。

        Args:
            source: 音视频输入地址
            subtitle_type: 字幕类型，可选值 ["webvtt", "srt"]，默认 "srt"
            url_expire: 产物超时时间，单位秒，默认一天，最长30天

        Returns:
            VideoEditResponse: 视频编辑结果响应

        Raises:
            APIError: 当语音转字幕失败时
        """
        request_params = {"source": source}
        if subtitle_type is not None:
            request_params["subtitle_type"] = subtitle_type
        if url_expire is not None:
            request_params["url_expire"] = url_expire

        request = AudioToSubtitleRequest(**request_params)

        response = self._request_with_response(
            method="POST",
            url=f"{self.base_url}/api/v1/integration/video_editing_utils?tool_name=audio_to_subtitle",
            json=request.to_api_request(),
        )

        status_code = response.headers.get("X-Api-Status-Code", "0")
        message = response.headers.get("X-Api-Message", "")

        if status_code != "0":
            raise APIError(
                f"语音转字幕失败，状态码: {status_code}, 错误信息: {message}",
                code=status_code,
                status_code=response.status_code,
            )

        response.raise_for_status()

        try:
            data = response.json()
        except Exception as e:
            raise APIError(
                f"响应解析失败: {str(e)}",
                status_code=response.status_code,
            )

        result = VideoEditResponse(**data)
        if not result.url:
            raise APIError(
                f"语音转字幕失败: 返回的 URL 为空",
                status_code=response.status_code,
            )
        return result

    @observe
    def extract_audio(
            self,
            video: str,
            format: Optional[str] = None,
            url_expire: Optional[int] = None,
    ) -> VideoEditResponse:
        """
        音频提取：提取视频文件中的音频。

        Args:
            video: 视频输入地址
            format: 输出格式，可选值 ["m4a", "mp3"]，默认 "m4a"
            url_expire: 产物有效时间，单位秒，默认一天，最大30天，最小1小时

        Returns:
            VideoEditResponse: 视频编辑结果响应

        Raises:
            APIError: 当音频提取失败时
        """
        request_params = {"video": video}
        if format is not None:
            request_params["format"] = format
        if url_expire is not None:
            request_params["url_expire"] = url_expire

        request = AudioExtractRequest(**request_params)

        response = self._request_with_response(
            method="POST",
            url=f"{self.base_url}/api/v1/integration/video_editing_utils?tool_name=audio_extract",
            json=request.to_api_request(),
        )

        status_code = response.headers.get("X-Api-Status-Code", "0")
        message = response.headers.get("X-Api-Message", "")

        if status_code != "0":
            raise APIError(
                f"音频提取失败，状态码: {status_code}, 错误信息: {message}",
                code=status_code,
                status_code=response.status_code,
            )

        response.raise_for_status()

        try:
            data = response.json()
        except Exception as e:
            raise APIError(
                f"响应解析失败: {str(e)}",
                status_code=response.status_code,
            )

        result = VideoEditResponse(**data)
        if not result.url:
            raise APIError(
                f"音频提取失败: 返回的 URL 为空",
                status_code=response.status_code,
            )
        return result

    @observe
    def video_trim(
            self,
            video: str,
            start_time: Optional[float] = None,
            end_time: Optional[float] = None,
            url_expire: Optional[int] = None,
    ) -> VideoEditResponse:
        """
        音视频裁剪：对视频、音频进行片段裁剪，支持输入开始、结束时间。

        Args:
            video: 视频输入地址
            start_time: 裁剪开始时间，单位：秒，默认为0
            end_time: 裁剪结束时间，单位：秒；默认为片源结尾
            url_expire: 产物有效时间，单位为秒，默认一天，最大30天

        Returns:
            VideoEditResponse: 视频编辑结果响应

        Raises:
            APIError: 当视频裁剪失败时
        """
        request_params = {"video": video}
        if start_time is not None:
            request_params["start_time"] = start_time
        if end_time is not None:
            request_params["end_time"] = end_time
        if url_expire is not None:
            request_params["url_expire"] = url_expire

        request = VideoTrimRequest(**request_params)

        response = self._request_with_response(
            method="POST",
            url=f"{self.base_url}/api/v1/integration/video_editing_utils?tool_name=video_trim",
            json=request.to_api_request(),
        )

        status_code = response.headers.get("X-Api-Status-Code", "0")
        message = response.headers.get("X-Api-Message", "")

        if status_code != "0":
            raise APIError(
                f"视频裁剪失败，状态码: {status_code}, 错误信息: {message}",
                code=status_code,
                status_code=response.status_code,
            )

        response.raise_for_status()

        try:
            data = response.json()
        except Exception as e:
            raise APIError(
                f"响应解析失败: {str(e)}",
                status_code=response.status_code,
            )

        result = VideoEditResponse(**data)
        if not result.url:
            raise APIError(
                f"视频裁剪失败: 返回的 URL 为空",
                status_code=response.status_code,
            )
        return result

    async def add_subtitles_async(
            self,
            video: str,
            subtitle_config: SubtitleConfig,
            subtitle_url: Optional[str] = None,
            text_list: Optional[List[TextItem]] = None,
            url_expire: Optional[int] = None,
    ) -> VideoEditResponse:
        """
        视频添加字幕（异步版本）：为视频添加字幕，视频支持MP4、AVI、MKV、MOV等常见格式，字幕文件支持SRT、VTT、ASS 等格式。
        支持指定字幕样式的配置，包括字体大小、字体 ID、字体颜色及字幕显示位置和尺寸等。
        
        适用于批量为多个视频添加字幕的场景。

        Args:
            video: 视频输入地址
            subtitle_config: 字幕配置（字体、位置、颜色等）
            subtitle_url: 字幕文件 url（可选）
            text_list: 文本序列（可选）
            url_expire: 产物url有效时间，单位秒，默认一天，最大30天

        Returns:
            VideoEditResponse: 视频编辑结果响应

        Raises:
            APIError: 当添加字幕失败时
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.add_subtitles,
            video,
            subtitle_config,
            subtitle_url,
            text_list,
            url_expire,
        )

    async def concat_videos_async(
            self,
            videos: List[str],
            transitions: Optional[List[str]] = None,
            url_expire: Optional[int] = None,
    ) -> VideoEditResponse:
        """
        视频拼接/音频拼接（异步版本），支持：
        （1）对输入的多个视频片段进行拼接，并支持添加转场。
        （2）对输入的多个音频片段进行拼接。
        
        适用于批量处理多个视频拼接任务的场景。

        Args:
            videos: 音视频列表，每个元素为视频 URL 地址
            transitions: 转场ID列表（可选），仅支持非交叠转场
            url_expire: 产物有效时间，单位秒，默认一天，最长30天

        Returns:
            VideoEditResponse: 视频编辑结果响应

        Raises:
            APIError: 当视频拼接失败时
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.concat_videos, videos, transitions, url_expire
        )

    async def compile_video_audio_async(
            self,
            video: str,
            audio: str,
            is_video_audio_sync: Optional[bool] = None,
            output_sync: Optional[OutputSync] = None,
            is_audio_reserve: Optional[bool] = None,
            url_expire: Optional[int] = None,
    ) -> VideoEditResponse:
        """
        音视频合成（异步版本）：将视频、音频叠加合成视频。
        
        适用于批量处理视频音频合成任务的场景。

        Args:
            video: 输入视频 URL
            audio: 输入音频 URL
            is_video_audio_sync: 是否执行音频视频对齐，默认保持原样输出，不做音视频对齐
            output_sync: 输出模式配置（对齐方式和基准），与 is_video_audio_sync 配合使用
            is_audio_reserve: 是否保留原视频流中的音频
            url_expire: 产物有效时间，单位秒，默认一天，最大30天

        Returns:
            VideoEditResponse: 视频编辑结果响应

        Raises:
            APIError: 当视频音频合成失败时
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.compile_video_audio,
            video,
            audio,
            is_video_audio_sync,
            output_sync,
            is_audio_reserve,
            url_expire,
        )

    async def audio_to_subtitle_async(
            self,
            source: str,
            subtitle_type: Optional[str] = None,
            url_expire: Optional[int] = None,
    ) -> VideoEditResponse:
        """
        语音转写字幕（异步版本）：将视频或音频中的语音内容转换为字幕文件。
        可以组合 add_subtitles（视频添加字幕）工具使用，将字幕合成到视频中。
        
        适用于批量处理语音转字幕任务的场景。

        Args:
            source: 音视频输入地址
            subtitle_type: 字幕类型，可选值 ["webvtt", "srt"]，默认 "srt"
            url_expire: 产物超时时间，单位秒，默认一天，最长30天

        Returns:
            VideoEditResponse: 视频编辑结果响应

        Raises:
            APIError: 当语音转字幕失败时
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.audio_to_subtitle, source, subtitle_type, url_expire
        )

    async def extract_audio_async(
            self,
            video: str,
            format: Optional[str] = None,
            url_expire: Optional[int] = None,
    ) -> VideoEditResponse:
        """
        音频提取（异步版本）：提取视频文件中的音频。
        
        适用于批量从多个视频中提取音频的场景。

        Args:
            video: 视频输入地址
            format: 输出格式，可选值 ["m4a", "mp3"]，默认 "m4a"
            url_expire: 产物有效时间，单位秒，默认一天，最大30天，最小1小时

        Returns:
            VideoEditResponse: 视频编辑结果响应

        Raises:
            APIError: 当音频提取失败时
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.extract_audio, video, format, url_expire
        )

    async def video_trim_async(
            self,
            video: str,
            start_time: Optional[float] = None,
            end_time: Optional[float] = None,
            url_expire: Optional[int] = None,
    ) -> VideoEditResponse:
        """
        音视频裁剪：对视频、音频进行片段裁剪，支持输入开始、结束时间（异步版本）

        Args:
            video: 视频输入地址
            start_time: 裁剪开始时间，单位：秒，默认为0
            end_time: 裁剪结束时间，单位：秒；默认为片源结尾
            url_expire: 产物有效时间，单位为秒，默认一天，最大30天

        Returns:
            VideoEditResponse: 视频编辑结果响应

        Raises:
            APIError: 当视频裁剪失败时
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.video_trim, video, start_time, end_time, url_expire
        )