"""Main entry point for the Context Tool application"""

import argparse
import yaml
from pathlib import Path
import uvicorn

from src.api import app, initialize_app


def load_config(config_path: Path) -> dict:
    """
    Load configuration from YAML file

    Args:
        config_path: Path to config.yaml

    Returns:
        Configuration dictionary
    """
    if not config_path.exists():
        print(f"Warning: Config file {config_path} not found, using defaults")
        return get_default_config()

    with open(config_path) as f:
        return yaml.safe_load(f)


def get_default_config() -> dict:
    """Get default configuration"""
    return {
        'app': {
            'name': 'Context Tool',
            'mode': 'demo'
        },
        'database': {
            'type': 'sqlite',
            'path': ':memory:'
        },
        'data': {
            'directory': './data',
            'auto_load': True
        },
        'semantic_search': {
            'enabled': True,
            'model': 'all-MiniLM-L6-v2',
            'similarity_threshold': 0.5
        },
        'ui': {
            'type': 'web',
            'port': 8000,
            'host': 'localhost'
        }
    }


def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(description='Context Tool - Text Selection Context Analyzer')
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    parser.add_argument(
        '--mode',
        type=str,
        choices=['demo', 'system', 'widget'],
        help='Operating mode: demo (web UI), system (system-wide monitoring), or widget (desktop widget)'
    )
    parser.add_argument(
        '--port',
        type=int,
        help='Port for web server (default: 8000)'
    )
    parser.add_argument(
        '--host',
        type=str,
        help='Host for web server (default: localhost)'
    )
    parser.add_argument(
        '--data-dir',
        type=str,
        help='Directory containing YAML data files (default: ./data)'
    )
    parser.add_argument(
        '--no-semantic',
        action='store_true',
        help='Disable semantic search (faster startup)'
    )
    parser.add_argument(
        '--system-mode',
        action='store_true',
        help='Enable system-wide clipboard monitoring'
    )
    parser.add_argument(
        '--markdown',
        action='store_true',
        help='Use markdown files instead of YAML (Obsidian-compatible)'
    )

    args = parser.parse_args()

    # Load configuration
    config_path = Path(args.config)
    config = load_config(config_path)

    # Override config with command line arguments
    if args.mode:
        config['app']['mode'] = args.mode
    if args.port:
        config['ui']['port'] = args.port
    if args.host:
        config['ui']['host'] = args.host
    if args.data_dir:
        config['data']['directory'] = args.data_dir
    if args.no_semantic:
        config['semantic_search']['enabled'] = False

    # Get configuration values
    data_dir = Path(config['data']['directory'])
    db_path = config['database']['path']
    enable_semantic = config['semantic_search']['enabled']
    host = config['ui']['host']
    port = config['ui']['port']
    mode = config['app']['mode']

    print(f"Starting Context Tool in {mode} mode...")
    print(f"Data directory: {data_dir}")
    print(f"Database: {db_path}")
    print(f"Semantic search: {'enabled' if enable_semantic else 'disabled'}")

    # Determine data format and directory
    use_markdown = args.markdown
    if use_markdown and not data_dir.name.endswith('-md'):
        # If markdown flag is set but data_dir is default, switch to data-md
        if str(data_dir) == './data':
            data_dir = Path('./data-md')
            print(f"Using markdown data directory: {data_dir}")

    # Initialize the application
    try:
        initialize_app(
            data_dir=data_dir,
            db_path=db_path,
            enable_semantic=enable_semantic,
            use_markdown=use_markdown
        )
    except Exception as e:
        print(f"Error initializing application: {e}")
        return 1

    # Check if system mode requested
    system_mode_enabled = args.system_mode or mode == 'system'

    # Run based on mode
    if mode == 'widget':
        # Widget mode - desktop UI with clipboard monitoring
        print("\nStarting desktop widget mode...")
        from src.widget_mode import run_widget_mode

        run_widget_mode(
            data_dir=data_dir,
            db_path=db_path,
            enable_semantic=enable_semantic,
            poll_interval=0.5,
            min_length=3,
            use_markdown=use_markdown
        )
        return 0

    elif mode == 'demo' or mode == 'web' or system_mode_enabled:
        print(f"\nStarting web server on http://{host}:{port}")
        print(f"API documentation: http://{host}:{port}/docs")

        if system_mode_enabled:
            print(f"\n🔍 System-wide clipboard monitoring ENABLED")
            print(f"   Any text you copy will be analyzed automatically")
            print(f"   Keep the web UI open to see results in real-time")

        print(f"\nPress Ctrl+C to stop\n")

        # Start system monitoring if requested
        if system_mode_enabled:
            from src.api import start_system_monitoring
            import asyncio

            # Create event loop for startup task
            async def run_server():
                # Start system monitoring
                await start_system_monitoring()

                # Start uvicorn server (this will block)
                config = uvicorn.Config(
                    app,
                    host=host,
                    port=port,
                    log_level="info"
                )
                server = uvicorn.Server(config)
                await server.serve()

            asyncio.run(run_server())
        else:
            # Regular uvicorn run without system monitoring
            uvicorn.run(
                app,
                host=host,
                port=port,
                log_level="info"
            )

    elif mode == 'system':
        print("Use --system-mode flag instead: python main.py --system-mode")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
