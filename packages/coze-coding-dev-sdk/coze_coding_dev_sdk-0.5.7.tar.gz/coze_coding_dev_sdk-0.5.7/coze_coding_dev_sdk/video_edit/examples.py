"""
视频编辑功能示例代码

本文件包含了 video_edit 模块的各种使用示例，包括：
1. 视频帧提取（关键帧、固定间隔、固定数量）
2. 视频剪辑（裁剪、拼接）
3. 字幕处理（添加字幕、音频转字幕）
4. 音频处理（提取音频、合成音视频）
"""

from coze_coding_dev_sdk.video_edit import (
    FrameExtractorClient,
    VideoEditClient,
    SubtitleConfig,
    FontPosConfig,
    TextItem,
    OutputSync,
)


def example_extract_by_key_frame():
    """示例1：按关键帧提取视频帧"""
    print("=" * 50)
    print("示例1：按关键帧提取视频帧")
    print("=" * 50)

    custom_headers = {"x-run-mode": "test_run"}
    client = FrameExtractorClient(custom_headers=custom_headers)

    response = client.extract_by_key_frame(
        url="https://example.com/video.mp4"
    )

    print(f"提取的关键帧数量: {len(response.data)}")
    for i, frame in enumerate(response.data[:3]):
        print(f"  帧 {i + 1}: 时间={frame.time}s, URL={frame.url}")
    print()


def example_extract_by_interval():
    """示例2：按固定时间间隔提取视频帧"""
    print("=" * 50)
    print("示例2：按固定时间间隔提取视频帧")
    print("=" * 50)

    custom_headers = {"x-run-mode": "test_run"}
    client = FrameExtractorClient(custom_headers=custom_headers)

    response = client.extract_by_interval(
        url="https://example.com/video.mp4",
        interval=2.0
    )

    print(f"每 2 秒提取一帧，共提取: {len(response.data)} 帧")
    for i, frame in enumerate(response.data[:3]):
        print(f"  帧 {i + 1}: 时间={frame.time}s, URL={frame.url}")
    print()


def example_extract_by_count():
    """示例3：按固定数量提取视频帧"""
    print("=" * 50)
    print("示例3：按固定数量提取视频帧")
    print("=" * 50)

    custom_headers = {"x-run-mode": "test_run"}
    client = FrameExtractorClient(custom_headers=custom_headers)

    response = client.extract_by_count(
        url="https://example.com/video.mp4",
        count=10
    )

    print(f"均匀提取 10 帧")
    for i, frame in enumerate(response.data):
        print(f"  帧 {i + 1}: 时间={frame.time}s, URL={frame.url}")
    print()


def example_video_trim():
    """示例4：视频裁剪"""
    print("=" * 50)
    print("示例4：视频裁剪")
    print("=" * 50)

    custom_headers = {"x-run-mode": "test_run"}
    client = VideoEditClient(custom_headers=custom_headers)

    response = client.video_trim(
        video="https://example.com/video.mp4",
        start_time=10.0,
        end_time=30.0,
        url_expire=3600
    )

    print(f"裁剪视频: 从 10 秒到 30 秒")
    print(f"结果 URL: {response.url}")
    print()


def example_concat_videos():
    """示例5：视频拼接"""
    print("=" * 50)
    print("示例5：视频拼接")
    print("=" * 50)

    custom_headers = {"x-run-mode": "test_run"}
    client = VideoEditClient(custom_headers=custom_headers)

    video_list = [
        "https://example.com/video1.mp4",
        "https://example.com/video2.mp4",
        "https://example.com/video3.mp4"
    ]

    response = client.concat_videos(
        video_list=video_list,
        url_expire=3600
    )

    print(f"拼接 {len(video_list)} 个视频")
    print(f"结果 URL: {response.url}")
    print()


def example_add_subtitles_with_text():
    """示例6：添加字幕（使用文本列表）"""
    print("=" * 50)
    print("示例6：添加字幕（使用文本列表）")
    print("=" * 50)

    custom_headers = {"x-run-mode": "test_run"}
    client = VideoEditClient(custom_headers=custom_headers)

    subtitle_config = SubtitleConfig(
        font_pos_config=FontPosConfig(
            pos_x="100",
            pos_y="900",
            width="1720",
            height="100"
        ),
        font_size=48,
        font_color="#FFFFFF",
        background_color="#000000",
        background_alpha=0.5
    )

    text_list = [
        TextItem(start_time=0.0, end_time=3.0, text="你好，世界！"),
        TextItem(start_time=3.0, end_time=6.0, text="欢迎使用视频编辑功能！"),
        TextItem(start_time=6.0, end_time=9.0, text="这是一个字幕示例。"),
    ]

    response = client.add_subtitles(
        video="https://example.com/video.mp4",
        subtitle_config=subtitle_config,
        text_list=text_list,
        url_expire=3600
    )

    print(f"添加了 {len(text_list)} 条字幕")
    print(f"结果 URL: {response.url}")
    print()


