"""Media management commands."""

import mimetypes
from pathlib import Path

import typer
import httpx
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from mushu.config import get_auth_token, get_config

app = typer.Typer(help="Media management commands")
console = Console()


def get_headers() -> dict:
    """Get auth headers."""
    token = get_auth_token()
    if not token:
        console.print("[red]Not authenticated. Run 'mushu auth login' first.[/red]")
        raise typer.Exit(1)
    return {"Authorization": f"Bearer {token}"}


@app.command("upload")
def upload(
    file_path: Path = typer.Argument(..., help="Path to image or video file"),
    org_id: str = typer.Option(
        None, "--org", "-o", help="Organization ID (uses default if not specified)"
    ),
    tenant_id: str = typer.Option(
        None, "--tenant", "-t", help="Tenant ID (optional, for tenant-specific media)"
    ),
):
    """Upload an image or video file."""
    config = get_config()

    # Use default org if not specified
    org_id = org_id or config.default_org
    if not org_id:
        console.print("[red]No org specified. Use --org or set default with 'mushu org use'[/red]")
        raise typer.Exit(1)

    if not file_path.exists():
        console.print(f"[red]File not found: {file_path}[/red]")
        raise typer.Exit(1)

    # Detect content type
    content_type, _ = mimetypes.guess_type(str(file_path))
    if not content_type:
        console.print("[red]Could not determine file type[/red]")
        raise typer.Exit(1)

    is_video = content_type.startswith("video/")
    is_image = content_type.startswith("image/")

    if not is_video and not is_image:
        console.print(f"[red]Unsupported file type: {content_type}[/red]")
        console.print("[dim]Supported: images (jpg, png, gif, webp) and videos (mp4, mov)[/dim]")
        raise typer.Exit(1)

    headers = get_headers()
    file_size = file_path.stat().st_size
    filename = file_path.name

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        try:
            if is_video:
                # Video upload flow (Cloudflare Stream)
                task = progress.add_task("Getting upload URL...", total=100)

                with httpx.Client(timeout=30) as client:
                    payload = {
                        "org_id": org_id,
                        "filename": filename,
                        "max_duration_seconds": 3600,
                    }
                    if tenant_id:
                        payload["tenant_id"] = tenant_id

                    response = client.post(
                        f"{config.media_url}/media/video/upload-url",
                        headers=headers,
                        json=payload,
                    )

                if response.status_code != 200:
                    console.print(f"[red]Failed to get upload URL: {response.text}[/red]")
                    raise typer.Exit(1)

                data = response.json()
                media_id = data["media_id"]
                video_id = data["video_id"]
                upload_url = data["upload_url"]

                progress.update(task, completed=10, description="Uploading to Stream...")

                # Upload to Stream
                with open(file_path, "rb") as f:
                    file_data = f.read()

                with httpx.Client(timeout=300) as client:
                    response = client.post(
                        upload_url,
                        files={"file": (filename, file_data, content_type)},
                    )

                if response.status_code not in (200, 201):
                    console.print(f"[red]Upload failed: {response.text}[/red]")
                    raise typer.Exit(1)

                progress.update(task, completed=100, description="Done!")

                console.print("\n[green]Video uploaded successfully![/green]")
                console.print(f"  Media ID: {media_id}")
                console.print(f"  Video ID: {video_id}")
                console.print(
                    "[dim]  Video is processing. Use 'mushu media get' to check status.[/dim]"
                )

            else:
                # Image upload flow (R2)
                task = progress.add_task("Getting upload URL...", total=100)

                with httpx.Client(timeout=30) as client:
                    payload = {
                        "org_id": org_id,
                        "filename": filename,
                        "content_type": content_type,
                        "size_bytes": file_size,
                    }
                    if tenant_id:
                        payload["tenant_id"] = tenant_id

                    response = client.post(
                        f"{config.media_url}/media/upload-url",
                        headers=headers,
                        json=payload,
                    )

                if response.status_code != 200:
                    console.print(f"[red]Failed to get upload URL: {response.text}[/red]")
                    raise typer.Exit(1)

                data = response.json()
                media_id = data["media_id"]
                upload_url = data["upload_url"]
                key = data["key"]

                progress.update(task, completed=10, description="Uploading to R2...")

                # Upload to R2
                with open(file_path, "rb") as f:
                    file_data = f.read()

                with httpx.Client(timeout=300) as client:
                    response = client.put(
                        upload_url,
                        content=file_data,
                        headers={"Content-Type": content_type},
                    )

                if response.status_code not in (200, 201):
                    console.print(f"[red]Upload failed: {response.status_code}[/red]")
                    raise typer.Exit(1)

                progress.update(task, completed=80, description="Confirming upload...")

                # Confirm upload
                with httpx.Client(timeout=30) as client:
                    response = client.post(
                        f"{config.media_url}/media/{media_id}/confirm",
                        headers=headers,
                    )

                if response.status_code != 200:
                    console.print(f"[red]Failed to confirm upload: {response.text}[/red]")
                    raise typer.Exit(1)

                progress.update(task, completed=100, description="Done!")

                console.print("\n[green]Image uploaded successfully![/green]")
                console.print(f"  Media ID: {media_id}")
                console.print(f"  Key: {key}")
                console.print("\n  Variants:")
                console.print(f"    Original:  {config.images_url}/t/original/{key}")
                console.print(f"    Thumbnail: {config.images_url}/t/thumbnail/{key}")
                console.print(f"    Small:     {config.images_url}/t/small/{key}")
                console.print(f"    Medium:    {config.images_url}/t/medium/{key}")
                console.print(f"    Large:     {config.images_url}/t/large/{key}")

        except httpx.RequestError as e:
            console.print(f"[red]Network error: {e}[/red]")
            raise typer.Exit(1)


