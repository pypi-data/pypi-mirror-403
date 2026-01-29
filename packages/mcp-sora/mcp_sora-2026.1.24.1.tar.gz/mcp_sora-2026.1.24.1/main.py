#!/usr/bin/env python3
"""
MCP Sora Server - AI Video Generation via AceDataCloud API.

A Model Context Protocol (MCP) server that provides tools for generating
AI videos using Sora through the AceDataCloud platform.
"""

import argparse
import logging
import sys
from importlib import metadata

from dotenv import load_dotenv

# Load environment variables before importing other modules
load_dotenv()

from core.config import settings
from core.server import mcp

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def safe_print(text: str) -> None:
    """Print to stderr safely, handling encoding issues."""
    if not sys.stderr.isatty():
        logger.debug(f"[MCP Sora] {text}")
        return

    try:
        print(text, file=sys.stderr)
    except UnicodeEncodeError:
        print(text.encode("ascii", errors="replace").decode(), file=sys.stderr)


def get_version() -> str:
    """Get the package version."""
    try:
        return metadata.version("mcp-sora")
    except metadata.PackageNotFoundError:
        return "dev"


def main() -> None:
    """Run the MCP Sora server."""
    parser = argparse.ArgumentParser(
        description="MCP Sora Server - AI Video Generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  mcp-sora                    # Run with stdio transport (default)
  mcp-sora --transport http   # Run with HTTP transport
  mcp-sora --version          # Show version

Environment Variables:
  ACEDATACLOUD_API_TOKEN     API token from AceDataCloud (required)
  SORA_DEFAULT_MODEL         Default model (default: sora-2)
  SORA_DEFAULT_SIZE          Default video size (default: large)
  SORA_DEFAULT_DURATION      Default duration in seconds (default: 15)
  SORA_DEFAULT_ORIENTATION   Default orientation (default: landscape)
  SORA_REQUEST_TIMEOUT       Request timeout in seconds (default: 300)
  LOG_LEVEL                  Logging level (default: INFO)
        """,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"mcp-sora {get_version()}",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport mode (default: stdio)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for HTTP transport (default: 8000)",
    )
    args = parser.parse_args()

    # Print startup banner
    safe_print("")
    safe_print("=" * 50)
    safe_print("  MCP Sora Server - AI Video Generation")
    safe_print("=" * 50)
    safe_print("")
    safe_print(f"  Version:     {get_version()}")
    safe_print(f"  Transport:   {args.transport}")
    safe_print(f"  Model:       {settings.default_model}")
    safe_print(f"  Size:        {settings.default_size}")
    safe_print(f"  Duration:    {settings.default_duration}s")
    safe_print(f"  Orientation: {settings.default_orientation}")
    safe_print(f"  Log Level:   {settings.log_level}")
    safe_print("")

    # Validate configuration
    if not settings.is_configured:
        safe_print("  [ERROR] ACEDATACLOUD_API_TOKEN not configured!")
        safe_print("  Get your token from https://platform.acedata.cloud")
        safe_print("")
        sys.exit(1)

    safe_print("  [OK] API token configured")
    safe_print("")

    # Import tools and prompts to register them
    safe_print("  Loading tools and prompts...")
    import prompts  # noqa: F401, I001
    import tools  # noqa: F401

    safe_print("  [OK] Tools and prompts loaded")
    safe_print("")
    safe_print("  Available tools:")
    safe_print("    - sora_generate_video")
    safe_print("    - sora_generate_video_from_image")
    safe_print("    - sora_generate_video_with_character")
    safe_print("    - sora_generate_video_async")
    safe_print("    - sora_get_task")
    safe_print("    - sora_get_tasks_batch")
    safe_print("    - sora_list_models")
    safe_print("    - sora_list_actions")
    safe_print("")
    safe_print("  Available prompts:")
    safe_print("    - sora_video_generation_guide")
    safe_print("    - sora_workflow_examples")
    safe_print("    - sora_prompt_writing_guide")
    safe_print("")
    safe_print("=" * 50)
    safe_print("  Ready for MCP connections")
    safe_print("=" * 50)
    safe_print("")

    # Run the server
    try:
        if args.transport == "http":
            mcp.run(transport="streamable-http", host="0.0.0.0", port=args.port)  # type: ignore[call-arg]
        else:
            mcp.run(transport="stdio")
    except KeyboardInterrupt:
        safe_print("\nShutdown requested")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
