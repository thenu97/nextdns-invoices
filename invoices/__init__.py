"""Cli module for invoices package."""

import typer

app = typer.Typer()


@app.command()
def main() -> None:
    """Run the invoices package."""
    from invoices.main import NextDNS

    NextDNS().send_email_via_mailgun()


if __name__ == "__main__":
    app()
