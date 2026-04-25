import os

import requests

import streamlit as st

from datetime import date

from pybaseball import playerid_lookup, statcast_batter

ODDS_API_KEY = os.getenv("ODDS_API_KEY")

st.title("🔥 MLB HR Real-Time AI Simulator")

player_name = st.text_input("Enter Player Name (First Last)")

def american_to_prob(odds):

    if odds > 0:

        return 100 / (odds + 100)

    return abs(odds) / (abs(odds) + 100)

def prob_to_american(prob):

    if prob >= 0.5:

        return round(-100 * prob / (1 - prob))

    return round(100 * (1 - prob) / prob)

def get_player_id(name):

    parts = name.split()

    df = playerid_lookup(parts[-1], parts[0])

    if df.empty:

        return None

    return int(df.iloc[-1]["key_mlbam"])

def get_stats(player_id):

    today = date.today().strftime("%Y-%m-%d")

    data = statcast_batter("2026-04-01", today, player_id)

    if data.empty:

        return None

    hr = len(data[data["events"] == "home_run"])

    pa = len(data)

    hard_hit = len(data[data["launch_speed"] >= 95]) / pa

    fly_ball = len(data[data["launch_angle"] >= 20]) / pa

    return {

        "hr_pa": hr / pa,

        "hard_hit": hard_hit,

        "fly_ball": fly_ball

    }

def get_odds(player_name):

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

    for game in r.json():

        for book in game.get("bookmakers", []):

            for market in book.get("markets", []):

                for outcome in market.get("outcomes", []):

                    if player_name.lower() in outcome.get("description", "").lower():

                        return outcome["price"]

    return None

if player_name:

    player_id = get_player_id(player_name)

    if not player_id:

        st.error("Player not found")

    else:

        stats = get_stats(player_id)

        odds = get_odds(player_name)

        if not stats or not odds:

            st.warning("Data not available")

        else:

            base = max(stats["hr_pa"], 0.04)

            adj = base * (1 + stats["hard_hit"] * 0.3) * (1 + stats["fly_ball"] * 0.25)

            prob = 1 - (1 - adj) ** 4

            fair_odds = prob_to_american(prob)

            implied = american_to_prob(odds)

            edge = prob - implied

            if edge > 0.08:

                signal = "🔥 ELITE"

            elif edge > 0.04:

                signal = "🔥 STRONG"

            elif edge > 0.015:

                signal = "👍 VALUE"

            else:

                signal = "❌ PASS"

            st.subheader(player_name)

            st.write(f"HR Probability: {round(prob*100,2)}%")

            st.write(f"Fair Odds: {fair_odds}")

            st.write(f"Sportsbook Odds: {odds}")

            st.write(f"Edge: {round(edge*100,2)}%")

            st.write(f"Signal: {signal}") if not stats:

    st.error("Statcast/player stats not found.")

elif not odds:

    st.error("HR odds not found. This usually means no HR prop is posted yet for this player.")
t
