import typer
from .service import start_task, stop_task, get_summary

app = typer.Typer()


@app.command()
def start(task: str):
    """Start tracking a task"""
    try:
        start_task(task)
        typer.echo(f"Started: {task}")
    except RuntimeError as e:
        typer.echo(f"{e}")


@app.command()
def stop():
    """Stop current task"""
    try:
        task, duration = stop_task()
        typer.echo(f"Stopped {task} ({duration})")
    except RuntimeError as e:
        typer.echo(f"{e}")


@app.command()
def summary():
    """Show time summary"""
    summary = get_summary()

    if not summary:
        typer.echo("No data yet")
        return

    typer.echo("\nTime summary:")
    for task, duration in summary.items():
        typer.echo(f"- {task}: {duration}")
