import json
import os
from typing import Optional

import click
from coze_coding_utils.runtime_ctx.context import new_context
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from sqlalchemy import True_

from ..core.config import Config
from ..core.exceptions import APIError
from ..video_edit import (
    FrameExtractorClient,
    VideoEditClient,
    SubtitleConfig,
    FontPosConfig,
    TextItem,
)
from .constants import RUN_MODE_HEADER, RUN_MODE_TEST

console = Console()


@click.group()
def video_edit():
    """视频编辑工具集"""
    pass


@video_edit.command()
@click.option("--url", "-u", required=True, help="视频 URL")
@click.option("--output", "-o", type=click.Path(), help="输出文件路径（JSON）")
@click.option("--mock", is_flag=True, help="使用 mock 模式（测试运行）")
@click.option(
    "--header",
    "-H",
    multiple=True,
    help="自定义 HTTP 请求头 (格式: 'Key: Value' 或 'Key=Value'，可多次使用)",
)
@click.option("--verbose", "-v", is_flag=True, help="显示详细的 HTTP 请求日志")
def extract_keyframe(
    url: str,
    output: Optional[str],
    mock: bool,
    header: tuple,
    verbose: bool,
):
    """按关键帧提取视频帧"""
    try:
        from .utils import parse_headers

        config = Config()

        ctx = None
        custom_headers = parse_headers(header) or {}

        if mock:
            ctx = new_context(method="video_edit.extract_keyframe", headers=custom_headers)
            custom_headers[RUN_MODE_HEADER] = RUN_MODE_TEST
            console.print("[yellow]🧪 Mock 模式已启用（测试运行）[/yellow]")

        client = FrameExtractorClient(
            config, ctx=ctx, custom_headers=custom_headers, verbose=verbose
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]提取关键帧中...", total=None)

            try:
                response = client.extract_by_key_frame(url=url)
                progress.update(task, description="[green]✓ 关键帧提取完成!")

            except APIError as e:
                progress.update(task, description="[red]✗ 关键帧提取失败")
                console.print(f"[red]错误: {str(e)}[/red]")
                raise click.Abort()

        table = Table(title="关键帧提取结果")
        table.add_column("索引", style="cyan", no_wrap=True)
        table.add_column("时间 (秒)", style="yellow")
        table.add_column("URL", style="green", overflow="fold")

        for frame in response.data.chunks[:10]:
            table.add_row(
                str(frame.index),
                f"{frame.timestamp_ms:.2f}",
                frame.screenshot
            )

        if len(response.data.chunks) > 10:
            table.add_row("...", "...", f"(还有 {len(response.data.chunks) - 10} 帧)")

        console.print(table)
        console.print(f"\n[cyan]总共提取了 {len(response.data.chunks)} 帧[/cyan]")

        if output:
            result = {
                "code": response.code,
                "message": response.message,
                "log_id": response.log_id,
                "frames": [
                    {
                        "index": frame.index,
                        "time": frame.timestamp_ms,
                        "url": frame.screenshot
                    }
                    for frame in response.data.chunks
                ]
            }
            with open(output, "w") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            console.print(f"\n[green]✓[/green] 结果已保存到: {output}")

    except Exception as e:
        console.print(f"[red]✗ 错误: {str(e)}[/red]")
        raise click.Abort()


