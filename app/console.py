from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    MofNCompleteColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
)
from rich.prompt import Prompt, Confirm


console = Console()


def print_info(message: str):
    console.print(message, style="blue")


def print_success(message: str):
    console.print(f"✅ {message}", style="green")


def print_warning(message: str):
    console.print(f"⚠️  {message}", style="yellow")


def print_error(message: str):
    console.print(f"❌ {message}", style="red")


def print_traceback():
    console.print_exception(max_frames=20)


def ask_question(message: str) -> str:
    return Prompt.ask(f"[bold cyan]{message}[/bold cyan]", console=console)


def ask_confirm(message: str, default: bool | None = None) -> bool:
    question = f"[bold yellow]{message}[/bold yellow]"
    if default is None:
        return Confirm.ask(question, console=console)
    else:
        return Confirm.ask(question, console=console, default=default)


def progress_bar(text: str) -> Progress:
    return Progress(
        SpinnerColumn(),
        TextColumn(f"[cyan]{text}[/cyan]"),
        BarColumn(),
        MofNCompleteColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(elapsed_when_finished=True),
        console=console,
        speed_estimate_period=180,
    )
