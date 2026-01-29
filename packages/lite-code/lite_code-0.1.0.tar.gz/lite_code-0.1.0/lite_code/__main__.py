"""Main entry point for lite-code CLI."""

from lite_code.cli import InteractiveCLI


def main():
    """Main entry point."""
    cli = InteractiveCLI()
    cli.start()


if __name__ == "__main__":
    main()
