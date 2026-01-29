"""Project initialization for noot."""

import subprocess
from pathlib import Path


def init_project(target_dir: Path, project_name: str) -> None:
    """
    Initialize a noot project in the target directory.

    Creates:
    - .git/ (git repository)
    - pyproject.toml (project configuration)
    - src/{project_name}/__init__.py (package)
    - cli/{project_name}.py (sample CLI)
    - tests/test_{project_name}.py (sample test)
    - .cassettes/cli/ (for LLM recordings)
    - .cassettes/http/ (for API recordings)

    Args:
        target_dir: Directory to initialize (usually cwd)
        project_name: Name of the project (lowercase, underscores allowed)

    Raises:
        FileExistsError: If files would be overwritten
        RuntimeError: If template files are missing
    """
    # Define file paths
    pyproject_file = target_dir / "pyproject.toml"
    src_init_file = target_dir / "src" / project_name / "__init__.py"
    cli_file = target_dir / "cli" / f"{project_name}.py"
    test_file = target_dir / "tests" / f"test_{project_name}.py"

    # Check for existing files
    for filepath in [pyproject_file, src_init_file, cli_file, test_file]:
        if filepath.exists():
            raise FileExistsError(
                f"File already exists: {filepath}\n"
                "Remove it or run init in a different directory."
            )

    # Find template files
    templates_dir = Path(__file__).parent / "templates"
    pyproject_template = templates_dir / "pyproject.toml.template"
    cli_template = templates_dir / "cli.py.template"
    test_template = templates_dir / "test_cli.py.template"

    for template in [pyproject_template, cli_template, test_template]:
        if not template.exists():
            raise RuntimeError(
                f"Template not found: {template}\n"
                "Package may be incorrectly installed."
            )

    # Initialize git repository
    subprocess.run(["git", "init"], cwd=target_dir, check=True, capture_output=True)

    # Create directory structure
    (target_dir / "src" / project_name).mkdir(parents=True, exist_ok=True)
    (target_dir / "cli").mkdir(exist_ok=True)
    (target_dir / "tests").mkdir(exist_ok=True)

    # Create cassettes directories
    (target_dir / ".cassettes" / "cli").mkdir(parents=True, exist_ok=True)
    (target_dir / ".cassettes" / "http").mkdir(parents=True, exist_ok=True)

    # Read templates and substitute project_name
    def sub(template: Path) -> str:
        return template.read_text().replace("{{project_name}}", project_name)

    pyproject_content = sub(pyproject_template)
    cli_content = sub(cli_template)
    test_content = sub(test_template)

    # Write files
    pyproject_file.write_text(pyproject_content)
    cli_file.write_text(cli_content)
    test_file.write_text(test_content)
    src_init_file.touch()

    # Make CLI executable
    cli_file.chmod(0o755)
