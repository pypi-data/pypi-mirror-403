"""CLI commands common to all repos."""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import toml
import typer

# Import cloud helper lazily inside functions to avoid heavy deps at module load


def test_github_actions_locally():
    """Run the script test_pytest_in_github_actions_container.sh.sh."""
    script_path = ".devcontainer/scripts/test_pytest_in_github_actions_container.sh"

    try:
        subprocess.check_call(["bash", script_path])
        print("Script ran successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running the script: {e}")


def delete_local_branch(branch_name: str, folder_path: str):
    """Delete a local Git branch after fetching with pruning.

    Args:
        branch_name: Name of the branch to delete
        folder_path: Path to the git repository folder
    """
    try:
        # Store current working directory
        original_dir = os.getcwd()

        # Change to the specified directory
        os.chdir(folder_path)
        print(f"Changed to directory: {folder_path}")

        # Delete the specified branch
        delete_branch_cmd = ["git", "branch", "-D", branch_name]
        subprocess.run(delete_branch_cmd, check=True)
        print(f"Deleted branch: {branch_name}")

        # Fetch changes from the remote repository and prune obsolete branches
        fetch_prune_cmd = ["git", "fetch", "-p"]
        subprocess.run(fetch_prune_cmd, check=True)
        print("Fetched changes and pruned obsolete branches")

    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running Git commands: {e}")
    finally:
        # Always return to the original directory
        os.chdir(original_dir)


def get_current_version_from_toml(file_path="pyproject.toml"):
    """Reads the version from a pyproject.toml file."""
    try:
        with open(file_path, "r") as f:
            content = f.read()
        version_match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
        if version_match:
            return version_match.group(1)
        else:
            raise ValueError(f"Could not find version string in {file_path}")
    except FileNotFoundError:
        raise FileNotFoundError(f"{file_path} not found.")
    except Exception as e:
        raise e


