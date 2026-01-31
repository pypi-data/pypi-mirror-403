"""Installation script for WebSocket extension."""

from pathlib import Path

from rich.console import Console

from paxx.templates.installer import TemplateInstaller

console = Console()


def install(project_path: Path, force: bool = False) -> None:
    """Install WebSocket extension.

    Args:
        project_path: Path to the project root.
        force: Whether to overwrite existing files.
    """
    installer = TemplateInstaller(project_path)
    component_dir = Path(__file__).parent

    # Copy templates to services/
    installer.copy_templates(component_dir / "templates", project_path / "services")

    # Add env vars
    installer.add_env_vars_from_file(component_dir / "env.json")

    # Print success and next steps
    installer.print_success("websocket")
    installer.print_next_steps()

    # WebSocket-specific usage instructions
    console.print()
    console.print("[bold]Basic WebSocket endpoint:[/bold]")
    console.print(
        "  [grey70]from fastapi import WebSocket, WebSocketDisconnect[/grey70]"
    )
    console.print("  [grey70]from services.ws import manager[/grey70]")
    console.print()
    console.print("  [grey70]@app.websocket('/ws/{client_id}')[/grey70]")
    console.print(
        "  [grey70]async def websocket_endpoint(websocket: WebSocket, "
        "client_id: str):[/grey70]"
    )
    console.print("  [grey70]    await manager.connect(websocket, client_id)[/grey70]")
    console.print("  [grey70]    try:[/grey70]")
    console.print("  [grey70]        while True:[/grey70]")
    console.print(
        "  [grey70]            data = await websocket.receive_text()[/grey70]"
    )
    console.print("  [grey70]            await manager.broadcast(data)[/grey70]")
    console.print("  [grey70]    except WebSocketDisconnect:[/grey70]")
    console.print("  [grey70]        manager.disconnect(client_id)[/grey70]")
    console.print()
    console.print("[bold]Room support:[/bold]")
    console.print("  [grey70]await manager.join_room(client_id, 'chat-room')[/grey70]")
    console.print(
        "  [grey70]await manager.broadcast_to_room("
        "'chat-room', {'msg': 'Hello!'})[/grey70]"
    )
    console.print()
    console.print("[bold]Multi-instance mode:[/bold]")
    console.print(
        "  Set [bold]WS_REDIS_URL[/bold] and call "
        "[grey70]await manager.start_pubsub()[/grey70] in lifespan"
    )
