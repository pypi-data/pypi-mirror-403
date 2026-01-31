import subprocess


def command_exists(command: str) -> bool:
    """Check if a system command exists using subprocess.call()."""
    # Use 'which' for Unix, 'where' for Windows
    cmd = ["which", command] if subprocess.os.name == "posix" else ["where", command]

    # Run the command, redirect stdout/stderr to avoid cluttering output
    return_code = subprocess.call(
        cmd,
        stdout=subprocess.PIPE,  # Suppress stdout
        stderr=subprocess.PIPE,  # Suppress stderr
    )

    # Return True if command exists (return code 0), else False
    return return_code == 0
