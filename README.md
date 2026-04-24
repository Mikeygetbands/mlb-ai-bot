# MLB HR AI Bot Starter

## What this does
Type a MLB player name and the app pulls:
- recent Statcast-style hitter data with pybaseball
- live HR prop odds from The Odds API
- model probability, fair odds, edge, and signal

## Step 1: Get an Odds API key
Create an account at The Odds API and copy your API key.

## Step 2: Run locally
Install Python, then run:

```bash
pip install -r requirements.txt
```

Set your key:

Mac/Linux:
```bash
export ODDS_API_KEY="your_key_here"
```

Windows CMD:
```bash
set ODDS_API_KEY=your_key_here
```

Run:

```bash
streamlit run app.py
```

## Step 3: Put it online
Upload these files to GitHub, then connect that GitHub repo to Streamlit Community Cloud.
In Streamlit Cloud, add ODDS_API_KEY under App settings > Secrets.