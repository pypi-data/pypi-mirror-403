"""
Gather SDK CLI - Connect Google ADK agents to Gather.is workspaces

Commands:
    gathersdk init       Create a new agent project with all boilerplate
    gathersdk serve      Start the SDK bridge (requires 'adk web' running)
    gathersdk discover   List agents found in directory

Run 'adk web' in a separate terminal for full ADK debugging at http://localhost:8000
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

import click

from .sdk import AgencySDK
from .discovery import discover_agents


# Template for the sample agent
AGENT_TEMPLATE = '''from google.adk import Agent

root_agent = Agent(
    name="{name}",
    model="gemini-2.5-flash",
    description="A helpful AI assistant",
    instruction="""You are a helpful AI assistant called {name}.

Your personality:
- Friendly and conversational
- Clear and concise in your responses
- Helpful and proactive

Keep responses focused and useful."""
)
'''

# Template for __init__.py
INIT_TEMPLATE = '''from .agent import root_agent
'''

# Template for .env.example
ENV_TEMPLATE = '''# Get your API key from: https://aistudio.google.com/apikey
GOOGLE_API_KEY=your_api_key_here
'''

# Template for gather.config.json placeholder
CONFIG_TEMPLATE = '''{
  "_instructions": "Replace this file with your gather.config.json from app.gather.is",
  "_steps": [
    "1. Go to https://app.gather.is",
    "2. Create or open a workspace",
    "3. Click the workspace dropdown (top-left)",
    "4. Select 'SDK Settings'",
    "5. Click 'Download gather.config.json'",
    "6. Replace this file with the downloaded one"
  ],
  "pocketnode_url": "https://app.gather.is",
  "workspace": "REPLACE_ME"
}
'''


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging")
def cli(verbose: bool):
    """Gather SDK - Connect Google ADK agents to Gather.is workspaces"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S"
    )


@cli.command()
@click.option(
    "--name", "-n",
    prompt="Agent name",
    help="Name for your first agent (lowercase, underscores ok)"
)
@click.option(
    "--dir", "-d",
    default=".",
    help="Directory to create project in"
)
def init(name: str, dir: str):
    """
    Create a new Gather.is agent project with all the boilerplate.

    This sets up everything you need to get started:
    - Agent folder with working sample code
    - Environment file template
    - Placeholder config (replace with your download from app.gather.is)

    \b
    After running this:
    1. Replace gather.config.json with your download from app.gather.is
    2. Copy .env.example to .env and add your Google API key
    3. Run: adk web (in one terminal)
    4. Run: gathersdk serve (in another terminal)
    """
    # Normalize agent name
    agent_name = name.lower().replace("-", "_").replace(" ", "_")

    # Validate name
    if not agent_name.isidentifier():
        click.echo(click.style(f"Invalid agent name: {name}", fg="red"))
        click.echo("Use lowercase letters, numbers, and underscores only.")
        sys.exit(1)

    project_dir = Path(dir).resolve()
    agent_dir = project_dir / agent_name

    # Check if agent already exists
    if agent_dir.exists():
        click.echo(click.style(f"Agent folder already exists: {agent_dir}", fg="red"))
        sys.exit(1)

    click.echo(click.style("\n🚀 Creating Gather.is agent project...\n", fg="cyan"))

    # Create agent folder
    agent_dir.mkdir(parents=True)
    click.echo(f"  Created {agent_name}/")

    # Create agent.py
    (agent_dir / "agent.py").write_text(AGENT_TEMPLATE.format(name=agent_name))
    click.echo(f"  Created {agent_name}/agent.py")

    # Create __init__.py
    (agent_dir / "__init__.py").write_text(INIT_TEMPLATE)
    click.echo(f"  Created {agent_name}/__init__.py")

    # Create .env.example (in project root)
    env_file = project_dir / ".env.example"
    if not env_file.exists():
        env_file.write_text(ENV_TEMPLATE)
        click.echo("  Created .env.example")

    # Create gather.config.json placeholder (in project root)
    config_file = project_dir / "gather.config.json"
    if not config_file.exists():
        config_file.write_text(CONFIG_TEMPLATE)
        click.echo("  Created gather.config.json (placeholder)")

    # Print success and next steps
    click.echo(click.style("\n✅ Project created successfully!\n", fg="green"))

    click.echo("Project structure:")
    click.echo(f"  {project_dir.name}/")
    click.echo(f"  ├── gather.config.json  ← Replace with download from app.gather.is")
    click.echo(f"  ├── .env.example        ← Copy to .env, add your Google API key")
    click.echo(f"  └── {agent_name}/")
    click.echo(f"      ├── __init__.py")
    click.echo(f"      └── agent.py        ← Your agent code")

    click.echo(click.style("\n📋 Next steps:\n", fg="yellow"))
    click.echo("  1. Get your config from Gather.is:")
    click.echo(click.style("     → Go to app.gather.is → Workspace dropdown → SDK Settings", fg="cyan"))
    click.echo("     → Download and replace gather.config.json")
    click.echo()
    click.echo("  2. Set up your API key:")
    click.echo(click.style("     cp .env.example .env", fg="cyan"))
    click.echo("     → Edit .env and add your Google API key")
    click.echo("     → Get a key at: https://aistudio.google.com/apikey")
    click.echo()
    click.echo("  3. Start the servers (two terminals):")
    click.echo(click.style("     Terminal 1: source .env && adk web", fg="cyan"))
    click.echo(click.style("     Terminal 2: source .env && gathersdk serve", fg="cyan"))
    click.echo()
    click.echo(f"  4. Chat with your agent at app.gather.is:")
    click.echo(click.style(f"     @{agent_name} hello!", fg="cyan"))
    click.echo()


