import os

import requests

import streamlit as st

from datetime import date

from pybaseball import playerid_lookup, statcast_batter

ODDS_API_KEY = os.getenv("ODDS_API_KEY")

st.set_page_config(page_title="MLB HR AI Bot", layout="centered")

st.title("🔥 MLB HR Real-Time AI Simulator")

player_name = st.text_input("Type player name", placeholder="Aaron Judge")

def american_to_prob(odds):

    odds = int(odds)

    if odds > 0:

        return 100 / (odds + 100)

    return abs(odds) / (abs(odds) + 100)

def prob_to_american(prob):

    if prob <= 0:

        return None

    if prob >= 0.5:

        return round(-100 * prob / (1 - prob))

    return round(100 * (1 - prob) / prob)

def get_mlb_player_id(name):

    parts = name.strip().split()

    if len(parts) < 2:

        return None

    last = parts[-1]

    first = " ".join(parts[:-1])

    df = playerid_lookup(last, first)

    if df.empty:

        return None

    return int(df.iloc[-1]["key_mlbam"])

def get_recent_batter_stats(player_id):

    today = date.today().strftime("%Y-%m-%d")

    data = statcast_batter("2026-04-01", today, player_id)

    if data.empty:

        return None

    batted = data[data["launch_speed"].notna()]

    pa = max(len(data), 1)

    hr = len(data[data["events"] == "home_run"])

    hard_hit = len(batted[batted["launch_speed"] >= 95]) / max(len(batted), 1)

    fly_ball = len(batted[batted["launch_angle"] >= 20]) / max(len(batted), 1)

    return {

        "hr_pa": hr / pa,

        "hard_hit": hard_hit,

        "fly_ball": fly_ball,

        "pa_sample": pa

    }

def get_hr_odds(player_name):

    url = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"

    params = {

        "apiKey": ODDS_API_KEY,

        "regions": "us",

        "markets": "batter_home_runs",

        "oddsFormat": "american"

    }

    r = requests.get(url, params=params)

    if r.status_code != 200:

        return None

    games = r.json()

    matches = []

    for game in games:

        for book in game.get("bookmakers", []):

            for market in book.get("markets", []):

                for outcome in market.get("outcomes", []):

                    if player_name.lower() in outcome.get("description", "").lower():

                        matches.append({

                            "book": book["title"],

                            "odds": outcome["price"]

                        })

    if not matches:

        return None

    return sorted(matches, key=lambda x: x["odds"], reverse=True)[0]

def run_sim(stats, sportsbook_odds):

    base_hr_pa = max(stats["hr_pa"], 0.04)

    hard_hit_boost = 1 + stats["hard_hit"] * 0.35

    fly_ball_boost = 1 + stats["fly_ball"] * 0.25

    adj_hr_pa = base_hr_pa * hard_hit_boost * fly_ball_boost

    hr_prob = 1 - (1 - adj_hr_pa) ** 4

    fair_odds = prob_to_american(hr_prob)

    implied_prob = american_to_prob(sportsbook_odds)

    edge = hr_prob - implied_prob

    if edge >= 0.08:

        signal = "🔥 ELITE"

    elif edge >= 0.04:

        signal = "🔥 STRONG"

    elif edge >= 0.015:

        signal = "👍 VALUE"

    else:

        signal = "❌ PASS"

    return hr_prob, fair_odds, implied_prob, edge, signal

if player_name and ODDS_API_KEY:

    player_id = get_mlb_player_id(player_name)

    if player_id:

        stats = get_recent_batter_stats(player_id)

        odds = get_hr_odds(player_name)

        if stats and odds:

            hr_prob, fair_odds, implied_prob, edge, signal = run_sim(stats, odds["odds"])

            st.subheader(player_name.title())

            st.write(f"HR Probability: {round(hr_prob*100,2)}%")

            st.write(f"Fair Odds: {round(fair_odds)}")

            st.write(f"Sportsbook Odds: {odds['odds']}")

            st.write(f"Edge: {round(edge*100,2)}%")

            st.write(f"Signal: {signal}")

        else:

            st.warning("Not enough data or odds found.")

    else:

        st.error("Player not found.")

elif player_name:

    st.error("Add your Odds API key 
