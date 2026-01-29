import enum

class PySortMode:
    kind: PySortModeKind
    reverse: bool = False

    def __init__(self, kind: PySortModeKind, reverse: bool = False): ...

class PySortModeKind(enum.Enum):
    Path = enum.auto()
    LastModified = enum.auto()
    LastAccessed = enum.auto()
    Created = enum.auto()

def search(
    patterns: list[str],
    paths: list[str] | None = None,
    globs: list[str] | None = None,
    heading: bool | None = None,
    after_context: int | None = None,
    before_context: int | None = None,
    separator_field_context: str | None = None,
    separator_field_match: str | None = None,
    separator_context: str | None = None,
    sort: PySortMode | None = None,
    max_count: int | None = None,
    line_number: bool | None = None,
    multiline: bool | None = None,
    case_sensitive: bool | None = None,
    smart_case: bool | None = None,
    no_ignore: bool | None = None,
    hidden: bool | None = None,
    json: bool | None = None,
) -> list[str]: ...
def files(
    patterns: list[str],
    paths: list[str] | None = None,
    globs: list[str] | None = None,
    heading: bool | None = None,
    after_context: int | None = None,
    before_context: int | None = None,
    separator_field_context: str | None = None,
    separator_field_match: str | None = None,
    separator_context: str | None = None,
    sort: PySortMode | None = None,
    max_count: int | None = None,
    line_number: bool | None = None,
    multiline: bool | None = None,
    case_sensitive: bool | None = None,
    smart_case: bool | None = None,
    no_ignore: bool | None = None,
    hidden: bool | None = None,
    json: bool | None = None,
    include_dirs: bool | None = None,
    max_depth: int | None = None,
    absolute: bool | None = None,
    relative_to: str | None = None,
) -> list[str]: ...

class FileInfo:
    """File information returned by files_with_info."""

    name: str
    """Full path to the file."""
    size: int
    """File size in bytes."""
    type: str
    """File type: 'file' or 'directory'."""
    created: float
    """Creation time as Unix timestamp."""
    islink: bool
    """Whether the file is a symlink."""
    mode: int
    """File mode/permissions."""
    uid: int
    """User ID (Unix only, 0 on Windows)."""
    gid: int
    """Group ID (Unix only, 0 on Windows)."""
    mtime: float
    """Modification time as Unix timestamp."""
    ino: int
    """Inode number (Unix only, 0 on Windows)."""
    nlink: int
    """Number of hard links."""

def files_with_info(
    patterns: list[str],
    paths: list[str] | None = None,
    globs: list[str] | None = None,
    sort: PySortMode | None = None,
    no_ignore: bool | None = None,
    hidden: bool | None = None,
    include_dirs: bool | None = None,
    max_depth: int | None = None,
    absolute: bool | None = None,
) -> dict[str, FileInfo]:
    """List files with detailed metadata.

    Returns a dictionary mapping file paths to FileInfo objects,
    similar to fsspec's detail=True mode.
    """
    ...