@cli.command()
@click.option(
    "--config", "-c",
    default="gather.config.json",
    help="Path to config file"
)
@click.option(
    "--dir", "-d",
    default=".",
    help="Directory to search for agents"
)
@click.option(
    "--adk-url",
    default="http://localhost:8000",
    help="ADK web server URL (run 'adk web' separately)"
)
def serve(config: str, dir: str, adk_url: str):
    """
    Start the SDK bridge connecting Tinode to ADK agents.

    IMPORTANT: You must run 'adk web' separately for full ADK integration:

    \b
    Terminal 1: adk web --port 8000
    Terminal 2: gathersdk serve

    This gives you full ADK debugging at http://localhost:8000
    """
    config_path = Path(config)

    if not config_path.exists():
        click.echo(f"Config file not found: {config}", err=True)
        click.echo("\nTo get a config file:")
        click.echo("  1. Go to your workspace settings in the web UI")
        click.echo("  2. Click 'SDK Access'")
        click.echo("  3. Download gather.config.json")
        sys.exit(1)

    try:
        sdk = AgencySDK.from_config(config_path, adk_server_url=adk_url)
    except Exception as e:
        click.echo(f"Failed to load config: {e}", err=True)
        sys.exit(1)

    # Run the async discover and serve
    try:
        asyncio.run(_serve_async(sdk, dir, adk_url))
    except KeyboardInterrupt:
        click.echo("\nShutting down...")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


async def _serve_async(sdk: AgencySDK, dir: str, adk_url: str):
    """Async portion of serve command"""
    import httpx
    from .discovery import discover_agents

    # First discover agents locally
    agents = discover_agents(dir)

    if not agents:
        raise click.ClickException(
            f"No agents found!\n\n"
            f"Searched in: {Path(dir).resolve()}\n\n"
            f"Expected structure:\n"
            f"  agents/\n"
            f"      my_agent/\n"
            f"          __init__.py  # from .agent import root_agent\n"
            f"          agent.py     # root_agent = Agent(...)"
        )

    click.echo(f"Found {len(agents)} agent(s): {', '.join(f'@{a.handle}' for a in agents)}")

    # Check ADK web server is running
    click.echo(f"\nChecking ADK server at {adk_url}...")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{adk_url}/list-apps")
            if resp.status_code == 200:
                click.echo(click.style("  ADK server is running", fg="green"))
            else:
                click.echo(click.style(f"  ADK server returned {resp.status_code}", fg="yellow"))
    except httpx.ConnectError:
        click.echo(click.style("  WARNING: ADK server not reachable!", fg="red"))
        click.echo()
        click.echo("  Start the ADK web server in another terminal:")
        click.echo(click.style(f"    adk web --port 8000", fg="cyan"))
        click.echo()
        click.echo("  This enables full ADK debugging at http://localhost:8000")
        click.echo()

    # Register with PocketNode
    click.echo(f"\nRegistering with {sdk.config.pocketnode_url}...")
    await sdk.discover(dir)

    if not sdk.runners:
        raise click.ClickException(
            "No agents could be registered!\n"
            "Check that your SDK token is valid."
        )

    # Run
    click.echo(f"\nConnecting to {sdk.config.server}")
    click.echo(f"Workspace: {sdk.config.workspace}")
    click.echo(f"ADK Server: {adk_url}")
    click.echo(f"Agents: {', '.join(f'@{r.agent.handle}' for r in sdk.runners)}")
    click.echo()
    click.echo(click.style("Debug your agents at: ", fg="white") + click.style(adk_url, fg="cyan"))
    click.echo()

    await sdk.run()


@cli.command()
@click.option(
    "--dir", "-d",
    default=".",
    help="Directory to search for agents"
)
def discover(dir: str):
    """Discover agents in a directory (without connecting)"""
    agents = discover_agents(dir)

    if not agents:
        click.echo("No agents found.")
        click.echo(f"\nSearched in: {Path(dir).resolve()}")
        return

    click.echo(f"Found {len(agents)} agent(s):\n")
    for agent in agents:
        click.echo(f"  @{agent.handle}")
        click.echo(f"    Path: {agent.path}")
        click.echo(f"    Agent: {type(agent.root_agent).__name__}")
        click.echo()


def main():
    cli()


if __name__ == "__main__":
    main()