def build_and_upload_wheel(bump_part: str = "patch"):
    """Build a Python wheel and upload to PyPI using UV.

    Automatically increments the version number in pyproject.toml before building
    based on the bump_part argument ('major', 'minor', 'patch').

    Expects PyPI authentication to be configured via the environment variable:
    - UV_PUBLISH_TOKEN

    Args:
        bump_part (str): The part of the version to bump. Defaults to 'patch'.
    """
    if bump_part not in ["major", "minor", "patch"]:
        print(
            f"Error: Invalid bump_part '{bump_part}'. Must be 'major', 'minor', or 'patch'."
        )
        return

    # ANSI color codes
    BLUE = "\033[94m"
    RESET = "\033[0m"

    # --- Authentication Setup ---
    token = os.environ.get("UV_PUBLISH_TOKEN")

    if not token:
        print("Error: PyPI authentication not configured.")
        print(
            "Please set the UV_PUBLISH_TOKEN environment variable with your PyPI API token."
        )
        return

    # Build the command with token authentication
    # IMPORTANT: Mask token for printing
    publish_cmd_safe_print = ["uv", "publish", "--token", "*****"]
    publish_cmd = ["uv", "publish", "--token", token]
    print("Using UV_PUBLISH_TOKEN for authentication.")

    # Use standard pyproject.toml
    pyproject_path = "pyproject.toml"
    if not Path(pyproject_path).exists():
        print("Error: pyproject.toml not found in current directory.")
        return
    current_version = None  # Initialize in case the first try block fails

    try:
        # --- Clean dist directory ---
        dist_dir = Path("dist")
        if dist_dir.exists():
            print(f"Removing existing build directory: {dist_dir}")
            shutil.rmtree(dist_dir)
        # --- End Clean dist directory ---

        # --- Version Bumping Logic ---
        current_version = get_current_version_from_toml(pyproject_path)
        print(f"Current version: {current_version}")

        try:
            major, minor, patch = map(int, current_version.split("."))
        except ValueError:
            print(
                f"Error: Could not parse version '{current_version}'. Expected format X.Y.Z"
            )
            return

        if bump_part == "major":
            major += 1
            minor = 0
            patch = 0
        elif bump_part == "minor":
            minor += 1
            patch = 0
        else:  # patch
            patch += 1

        new_version = f"{major}.{minor}.{patch}"
        print(f"Bumping {bump_part} version to: {new_version}")

        # Read pyproject.toml
        with open(pyproject_path, "r") as f:
            content = f.read()

        # Replace the version string
        pattern = re.compile(
            f'^version\s*=\s*"{re.escape(current_version)}"', re.MULTILINE
        )
        new_content, num_replacements = pattern.subn(
            f'version = "{new_version}"', content
        )

        if num_replacements == 0:
            print(
                f"Error: Could not find 'version = \"{current_version}\"' in {pyproject_path}"
            )
            return  # Exit before build/publish if version wasn't updated
        if num_replacements > 1:
            print(
                f"Warning: Found multiple version lines for '{current_version}'. Only the first was updated."
            )

        # Write the updated content back
        with open(pyproject_path, "w") as f:
            f.write(new_content)
        print(f"Updated {pyproject_path} with version {new_version}")

        # --- End Version Bumping Logic ---

        # Build wheel and sdist
        build_cmd = ["uv", "build"]
        print(f"Running command: {BLUE}{' '.join(build_cmd)}{RESET}")
        subprocess.run(build_cmd, check=True)

        # Upload to PyPI
        print(f"Running command: {BLUE}{' '.join(publish_cmd_safe_print)}{RESET}")
        subprocess.run(publish_cmd, check=True)

        print(f"Successfully built and uploaded version {new_version} to PyPI")

        # Re-install DHT in Pixi environment when building from DHT itself
        try:
            proj_toml = toml.load(pyproject_path)
            proj_name = proj_toml.get("project", {}).get("name")
            if proj_name == "dayhoff-tools":
                print("Re-installing dayhoff-tools into the Pixi environment...")
                reinstall_cmd = ["pixi", "install"]
                print(f"Running command: {BLUE}{' '.join(reinstall_cmd)}{RESET}")
                subprocess.run(reinstall_cmd, check=True)
                print("dayhoff-tools reinstalled in the Pixi environment.")
        except subprocess.CalledProcessError as e:
            print(f"Warning: Failed to reinstall dayhoff-tools locally: {e}")
        except Exception:
            pass  # Not dayhoff-tools or couldn't read toml

    except FileNotFoundError:
        print(f"Error: {pyproject_path} not found.")
        # No version change happened, so no rollback needed
    except subprocess.CalledProcessError as e:
        print(f"Error during build/upload: {e}")
        # Attempt to roll back version change only if it was bumped successfully
        if current_version and new_version:
            try:
                print(
                    f"Attempting to revert version in {pyproject_path} back to {current_version}..."
                )
                with open(pyproject_path, "r") as f:
                    content_revert = f.read()
                # Use new_version in pattern for reverting
                pattern_revert = re.compile(
                    f'^version\s*=\s*"{re.escape(new_version)}"', re.MULTILINE
                )
                reverted_content, num_revert = pattern_revert.subn(
                    f'version = "{current_version}"', content_revert
                )
                if num_revert > 0:
                    with open(pyproject_path, "w") as f:
                        f.write(reverted_content)
                    print(f"Successfully reverted version in {pyproject_path}.")
                else:
                    print(
                        f"Warning: Could not find version {new_version} to revert in {pyproject_path}."
                    )

            except Exception as revert_e:
                print(f"Warning: Failed to revert version change: {revert_e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        # Attempt rollback if version was bumped
        if current_version and "new_version" in locals() and new_version:
            try:
                print(f"Attempting to revert version back to {current_version}...")
                with open(pyproject_path, "r") as f:
                    content_revert = f.read()
                pattern_revert = re.compile(
                    f'^version\\s*=\\s*"{re.escape(new_version)}"', re.MULTILINE
                )
                reverted_content, num_revert = pattern_revert.subn(
                    f'version = "{current_version}"', content_revert
                )
                if num_revert > 0:
                    with open(pyproject_path, "w") as f:
                        f.write(reverted_content)
                    print("Successfully reverted version in pyproject.toml.")
                else:
                    print(f"Warning: Could not find version {new_version} to revert.")
            except Exception as revert_e:
                print(f"Warning: Failed to revert version change: {revert_e}")


