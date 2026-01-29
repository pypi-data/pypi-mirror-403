import subprocess
from typing import Optional, Tuple


def run_git_command(args: list, check: bool = True) -> Tuple[bool, str]:
    """Run a git command and return (success, output)"""
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            check=check,
        )
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr.strip()
    except FileNotFoundError:
        return False, "git command not found"


def get_current_branch() -> Optional[str]:
    """Get the current git branch"""
    success, output = run_git_command(["branch", "--show-current"], check=False)
    return output if success and output else None


def get_remote_url(remote: str = "origin") -> Optional[str]:
    """Get the remote URL"""
    success, output = run_git_command(
        ["config", "--get", f"remote.{remote}.url"], check=False
    )
    return output if success else None


def checkout_branch(branch: str, create: bool = False) -> bool:
    """Checkout a branch"""
    args = ["checkout"]
    if create:
        args.append("-b")
    args.append(branch)
    success, _ = run_git_command(args, check=False)
    return success


def fetch_ref(remote: str, ref: str) -> bool:
    """Fetch a specific ref from remote"""
    success, _ = run_git_command(["fetch", remote, ref], check=False)
    return success


def get_diff(base: str, head: str) -> Optional[str]:
    """Get diff between two refs"""
    success, output = run_git_command(["diff", f"{base}...{head}"], check=False)
    return output if success else None


def get_merge_base(ref1: str, ref2: str) -> Optional[str]:
    """Get merge base between two refs"""
    success, output = run_git_command(["merge-base", ref1, ref2], check=False)
    return output if success else None
