"""GitHub request and error models.

Pydantic models for GitHub tool inputs and error responses.
"""

from typing import Annotated

from pydantic import BaseModel, Field


class GetRepoRequest(BaseModel):
    """Request to get repository metadata.

    Agent Usage: Use this to get basic information about a GitHub repository
    including description, default branch, topics, and statistics.
    """

    owner: Annotated[
        str,
        Field(description="Repository owner (username or organization)"),
    ]

    repo: Annotated[
        str,
        Field(description="Repository name"),
    ]


class ListFilesRequest(BaseModel):
    """Request to list files in a directory.

    Agent Usage: Use this to browse the file structure of a repository.
    Start from the root (empty path) and navigate into subdirectories.
    """

    owner: Annotated[
        str,
        Field(description="Repository owner"),
    ]

    repo: Annotated[
        str,
        Field(description="Repository name"),
    ]

    path: Annotated[
        str,
        Field(default="", description="Path relative to repo root (empty for root)"),
    ]

    ref: Annotated[
        str | None,
        Field(default=None, description="Branch, tag, or commit SHA (default branch if None)"),
    ]


class ReadFileRequest(BaseModel):
    """Request to read file content.

    Agent Usage: Use this to read the contents of a specific file.
    Combine with list_files to find files first.
    """

    owner: Annotated[
        str,
        Field(description="Repository owner"),
    ]

    repo: Annotated[
        str,
        Field(description="Repository name"),
    ]

    path: Annotated[
        str,
        Field(description="Path to file relative to repo root"),
    ]

    ref: Annotated[
        str | None,
        Field(default=None, description="Branch, tag, or commit SHA (default branch if None)"),
    ]


class SearchCodeRequest(BaseModel):
    """Request to search code.

    Agent Usage: Use this to find code containing specific terms, patterns,
    or identifiers. Can search within a specific repo or across GitHub.
    """

    query: Annotated[
        str,
        Field(description="Search query (e.g., 'class UserService', 'TODO fix')"),
    ]

    owner: Annotated[
        str | None,
        Field(default=None, description="Optional owner to scope search"),
    ]

    repo: Annotated[
        str | None,
        Field(default=None, description="Optional repo name to scope search (requires owner)"),
    ]

    limit: Annotated[
        int,
        Field(default=10, ge=1, le=100, description="Maximum results to return"),
    ]


class GetCommitsRequest(BaseModel):
    """Request to get commit history.

    Agent Usage: Use this to see recent changes to a file or repository.
    Useful for understanding when and why code changed.
    """

    owner: Annotated[
        str,
        Field(description="Repository owner"),
    ]

    repo: Annotated[
        str,
        Field(description="Repository name"),
    ]

    path: Annotated[
        str | None,
        Field(default=None, description="Optional file path to filter commits"),
    ]

    ref: Annotated[
        str | None,
        Field(default=None, description="Branch, tag, or commit to start from"),
    ]

    limit: Annotated[
        int,
        Field(default=10, ge=1, le=100, description="Maximum commits to return"),
    ]


class GetPRRequest(BaseModel):
    """Request to get pull request details.

    Agent Usage: Use this to get information about a specific PR
    including title, description, author, and merge status.
    """

    owner: Annotated[
        str,
        Field(description="Repository owner"),
    ]

    repo: Annotated[
        str,
        Field(description="Repository name"),
    ]

    number: Annotated[
        int,
        Field(ge=1, description="Pull request number"),
    ]


class Error(BaseModel):
    """Error response from GitHub operations.

    Used as union return type: `RepoInfo | Error`, `list[TreeEntry] | Error`, etc.
    """

    description: Annotated[
        str,
        Field(description="Error message explaining what went wrong"),
    ]
