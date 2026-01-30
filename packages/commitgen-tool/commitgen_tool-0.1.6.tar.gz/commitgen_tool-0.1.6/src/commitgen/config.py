import os
import typer
from pathlib import Path
from dotenv import load_dotenv

CONFIG_DIR = Path.home() / ".config" / "commitgen"
CONFIG_FILE = CONFIG_DIR / "config.env"


def load_config():
    """
    Load user config if it exists.
    """
    if CONFIG_FILE.exists():
        load_dotenv(CONFIG_FILE)


def ensure_api_key():
    """
    Ensure OpenAI API key is available.
    """
    load_config()

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        typer.secho(
            "❌ OpenAI API key not found.\n"
            "Run `commitgen config` to set it up.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    return api_key
