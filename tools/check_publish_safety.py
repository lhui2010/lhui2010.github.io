#!/usr/bin/env python3
"""Local-only publication guard. Reports paths/rule names, never matched values."""
import argparse
from pathlib import Path
import re
import subprocess

RULES = {
    "private-key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "openai-key": re.compile(rb"\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{24,}"),
    "slack-token": re.compile(rb"\b(?:xox[baprs]-[A-Za-z0-9-]{20,}|xapp-[A-Za-z0-9-]{20,})"),
    "github-token": re.compile(rb"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})"),
    "firecrawl-key": re.compile(rb"\bfc-[A-Za-z0-9]{24,}"),
    "aws-access-id": re.compile(rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "jwt": re.compile(rb"\beyJ[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{16,}"),
    "url-credentials": re.compile(rb"https?://[^\s/:@]{1,80}:[^\s/@]{6,}@"),
    "url-token-param": re.compile(rb"(?i)[?&](?:api_?key|access_?token|token|secret|password)=[A-Za-z0-9._~-]{12,}"),
    "literal-credential": re.compile(
        rb"""(?im)\b(?:api[_-]?key|client[_-]?secret|access[_-]?token|bot[_-]?token|password)\b["']?\s*[:=]\s*["']([A-Za-z0-9_./+\-=]{20,})["']"""),
}
RUNTIME = re.compile(
    r"(^|/)(?:\.state|\.cache|\.firecrawl|\.venv|__pycache__|browser-profile[^/]*|profiles|db|\.ssh|\.aws|credentials|secrets)/"
    r"|(^|/)(?:\.env(?:\..*)?|[^/]*cookies[^/]*\.(?:txt|json)|storage[_-]?state[^/]*\.json|[^/]*credentials[^/]*\.(?:json|ya?ml|toml)|Cookies|Login Data|Local State|\.netrc|\.npmrc)$"
    r"|\.(?:sqlite(?:3)?(?:-wal|-shm)?|db(?:-wal|-shm)?|log(?:\..*)?|pem|key)$", re.I)


def paths(repo, staged):
    command = (["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"]
               if staged else ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"])
    return sorted(set(x.decode() for x in subprocess.check_output(command, cwd=repo).split(b"\0") if x))


def audit(repo, staged=False):
    hits = []
    files = paths(repo, staged)
    for name in files:
        if RUNTIME.search(name):
            hits.append((name, "runtime-or-private-path"))
            continue
        if staged:
            body = subprocess.check_output(["git", "show", ":" + name], cwd=repo)
        else:
            path = repo / name
            if path.is_symlink() or not path.is_file():
                continue
            body = path.read_bytes()
        for label, pattern in RULES.items():
            if pattern.search(body):
                hits.append((name, label))
    return len(files), hits


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--staged", action="store_true")
    args = parser.parse_args()
    count, hits = audit(Path(args.repo).resolve(), args.staged)
    for path, rule in hits:
        print(f"BLOCKED {path}: {rule}")
    print(f"Checked {count} candidate files; findings={len(hits)}; values never printed")
    raise SystemExit(bool(hits))


if __name__ == "__main__":
    main()