@video_edit.command()
@click.option("--url", "-u", required=True, help="视频 URL")
@click.option("--interval", "-i", required=True, type=int, help="抽帧间隔（毫秒）")
@click.option("--output", "-o", type=click.Path(), help="输出文件路径（JSON）")
@click.option("--mock", is_flag=True, help="使用 mock 模式（测试运行）")
@click.option(
    "--header",
    "-H",
    multiple=True,
    help="自定义 HTTP 请求头 (格式: 'Key: Value' 或 'Key=Value'，可多次使用)",
)
@click.option("--verbose", "-v", is_flag=True, help="显示详细的 HTTP 请求日志")
def extract_interval(
    url: str,
    interval: int,
    output: Optional[str],
    mock: bool,
    header: tuple,
    verbose: bool,
):
    """按固定时间间隔提取视频帧"""
    try:
        from .utils import parse_headers

        config = Config()

        ctx = None
        custom_headers = parse_headers(header) or {}

        if mock:
            ctx = new_context(method="video_edit.extract_interval", headers=custom_headers)
            custom_headers[RUN_MODE_HEADER] = RUN_MODE_TEST
            console.print("[yellow]🧪 Mock 模式已启用（测试运行）[/yellow]")

        client = FrameExtractorClient(
            config, ctx=ctx, custom_headers=custom_headers, verbose=verbose
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"[cyan]按 {interval} 秒间隔提取帧中...", total=None)

            try:
                response = client.extract_by_interval(url=url, interval_ms=interval)
                progress.update(task, description="[green]✓ 间隔抽帧完成!")

            except APIError as e:
                progress.update(task, description="[red]✗ 间隔抽帧失败")
                console.print(f"[red]错误: {str(e)}[/red]")
                raise click.Abort()

        table = Table(title=f"间隔抽帧结果 (每 {interval} 秒)")
        table.add_column("索引", style="cyan", no_wrap=True)
        table.add_column("时间 (秒)", style="yellow")
        table.add_column("URL", style="green", overflow="fold")

        for frame in response.data.chunks[:10]:
            table.add_row(
                str(frame.index),
                f"{frame.timestamp_ms:.2f}",
                frame.screenshot
            )

        if len(response.data.chunks) > 10:
            table.add_row("...", "...", f"(还有 {len(response.data.chunks) - 10} 帧)")

        console.print(table)
        console.print(f"\n[cyan]总共提取了 {len(response.data.chunks)} 帧[/cyan]")

        if output:
            result = {
                "code": response.code,
                "message": response.message,
                "log_id": response.log_id,
                "interval": interval,
                "frames": [
                    {
                        "index": frame.index,
                        "time": frame.timestamp_ms,
                        "url": frame.screenshot
                    }
                    for frame in response.data.chunks
                ]
            }
            with open(output, "w") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            console.print(f"\n[green]✓[/green] 结果已保存到: {output}")

    except Exception as e:
        console.print(f"[red]✗ 错误: {str(e)}[/red]")
        raise click.Abort()


@video_edit.command()
@click.option("--url", "-u", required=True, help="视频 URL")
@click.option("--count", "-c", required=True, type=int, help="提取帧数")
@click.option("--output", "-o", type=click.Path(), help="输出文件路径（JSON）")
@click.option("--mock", is_flag=True, help="使用 mock 模式（测试运行）")
@click.option(
    "--header",
    "-H",
    multiple=True,
    help="自定义 HTTP 请求头 (格式: 'Key: Value' 或 'Key=Value'，可多次使用)",
)
@click.option("--verbose", "-v", is_flag=True, help="显示详细的 HTTP 请求日志")
def extract_count(
    url: str,
    count: int,
    output: Optional[str],
    mock: bool,
    header: tuple,
    verbose: bool,
):
    """按固定数量提取视频帧"""
    try:
        from .utils import parse_headers

        config = Config()

        ctx = None
        custom_headers = parse_headers(header) or {}

        if mock:
            ctx = new_context(method="video_edit.extract_count", headers=custom_headers)
            custom_headers[RUN_MODE_HEADER] = RUN_MODE_TEST
            console.print("[yellow]🧪 Mock 模式已启用（测试运行）[/yellow]")

        client = FrameExtractorClient(
            config, ctx=ctx, custom_headers=custom_headers, verbose=verbose
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"[cyan]提取 {count} 帧中...", total=None)

            try:
                response = client.extract_by_count(url=url, count=count)
                progress.update(task, description="[green]✓ 定量抽帧完成!")

            except APIError as e:
                progress.update(task, description="[red]✗ 定量抽帧失败")
                console.print(f"[red]错误: {str(e)}[/red]")
                raise click.Abort()

        table = Table(title=f"定量抽帧结果 (共 {count} 帧)")
        table.add_column("索引", style="cyan", no_wrap=True)
        table.add_column("时间 (秒)", style="yellow")
        table.add_column("URL", style="green", overflow="fold")

        for frame in response.data.chunks:
            table.add_row(
                str(frame.index),
                f"{frame.timestamp_ms:.2f}",
                frame.screenshot
            )

        console.print(table)

        if output:
            result = {
                "code": response.code,
                "message": response.message,
                "log_id": response.log_id,
                "count": count,
                "frames": [
                    {
                        "index": frame.index,
                        "time": frame.timestamp_ms,
                        "url": frame.screenshot
                    }
                    for frame in response.data.chunks
                ]
            }
            with open(output, "w") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            console.print(f"\n[green]✓[/green] 结果已保存到: {output}")

    except Exception as e:
        console.print(f"[red]✗ 错误: {str(e)}[/red]")
        raise click.Abort()


