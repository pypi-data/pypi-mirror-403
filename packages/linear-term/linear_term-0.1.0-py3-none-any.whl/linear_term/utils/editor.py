"""External editor integration for Linear TUI."""

import os
import subprocess
import tempfile
from pathlib import Path


def get_editor() -> str:
    """Get the user's preferred editor."""
    return os.environ.get("EDITOR") or os.environ.get("VISUAL") or "vi"


def edit_in_external_editor(
    content: str = "",
    prefix: str = "linear-term-",
    suffix: str = ".md",
) -> str | None:
    """
    Open content in external editor and return edited content.

    Returns None if editing was cancelled or failed.
    """
    editor = get_editor()

    # Create temp file with content
    with tempfile.NamedTemporaryFile(
        mode="w",
        prefix=prefix,
        suffix=suffix,
        delete=False,
    ) as f:
        f.write(content)
        temp_path = Path(f.name)

    try:
        # Get original modification time
        original_mtime = temp_path.stat().st_mtime

        # Open editor
        result = subprocess.run(
            [editor, str(temp_path)],
            check=True,
        )

        if result.returncode != 0:
            return None

        # Check if file was modified
        new_mtime = temp_path.stat().st_mtime
        if new_mtime == original_mtime:
            # File wasn't modified, treat as cancel
            return None

        # Read edited content
        edited_content = temp_path.read_text()
        return edited_content

    except subprocess.CalledProcessError:
        return None
    except FileNotFoundError:
        return None
    finally:
        # Clean up temp file
        try:
            temp_path.unlink()
        except Exception:
            pass


def edit_description_with_template(
    current_description: str = "",
    issue_identifier: str = "",
) -> str | None:
    """
    Edit issue description in external editor with a template.

    Returns edited description or None if cancelled.
    """
    template = f"""# Editing description for {issue_identifier}
# Lines starting with # will be ignored.
# Save and close the editor to apply changes.
# Leave empty or don't save to cancel.

{current_description}"""

    result = edit_in_external_editor(template, prefix=f"linear-{issue_identifier}-")

    if result is None:
        return None

    # Remove comment lines
    lines = result.split("\n")
    content_lines = [line for line in lines if not line.startswith("#")]
    edited = "\n".join(content_lines).strip()

    return edited if edited else None
