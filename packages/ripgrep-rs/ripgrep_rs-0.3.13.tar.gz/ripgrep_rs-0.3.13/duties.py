"""Project tasks."""

from __future__ import annotations

from duty import duty


@duty(capture=False)
def build(ctx):
    """Build the package."""
    ctx.run("maturin build --release")


@duty(capture=False)
def develop(ctx):
    """Install package in development mode."""
    ctx.run("maturin develop")


@duty(capture=False)
def test(ctx):
    """Run tests."""
    ctx.run("python test.py")


@duty(capture=False)
def clean(ctx):
    """Clean build artifacts."""
    ctx.run("cargo clean")
    ctx.run("rm -rf dist/ target/wheels/")


@duty(capture=False)
def update(ctx):
    """Update all dependencies."""
    ctx.run("cargo update")
    ctx.run("uv lock --upgrade")
    ctx.run("uv sync")


@duty(capture=False)
def lint(ctx):
    """Lint and format the code."""
    ctx.run("cargo fmt --all")
    ctx.run("cargo clippy --all-targets --all-features -- -D warnings")


@duty(capture=False)
def lint_check(ctx):
    """Check linting without fixing."""
    ctx.run("cargo fmt --all -- --check")
    ctx.run("cargo clippy --all-targets --all-features -- -D warnings")


@duty(capture=False)
def version(ctx, bump: str = "patch"):
    """Bump version (major|minor|patch)."""
    import re
    from pathlib import Path

    # Read current version from Cargo.toml
    cargo_toml = Path("Cargo.toml")
    content = cargo_toml.read_text()
    match = re.search(r'^version = "(\d+\.\d+\.\d+)"', content, re.MULTILINE)
    if not match:
        raise ValueError("Could not find version in Cargo.toml")

    old_version = match.group(1)
    major, minor, patch = map(int, old_version.split("."))

    if bump == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump == "minor":
        minor += 1
        patch = 0
    elif bump == "patch":
        patch += 1
    else:
        raise ValueError(f"Invalid bump type: {bump}")

    new_version = f"{major}.{minor}.{patch}"
    print(f"Bumping version: {old_version} -> {new_version}")

    # Update Cargo.toml
    content = re.sub(
        r'^version = "\d+\.\d+\.\d+"',
        f'version = "{new_version}"',
        content,
        count=1,
        flags=re.MULTILINE,
    )
    cargo_toml.write_text(content)

    # Update pyproject.toml
    pyproject = Path("pyproject.toml")
    py_content = pyproject.read_text()
    py_content = re.sub(
        r'^version = "\d+\.\d+\.\d+"',
        f'version = "{new_version}"',
        py_content,
        count=1,
        flags=re.MULTILINE,
    )
    pyproject.write_text(py_content)

    # Update Cargo.lock
    ctx.run("cargo check")

    # Git operations
    ctx.run("git add Cargo.toml Cargo.lock pyproject.toml")
    ctx.run(f'git commit -m "chore: bump version to {new_version}"')
    ctx.run(f"git tag v{new_version}")
    print(f"Created tag: v{new_version}")
    print("Run 'git push && git push --tags' to trigger release")
