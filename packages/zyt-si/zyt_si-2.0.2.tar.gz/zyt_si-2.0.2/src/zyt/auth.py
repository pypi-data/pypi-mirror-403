import shutil
import subprocess
def detect_auth_method():
    """
    Returns: 'gh', 'ssh', or 'https'
    """
    def has_cmd(cmd):
        return shutil.which(cmd) is not None
    if has_cmd("gh"):
        try:
            subprocess.run(
                ["gh", "auth", "status"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
            return "gh"
        except subprocess.CalledProcessError:
            pass
    try:
        subprocess.run(
            ["ssh", "-T", "git@github.com"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5
        )
        return "ssh"
    except Exception:
        pass
    
    return "https"