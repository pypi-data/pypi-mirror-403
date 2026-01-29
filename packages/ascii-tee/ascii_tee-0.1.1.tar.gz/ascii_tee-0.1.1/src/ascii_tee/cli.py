"""ASCII Tee CLI - Generate custom ASCII art t-shirts."""

import os
import webbrowser
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from ascii_tee.api import APIClient, APIError
from ascii_tee.display import display_image
from ascii_tee.models import Color, Design, Order, Size
from ascii_tee.preview import generate_preview, generate_print_file

app = typer.Typer(
    name="ascii-tee",
    help="Generate custom ASCII art t-shirts",
    no_args_is_help=False,
)
console = Console()

# API URL - override with env var for local development
API_URL = os.environ.get("ASCII_TEE_API_URL", "https://ascii-tee-api.cdinnison.workers.dev")


def display_ascii(ascii_art: str, prompt: str) -> None:
    """Display ASCII art in a styled panel."""
    title = f"[bold]{prompt[:40]}...[/]" if len(prompt) > 40 else f"[bold]{prompt}[/]"
    console.print(Panel(ascii_art, title=title, border_style="cyan", padding=(1, 2)))


def show_order_summary(order: Order) -> None:
    """Display order summary table."""
    table = Table(border_style="cyan", show_header=False, padding=(0, 1))
    table.add_column("Item", style="bold")
    table.add_column("Value", justify="right")

    color_display = order.color.title()
    table.add_row("Design", f'"{order.design.prompt[:30]}..."')
    table.add_row("Style", f"{color_display} shirt")
    table.add_row("Size", order.size)
    table.add_row("Quantity", str(order.quantity))
    table.add_row("", "")
    table.add_row("Subtotal", f"[bold]{order.subtotal_dollars}[/]")
    table.add_row("Shipping", "[dim]Calculated at checkout[/]")

    console.print(Panel(table, title="[bold]Order Summary[/]", border_style="green"))


def interactive_generate(client: APIClient, initial_prompt: str | None = None, remove_bg: bool = True) -> Design:
    """Interactive loop for generating ASCII art with regenerate option."""
    if initial_prompt:
        prompt = initial_prompt
    else:
        prompt = Prompt.ask("\n[bold cyan]What do you want on your shirt?[/]")

    with console.status("[bold green]Generating ASCII art...", spinner="dots"):
        design = client.generate_ascii(prompt, remove_background=remove_bg)

    display_ascii(design.ascii_art, prompt)

    while True:
        choice = Prompt.ask(
            "\n[R]egenerate  [E]dit prompt  [B]ackground toggle  [C]ontinue",
            choices=["r", "e", "b", "c", "R", "E", "B", "C"],
            default="c",
        ).lower()

        if choice == "r":
            with console.status("[bold green]Regenerating...", spinner="dots"):
                design = client.generate_ascii(prompt, remove_background=remove_bg)
            display_ascii(design.ascii_art, prompt)

        elif choice == "e":
            prompt = Prompt.ask("[bold cyan]New prompt[/]")
            with console.status("[bold green]Generating...", spinner="dots"):
                design = client.generate_ascii(prompt, remove_background=remove_bg)
            display_ascii(design.ascii_art, prompt)

        elif choice == "b":
            remove_bg = not remove_bg
            status = "removed" if remove_bg else "included"
            console.print(f"[dim]Background will be {status}[/]")
            with console.status("[bold green]Regenerating...", spinner="dots"):
                design = client.generate_ascii(prompt, remove_background=remove_bg)
            display_ascii(design.ascii_art, prompt)

        else:
            return design


