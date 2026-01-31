# src/markdown2feishu/cli.py
"""Command-line interface for markdown2feishu."""

import asyncio
import sys


def main():
    """Main CLI entry point."""
    try:
        import click
    except ImportError:
        print("CLI requires click. Install with: pip install markdown2feishu[cli]")
        sys.exit(1)

    @click.command()
    @click.argument("file", type=click.Path(exists=True))
    @click.option("--title", "-t", help="Document title")
    @click.option("--webhook", "-w", is_flag=True, help="Send to webhook instead of creating document")
    @click.option("--folder", "-f", help="Folder token for document")
    def push(file: str, title: str, webhook: bool, folder: str):
        """Push Markdown file to Feishu.

        FILE: Path to Markdown file to push
        """
        from markdown2feishu.client import FeishuClient
        from pathlib import Path

        async def run():
            async with FeishuClient() as client:
                content = Path(file).read_text(encoding="utf-8")

                if webhook:
                    success = await client.send_webhook(content, title)
                    if success:
                        click.echo("✓ Message sent to webhook")
                    else:
                        click.echo("✗ Failed to send message", err=True)
                        sys.exit(1)
                else:
                    doc = await client.push_file(file, title, folder)
                    click.echo(f"✓ Document created: {doc.url}")

        try:
            asyncio.run(run())
        except ValueError as e:
            click.echo(f"✗ Configuration error: {e}", err=True)
            sys.exit(1)
        except Exception as e:
            click.echo(f"✗ Error: {e}", err=True)
            sys.exit(1)

    push()


if __name__ == "__main__":
    main()
