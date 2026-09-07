"""
Job sources. Each function returns a list of dicts:
    {src, title, company, loc, url, text}
All free. No credentials required. Failures are swallowed so one dead
source never kills the run.
"""
import re
import html
import time
import httpx

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
HDR = {"User-Agent": UA}


def _get(url, **kw):
    return httpx.get(url, headers=HDR, timeout=30, follow_redirects=True, **kw)


def microsoft(keywords, location):
    """Microsoft Careers public search API."""
    u = "https://gcsservices.careers.microsoft.com/search/api/v1/search"
    p = {"q": keywords, "lc": location, "l": "en_us",
         "pg": 1, "pgSz": 50, "o": "Relevance"}
    r = _get(u, params=p)
    jobs = (r.json().get("operationResult", {})
            .get("result", {}).get("jobs", []))
    out = []
    for j in jobs:
        props = j.get("properties", {}) or {}
        locs = props.get("locations", []) or []
        jid = j.get("jobId", "")
        out.append({
            "src": "Microsoft",
            "title": j.get("title", ""),
            "company": "Microsoft",
            "loc": ", ".join(locs),
            "url": f"https://jobs.careers.microsoft.com/global/en/job/{jid}",
            "text": (j.get("title", "") + " " + str(props.get("description", "")))[:3000],
        })
    return out


def linkedin(keywords, location, pages=3, pause=3.0):
    """
    LinkedIn PUBLIC guest endpoint (no login). ToS-gray, rate-limited,
    returns a subset. Keep volume low. Personal use only.
    """
    base = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    out = []
    for pg in range(pages):
        p = {"keywords": keywords, "location": location, "start": pg * 25}
        try:
            r = _get(base, params=p)
        except Exception as e:
            print("  linkedin request failed:", e)
            break
        if r.status_code != 200:
            print("  linkedin http", r.status_code, "(throttled or blocked) — stopping")
            break
        cards = re.findall(r"<li>.*?</li>", r.text, re.S)
        if not cards:
            break
        for c in cards:
            t = re.search(r'job-search-card__title[^>]*>\s*(.*?)\s*<', c, re.S)
            co = re.search(r'hidden-nested-link[^>]*>\s*(.*?)\s*<', c, re.S)
            lo = re.search(r'job-search-card__location[^>]*>\s*(.*?)\s*<', c, re.S)
            url = re.search(r'href="(https://[^"]*?/jobs/view/[^"?]+)', c)
            if not (t and url):
                continue
            title = html.unescape(t.group(1).strip())
            comp = html.unescape(co.group(1).strip()) if co else ""
            out.append({
                "src": "LinkedIn",
                "title": title,
                "company": comp,
                "loc": html.unescape(lo.group(1).strip()) if lo else location,
                "url": url.group(1).split("?")[0],
                "text": f"{title} {comp}",  # guest feed has no description
            })
        time.sleep(pause)  # be gentle — this keeps you unblocked
    return out


def remotive(keywords):
    """Remotive free API — remote roles."""
    r = _get("https://remotive.com/api/remote-jobs", params={"search": keywords})
    out = []
    for j in r.json().get("jobs", [])[:60]:
        out.append({
            "src": "Remotive",
            "title": j.get("title", ""),
            "company": j.get("company_name", ""),
            "loc": j.get("candidate_required_location", ""),
            "url": j.get("url", ""),
            "text": (j.get("title", "") + " " + j.get("description", ""))[:3000],
        })
    return out


def arbeitnow():
    """Arbeitnow free job board API — EU + remote."""
    r = _get("https://www.arbeitnow.com/api/job-board-api")
    out = []
    for j in r.json().get("data", [])[:60]:
        out.append({
            "src": "Arbeitnow",
            "title": j.get("title", ""),
            "company": j.get("company_name", ""),
            "loc": j.get("location", ""),
            "url": j.get("url", ""),
            "text": (j.get("title", "") + " " + j.get("description", ""))[:3000],
        })
    return out
