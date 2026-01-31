import json
import os
from typing import Optional

import click
from coze_coding_utils.runtime_ctx.context import new_context
from rich.console import Console

from ..core.config import Config
from ..embedding import EmbeddingClient
from .constants import RUN_MODE_HEADER, RUN_MODE_TEST

console = Console()


@click.command()
@click.option(
    "--text",
    "-t",
    multiple=True,
    help="Text to embed (can be used multiple times)",
)
@click.option(
    "--image-url",
    multiple=True,
    help="Image URL to embed (can be used multiple times)",
)
@click.option(
    "--video-url",
    multiple=True,
    help="Video URL to embed (can be used multiple times)",
)
@click.option(
    "--dimensions",
    "-d",
    type=int,
    help="Output embedding dimensions",
)
@click.option(
    "--instructions",
    help="Instructions for embedding generation",
)
@click.option(
    "--multi-embedding",
    is_flag=True,
    help="Enable multi-embedding mode",
)
@click.option(
    "--sparse-embedding",
    is_flag=True,
    help="Enable sparse embedding mode",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file path for embedding JSON",
)
@click.option("--mock", is_flag=True, help="使用 mock 模式（测试运行）")
@click.option(
    "--header",
    "-H",
    multiple=True,
    help="自定义 HTTP 请求头 (格式: 'Key: Value' 或 'Key=Value'，可多次使用)",
)
@click.option("--verbose", "-v", is_flag=True, help="显示详细的 HTTP 请求日志")
def embedding(
    text: tuple,
    image_url: tuple,
    video_url: tuple,
    dimensions: Optional[int],
    instructions: Optional[str],
    multi_embedding: bool,
    sparse_embedding: bool,
    output: Optional[str],
    mock: bool,
    header: tuple,
    verbose: bool,
):
    """Generate embeddings for text, images, or videos using AI."""
    try:
        has_text = len(text) > 0
        has_image = len(image_url) > 0
        has_video = len(video_url) > 0

        if not has_text and not has_image and not has_video:
            console.print(
                "[red]Error: At least one of --text, --image-url, or --video-url is required[/red]"
            )
            raise click.Abort()

        from .utils import parse_headers

        config = Config()

        ctx = None
        custom_headers = parse_headers(header) or {}

        if mock:
            ctx = new_context(method="embedding.embed", headers=custom_headers)
            custom_headers[RUN_MODE_HEADER] = RUN_MODE_TEST
            console.print("[yellow]🧪 Mock 模式已启用（测试运行）[/yellow]")

        client = EmbeddingClient(
            config, ctx=ctx, custom_headers=custom_headers, verbose=verbose
        )

        console.print("[bold cyan]Generating embeddings...[/bold cyan]")

        if has_text:
            console.print(f"Texts: [yellow]{len(text)} items[/yellow]")
        if has_image:
            console.print(f"Images: [yellow]{len(image_url)} items[/yellow]")
        if has_video:
            console.print(f"Videos: [yellow]{len(video_url)} items[/yellow]")

        response = client.embed(
            texts=list(text) if has_text else None,
            image_urls=list(image_url) if has_image else None,
            video_urls=list(video_url) if has_video else None,
            dimensions=dimensions,
            instructions=instructions,
            multi_embedding=multi_embedding,
            sparse_embedding=sparse_embedding,
        )

        console.print(f"[green]✓[/green] Embeddings generated successfully!")
        console.print(f"Model: [cyan]{response.model}[/cyan]")

        if response.embedding:
            console.print(
                f"Embedding dimensions: [cyan]{len(response.embedding)}[/cyan]"
            )
            first_5 = response.embedding[:5]
            console.print(f"First 5 values: [dim]{first_5}...[/dim]")

        if response.multi_embeddings:
            console.print(
                f"Multi-embedding vectors: [cyan]{len(response.multi_embeddings)}[/cyan]"
            )

        if response.sparse_embeddings:
            console.print(
                f"Sparse embedding items: [cyan]{len(response.sparse_embeddings)}[/cyan]"
            )

        if response.usage:
            console.print(f"Tokens used: [dim]{response.usage.total_tokens}[/dim]")

        if output:
            os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True)

            output_data = {
                "object": response.object,
                "model": response.model,
                "id": response.id,
                "created": response.created,
            }

            if response.data:
                output_data["data"] = {
                    "object": response.data.object,
                    "index": response.data.index,
                }
                if response.data.embedding:
                    output_data["data"]["embedding"] = response.data.embedding
                if response.data.multi_embedding:
                    output_data["data"]["multi_embedding"] = response.data.multi_embedding
                if response.data.sparse_embedding:
                    output_data["data"]["sparse_embedding"] = [
                        {"index": item.index, "value": item.value}
                        for item in response.data.sparse_embedding
                    ]

            if response.usage:
                output_data["usage"] = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
                if response.usage.prompt_tokens_details:
                    output_data["usage"]["prompt_tokens_details"] = {
                        "image_tokens": response.usage.prompt_tokens_details.image_tokens,
                        "text_tokens": response.usage.prompt_tokens_details.text_tokens,
                    }

            with open(output, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            console.print(f"[green]✓[/green] Embedding saved to: [bold]{output}[/bold]")

    except Exception as e:
        console.print(f"[red]✗ Error: {str(e)}[/red]")
        raise click.Abort()