@video_edit.command()
@click.option("--video", "-v", required=True, help="视频 URL")
@click.option("--start", "-s", required=True, type=float, help="开始时间（秒）")
@click.option("--end", "-e", required=True, type=float, help="结束时间（秒）")
@click.option("--output", "-o", type=click.Path(), help="输出文件路径（JSON）")
@click.option("--mock", is_flag=True, help="使用 mock 模式（测试运行）")
@click.option(
    "--header",
    "-H",
    multiple=True,
    help="自定义 HTTP 请求头 (格式: 'Key: Value' 或 'Key=Value'，可多次使用)",
)
@click.option("--verbose", is_flag=True, help="显示详细的 HTTP 请求日志")
def trim(
    video: str,
    start: float,
    end: float,
    output: Optional[str],
    mock: bool,
    header: tuple,
    verbose: bool,
):
    """裁剪视频"""
    try:
        from .utils import parse_headers

        config = Config()

        ctx = None
        custom_headers = parse_headers(header) or {}

        if mock:
            ctx = new_context(method="video_edit.trim", headers=custom_headers)
            custom_headers[RUN_MODE_HEADER] = RUN_MODE_TEST
            console.print("[yellow]🧪 Mock 模式已启用（测试运行）[/yellow]")

        client = VideoEditClient(
            config, ctx=ctx, custom_headers=custom_headers, verbose=verbose
        )

        console.print(f"[cyan]裁剪视频: {start}s - {end}s (时长: {end - start}s)[/cyan]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]裁剪视频中...", total=None)

            try:
                response = client.video_trim(
                    video=video,
                    start_time=start,
                    end_time=end
                )
                progress.update(task, description="[green]✓ 视频裁剪完成!")

            except APIError as e:
                progress.update(task, description="[red]✗ 视频裁剪失败")
                console.print(f"[red]错误: {str(e)}[/red]")
                raise click.Abort()

        table = Table(title="视频裁剪结果")
        table.add_column("字段", style="cyan", no_wrap=True)
        table.add_column("值", style="green", overflow="fold")

        table.add_row("请求 ID", response.req_id)
        table.add_row("视频 URL", response.url)
        if response.message:
            table.add_row("消息", response.message)
        if response.video_meta:
            table.add_row("时长", f"{response.video_meta.duration:.2f}s")
            table.add_row("分辨率", response.video_meta.resolution)

        console.print(table)
        console.print(f"\n[cyan]完整视频 URL:[/cyan]")
        console.print(f"[green]{response.url}[/green]")

        if output:
            result = {
                "req_id": response.req_id,
                "url": response.url,
                "message": response.message,
                "video_meta": {
                    "duration": response.video_meta.duration,
                    "resolution": response.video_meta.resolution,
                    "type": response.video_meta.type
                } if response.video_meta else None
            }
            with open(output, "w") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            console.print(f"\n[green]✓[/green] 结果已保存到: {output}")

    except Exception as e:
        console.print(f"[red]✗ 错误: {str(e)}[/red]")
        raise click.Abort()


