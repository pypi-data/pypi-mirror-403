import sys

from .utils import setup_logger

logger = setup_logger('main')

def main():
    """
    Main entry point that dispatches execution to either the web app or the CLI.
    """
    # Check if we are launching the web interface (must be the first argument)
    if len(sys.argv) > 1 and sys.argv[1] == 'web':
        # Launching Web Interface
        try:
            from .app import launch_app
            launch_app()
        except ImportError as e:
            logger.error(f"Failed to import app: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error launching app: {e}")
            sys.exit(1)
    else:
        # Launching CLI
        try:
            from .cli import run_cli
            run_cli()
        except KeyboardInterrupt:
            sys.exit(130)
        except Exception as e:
            # Let argparse handle its own errors (SystemExit), but catch others
            # Assuming run_cli handles most logic errors but might bubble up unexpected ones
            # If it's SystemExit (argparse help/error), we don't log as error.
            if isinstance(e, SystemExit):
                raise
            logger.error(f"Unexpected error: {e}")
            sys.exit(1)

if __name__ == '__main__':
    main()
