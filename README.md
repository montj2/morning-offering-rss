# Morning Offering (Unofficial RSS)

This repo builds a personal, unofficial RSS feed from [morningoffering.com](https://www.morningoffering.com).  
Subscribe after setup: `https://montj2.github.io/morning-offering-rss/feed.xml`

## Setup
1. Fork or create this repo.
2. Enable **GitHub Pages** for the repo (Settings → Pages → Branch: `gh-pages`).
3. Make sure Actions are enabled in the repo.
4. Adjust the cron time in `.github/workflows/build.yml` if desired.

## Local test
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/generate_feed.py
open feed.xml