@video_edit.command()
@click.option("--videos", "-v", required=True, help="视频 URL 列表（逗号分隔）")
@click.option("--output", "-o", type=click.Path(), help="输出文件路径（JSON）")
@click.option("--mock", is_flag=True, help="使用 mock 模式（测试运行）")
@click.option(
    "--header",
    "-H",
    multiple=True,
    help="自定义 HTTP 请求头 (格式: 'Key: Value' 或 'Key=Value'，可多次使用)",
)
@click.option("--verbose", is_flag=True, help="显示详细的 HTTP 请求日志")
def concat(
    videos: str,
    output: Optional[str],
    mock: bool,
    header: tuple,
    verbose: bool,
):
    """拼接多个视频"""
    try:
        from .utils import parse_headers

        config = Config()

        ctx = None
        custom_headers = parse_headers(header) or {}

        if mock:
            ctx = new_context(method="video_edit.concat", headers=custom_headers)
            custom_headers[RUN_MODE_HEADER] = RUN_MODE_TEST
            console.print("[yellow]🧪 Mock 模式已启用（测试运行）[/yellow]")

        client = VideoEditClient(
            config, ctx=ctx, custom_headers=custom_headers, verbose=verbose
        )

        video_list = [v.strip() for v in videos.split(",")]
        console.print(f"[cyan]拼接 {len(video_list)} 个视频[/cyan]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]拼接视频中...", total=None)

            try:
                response = client.concat_videos(videos=video_list)
                progress.update(task, description="[green]✓ 视频拼接完成!")

            except APIError as e:
                progress.update(task, description="[red]✗ 视频拼接失败")
                console.print(f"[red]错误: {str(e)}[/red]")
                raise click.Abort()

        table = Table(title="视频拼接结果")
        table.add_column("字段", style="cyan", no_wrap=True)
        table.add_column("值", style="green", overflow="fold")

        table.add_row("请求 ID", response.req_id)
        table.add_row("视频 URL", response.url)
        if response.message:
            table.add_row("消息", response.message)
        if response.video_meta:
            table.add_row("时长", f"{response.video_meta.duration:.2f}s")
            table.add_row("分辨率", response.video_meta.resolution)

        console.print(table)
        console.print(f"\n[cyan]完整视频 URL:[/cyan]")
        console.print(f"[green]{response.url}[/green]")

        if output:
            result = {
                "req_id": response.req_id,
                "url": response.url,
                "message": response.message,
                "video_meta": {
                    "duration": response.video_meta.duration,
                    "resolution": response.video_meta.resolution,
                    "type": response.video_meta.type
                } if response.video_meta else None
            }
            with open(output, "w") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            console.print(f"\n[green]✓[/green] 结果已保存到: {output}")

    except Exception as e:
        console.print(f"[red]✗ 错误: {str(e)}[/red]")
        raise click.Abort()


@video_edit.command()
@click.option("--video", "-v", required=True, help="视频 URL")
@click.option("--subtitle", "-s", required=True, help="字幕文件 URL（SRT/VTT）")
@click.option("--text", "-t", help="文本内容（格式: start,end,text；多个用 | 分隔）")
@click.option("--font-size", type=int, default=40, help="字体大小")
@click.option("--font-color", default="#FFFFFFFF", help="字体颜色（十六进制）")
@click.option("--pos-x", default="0", help="字幕 X 坐标")
@click.option("--pos-y", default="90%", help="字幕 Y 坐标")
@click.option("--width", default="100%", help="字幕宽度")
@click.option("--height", default="10%", help="字幕高度")
@click.option("--output", "-o", type=click.Path(), help="输出文件路径（JSON）")
@click.option("--mock", is_flag=True, help="使用 mock 模式（测试运行）")
@click.option(
    "--header",
    "-H",
    multiple=True,
    help="自定义 HTTP 请求头 (格式: 'Key: Value' 或 'Key=Value'，可多次使用)",
)
@click.option("--verbose", is_flag=True, help="显示详细的 HTTP 请求日志")
def add_subtitle(
    video: str,
    subtitle: Optional[str],
    text: Optional[str],
    font_size: Optional[int],
    font_color: Optional[str],
    pos_x: Optional[str],
    pos_y: Optional[str],
    width: Optional[str],
    height: Optional[str],
    output: Optional[str],
    mock: bool,
    header: tuple,
    verbose: bool,
):
    """为视频添加字幕"""
    try:
        from .utils import parse_headers

        if not subtitle and not text:
            console.print("[red]错误: 必须提供 --subtitle 或 --text 参数[/red]")
            raise click.Abort()

        config = Config()

        ctx = None
        custom_headers = parse_headers(header) or {}

        if mock:
            ctx = new_context(method="video_edit.add_subtitle", headers=custom_headers)
            custom_headers[RUN_MODE_HEADER] = RUN_MODE_TEST
            console.print("[yellow]🧪 Mock 模式已启用（测试运行）[/yellow]")

        client = VideoEditClient(
            config, ctx=ctx, custom_headers=custom_headers, verbose=verbose
        )

        subtitle_config = SubtitleConfig(
            font_pos_config=FontPosConfig(
                pos_x=pos_x,
                pos_y=pos_y,
                width=width,
                height=height
            ),
            font_size=font_size,
            font_color=font_color
        )

        text_list = None
        subtitle_url = None

        if text:
            text_list = []
            for item in text.split("|"):
                parts = item.strip().split(",", 2)
                if len(parts) == 3:
                    start_time, end_time, text_content = parts
                    text_list.append(TextItem(
                        start_time=float(start_time),
                        end_time=float(end_time),
                        text=text_content
                    ))
            console.print(f"[cyan]添加 {len(text_list)} 条文本字幕[/cyan]")
        elif subtitle:
            console.print(f"[cyan]使用字幕文件: {subtitle}[/cyan]")
            subtitle_url = subtitle

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]添加字幕中...", total=None)

            try:
                response = client.add_subtitles(
                    video=video,
                    subtitle_config=subtitle_config,
                    subtitle_url=subtitle_url,
                    text_list=text_list
                )
                progress.update(task, description="[green]✓ 字幕添加完成!")

            except APIError as e:
                progress.update(task, description="[red]✗ 字幕添加失败")
                console.print(f"[red]错误: {str(e)}[/red]")
                raise click.Abort()

        table = Table(title="字幕添加结果")
        table.add_column("字段", style="cyan", no_wrap=True)
        table.add_column("值", style="green", overflow="fold")

        table.add_row("请求 ID", response.req_id)
        table.add_row("视频 URL", response.url)
        if response.message:
            table.add_row("消息", response.message)

        console.print(table)
        console.print(f"\n[cyan]完整视频 URL:[/cyan]")
        console.print(f"[green]{response.url}[/green]")

        if output:
            result = {
                "req_id": response.req_id,
                "url": response.url,
                "message": response.message
            }
            with open(output, "w") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            console.print(f"\n[green]✓[/green] 结果已保存到: {output}")

    except Exception as e:
        console.print(f"[red]✗ 错误: {str(e)}[/red]")
        raise click.Abort()


