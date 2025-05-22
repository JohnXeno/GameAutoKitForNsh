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
    
    if engine.workflow_config: # Check if config was loaded successfully
        main_logger.info(f"Successfully loaded workflow: {engine.workflow_config.get('name', 'Unnamed Workflow')}")
        engine.run()
    else:
        # WorkflowEngine's __init__ already logs the failure to load.
        # We can add a main-specific message here if needed, or rely on engine's log.
        main_logger.error(f"Failed to initialize WorkflowEngine for '{args.workflow}'. Check previous logs for details.")
        sys.exit(1)

if __name__ == '__main__':
    main()
