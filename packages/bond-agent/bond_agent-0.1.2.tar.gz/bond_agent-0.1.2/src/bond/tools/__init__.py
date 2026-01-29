"""Bond toolsets for agent capabilities.

Provides ready-to-use toolsets for common agent capabilities:
- GitHub: Browse and analyze GitHub repositories
- GitHunter: Forensic code ownership analysis
- Memory: Semantic memory with vector databases
- Schema: Database schema exploration

Example:
    ```python
    from bond import BondAgent
    from bond.tools import BondToolDeps, github_toolset, githunter_toolset

    # Create composite deps for multiple toolsets
    deps = BondToolDeps(github_token=os.environ["GITHUB_TOKEN"])

    # Create agent with multiple capabilities
    agent = BondAgent(
        name="code-analyst",
        instructions="You analyze code repositories.",
        model="openai:gpt-4o",
        toolsets=[github_toolset, githunter_toolset],
        deps=deps,
    )
    ```
"""

from bond.tools._composite import BondToolDeps
from bond.tools.github import GitHubAdapter, GitHubProtocol, github_toolset
from bond.tools.githunter import GitHunterAdapter, GitHunterProtocol, githunter_toolset
from bond.tools.memory import AgentMemoryProtocol, memory_toolset

__all__ = [
    # Composite deps
    "BondToolDeps",
    # GitHub
    "github_toolset",
    "GitHubAdapter",
    "GitHubProtocol",
    # GitHunter
    "githunter_toolset",
    "GitHunterAdapter",
    "GitHunterProtocol",
    # Memory
    "memory_toolset",
    "AgentMemoryProtocol",
]
