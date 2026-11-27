"""Build today's devlog entry from GitHub activity + optional notes in notes/YYYY-MM-DD.md."""
import json, os, urllib.request
from collections import defaultdict
from datetime import datetime, timezone, timedelta

USER = "janveryuu"
SKIP = {f"{USER}/ph-daily-pulse", f"{USER}/devlog"}
PHT = timezone(timedelta(hours=8))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def api(path):
    req = urllib.request.Request("https://api.github.com" + path,
                                 headers={"Accept": "application/vnd.github+json",
                                          "Authorization": f"Bearer {os.environ.get('GITHUB_TOKEN', '')}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main():
    today = datetime.now(PHT).date()
    events = []
    for page in (1, 2, 3):
        batch = api(f"/users/{USER}/events?per_page=100&page={page}")
        events += batch
        if len(batch) < 100:
            break

    commits, prs, issues, created = defaultdict(list), [], [], []
    for e in events:
        if datetime.fromisoformat(e["created_at"].replace("Z", "+00:00")).astimezone(PHT).date() != today:
            continue
        repo, p = e["repo"]["name"], e["payload"]
        if repo in SKIP:
            continue
        if e["type"] == "PushEvent":
            for c in p.get("commits", []):
                commits[repo].append((c.get("message") or "commit").splitlines()[0])
            if not p.get("commits"):
                branch = p.get("ref", "").split("/")[-1]
                msg = f"pushed to {branch}"
                if p.get("head"):
                    try:
                        msg = api(f"/repos/{repo}/commits/{p['head']}")["commit"]["message"].splitlines()[0] + f" ({branch})"
                    except Exception:
                        pass
                commits[repo].append(msg)
        elif e["type"] == "PullRequestEvent":
            pr = p.get("pull_request", {})
            n = pr.get("number") or p.get("number")
            title = pr.get("title") or ""
            prs.append(f"{p.get('action', 'updated')} [{repo}#{n}](https://github.com/{repo}/pull/{n})" + (f": {title}" if title else ""))
        elif e["type"] == "IssuesEvent":
            i = p.get("issue", {})
            n = i.get("number")
            title = i.get("title") or ""
            issues.append(f"{p.get('action', 'updated')} [{repo}#{n}](https://github.com/{repo}/issues/{n})" + (f": {title}" if title else ""))
        elif e["type"] == "CreateEvent" and p.get("ref_type") == "repository":
            created.append(f"[{repo}](https://github.com/{repo})")

    notes_path = os.path.join(ROOT, "notes", f"{today}.md")
    notes = open(notes_path, encoding="utf-8").read().strip() if os.path.exists(notes_path) else ""

    lines = [f"# Devlog — {today:%A, %B %d, %Y}", ""]
    if created:
        lines += ["## New repos", *[f"- {r}" for r in created], ""]
    if commits:
        lines += ["## Commits"]
        for repo, msgs in commits.items():
            lines.append(f"- **[{repo}](https://github.com/{repo})** ({len(msgs)})")
            lines += [f"  - {m}" for m in dict.fromkeys(msgs)]
        lines.append("")
    if prs:
        lines += ["## Pull requests", *[f"- {x}" for x in prs], ""]
    if issues:
        lines += ["## Issues", *[f"- {x}" for x in issues], ""]
    if notes:
        lines += ["## Notes", notes, ""]
    if len(lines) == 2:
        lines += ["_No public activity today. Rest day._", ""]

    lines.append(f"_Last synced: {datetime.now(PHT):%I:%M %p} PHT_")
    out = os.path.join(ROOT, "entries", f"{today:%Y}", f"{today}.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write("\n".join(lines))

    # index README
    entries = sorted((os.path.join(d, f) for d, _, fs in os.walk(os.path.join(ROOT, "entries")) for f in fs if f.endswith(".md")), reverse=True)
    idx = ["# Devlog", "", f"Daily log of what I built, auto-generated from my GitHub activity. **{len(entries)} entries.**", "", "## Recent"]
    for path in entries[:30]:
        rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
        idx.append(f"- [{os.path.basename(path)[:-3]}]({rel})")
    open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write("\n".join(idx) + "\n")
    print("wrote", out, f"commits={sum(map(len, commits.values()))} prs={len(prs)} issues={len(issues)}")


if __name__ == "__main__":
    main()
