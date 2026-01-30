"""Main CLI entry point."""

import sys

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from .agent import Agent, set_direct_output_callback
from .api import CircleMsClient
from .auth import AuthManager
from .config import Config

console = Console()

STYLE = Style.from_dict(
    {
        "prompt": "bold cyan",
    }
)

WELCOME_MESSAGE = """
# コミケWebカタログ CLI

自然言語でコミケWebカタログを検索できます。

**コマンド例:**
- 「東方のサークルを検索して」
- 「お気に入り一覧を見せて」
- 「wcid 12345678 のサークル詳細を教えて」

**特殊コマンド:**
- `/help` - ヘルプを表示
- `/clear` - 会話履歴をクリア
- `/quit` または `/exit` - 終了
"""


def print_welcome():
    """Print welcome message."""
    console.print(Panel(Markdown(WELCOME_MESSAGE), title="Welcome", border_style="cyan"))


def print_response(text: str):
    """Print agent response."""
    console.print()
    console.print(Markdown(text))
    console.print()


def main():
    """Main entry point."""
    try:
        config = Config.load()
    except ValueError as e:
        console.print(f"[red]設定エラー: {e}[/red]")
        console.print("`~/.comike_cli/.env` に環境変数を設定してください。")
        sys.exit(1)

    try:
        auth_manager = AuthManager(
            client_id=config.circle_ms_client_id,
            client_secret=config.circle_ms_client_secret,
            token_file=config.token_file,
        )
        # Trigger authentication before starting the CLI
        console.print("[dim]認証を確認中...[/dim]")
        auth_manager.get_token()
        console.print("[green]認証完了[/green]")

        api_client = CircleMsClient(auth_manager)
        agent = Agent(config.openai_api_key, api_client)

        # Set callback for direct output (e.g., images)
        set_direct_output_callback(lambda text: console.print(text))
    except Exception as e:
        console.print(f"[red]初期化エラー: {e}[/red]")
        sys.exit(1)
    print_welcome()

    history_file = config.token_file.parent / "history.txt"
    history_file.parent.mkdir(parents=True, exist_ok=True)
    session: PromptSession = PromptSession(
        history=FileHistory(str(history_file)),
        style=STYLE,
    )

    while True:
        try:
            user_input = session.prompt("comike> ").strip()

            if not user_input:
                continue

            # Handle special commands
            if user_input.startswith("/"):
                cmd = user_input.lower()
                if cmd in ("/quit", "/exit", "/q"):
                    console.print("[dim]終了します。[/dim]")
                    break
                elif cmd == "/clear":
                    agent.reset()
                    console.print("[dim]会話履歴をクリアしました。[/dim]")
                    continue
                elif cmd == "/help":
                    print_welcome()
                    continue
                else:
                    console.print(f"[yellow]不明なコマンド: {user_input}[/yellow]")
                    continue

            # Process with agent
            with console.status("[bold cyan]考え中...[/bold cyan]"):
                response = agent.chat(user_input)

            print_response(response)

        except KeyboardInterrupt:
            console.print("\n[dim]Ctrl+C で中断しました。/quit で終了できます。[/dim]")
            continue
        except EOFError:
            console.print("\n[dim]終了します。[/dim]")
            break
        except Exception as e:
            console.print(f"[red]エラー: {e}[/red]")
            continue


if __name__ == "__main__":
    main()
