"""CLI commands for pulse-workflow-mcp."""

import shutil
import sys
from pathlib import Path


def get_skills_source() -> Path:
    """Get the path to bundled skills."""
    return Path(__file__).parent / "skills"


def get_skills_dest() -> Path:
    """Get the destination path for skills."""
    return Path.home() / ".claude" / "skills"


def install_skills(force: bool = False) -> None:
    """Install Pulse skills to ~/.claude/skills/"""
    src = get_skills_source()
    dest = get_skills_dest()

    if not src.exists():
        print(f"Error: Skills not found at {src}", file=sys.stderr)
        sys.exit(1)

    # Create destination if needed
    dest.mkdir(parents=True, exist_ok=True)

    skill_dirs = ["pulse", "pulse-create", "pulse-edit", "pulse-publish"]
    installed = []
    skipped = []

    for skill in skill_dirs:
        skill_src = src / skill
        skill_dest = dest / skill

        if not skill_src.exists():
            continue

        if skill_dest.exists() and not force:
            skipped.append(skill)
            continue

        if skill_dest.exists():
            shutil.rmtree(skill_dest)

        shutil.copytree(skill_src, skill_dest)
        installed.append(skill)

    if installed:
        print(f"Installed skills: {', '.join(installed)}")
    if skipped:
        print(f"Skipped (already exist): {', '.join(skipped)}")
        print("Use --force to overwrite existing skills")

    print(f"\nSkills installed to: {dest}")


def uninstall_skills() -> None:
    """Remove Pulse skills from ~/.claude/skills/"""
    dest = get_skills_dest()
    skill_dirs = ["pulse", "pulse-create", "pulse-edit", "pulse-publish"]
    removed = []

    for skill in skill_dirs:
        skill_dest = dest / skill
        if skill_dest.exists():
            shutil.rmtree(skill_dest)
            removed.append(skill)

    if removed:
        print(f"Removed skills: {', '.join(removed)}")
    else:
        print("No Pulse skills found to remove")


def print_usage() -> None:
    """Print CLI usage."""
    print("""pulse-workflow-mcp - MCP server for Pulse workflows

Usage:
    pulse-workflow-mcp                  Start the MCP server
    pulse-workflow-mcp install-skills   Install skills to ~/.claude/skills/
    pulse-workflow-mcp install-skills --force   Overwrite existing skills
    pulse-workflow-mcp uninstall-skills Remove skills from ~/.claude/skills/
    pulse-workflow-mcp --help           Show this help
""")


def main() -> None:
    """CLI entry point."""
    args = sys.argv[1:]

    if not args:
        # No args = start server
        from .server import main as server_main

        server_main()
        return

    cmd = args[0]

    if cmd in ("--help", "-h", "help"):
        print_usage()
    elif cmd == "install-skills":
        force = "--force" in args or "-f" in args
        install_skills(force=force)
    elif cmd == "uninstall-skills":
        uninstall_skills()
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
