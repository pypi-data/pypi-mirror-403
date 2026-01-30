import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import commitgen.git_utils as git_utils
from commitgen import ai
from commitgen.config import CONFIG_DIR, CONFIG_FILE

app = typer.Typer(help="CommitGen – AI-powered Conventional Commit generator")
console = Console()


@app.command()
def commit(push: bool = typer.Option(False, "--push", "-p", help="Push the commit after committing"),
           auto: bool = typer.Option(False, "--auto", "-a", help="Automatically commit with generated message and push")):
    """
    Generate a Conventional Commit message from staged changes.
    """

    current_context = ""
    message = None
    diff_text = None

    if not git_utils.verify_repo():
        console.print(Panel("[bold red]You are not inside a Git repository[/bold red]", title="Error", border_style="red"))
        raise typer.Exit(code=1)

    if auto:
        # --- Ensure staged changes ---
        if not git_utils.has_staged_changes():
            git_utils.stage_all_changes()

        diff_text = git_utils.get_staged_diff()
        if not diff_text.strip():
            console.print("[red]No changes detected[/red]")
            raise typer.Exit(code=1)

        message = ai.generate_commit_message(diff_text, current_context)
        if not message.strip():
            message = ai._fallback_commit_message(diff_text, current_context)

        git_utils.commit_changes(message)
        console.print(Panel("[green]✅ Auto commit successful![/green]", title="Success", border_style="green"))

        if push or True:
            git_utils.push_changes()
            console.print(Panel("[green]✅ Auto push complete![/green]", title="Success", border_style="green"))

        raise typer.Exit()


    if not git_utils.has_staged_changes():
        console.print(Panel("[yellow]No staged changes detected.[/yellow]", title="Info", border_style="yellow"))

        choice = typer.prompt(
            "(a) stage all, (s) select files, (q) quit"
        ).lower()

        if choice == 'a':
            git_utils.stage_all_changes()
        elif choice == 's':
            files = git_utils.get_modified_files()

            if not files:
                console.print("[red]No files to stage[/red]")
                raise typer.Exit(code=1)

            for i, f in enumerate(files, 1):
                console.print(f"[{i}] {f}")

            selection = typer.prompt(
                "Select files (comma-separated numbers)"
            )

            try:
                indexes = [int(i.strip()) for i in selection.split(",")]
                for i in indexes:
                    git_utils.stage_file(files[i - 1])

                console.print(
                    Panel(
                        "[green]Selected files staged successfully[/green]",
                        title="Success",
                        border_style="green",
                    )
                )
            except ValueError:
                console.print("[red]Invalid selection[/red]")
                raise typer.Exit(code=1)

        else:
            raise typer.Exit(code=1)

    while True:
        if diff_text is None:
            diff_text = git_utils.get_staged_diff()

            if not diff_text.strip():
                console.print(
                    Panel(
                        "[bold red]Unable to retrieve staged changes[/bold red]",
                        title="Error",
                        border_style="red",
                    )
                )
                raise typer.Exit(code=1)

        if message is None:
            message = ai.generate_commit_message(diff_text, current_context)

            if not message.strip() or not message:
                console.print(
                    Panel(
                        "[bold red]Failed to generate commit message. using fallback[/bold red]",
                        title="Error",
                        border_style="red",
                    )
                )
                message = ai._fallback_commit_message(diff_text, current_context)

        # --- Suggested Commit Message ---
        console.print(Panel(message, title="💡 Suggested Commit Message", border_style="cyan"))

        choice = typer.prompt("(a) accept, (r) regenerate with context, (i) inline edit, (e) extended inline edit in custom editor, or (q)uit?")

        if choice.lower() == 'a':
            git_utils.commit_changes(message)
            console.print(Panel("[green]✅ Commit successful![/green]", title="Success", border_style="green"))
            break

        elif choice.lower() == 'r':
            extra_context = typer.prompt("Add context to refine this message").strip()

            if not extra_context:
                continue

            message = ai.refine_commit_message(message, extra_context)

        elif choice.lower() == 'i':
            edited = typer.prompt(
                "Edited commit message",
            ).strip()

            if not edited:
                console.print(
                    Panel(
                        "[red]Commit message cannot be empty.[/red]",
                        title="Error",
                        border_style="red",
                    )
                )
                continue
            message = edited

        elif choice.lower() == 'e':
            console.print(
                "[dim]Tip: Save the file before closing the editor to apply changes. Press Ctrl+S to save![/dim]"
            )

            edited_message = typer.edit(editor_template(message))

            # User closed editor without saving
            if edited_message is None:
                console.print(
                    Panel(
                        "[yellow]Editor closed without saving. Keeping previous message.[/yellow]",
                        title="Info",
                        border_style="yellow",
                    )
                )
                continue

            edited_message = "\n".join(
                line for line in edited_message.splitlines() if not line.strip().startswith("#")
            ).strip()

            if not edited_message:
                console.print(
                Panel(
                        "[red]Commit message cannot be empty.[/red]",
                        title="Error",
                        border_style="red",
                    )
                )
                continue

            message = edited_message

            console.print(Panel(message, title="✏️ Edited Message", border_style="green"))

            if typer.confirm("Accept this edited message?"):
                git_utils.commit_changes(message)
                console.print(
                    Panel("[green]✅ Commit successful![/green]", title="Success", border_style="green")
                )
                break


        elif choice.lower() == 'q':
            console.print(Panel("[yellow]Commit aborted by user[/yellow]", title="Aborted", border_style="yellow"))
            raise typer.Exit(code=1)

    if push:
        console.print(Panel("[cyan]Pushing changes...[/cyan]", title="Info", border_style="cyan"))
        git_utils.push_changes()
        console.print(Panel("[green]✅ Push complete![/green]", title="Success", border_style="green"))
    else:
        push_choice = typer.prompt("Do you want to push the commit now? (y/n)").lower()
        if push_choice == 'y':
            console.print(Panel("[cyan]Pushing changes...[/cyan]", title="Info", border_style="cyan"))
            git_utils.push_changes()
            console.print(Panel("[green]✅ Push complete![/green]", title="Success", border_style="green"))
        else:
            console.print(Panel("[yellow]Remember to push your commit later![/yellow]", title="Reminder", border_style="yellow"))


@app.command()
def version():
    """Show CommitGen version."""
    console.print(Panel("CommitGen version: 0.1.5", title="Version", border_style="cyan"))


@app.command()
def config():
    """Configure commitgen settings (API keys, preferences, etc.)"""
    api_key = typer.prompt("Enter your OpenAI API Key", hide_input=True)

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(f"OPENAI_API_KEY={api_key}\n")

    console.print(Panel("[green]API key saved successfully![/green]", title="Success", border_style="green"))


def editor_template(message: str) -> str:
    return (
        "# CommitGen – Extended Commit Message Editor\n"
        "#\n"
        "# Save the file before closing to apply changes.\n"
        "# VS Code: Ctrl+S (Windows/Linux) or Cmd+S (macOS)\n"
        "# Vim: :wq\n"
        "# Nano: Ctrl+O, Enter, then Ctrl+X\n"
        "#\n"
        "# Lines starting with '#' will be ignored.\n"
        "#\n\n"
        f"{message}\n"
    )
