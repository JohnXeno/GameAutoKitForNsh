import argparse
from workflow_engine import WorkflowEngine
import sys # For sys.exit
import logging

def main():
    """
    Main function to parse arguments and run the workflow engine.
    """
    parser = argparse.ArgumentParser(description="Run a workflow from a JSON configuration file.")
    parser.add_argument(
        '--workflow',
        '-w',
        type=str,
        required=True,
        help="Path to the workflow JSON file."
    )
    parser.add_argument(
        '--loglevel',
        '-l',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help="Set the logging level (default: INFO)."
    )

    args = parser.parse_args()

    # Configure logging
    numeric_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {args.loglevel}')
    
    logging.basicConfig(level=numeric_level, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        stream=sys.stdout) # Explicitly log to stdout

    main_logger = logging.getLogger(__name__) # Logger for main.py itself

    if not args.workflow:
        main_logger.error("Workflow file path must be provided.")
        parser.print_help()
        sys.exit(1)

    # Instantiate and run the workflow engine
    main_logger.info(f"Loading workflow from: {args.workflow}")
    engine = WorkflowEngine(config_path=args.workflow) # WorkflowEngine will use the root logger's config
    
    try:
        if engine.workflow_config: # Check if config was loaded successfully
            main_logger.info(f"Successfully loaded workflow: {engine.workflow_config.get('name', 'Unnamed Workflow')}")
            engine.run()
        else:
            # WorkflowEngine's __init__ already logs the failure to load.
            # We can add a main-specific message here if needed, or rely on engine's log.
            main_logger.error(f"Failed to initialize WorkflowEngine for '{args.workflow}'. Check previous logs for details.")
            sys.exit(1) # Exit if engine didn't load config
    except Exception as e:
        main_logger.error(f"Exception occurred during workflow execution: {e}", exc_info=True)
        sys.exit(1) # Exit on other exceptions during run

def run_main(argv=None):
    """
    Encapsulates the main script logic for testability.
    If argv is None, uses sys.argv.
    """
    # If using this function for testing, sys.argv might be manipulated by test runner.
    # It's better to parse 'argv' if provided.
    # However, the original main() function directly calls parser.parse_args()
    # which uses sys.argv by default. For testing, we'll mock sys.argv.
    # The 'main()' function below remains the primary entry point for the script itself.
    main()


if __name__ == '__main__':
    # This is the actual entry point when script is run
    main()
