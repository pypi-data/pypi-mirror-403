#!/usr/bin/env python3
import os
import sys
import re
import subprocess
import argparse
from datetime import datetime

def run_command(command, shell=True, env=None):
    """Run a shell command and return its output."""
    print(f"Executing: {command}")
    result = subprocess.run(command, shell=shell, env=env, text=True)
    if result.returncode != 0:
        print(f"Error executing command: {command}")
        sys.exit(1)
    return result

def update_version(increment_type="patch"):
    """Update version in pyproject.toml."""
    with open("pyproject.toml", "r") as f:
        content = f.read()

    version_match = re.search(r'version = "(\d+)\.(\d+)\.(\d+)"', content)
    if not version_match:
        print("Could not find version in pyproject.toml")
        sys.exit(1)

    major, minor, patch = map(int, version_match.groups())
    
    if increment_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif increment_type == "minor":
        minor += 1
        patch = 0
    else:
        patch += 1

    new_version = f"{major}.{minor}.{patch}"
    new_content = re.sub(r'version = "\d+\.\d+\.\d+"', f'version = "{new_version}"', content)

    with open("pyproject.toml", "w") as f:
        f.write(new_content)
    
    print(f"Updated version to {new_version}")
    return new_version

def update_changelog(version, patchnotes):
    """Update CHANGELOG.md with new version and notes."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    new_entry = f"\n## [{version}] - {date_str}\n\n"
    
    if patchnotes:
        if patchnotes.startswith("- "):
            new_entry += patchnotes + "\n"
        else:
            # Format as bullet points if it's a multiline string without bullets
            lines = patchnotes.strip().split("\n")
            for line in lines:
                new_entry += f"- {line.strip()}\n"
    else:
        new_entry += "- Minor updates and improvements\n"

    # Read existing changelog
    changelog_path = "CHANGELOG.md"
    if os.path.exists(changelog_path):
        with open(changelog_path, "r") as f:
            old_content = f.read()
        
        # Insert after header if it exists
        if "# Changelog" in old_content:
            parts = old_content.split("# Changelog", 1)
            final_content = parts[0] + "# Changelog" + new_entry + parts[1]
        else:
            final_content = new_entry + old_content
    else:
        final_content = "# Changelog\n" + new_entry

    with open(changelog_path, "w") as f:
        f.write(final_content)
    
    print("Updated CHANGELOG.md")

def main():
    parser = argparse.ArgumentParser(description="Update version, changelog, and publish to PyPI")
    parser.add_argument("notes", help="Patch notes for the new version")
    parser.add_argument("--type", choices=["patch", "minor", "major"], default="patch", help="Type of version increment")
    parser.add_argument("--skip-publish", action="store_true", help="Only update files, don't build or publish")
    
    args = parser.parse_args()

    # 1. Update files
    new_version = update_version(args.type)
    update_changelog(new_version, args.notes)

    if args.skip_publish:
        print("Skipping build and publish steps.")
        return

    # 2. Clean old builds
    print("Cleaning old builds...")
    if os.path.exists("dist"):
        import shutil
        shutil.rmtree("dist")
    if os.path.exists("build"):
        import shutil
        shutil.rmtree("build")

    # 3. Build
    # Using python3 -m build as suggested in PUBLISHING.md
    run_command("python3 -m build")

    # 4. Publish
    print("Publishing to PyPI...")
    # Source .env and export variables for twine
    # Note: We use a subshell to keep env variables scoped
    publish_cmd = (
        "source .env && "
        "export TWINE_USERNAME=$PYPI_USERNAME && "
        "export TWINE_PASSWORD=$PYPI_TOKEN && "
        "twine upload dist/*"
    )
    
    # We use executable='/bin/bash' to ensure 'source' works
    subprocess.run(publish_cmd, shell=True, executable='/bin/bash', check=True)

    print(f"\nSuccessfully published version {new_version} to PyPI!")

if __name__ == "__main__":
    main()
