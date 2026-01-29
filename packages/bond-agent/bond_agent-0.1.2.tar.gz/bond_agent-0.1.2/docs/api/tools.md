# Tools Module

Bond includes bundled toolsets for common agent use cases.

## Memory Toolset

The memory toolset provides semantic memory storage with vector search.

### Protocol

::: bond.tools.memory.AgentMemoryProtocol
    options:
      show_source: true

### Models

::: bond.tools.memory.Memory
    options:
      show_source: true

::: bond.tools.memory.SearchResult
    options:
      show_source: true

### Backends

#### Qdrant

::: bond.tools.memory.QdrantMemoryStore
    options:
      show_source: false

#### pgvector

::: bond.tools.memory.PgVectorMemoryStore
    options:
      show_source: false

### Factory Function

::: bond.tools.memory.create_memory_backend
    options:
      show_source: false

### Toolset

::: bond.tools.memory.memory_toolset
    options:
      show_source: false

---

## Schema Toolset

The schema toolset provides database schema lookup capabilities.

### Protocol

::: bond.tools.schema.SchemaLookupProtocol
    options:
      show_source: true

### Models

::: bond.tools.schema.TableSchema
    options:
      show_source: true

::: bond.tools.schema.ColumnSchema
    options:
      show_source: true

### Toolset

::: bond.tools.schema.schema_toolset
    options:
      show_source: false

---

## GitHub Toolset

The GitHub toolset provides tools to browse and analyze any GitHub repository.

### Protocol

::: bond.tools.github.GitHubProtocol
    options:
      show_source: true

### Adapter

::: bond.tools.github.GitHubAdapter
    options:
      show_source: false

### Types

::: bond.tools.github.RepoInfo
    options:
      show_source: true

::: bond.tools.github.TreeEntry
    options:
      show_source: true

::: bond.tools.github.FileContent
    options:
      show_source: true

::: bond.tools.github.CodeSearchResult
    options:
      show_source: true

::: bond.tools.github.Commit
    options:
      show_source: true

::: bond.tools.github.CommitAuthor
    options:
      show_source: true

::: bond.tools.github.PullRequest
    options:
      show_source: true

::: bond.tools.github.PullRequestUser
    options:
      show_source: true

### Exceptions

::: bond.tools.github.GitHubError
    options:
      show_source: true

::: bond.tools.github.RepoNotFoundError
    options:
      show_source: true

::: bond.tools.github.FileNotFoundError
    options:
      show_source: true

::: bond.tools.github.PRNotFoundError
    options:
      show_source: true

::: bond.tools.github.RateLimitedError
    options:
      show_source: true

::: bond.tools.github.AuthenticationError
    options:
      show_source: true

### Toolset

::: bond.tools.github.github_toolset
    options:
      show_source: false

---

## GitHunter Toolset

The GitHunter toolset provides forensic code ownership analysis tools.

### Protocol

::: bond.tools.githunter.GitHunterProtocol
    options:
      show_source: true

### Types

::: bond.tools.githunter.BlameResult
    options:
      show_source: true

::: bond.tools.githunter.FileExpert
    options:
      show_source: true

::: bond.tools.githunter.PRDiscussion
    options:
      show_source: true

::: bond.tools.githunter.AuthorProfile
    options:
      show_source: true

### Request Models

::: bond.tools.githunter.BlameLineRequest
    options:
      show_source: true

::: bond.tools.githunter.FindPRDiscussionRequest
    options:
      show_source: true

::: bond.tools.githunter.GetExpertsRequest
    options:
      show_source: true

### Toolset

::: bond.tools.githunter.githunter_toolset
    options:
      show_source: false
