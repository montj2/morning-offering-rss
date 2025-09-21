# Morning Offering (Unofficial RSS)

This repo builds a personal, unofficial RSS feed from [morningoffering.com](https://www.morningoffering.com).  
Subscribe after setup: `https://montj2.github.io/morning-offering-rss/feed.xml`

## Setup

### Option 1: Use this existing repo
1. Push this repo to GitHub as `morning-offering-rss`
2. Enable **GitHub Pages** for the repo (Settings → Pages → Branch: `gh-pages`)
3. Make sure Actions are enabled in the repo
4. The workflow will run daily at 10:10 AM UTC (adjust in `.github/workflows/build.yml` if desired)

### Option 2: Fork/clone setup
1. Fork or clone this repo to your GitHub account
2. Update the feed URL in this README if using a different repo name
3. Enable **GitHub Pages** for the repo (Settings → Pages → Branch: `gh-pages`)
4. Make sure Actions are enabled in the repo
5. Adjust the cron time in `.github/workflows/build.yml` if desired

### Push existing repo to GitHub
```bash
# Add your GitHub repo as origin
git remote add origin https://github.com/montj2/morning-offering-rss.git

# Push main branch
git push -u origin main

# Push gh-pages branch (needed for GitHub Pages)
git push -u origin gh-pages
```

## Local test
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/generate_feed.py
open feed.xml
