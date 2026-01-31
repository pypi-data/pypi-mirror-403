import argparse
import asyncio
import os
import sys

from pydantic import AnyUrl, ValidationError

from devopness_mcp_server_proxy.server import proxy_run


def run() -> None:
    parser = argparse.ArgumentParser(description="Devopness MCP Server")

    parser.add_argument(
        "--mcp-url",
        type=str,
        default="https://mcp.devopness.com/mcp/",
        help="URL of the MCP Server (default: https://mcp.devopness.com/mcp/)",
    )

    parser.add_argument(
        "--devopness-token",
        type=str,
        help="Devopness Token for authentication",
    )

    args = parser.parse_args()

    # Validate MCP URL
    try:
        validated_url = AnyUrl(args.mcp_url)

    except ValidationError:
        print(
            (f"Error: Invalid MCP URL '{args.mcp_url}'. Should be a valid HTTP URL."),
            file=sys.stderr,
        )

        sys.exit(1)

    # Get the Devopness Token from flag or environment variable
    devopness_token = args.devopness_token

    if not devopness_token:
        devopness_token = os.getenv("DEVOPNESS_TOKEN")

    if not devopness_token:
        print("Error: Devopness Token is required.", file=sys.stderr)

        print(
            "Please provide it via "
            "DEVOPNESS_TOKEN environment variable or "
            "--devopness-token.",
            file=sys.stderr,
        )

        sys.exit(1)

    asyncio.run(
        proxy_run(
            mcp_url=str(validated_url),
            devopness_token=devopness_token,
        ),
    )


if __name__ == "__main__":
    run()