@video_edit.command()
@click.option("--video", "-v", required=True, help="视频 URL")
@click.option("--output", "-o", type=click.Path(), help="输出文件路径（JSON）")
@click.option("--mock", is_flag=True, help="使用 mock 模式（测试运行）")
@click.option(
    "--header",
    "-H",
    multiple=True,
    help="自定义 HTTP 请求头 (格式: 'Key: Value' 或 'Key=Value'，可多次使用)",
)
@click.option("--verbose", is_flag=True, help="显示详细的 HTTP 请求日志")
def extract_audio(
    video: str,
    output: Optional[str],
    mock: bool,
    header: tuple,
    verbose: bool,
):
    """从视频中提取音频"""
    try:
        from .utils import parse_headers

        config = Config()

        ctx = None
        custom_headers = parse_headers(header) or {}

        if mock:
            ctx = new_context(method="video_edit.extract_audio", headers=custom_headers)
            custom_headers[RUN_MODE_HEADER] = RUN_MODE_TEST
            console.print("[yellow]🧪 Mock 模式已启用（测试运行）[/yellow]")

        client = VideoEditClient(
            config, ctx=ctx, custom_headers=custom_headers, verbose=verbose
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]提取音频中...", total=None)

            try:
                response = client.extract_audio(video=video)
                progress.update(task, description="[green]✓ 音频提取完成!")

            except APIError as e:
                progress.update(task, description="[red]✗ 音频提取失败")
                console.print(f"[red]错误: {str(e)}[/red]")
                raise click.Abort()

        table = Table(title="音频提取结果")
        table.add_column("字段", style="cyan", no_wrap=True)
        table.add_column("值", style="green", overflow="fold")

        table.add_row("请求 ID", response.req_id)
        table.add_row("音频 URL", response.url)
        if response.message:
            table.add_row("消息", response.message)

        console.print(table)
        console.print(f"\n[cyan]完整音频 URL:[/cyan]")
        console.print(f"[green]{response.url}[/green]")

        if output:
            result = {
                "req_id": response.req_id,
                "url": response.url,
                "message": response.message
            }
            with open(output, "w") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            console.print(f"\n[green]✓[/green] 结果已保存到: {output}")

    except Exception as e:
        console.print(f"[red]✗ 错误: {str(e)}[/red]")
        raise click.Abort()


