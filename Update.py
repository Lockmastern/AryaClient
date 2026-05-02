import sys
import os
import urllib.request
import subprocess
import tempfile

# ── Bootstrap: resolve project root and load local config ────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from main.config.config import (
    title,
    main_version,
    updater_version,
    author,
    update_repo,
    config_repo,
)

# ── Helpers ───────────────────────────────────────────────────────────────────

def fetch_text(url: str) -> str | None:
    """Download raw text from a URL. Returns None on failure."""
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        print(f"[ERROR] Could not fetch {url}: {e}")
        return None


def parse_version(source: str, key: str) -> str | None:
    """
    Extract a version string from a Python config source.
    Matches lines like:  main_version = '1.2.3'
    Requires an exact key match (nothing between key and =).
    """
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith(key) and stripped[len(key):].lstrip().startswith("="):
            parts = stripped.split("=", 1)
            if len(parts) == 2:
                return parts[1].strip().strip("'\"")
    return None


def version_tuple(v: str) -> tuple[int, ...]:
    """Convert '1.2.3' → (1, 2, 3) for numeric comparison."""
    try:
        return tuple(int(x) for x in v.split("."))
    except ValueError:
        return (0,)


def write_file(path: str, content: str) -> bool:
    """Write content to path. Returns True on success."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except OSError as e:
        print(f"[ERROR] Could not write {path}: {e}")
        return False


def replace_self(new_source: str, remote_config_src: str) -> None:
    """
    Write config.py first (so the re-launched process sees the new version),
    then atomically overwrite this script and spawn a fresh copy of it.
    """
    # 1. Persist the new config before anything else
    config_path = os.path.join(SCRIPT_DIR, "main", "config", "config.py")
    if write_file(config_path, remote_config_src):
        print("[✓] config.py updated")

    # 2. Atomically overwrite Update.py via a temp file
    updater_path = os.path.abspath(__file__)
    tmp_fd, tmp_path = tempfile.mkstemp(dir=SCRIPT_DIR, suffix=".py")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            f.write(new_source)
        os.replace(tmp_path, updater_path)
    except Exception as e:
        os.unlink(tmp_path)
        print(f"[ERROR] Self-update failed: {e}")
        return

    # 3. Spawn the updated script and exit this old process
    print("[UPDATER] Self-update complete. Re-launching …\n")
    subprocess.Popen([sys.executable, updater_path] + sys.argv[1:])
    sys.exit(0)


# ── Main logic ────────────────────────────────────────────────────────────────

def main() -> None:
    print(f"{'─' * 50}")
    print(f"  {title}  |  Update Manager")
    print(f"  Author : {author}")
    print(f"  Local  : main={main_version}  updater={updater_version}")
    print(f"{'─' * 50}\n")

    # 1. Fetch remote config for authoritative version numbers
    print("[*] Fetching remote config …")
    remote_config_src = fetch_text(config_repo)
    if remote_config_src is None:
        print("[WARN] Could not reach GitHub. Launching local copy.\n")
        launch_main()
        return

    remote_main_ver    = parse_version(remote_config_src, "main_version")
    remote_updater_ver = parse_version(remote_config_src, "updater_version")

    if not remote_main_ver or not remote_updater_ver:
        print("[WARN] Could not parse remote versions. Launching local copy.\n")
        launch_main()
        return

    print(f"[*] Remote : main={remote_main_ver}  updater={remote_updater_ver}\n")

    # 2. Self-update check (always before main update)
    if version_tuple(remote_updater_ver) > version_tuple(updater_version):
        print(f"[UPDATE] Updater {updater_version} → {remote_updater_ver}")
        new_updater_src = fetch_text(update_repo)
        if new_updater_src is None:
            print("[WARN] Could not download new updater. Skipping self-update.")
        else:
            replace_self(new_updater_src, remote_config_src)
            # replace_self() does not return on success
    else:
        print("[OK] Updater is up to date.")

    # 3. Main project update check
    if version_tuple(remote_main_ver) > version_tuple(main_version):
        print(f"[UPDATE] Main {main_version} → {remote_main_ver}")
        update_main_files(remote_config_src, remote_main_ver)
    else:
        print("[OK] Main project is up to date.")

    # 4. Launch
    print()
    launch_main()


def update_main_files(remote_config_src: str, new_ver: str) -> None:
    """Update local files to match the remote version."""
    config_path = os.path.join(SCRIPT_DIR, "main", "config", "config.py")
    if write_file(config_path, remote_config_src):
        print(f"[✓] config.py → {new_ver}")

    # Add more files here as the project grows:
    # src = fetch_text(some_raw_url)
    # if src: write_file(os.path.join(SCRIPT_DIR, "main", "core.py"), src)


def launch_main() -> None:
    """Spawn main.py as a fully independent process, then exit."""
    main_path = os.path.join(SCRIPT_DIR, "main.py")
    if not os.path.exists(main_path):
        print(f"[ERROR] main.py not found at: {main_path}")
        sys.exit(1)
    print(f"[*] Launching {title} …\n")
    subprocess.Popen(
        [sys.executable, main_path],
        cwd=SCRIPT_DIR,
        close_fds=True,
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
# extra little update comment
