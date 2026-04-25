import os

import requests

import streamlit as st

from datetime import date, timedelta

from pybaseball import playerid_lookup, statcast_batter

ODDS_API_KEY = os.getenv("ODDS_API_KEY")

st.set_page_config(page_title="MLB HR God Tier Bot", layout="centered")

st.title("🔥 MLB HR God Tier AI Simulator")

player_name = st.text_input("Enter MLB Player Name", placeholder="Aaron Judge")

def american_to_prob(odds):

    odds = int(odds)

    if odds > 0:

        return 100 / (odds + 100)

    return abs(odds) / (abs(odds) + 100)

def prob_to_american(prob):

    if prob >= 0.5:

        return round(-100 * prob / (1 - prob))

    return round(100 * (1 - prob) / prob)

def get_player_id(name):

    parts = name.strip().split()

    if len(parts) < 2:

        return None

    first = parts[0]

    last = parts[-1]

    try:

        df = playerid_lookup(last, first)

        if df.empty:

            return None

        return int(df.iloc[-1]["key_mlbam"])

    except Exception:

        return None

def get_recent_stats(player_id):

    end = date.today()

    start = end - timedelta(days=30)

    try:

        data = statcast_batter(

            start.strftime("%Y-%m-%d"),

            end.strftime("%Y-%m-%d"),

            player_id

        )

    except Exception:

        return None

    if data.empty:

        return None

    batted = data[data["launch_speed"].notna()]

    pa = max(len(data), 1)

    hr = len(data[data["events"] == "home_run"])

    hard_hit = len(batted[batted["launch_speed"] >= 95]) / max(len(batted), 1)

    barrel_like = len(

        batted[

            (batted["launch_speed"] >= 98) &

            (batted["launch_angle"] >= 26) &

            (batted["launch_angle"] <= 30)

        ]

    ) / max(len(batted), 1)

    fly_ball = len(

        batted[

            (batted["launch_angle"] >= 20) &

            (batted["launch_angle"] <= 50)

        ]

    ) / max(len(batted), 1)

    avg_ev = batted["launch_speed"].mean() if not batted.empty else 0

    return {

        "pa": pa,

        "hr": hr,

        "hr_pa": hr / pa,

        "hard_hit": hard_hit,

        "barrel_like": barrel_like,

        "fly_ball": fly_ball,

        "avg_ev": avg_ev

    }

def get_mlb_events():

    if not ODDS_API_KEY:

        return []

    url = "https://api.the-odds-api.com/v4/sports/baseball_mlb/events"

    params = {

        "apiKey": ODDS_API_KEY

    }

    try:

        r = requests.get(url, params=params, timeout=20)

        if r.status_code != 200:

            return []

        return r.json()

    except Exception:

        return []

def get_hr_odds_for_player(player_name):

    events = get_mlb_events()

    matches = []

    for event in events:

        event_id = event.get("id")

        odds_url = f"https://api.the-odds-api.com/v4/sports/baseball_mlb/events/{event_id}/odds"

        params = {

            "apiKey": ODDS_API_KEY,

            "regions": "us",

            "markets": "batter_home_runs",

            "oddsFormat": "american"

        }

        try:

            r = requests.get(odds_url, params=params, timeout=20)

            if r.status_code != 200:

                continue

            game = r.json()

            for book in game.get("bookmakers", []):

                for market in book.get("markets", []):

                    for outcome in market.get("outcomes", []):

                        desc = outcome.get("description", "") or outcome.get("name", "")

                        if player_name.lower() in desc.lower():

                            matches.append({

                                "book": book.get("title", "Unknown"),

                                "odds": outcome.get("price"),

                                "game": f"{game.get('away_team')} @ {game.get('home_team')}",

                                "description": desc

                            })

        except Exception:

            continue

    if not matches:

        return None

    return sorted(matches, key=lambda x: int(x["odds"]), reverse=True)[0]

def run_god_model(stats, odds):

    base_hr_pa = max(stats["hr_pa"], 0.035)

    hard_hit_boost = 1 + stats["hard_hit"] * 0.35

    barrel_boost = 1 + stats["barrel_like"] * 0.75

    fly_ball_boost = 1 + stats["fly_ball"] * 0.25

    avg_ev_boost = 1.00

    if stats["avg_ev"] >= 92:

        avg_ev_boost = 1.08

    elif stats["avg_ev"] >= 90:

        avg_ev_boost = 1.04

    elif stats["avg_ev"] < 86:

        avg_ev_boost = 0.92

    adj_hr_pa = base_hr_pa * hard_hit_boost * barrel_boost * fly_ball_boost * avg_ev_boost

    plate_appearances = 4

    hr_prob = 1 - (1 - adj_hr_pa) ** plate_appearances

    fair_odds = prob_to_american(hr_prob)

    implied_prob = american_to_prob(odds)

    edge = hr_prob - implied_prob

    if edge >= 0.08:

        signal = "🔥 GOD TIER"

    elif edge >= 0.05:

        signal = "🔥 ELITE"

    elif edge >= 0.025:

        signal = "✅ VALUE"

    else:

        signal = "❌ PASS"

    return {

        "hr_prob": hr_prob,

        "fair_odds": fair_odds,

        "implied_prob": implied_prob,

        "edge": edge,

        "signal": signal,

        "adj_hr_pa": adj_hr_pa

    }

if player_name:

    if not ODDS_API_KEY:

        st.error("Missing ODDS_API_KEY. Add it in Streamlit Secrets.")

    else:

        with st.spinner("Running God Tier simulation..."):

            player_id = get_player_id(player_name)

            if not player_id:

                st.error("Player not found. Use full name like Aaron Judge.")

            else:

                stats = get_recent_stats(player_id)

                if not stats:

                    st.error("Statcast data not found for this player.")

                else:

                    odds_data = get_hr_odds_for_player(player_name)

                    if not odds_data:

                        st.error("HR odds not found right now. The sportsbook may not have this player’s HR prop posted yet.")

                        st.info("Try Aaron Judge, Shohei Ohtani, Kyle Schwarber, Juan Soto, Pete Alonso, or check closer to game time.")

                    else:

                        result = run_god_model(stats, odds_data["odds"])

                        st.subheader(player_name.title())

                        col1, col2 = st.columns(2)

                        col1.metric("HR Probability", f"{result['hr_prob']*100:.1f}%")

                        col2.metric("Signal", result["signal"])

                        col3, col4 = st.columns(2)

                        col3.metric("Fair Odds", result["fair_odds"])

                        col4.metric("Best Odds", odds_data["odds"])

                        st.metric("Edge", f"{result['edge']*100:.1f}%")

                        st.write("Sportsbook:", odds_data["book"])

                        st.write("Game:", odds_data["game"])

                        st.write("Recent PA Sample:", stats["pa"])

                        st.write("Recent HR:", stats["hr"])

                        st.write("Hard Hit %:", f"{stats['hard_hit']*100:.1f}%")

                        st.write("Fly Ball %:", f"{stats['fly_ball']*100:.1f}%")

                        st.write("Barrel-like %:", f"{stats['barrel_like']*100:.1f}%")

                        st.write("Avg Exit Velocity:", f"{stats['avg_ev']:.1f} mph")

                        st.warning("This is a model estimate, not a guaranteed bet. Use bankroll control.")