@app.command("list")
def list_media(
    org_id: str = typer.Option(
        None, "--org", "-o", help="Organization ID (uses default if not specified)"
    ),
    tenant_id: str = typer.Option(None, "--tenant", "-t", help="Filter by tenant ID"),
    media_type: str = typer.Option(None, "--type", help="Filter by type (image, video)"),
):
    """List media items for an organization."""
    config = get_config()

    org_id = org_id or config.default_org
    if not org_id:
        console.print("[red]No org specified. Use --org or set default with 'mushu org use'[/red]")
        raise typer.Exit(1)

    headers = get_headers()

    try:
        with httpx.Client(timeout=30) as client:
            if tenant_id:
                url = f"{config.media_url}/media/tenant/{tenant_id}?org_id={org_id}"
            else:
                url = f"{config.media_url}/media/org/{org_id}"

            response = client.get(url, headers=headers)

        if response.status_code != 200:
            console.print(f"[red]Failed to list media: {response.text}[/red]")
            raise typer.Exit(1)

        data = response.json()
        items = data.get("items", [])

        # Filter by type if specified
        if media_type:
            items = [i for i in items if i["media_type"] == media_type]

        if not items:
            console.print("[dim]No media found[/dim]")
            return

        table = Table(title="Media Items")
        table.add_column("ID", style="cyan")
        table.add_column("Filename")
        table.add_column("Type")
        table.add_column("Status")
        table.add_column("Size")
        table.add_column("Created")

        for item in items:
            size = format_bytes(item["size_bytes"])
            created = item["created_at"][:10]  # Just the date
            status_style = "green" if item["status"] == "ready" else "yellow"

            table.add_row(
                item["media_id"][:12] + "...",
                item["filename"][:30] + ("..." if len(item["filename"]) > 30 else ""),
                item["media_type"],
                f"[{status_style}]{item['status']}[/{status_style}]",
                size,
                created,
            )

        console.print(table)
        console.print(f"\n[dim]Total: {len(items)} items[/dim]")

    except httpx.RequestError as e:
        console.print(f"[red]Network error: {e}[/red]")
        raise typer.Exit(1)


