import os
from bond import BondAgent
from bond.server import create_bond_server, ServerConfig
from bond.tools import BondToolDeps, github_toolset

# Check for API keys
if "OPENAI_API_KEY" not in os.environ:
    print("WARNING: OPENAI_API_KEY not found in environment variables.")
    print("The server may fail to generate responses.")

if "GITHUB_TOKEN" not in os.environ:
    print("WARNING: GITHUB_TOKEN not found in environment variables.")
    print("GitHub tools will not work without a token.")
    print("Set it with: export GITHUB_TOKEN=ghp_...")


def list_files(directory: str = ".") -> str:
    """List files in the given directory."""
    try:
        files = os.listdir(directory)
        return "\n".join(files)
    except Exception as e:
        return f"Error: {e}"


# Create composite deps for GitHub tools
deps = BondToolDeps(github_token=os.environ.get("GITHUB_TOKEN"))

agent = BondAgent(
    name="test-assistant",
    instructions="""You are a helpful assistant with access to GitHub.

You can:
- Browse any GitHub repository (list files, read files, get repo info)
- Search code in repositories
- View commits and pull requests
- List local files using the list_files tool

When asked about GitHub repositories, use the github tools to fetch real data.

IMPORTANT: If a tool returns a rate limit error, do NOT retry. Just explain to the user that you hit the rate limit and they should try again later.""",
    model="openai:gpt-4o-mini",
    toolsets=[[list_files], github_toolset],
    deps=deps,
    max_retries=1,  # Reduce retries to prevent rate limit loops
)

# Configure server with explicit CORS origins
# Include multiple Vite ports since it auto-increments when ports are busy
config = ServerConfig(
    cors_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:5177",
        "http://localhost:5178",
        "http://localhost:5179",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
        "http://127.0.0.1:5177",
        "http://127.0.0.1:5178",
        "http://127.0.0.1:5179",
        "http://localhost:8000",
    ]
)

app = create_bond_server(agent, config=config)

if __name__ == "__main__":
    import uvicorn

    print("Starting Bond Test Server on http://0.0.0.0:8000")
    print(f"GitHub Token: {'configured' if os.environ.get('GITHUB_TOKEN') else 'NOT SET'}")
    print(f"Allowed Origins: {config.cors_origins}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