def example_add_subtitles_with_file():
    """示例7：添加字幕（使用字幕文件）"""
    print("=" * 50)
    print("示例7：添加字幕（使用字幕文件）")
    print("=" * 50)

    custom_headers = {"x-run-mode": "test_run"}
    client = VideoEditClient(custom_headers=custom_headers)

    subtitle_config = SubtitleConfig(
        font_pos_config=FontPosConfig(
            pos_x="0",
            pos_y="800",
            width="1920",
            height="200"
        ),
        font_size=36,
        font_color="#FFFF00"
    )

    response = client.add_subtitles(
        video="https://example.com/video.mp4",
        subtitle_config=subtitle_config,
        subtitle_url="https://example.com/subtitle.srt",
        url_expire=3600
    )

    print(f"使用字幕文件添加字幕")
    print(f"结果 URL: {response.url}")
    print()


def example_audio_to_subtitle():
    """示例8：音频转字幕"""
    print("=" * 50)
    print("示例8：音频转字幕")
    print("=" * 50)

    custom_headers = {"x-run-mode": "test_run"}
    client = VideoEditClient(custom_headers=custom_headers)

    response = client.audio_to_subtitle(
        audio="https://example.com/audio.mp3",
        url_expire=3600
    )

    print(f"音频转字幕完成")
    print(f"字幕文件 URL: {response.url}")
    print()


def example_audio_extract():
    """示例9：提取视频音频"""
    print("=" * 50)
    print("示例9：提取视频音频")
    print("=" * 50)
    
    custom_headers = {"x-run-mode": "test_run"}
    client = VideoEditClient(custom_headers=custom_headers)
    
    response = client.extract_audio(
        video="https://example.com/video.mp4",
        url_expire=3600
    )

    print(f"提取音频完成")
    print(f"音频文件 URL: {response.url}")
    print()


def example_compile_video_audio():
    """示例10：合成视频和音频"""
    print("=" * 50)
    print("示例10：合成视频和音频")
    print("=" * 50)

    custom_headers = {"x-run-mode": "test_run"}
    client = VideoEditClient(custom_headers=custom_headers)

    response = client.compile_video_audio(
        video="https://example.com/video_no_audio.mp4",
        audio="https://example.com/audio.mp3",
        url_expire=3600
    )

    print(f"合成视频和音频完成")
    print(f"结果 URL: {response.url}")
    print()


def example_async_operations():
    """示例11：异步操作示例"""
    print("=" * 50)
    print("示例11：异步操作示例")
    print("=" * 50)

    import asyncio

    async def async_example():
        custom_headers = {"x-run-mode": "test_run"}
        frame_client = FrameExtractorClient(custom_headers=custom_headers)
        edit_client = VideoEditClient(custom_headers=custom_headers)

        frame_response = await frame_client.extract_by_key_frame_async(
            url="https://example.com/video.mp4"
        )
        print(f"异步提取关键帧: {len(frame_response.data)} 帧")

        trim_response = await edit_client.video_trim_async(
            video="https://example.com/video.mp4",
            start_time=5.0,
            end_time=15.0
        )
        print(f"异步裁剪视频: {trim_response.url}")

    asyncio.run(async_example())
    print()


def example_with_output_sync():
    """示例12：使用同步输出配置"""
    print("=" * 50)
    print("示例12：使用同步输出配置")
    print("=" * 50)

    custom_headers = {"x-run-mode": "test_run"}
    client = VideoEditClient(custom_headers=custom_headers)

    output_sync = OutputSync(
        bucket="my-bucket",
        key="output/trimmed_video.mp4"
    )

    response = client.video_trim(
        video="https://example.com/video.mp4",
        start_time=0.0,
        end_time=10.0,
        output_sync=output_sync
    )

    print(f"视频已同步到指定位置")
    print(f"结果 URL: {response.url}")
    print()


def main():
    """运行所有示例"""
    print("\n" + "=" * 50)
    print("视频编辑功能示例集合")
    print("=" * 50 + "\n")

    try:
        example_extract_by_key_frame()
        example_extract_by_interval()
        example_extract_by_count()
        example_video_trim()
        example_concat_videos()
        example_add_subtitles_with_text()
        example_add_subtitles_with_file()
        example_audio_to_subtitle()
        example_audio_extract()
        example_compile_video_audio()
        example_async_operations()
        example_with_output_sync()

        print("=" * 50)
        print("所有示例运行完成！")
        print("=" * 50)

    except Exception as e:
        print(f"\n运行示例时出错: {e}")


if __name__ == "__main__":
    main()
