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
