import subprocess

def verify_repo():
    """
    Verify that the current directory is inside a Git repository.
    """

    result =  subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    return result.returncode == 0

def stage_all_changes():
    """
    Stage all changes in the Git repository.
    """
    subprocess.run(
        ["git", "add", "."]
    )

def has_staged_changes():
    """
    Check if there are any staged changes in the Git repository.
    """
    result = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    return result.returncode == 1

def get_staged_diff():
    """
    Returns the text of the staged changes.
    """
    result = subprocess.run(
        ["git", "diff", "--staged"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",  # <- prevents crashes
    )

    if result.returncode != 0:
        return ""

    return result.stdout or ""

def push_changes():
    """
    Push committed changes to the remote repository.
    """
    subprocess.run(
        ["git", "push"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

def commit_changes(commit_message: str):
    """
    Commit staged changes with the provided commit message.
    """
    subprocess.run(
        ["git", "commit", "-m", commit_message],
        check=True
    )

def get_modified_files():
    """
    Get a list of modified files in the Git repository.
    """

    result = subprocess.run(
        ["git", "status", "--porcelain"],
        stdout=subprocess.PIPE,
        text=True,
    )

    files = []
    for line in result.stdout.splitlines():
        files.append(line[3:])

    return files


def stage_file(path: str):
    """
    Stage a specific file in the Git repository.
    """
    
    subprocess.run(["git", "add", path])
