# Job Radar

Fetches jobs from free sources (Microsoft Careers, LinkedIn public feed, Remotive, Arbeitnow),
scores each against your resume, and sends new matches to your **WhatsApp** every morning at
**9:00 AM IST**. Runs free on **GitHub Actions**. No servers, no paid APIs.

## What each file does
- `config.py` — your search: keywords, location, resume terms/weights, which sources. **Edit this.**
- `sources.py` — the free job-source fetchers.
- `notify.py` — WhatsApp delivery via CallMeBot.
- `main.py` — fetch → score → dedupe → send.
- `seen.json` — jobs already sent (so you never get the same job twice).
- `.github/workflows/daily.yml` — the 9 AM IST cron.

---

## 1. One-time WhatsApp setup (2 minutes, free)
From the phone **+91 8655016964** (the number that will receive alerts):
1. Save **+34 644 84 71 89** as a WhatsApp contact.
2. Send it this exact message: `I allow callmebot to send me messages`
3. It replies with your **apikey** (a number). Keep it.

> CallMeBot is a free personal-use WhatsApp bridge. Free tier easily covers one daily digest.

## 2. Test locally (optional)
```bash
cd job-radar
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt

# preview matches without sending
python main.py --dry

# send a real WhatsApp test
set WHATSAPP_PHONE=918655016964
set CALLMEBOT_APIKEY=YOUR_KEY
python main.py --all
```

## 3. Deploy free (GitHub Actions)
1. Create a **new GitHub repo** (private is fine — Actions free minutes cover this easily).
2. Push this folder:
   ```bash
   cd job-radar
   git init && git add . && git commit -m "job radar"
   git branch -M main
   git remote add origin https://github.com/<you>/job-radar.git
   git push -u origin main
   ```
3. In the repo: **Settings → Secrets and variables → Actions → New repository secret**. Add two:
   - `WHATSAPP_PHONE` = `918655016964`
   - `CALLMEBOT_APIKEY` = your key from step 1
4. **Actions** tab → enable workflows → open **Job Radar Daily** → **Run workflow** to test now.
5. Done. It runs every day at 9 AM IST automatically.

## Tuning
- Fewer, closer matches: raise `MIN_SCORE` in `config.py` (e.g. 35).
- More AI/security roles: bump those weights in `RESUME_TERMS`.
- Different time: edit the cron in `daily.yml` (it's in **UTC**; 9 AM IST = `30 3 * * *`).
- Add companies: extend `sources.py` with Greenhouse/Lever boards.

## Notes & limits
- **LinkedIn** uses its public no-login feed: it returns a *subset*, is rate-limited, and has
  no job descriptions (so those score on title only). Keep `LINKEDIN_PAGES` low (2–3) to avoid
  IP throttling. For full LinkedIn coverage, also turn on LinkedIn's own free Job Alerts.
- If a source is down, the run skips it and continues.
- `seen.json` is committed back after each run so dedupe survives across days.
