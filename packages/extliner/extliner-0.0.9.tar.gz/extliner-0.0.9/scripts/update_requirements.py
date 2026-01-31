import requests
import re
from pathlib import Path

PYPI_URL = "https://pypi.org/pypi/{}/json"

REQ_FILE = "requirements.txt"

# matches: package==1.2.3
REQ_PATTERN = re.compile(
    r"^\s*([A-Za-z0-9_.-]+)\s*==\s*([^\s#]+)"
)


def get_latest_version(package: str) -> str | None:
    try:
        resp = requests.get(PYPI_URL.format(package), timeout=5)
        if resp.status_code == 200:
            return resp.json()["info"]["version"]
    except Exception:
        pass
    return None


def update_requirements(path: Path):
    updated_lines = []
    changed = False

    for line in path.read_text().splitlines():
        stripped = line.strip()

        # keep comments, blanks, editable installs, urls
        if (
            not stripped
            or stripped.startswith("#")
            or stripped.startswith("-e")
            or "://" in stripped
        ):
            updated_lines.append(line)
            continue

        match = REQ_PATTERN.match(line)
        if not match:
            updated_lines.append(line)
            continue

        package, current_version = match.groups()
        latest = get_latest_version(package)

        if latest and latest != current_version:
            print(f"{package}: {current_version} → {latest}")
            updated_lines.append(f"{package}=={latest}")
            changed = True
        else:
            updated_lines.append(line)

    if changed:
        path.write_text("\n".join(updated_lines) + "\n")
        print("\nrequirements.txt updated ✔")
    else:
        print("\nAll dependencies already at latest versions ✔")


if __name__ == "__main__":
    update_requirements(Path(REQ_FILE))
