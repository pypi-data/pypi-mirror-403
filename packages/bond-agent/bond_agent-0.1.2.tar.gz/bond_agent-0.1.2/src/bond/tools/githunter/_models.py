"""GitHunter request and error models.

Pydantic models for GitHunter tool inputs and error responses.
"""

from typing import Annotated

from pydantic import BaseModel, Field


class BlameLineRequest(BaseModel):
    """Request to get blame information for a specific line.

    Agent Usage: Use this when you need to know who last modified a specific
    line of code, what commit changed it, and when.
    """

    repo_path: Annotated[
        str,
        Field(description="Path to the git repository root"),
    ]

    file_path: Annotated[
        str,
        Field(description="Path to file relative to repo root"),
    ]

    line_no: Annotated[
        int,
        Field(ge=1, description="Line number to blame (1-indexed)"),
    ]


class FindPRDiscussionRequest(BaseModel):
    """Request to find PR discussion for a commit.

    Agent Usage: Use this when you have a commit hash and want to find
    the pull request discussion that introduced it.
    """

    repo_path: Annotated[
        str,
        Field(description="Path to the git repository root"),
    ]

    commit_hash: Annotated[
        str,
        Field(min_length=7, description="Full or abbreviated commit SHA"),
    ]


class GetExpertsRequest(BaseModel):
    """Request to get file experts based on commit frequency.

    Agent Usage: Use this when you need to identify who has the most
    knowledge about a file based on their commit history.
    """

    repo_path: Annotated[
        str,
        Field(description="Path to the git repository root"),
    ]

    file_path: Annotated[
        str,
        Field(description="Path to file relative to repo root"),
    ]

    window_days: Annotated[
        int,
        Field(default=90, ge=0, description="Days of history to consider (0=all time)"),
    ]

    limit: Annotated[
        int,
        Field(default=3, ge=1, le=10, description="Maximum number of experts to return"),
    ]


class Error(BaseModel):
    """Error response from GitHunter operations.

    Used as union return type: `BlameResult | Error`, `PRDiscussion | None | Error`, etc.
    """

    description: Annotated[
        str,
        Field(description="Error message explaining what went wrong"),
    ]