def select_options(design: Design, defaults: dict) -> Order:
    """Interactive selection of color, size, and quantity."""
    # Color selection
    console.print("\n[bold]Shirt Color[/]")
    color_choice = Prompt.ask(
        "  (b)lack shirt / white print  or  (w)hite shirt / black print",
        choices=["b", "w", "B", "W"],
        default="b" if defaults.get("color", "black") == "black" else "w",
    ).lower()
    color: Color = "black" if color_choice == "b" else "white"

    # Size selection
    console.print("\n[bold]Size[/]")
    size: Size = Prompt.ask(
        "  Choose size",
        choices=["S", "M", "L", "XL", "2XL", "s", "m", "l", "xl", "2xl"],
        default=defaults.get("size", "L"),
    ).upper()  # type: ignore

    # Quantity
    qty_str = Prompt.ask("\n[bold]Quantity[/]", default=str(defaults.get("quantity", 1)))
    try:
        quantity = max(1, int(qty_str))
    except ValueError:
        quantity = 1

    return Order(design=design, color=color, size=size, quantity=quantity)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    prompt: Optional[str] = typer.Argument(None, help="What do you want on your shirt?"),
    color: str = typer.Option("black", "--color", "-c", help="Shirt color: black | white"),
    size: str = typer.Option("L", "--size", "-s", help="Shirt size: S | M | L | XL | 2XL"),
    qty: int = typer.Option(1, "--qty", "-q", help="Quantity"),
    remove_background: bool = typer.Option(True, "--remove-background/--keep-background", "-r/-R", help="Remove or keep background dots"),
    no_preview: bool = typer.Option(False, "--no-preview", help="Skip t-shirt preview"),
    open_preview: bool = typer.Option(False, "--open", help="Open preview in browser"),
    checkout: bool = typer.Option(False, "--checkout", help="Skip confirmations, go to checkout"),
) -> None:
    """Generate custom ASCII art t-shirts.

    Run without arguments for interactive mode, or provide a prompt directly:

        ascii-tee "a robot playing guitar"
    """
    if ctx.invoked_subcommand is not None:
        return

    console.print("\n[bold cyan]ASCII Tee[/] - Custom ASCII art t-shirts\n")

    client = APIClient(base_url=API_URL)

    try:
        # Step 1: Generate ASCII art
        design = interactive_generate(client, prompt, remove_bg=remove_background)

        # Step 2: Preview
        preview_path = None
        if not no_preview:
            console.print()
            # Default to black for first preview, user can change
            preview_color: Color = "black" if color == "black" else "white"

            try:
                with console.status("[bold green]Generating preview...", spinner="dots"):
                    preview_path = generate_preview(design, preview_color)
                display_image(preview_path, force_browser=open_preview)
            except FileNotFoundError as e:
                console.print(f"[yellow]Preview unavailable: {e}[/]")
                console.print("[dim]Continuing without preview...[/]")

        # Step 3: Select options
        defaults = {"color": color, "size": size, "quantity": qty}
        order = select_options(design, defaults)

        # Regenerate preview if color changed
        if not no_preview and order.color != preview_color:
            try:
                with console.status("[bold green]Updating preview...", spinner="dots"):
                    preview_path = generate_preview(design, order.color)
                display_image(preview_path, force_browser=open_preview)
            except FileNotFoundError:
                pass

        # Step 4: Order summary and confirmation
        console.print()
        show_order_summary(order)

        if not checkout:
            choice = Prompt.ask(
                "\n[P]roceed to checkout  [X] Cancel",
                choices=["p", "x", "P", "X"],
                default="p",
            ).lower()

            if choice == "x":
                console.print("\n[dim]Order cancelled.[/]")
                raise typer.Exit()

        # Step 5: Upload preview and print file, then create checkout session
        image_url = None
        print_file_url = None

        with console.status("[bold green]Preparing files for print...", spinner="dots"):
            # Upload preview image for Stripe checkout page
            if preview_path and preview_path.exists():
                try:
                    image_url = client.upload_preview(design.id, preview_path)
                except APIError:
                    pass  # Continue without image if upload fails

            # Generate and upload high-res print file for Printful
            try:
                print_path = generate_print_file(design, order.color)
                print_file_url = client.upload_print_file(design.id, order.color, print_path)
            except (APIError, Exception):
                pass  # Continue without print file if generation/upload fails

        with console.status("[bold green]Creating checkout...", spinner="dots"):
            checkout_url = client.create_checkout(order, image_url=image_url, print_file_url=print_file_url)

        console.print(f"\n[bold green]Opening checkout in browser...[/]")
        console.print(f"[dim]{checkout_url}[/]\n")
        webbrowser.open(checkout_url)

    except APIError as e:
        console.print(f"\n[bold red]Error:[/] {e}")
        raise typer.Exit(1)

    except KeyboardInterrupt:
        console.print("\n\n[dim]Cancelled.[/]")
        raise typer.Exit()


if __name__ == "__main__":
    app()
