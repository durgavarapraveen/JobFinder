"""
Job Radar — fetch jobs from free sources, score against your resume,
send new matches to WhatsApp. Runs daily via GitHub Actions.

    python main.py            # normal run (sends only NEW jobs)
    python main.py --all      # ignore dedupe, send top matches anyway
    python main.py --dry      # print, don't send, don't update seen.json
"""
import re
import sys
import json
import datetime
from pathlib import Path

# Windows consoles default to cp1252 and choke on emoji / ≥. Force UTF-8.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import config as C
import sources as S
import notify

HERE = Path(__file__).parent
SEEN_FILE = HERE / "seen.json"
RESUME_TXT = HERE / "resume.txt"
RESUME_PDF = HERE / "resume.pdf"


def _read_resume_text():
    """Prefer resume.pdf if present, else resume.txt. Returns lowercased text."""
    if RESUME_PDF.exists():
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(RESUME_PDF))
            return "\n".join((p.extract_text() or "") for p in reader.pages).lower()
        except Exception as e:
            print(f"  couldn't read resume.pdf ({e}); falling back to resume.txt")
    if RESUME_TXT.exists():
        return RESUME_TXT.read_text(encoding="utf-8", errors="ignore").lower()
    return ""


def load_resume_tokens():
    """Words from your resume (pdf or txt) become bonus match signal."""
    txt = _read_resume_text()
    return {w for w in re.findall(r"[a-z][a-z0-9+.#]{2,}", txt) if w not in _STOP}


_STOP = {"the", "and", "for", "with", "you", "your", "our", "are", "was", "will",
         "have", "has", "from", "this", "that", "who", "how", "all", "can", "not",
         "job", "role", "team", "work", "years", "experience", "using", "into"}

_RESUME_TOKENS = None


# ── scoring ────────────────────────────────────────────────────────────────
def score(job) -> int:
    global _RESUME_TOKENS
    if _RESUME_TOKENS is None:
        _RESUME_TOKENS = load_resume_tokens()
    text = (job.get("text", "") + " " + job.get("title", "")).lower()

    # Primary signal: weighted resume terms from config.py
    raw = sum(w for term, w in C.RESUME_TERMS.items() if term in text)
    max_possible = sum(sorted(C.RESUME_TERMS.values(), reverse=True)[:8])
    base = 100 * raw / max_possible if max_possible else 0

    # Bonus: overlap with your full resume.txt (capped so it can't dominate)
    if _RESUME_TOKENS:
        job_tokens = set(re.findall(r"[a-z][a-z0-9+.#]{2,}", text))
        overlap = len(job_tokens & _RESUME_TOKENS)
        base += min(20, overlap)  # up to +20

    return min(100, round(base))


def excluded(title: str) -> bool:
    t = title.lower()
    return any(x in t for x in C.EXCLUDE_TITLE)


# ── fetch ──────────────────────────────────────────────────────────────────
def fetch_all():
    jobs, plan = [], []
    if C.SOURCES.get("microsoft"):
        plan.append(("Microsoft", lambda: S.microsoft(C.KEYWORDS, C.LOCATION)))
    if C.SOURCES.get("linkedin"):
        plan.append(("LinkedIn", lambda: S.linkedin(C.KEYWORDS, C.LOCATION, C.LINKEDIN_PAGES)))
    if C.SOURCES.get("remotive"):
        plan.append(("Remotive", lambda: S.remotive(C.KEYWORDS)))
    if C.SOURCES.get("arbeitnow"):
        plan.append(("Arbeitnow", S.arbeitnow))
    for name, fn in plan:
        try:
            got = fn()
            print(f"  {name}: {len(got)}")
            jobs += got
        except Exception as e:
            print(f"  {name}: FAILED {e}")
    return jobs


# ── dedupe ─────────────────────────────────────────────────────────────────
def load_seen():
    if SEEN_FILE.exists():
        try:
            return set(json.loads(SEEN_FILE.read_text()))
        except Exception:
            return set()
    return set()


def save_seen(seen):
    SEEN_FILE.write_text(json.dumps(sorted(seen), indent=0))


def key(job):
    return re.sub(r"[?#].*$", "", job.get("url", "")) or job.get("title", "")


# ── format ─────────────────────────────────────────────────────────────────
def render(jobs):
    today = datetime.date.today().strftime("%d %b %Y")
    lines = [f"🎯 Job Radar — {today}", f"{len(jobs)} new match(es)", ""]
    for j in jobs:
        lines.append(f"[{j['score']}] {j['title']}")
        who = " · ".join(x for x in (j.get("company"), j.get("loc")) if x)
        if who:
            lines.append(f"   {who}  ({j['src']})")
        lines.append(f"   {j['url']}")
        lines.append("")
    return "\n".join(lines).strip()


# ── main ───────────────────────────────────────────────────────────────────
def main():
    dry = "--dry" in sys.argv
    ignore_seen = "--all" in sys.argv

    print("Fetching…")
    jobs = fetch_all()

    # score + filter
    ranked = []
    for j in jobs:
        if not j.get("url") or excluded(j.get("title", "")):
            continue
        j["score"] = score(j)
        if j["score"] >= C.MIN_SCORE:
            ranked.append(j)

    # dedupe by url within this run
    uniq, seen_now = [], set()
    for j in sorted(ranked, key=lambda x: x["score"], reverse=True):
        k = key(j)
        if k in seen_now:
            continue
        seen_now.add(k)
        uniq.append(j)

    seen = set() if ignore_seen else load_seen()
    fresh = [j for j in uniq if key(j) not in seen]
    fresh = fresh[: C.TOP_N]

    print(f"Total scored ≥{C.MIN_SCORE}: {len(uniq)} | new this run: {len(fresh)}")

    if not fresh:
        print("Nothing new to send.")
        return

    msg = render(fresh)
    if dry:
        print("\n----- DRY RUN -----\n" + msg)
        return

    sent = notify.send(msg)
    if sent or True:  # record as seen even if WA hiccups, to avoid repeat spam
        for j in fresh:
            seen.add(key(j))
        save_seen(seen)
    print("Done." if sent else "Sent with warnings (see above).")


if __name__ == "__main__":
    main()