@app.command("get")
def get_media(
    media_id: str = typer.Argument(..., help="Media ID"),
):
    """Get details for a media item."""
    config = get_config()
    headers = get_headers()

    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(
                f"{config.media_url}/media/{media_id}",
                headers=headers,
            )

        if response.status_code == 404:
            console.print("[red]Media not found[/red]")
            raise typer.Exit(1)

        if response.status_code != 200:
            console.print(f"[red]Failed to get media: {response.text}[/red]")
            raise typer.Exit(1)

        item = response.json()

        console.print("\n[bold]Media Details[/bold]")
        console.print(f"  ID:           {item['media_id']}")
        console.print(f"  Filename:     {item['filename']}")
        console.print(f"  Type:         {item['media_type']}")
        console.print(f"  Content-Type: {item['content_type']}")
        console.print(f"  Size:         {format_bytes(item['size_bytes'])}")
        console.print(f"  Status:       {item['status']}")
        console.print(f"  Organization: {item['org_id']}")
        if item.get("tenant_id"):
            console.print(f"  Tenant:       {item['tenant_id']}")
        console.print(f"  Created:      {item['created_at']}")

        # Get variant URLs for images
        if item["media_type"] == "image" and item["status"] == "ready":
            try:
                response = client.get(
                    f"{config.media_url}/media/{media_id}/images",
                    headers=headers,
                )
                if response.status_code == 200:
                    urls = response.json()
                    console.print("\n[bold]Image Variants[/bold]")
                    console.print(f"  Original:  {urls['original']}")
                    console.print(f"  Thumbnail: {urls['thumbnail']}")
                    console.print(f"  Small:     {urls['small']}")
                    console.print(f"  Medium:    {urls['medium']}")
                    console.print(f"  Large:     {urls['large']}")
            except Exception:
                pass

        # Get video info
        if item["media_type"] == "video":
            try:
                response = client.get(
                    f"{config.media_url}/media/{media_id}/video",
                    headers=headers,
                )
                if response.status_code == 200:
                    video = response.json()
                    console.print("\n[bold]Video Info[/bold]")
                    console.print(f"  Video ID:    {video['video_id']}")
                    console.print(f"  Status:      {video['status']}")
                    console.print(f"  Ready:       {'Yes' if video['ready_to_stream'] else 'No'}")
                    if video.get("duration"):
                        console.print(f"  Duration:    {format_duration(video['duration'])}")
                    if video.get("playback_hls"):
                        console.print(f"  HLS URL:     {video['playback_hls']}")
                    if video.get("playback_dash"):
                        console.print(f"  DASH URL:    {video['playback_dash']}")
            except Exception:
                pass

    except httpx.RequestError as e:
        console.print(f"[red]Network error: {e}[/red]")
        raise typer.Exit(1)


@app.command("delete")
def delete_media(
    media_id: str = typer.Argument(..., help="Media ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete a media item."""
    config = get_config()
    headers = get_headers()

    if not force:
        confirm = typer.confirm(f"Delete media {media_id}?")
        if not confirm:
            raise typer.Abort()

    try:
        with httpx.Client(timeout=30) as client:
            response = client.delete(
                f"{config.media_url}/media/{media_id}",
                headers=headers,
            )

        if response.status_code == 404:
            console.print("[red]Media not found[/red]")
            raise typer.Exit(1)

        if response.status_code != 200:
            console.print(f"[red]Failed to delete media: {response.text}[/red]")
            raise typer.Exit(1)

        console.print("[green]Media deleted[/green]")

    except httpx.RequestError as e:
        console.print(f"[red]Network error: {e}[/red]")
        raise typer.Exit(1)


@app.command("url")
def get_url(
    media_id: str = typer.Argument(..., help="Media ID"),
    variant: str = typer.Option(
        "original",
        "--variant",
        "-v",
        help="Image variant (original, thumbnail, small, medium, large)",
    ),
):
    """Get download URL for a media item."""
    config = get_config()
    headers = get_headers()

    try:
        with httpx.Client(timeout=30) as client:
            # First get the media info
            response = client.get(
                f"{config.media_url}/media/{media_id}",
                headers=headers,
            )

        if response.status_code == 404:
            console.print("[red]Media not found[/red]")
            raise typer.Exit(1)

        if response.status_code != 200:
            console.print(f"[red]Failed to get media: {response.text}[/red]")
            raise typer.Exit(1)

        item = response.json()

        if item["media_type"] == "image" and item["status"] == "ready":
            # Get image variant URLs
            response = client.get(
                f"{config.media_url}/media/{media_id}/images",
                headers=headers,
            )
            if response.status_code == 200:
                urls = response.json()
                url = urls.get(variant, urls["original"])
                console.print(url)
            else:
                console.print("[red]Failed to get URLs[/red]")
                raise typer.Exit(1)

        elif item["media_type"] == "video":
            # Get video playback URL
            response = client.get(
                f"{config.media_url}/media/{media_id}/video",
                headers=headers,
            )
            if response.status_code == 200:
                video = response.json()
                if video.get("playback_hls"):
                    console.print(video["playback_hls"])
                else:
                    console.print(
                        f"[yellow]Video not ready yet. Status: {video['status']}[/yellow]"
                    )
            else:
                console.print("[red]Failed to get video info[/red]")
                raise typer.Exit(1)

        else:
            # Get presigned download URL
            response = client.get(
                f"{config.media_url}/media/{media_id}/url",
                headers=headers,
            )
            if response.status_code == 200:
                data = response.json()
                console.print(data["url"])
            else:
                console.print("[red]Failed to get URL[/red]")
                raise typer.Exit(1)

    except httpx.RequestError as e:
        console.print(f"[red]Network error: {e}[/red]")
        raise typer.Exit(1)


def format_bytes(size: int) -> str:
    """Format bytes to human readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def format_duration(seconds: float) -> str:
    """Format seconds to mm:ss."""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins}:{secs:02d}"