@video_edit.command()
@click.option("--audio", "-a", required=True, help="音频 URL")
@click.option("--output", "-o", type=click.Path(), help="输出文件路径（JSON）")
@click.option("--mock", is_flag=True, help="使用 mock 模式（测试运行）")
@click.option(
    "--header",
    "-H",
    multiple=True,
    help="自定义 HTTP 请求头 (格式: 'Key: Value' 或 'Key=Value'，可多次使用)",
)
@click.option("--verbose", is_flag=True, help="显示详细的 HTTP 请求日志")
def audio_to_subtitle(
    audio: str,
    output: Optional[str],
    mock: bool,
    header: tuple,
    verbose: bool,
):
    """将音频转换为字幕"""
    try:
        from .utils import parse_headers

        config = Config()

        ctx = None
        custom_headers = parse_headers(header) or {}

        if mock:
            ctx = new_context(method="video_edit.audio_to_subtitle", headers=custom_headers)
            custom_headers[RUN_MODE_HEADER] = RUN_MODE_TEST
            console.print("[yellow]🧪 Mock 模式已启用（测试运行）[/yellow]")

        client = VideoEditClient(
            config, ctx=ctx, custom_headers=custom_headers, verbose=verbose
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]音频转字幕中...", total=None)

            try:
                response = client.audio_to_subtitle(source=audio)
                progress.update(task, description="[green]✓ 音频转字幕完成!")

            except APIError as e:
                progress.update(task, description="[red]✗ 音频转字幕失败")
                console.print(f"[red]错误: {str(e)}[/red]")
                raise click.Abort()

        table = Table(title="音频转字幕结果")
        table.add_column("字段", style="cyan", no_wrap=True)
        table.add_column("值", style="green", overflow="fold")

        table.add_row("请求 ID", response.req_id)
        table.add_row("字幕 URL", response.url)
        if response.message:
            table.add_row("消息", response.message)

        console.print(table)
        console.print(f"\n[cyan]完整字幕 URL:[/cyan]")
        console.print(f"[green]{response.url}[/green]")

        if output:
            result = {
                "req_id": response.req_id,
                "url": response.url,
                "message": response.message
            }
            with open(output, "w") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            console.print(f"\n[green]✓[/green] 结果已保存到: {output}")

    except Exception as e:
        console.print(f"[red]✗ 错误: {str(e)}[/red]")
        raise click.Abort()


@video_edit.command()
@click.option("--video", "-v", required=True, help="视频 URL")
@click.option("--audio", "-a", required=True, help="音频 URL")
@click.option("--output", "-o", type=click.Path(), help="输出文件路径（JSON）")
@click.option("--mock", is_flag=True, help="使用 mock 模式（测试运行）")
@click.option(
    "--header",
    "-H",
    multiple=True,
    help="自定义 HTTP 请求头 (格式: 'Key: Value' 或 'Key=Value'，可多次使用)",
)
@click.option("--verbose", is_flag=True, help="显示详细的 HTTP 请求日志")
def merge_audio(
    video: str,
    audio: str,
    output: Optional[str],
    mock: bool,
    header: tuple,
    verbose: bool,
):
    """合成视频和音频"""
    try:
        from .utils import parse_headers

        config = Config()

        ctx = None
        custom_headers = parse_headers(header) or {}

        if mock:
            ctx = new_context(method="video_edit.merge_audio", headers=custom_headers)
            custom_headers[RUN_MODE_HEADER] = RUN_MODE_TEST
            console.print("[yellow]🧪 Mock 模式已启用（测试运行）[/yellow]")

        client = VideoEditClient(
            config, ctx=ctx, custom_headers=custom_headers, verbose=verbose
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]合成视频和音频中...", total=None)

            try:
                response = client.compile_video_audio(video=video, audio=audio)
                progress.update(task, description="[green]✓ 视频音频合成完成!")

            except APIError as e:
                progress.update(task, description="[red]✗ 视频音频合成失败")
                console.print(f"[red]错误: {str(e)}[/red]")
                raise click.Abort()

        table = Table(title="视频音频合成结果")
        table.add_column("字段", style="cyan", no_wrap=True)
        table.add_column("值", style="green", overflow="fold")

        table.add_row("请求 ID", response.req_id)
        table.add_row("视频 URL", response.url)
        if response.message:
            table.add_row("消息", response.message)
        if response.video_meta:
            table.add_row("时长", f"{response.video_meta.duration:.2f}s")
            table.add_row("分辨率", response.video_meta.resolution)

        console.print(table)
        console.print(f"\n[cyan]完整视频 URL:[/cyan]")
        console.print(f"[green]{response.url}[/green]")

        if output:
            result = {
                "req_id": response.req_id,
                "url": response.url,
                "message": response.message,
                "video_meta": {
                    "duration": response.video_meta.duration,
                    "resolution": response.video_meta.resolution,
                    "type": response.video_meta.type
                } if response.video_meta else None
            }
            with open(output, "w") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            console.print(f"\n[green]✓[/green] 结果已保存到: {output}")

    except Exception as e:
        console.print(f"[red]✗ 错误: {str(e)}[/red]")
        raise click.Abort()


if __name__ == "__main__":
    video_edit()
