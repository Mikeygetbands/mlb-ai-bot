import os, requests

import streamlit as st

from datetime import date, timedelta

from pybaseball import playerid_lookup, statcast_batter

ODDS_API_KEY = os.getenv("ODDS_API_KEY")

TOP_30 = [

    "Aaron Judge","Shohei Ohtani","Juan Soto","Kyle Schwarber","Pete Alonso",

    "Yordan Alvarez","Vladimir Guerrero Jr.","Fernando Tatis Jr.","Ronald Acuna Jr.",

    "Mookie Betts","Bryce Harper","Matt Olson","Austin Riley","Rafael Devers",

    "Manny Machado","Corey Seager","Julio Rodriguez","Bobby Witt Jr.","Gunnar Henderson",

    "Elly De La Cruz","Adolis Garcia","Jose Ramirez","Mike Trout","Giancarlo Stanton",

    "Cal Raleigh","Salvador Perez","Luis Robert Jr.","Teoscar Hernandez",

    "Marcell Ozuna","Oneil Cruz"

]

BOOKS = {

    "fanduel": "FanDuel",

    "draftkings": "DraftKings",

    "betmgm": "BetMGM",

    "caesars": "Caesars",

    "betrivers": "BetRivers",

    "espnbet": "ESPN BET",

    "fanatics": "Fanatics"

}

MARKETS = {

    "HR": "batter_home_runs",

    "RBI": "batter_rbis",

    "HRR": "batter_hits_runs_rbis"

}

st.set_page_config(page_title="God Tier MLB Prop AI", layout="wide")

st.title("🔥 God Tier MLB AI Prop Simulator")

st.caption("HR • RBI • HRR • Weather • Multi-Sportsbook Odds • Top 30 Hitters")

def american_to_prob(odds):

    odds = int(odds)

    return 100 / (odds + 100) if odds > 0 else abs(odds) / (abs(odds) + 100)

def prob_to_american(prob):

    if prob >= 0.5:

        return round(-100 * prob / (1 - prob))

    return round(100 * (1 - prob) / prob)

def get_player_id(name):

    parts = name.strip().split()

    if len(parts) < 2:

        return None

    try:

        df = playerid_lookup(parts[-1], parts[0])

        if df.empty:

            return None

        return int(df.iloc[-1]["key_mlbam"])

    except:

        return None

def get_stats(player_id):

    end = date.today()

    start = end - timedelta(days=30)

    try:

        data = statcast_batter(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"), player_id)

    except:

        return None

    if data.empty:

        return None

    batted = data[data["launch_speed"].notna()]

    pa = max(len(data), 1)

    hr = len(data[data["events"] == "home_run"])

    hit = len(data[data["events"].isin(["single","double","triple","home_run"])])

    rbi = data["post_bat_score"].fillna(0).sum() if "post_bat_score" in data else 0

    hard_hit = len(batted[batted["launch_speed"] >= 95]) / max(len(batted), 1)

    fly_ball = len(batted[(batted["launch_angle"] >= 20) & (batted["launch_angle"] <= 50)]) / max(len(batted), 1)

    avg_ev = batted["launch_speed"].mean() if not batted.empty else 88

    return {

        "PA": pa,

        "HR": hr,

        "H": hit,

        "RBI": rbi,

        "HR_PA": hr / pa,

        "H_PA": hit / pa,

        "RBI_PA": rbi / pa if pa else 0,

        "HardHit": hard_hit,

        "FlyBall": fly_ball,

        "AvgEV": avg_ev

    }

def weather_boost():

    temp = st.sidebar.slider("Game Temperature", 45, 100, 75)

    wind = st.sidebar.slider("Wind Out MPH", 0, 25, 5)

    boost = 1.00

    if temp >= 80: boost += 0.06

    elif temp >= 70: boost += 0.03

    elif temp <= 55: boost -= 0.05

    if wind >= 12: boost += 0.08

    elif wind >= 8: boost += 0.04

    return boost

def get_events():

    if not ODDS_API_KEY:

        return []

    try:

        r = requests.get(

            "https://api.the-odds-api.com/v4/sports/baseball_mlb/events",

            params={"apiKey": ODDS_API_KEY},

            timeout=15

        )

        return r.json() if r.status_code == 200 else []

    except:

        return []

def get_best_odds(player, market):

    if not ODDS_API_KEY:

        return None

    best = None

    events = get_events()

    for event in events:

        eid = event.get("id")

        url = f"https://api.the-odds-api.com/v4/sports/baseball_mlb/events/{eid}/odds"

        params = {

            "apiKey": ODDS_API_KEY,

            "regions": "us",

            "markets": market,

            "oddsFormat": "american",

            "bookmakers": ",".join(BOOKS.keys())

        }

        try:

            r = requests.get(url, params=params, timeout=15)

            if r.status_code != 200:

                continue

            game = r.json()

            for book in game.get("bookmakers", []):

                for m in book.get("markets", []):

                    for out in m.get("outcomes", []):

                        desc = out.get("description", "") or out.get("name", "")

                        if player.lower() in desc.lower():

                            odds = out.get("price")

                            if odds is None:

                                continue

                            item = {

                                "book": book.get("title", "Unknown"),

                                "odds": int(odds),

                                "game": f"{game.get('away_team')} @ {game.get('home_team')}"

                            }

                            if best is None or item["odds"] > best["odds"]:

                                best = item

        except:

            continue

    return best

def model_probability(stats, prop_type, boost):

    if prop_type == "HR":

        base = max(stats["HR_PA"], 0.035)

        adj = base * (1 + stats["HardHit"] * 0.35) * (1 + stats["FlyBall"] * 0.30) * boost

        prob = 1 - (1 - adj) ** 4

    elif prop_type == "RBI":

        base = max(stats["RBI_PA"], 0.18)

        adj = base * (1 + stats["HardHit"] * 0.20) * boost

        prob = 1 - (1 - min(adj, 0.45)) ** 4

    else:  # HRR = Hits + Runs + RBI style prop estimate

        base = max(stats["H_PA"] + stats["RBI_PA"], 0.35)

        adj = min(base * (1 + stats["HardHit"] * 0.15) * boost, 0.65)

        prob = 1 - (1 - adj) ** 4

    return min(max(prob, 0.01), 0.75)

def grade(edge):

    if edge >= 0.10:

        return "🔥 GOD TIER"

    elif edge >= 0.06:

        return "🔥 ELITE"

    elif edge >= 0.03:

        return "✅ VALUE"

    else:

        return "❌ PASS"

boost = weather_boost()

tab1, tab2 = st.tabs(["🔎 Single Player", "🏆 Top 30 Board"])

with tab1:

    prop = st.selectbox("Choose Prop", ["HR", "RBI", "HRR"])

    player = st.text_input("Enter Player Name", placeholder="Aaron Judge")

    manual = st.number_input("Manual Sportsbook Odds Fallback", value=300, step=5)

    if player:

        pid = get_player_id(player)

        if not pid:

            st.error("Player not found. Use full name.")

        else:

            stats = get_stats(pid)

            if not stats:

                st.error("Stats not found.")

            else:

                odds_data = get_best_odds(player, MARKETS[prop])

                odds = odds_data["odds"] if odds_data else manual

                prob = model_probability(stats, prop, boost)

                fair = prob_to_american(prob)

                implied = american_to_prob(odds)

                edge = prob - implied

                c1, c2, c3, c4 = st.columns(4)

                c1.metric("Probability", f"{prob*100:.1f}%")

                c2.metric("Fair Odds", fair)

                c3.metric("Best Odds", odds)

                c4.metric("Signal", grade(edge))

                st.metric("Edge", f"{edge*100:.1f}%")

                if odds_data:

                    st.success(f"Best Book: {odds_data['book']} | Game: {odds_data['game']}")

                else:

                    st.warning("Live odds not found. Using manual odds fallback.")

                st.write("Recent PA:", stats["PA"])

                st.write("Hard Hit %:", f"{stats['HardHit']*100:.1f}%")

                st.write("Fly Ball %:", f"{stats['FlyBall']*100:.1f}%")

                st.write("Avg EV:", f"{stats['AvgEV']:.1f} mph")

with tab2:

    prop2 = st.selectbox("Board Prop", ["HR", "RBI", "HRR"], key="boardprop")

    manual_board_odds = st.number_input("Default Manual Odds If Missing", value=300, step=5)

    rows = []

    if st.button("Run Top 30 Board"):

        with st.spinner("Running Top 30 simulations..."):

            for p in TOP_30:

                pid = get_player_id(p)

                if not pid:

                    continue

                stats = get_stats(pid)

                if not stats:

                    continue

                odds_data = get_best_odds(p, MARKETS[prop2])

                odds = odds_data["odds"] if odds_data else manual_board_odds

                prob = model_probability(stats, prop2, boost)

                fair = prob_to_american(prob)

                implied = american_to_prob(odds)

                edge = prob - implied

                rows.append({

                    "Player": p,

                    "Prop": prop2,

                    "Prob %": round(prob * 100, 1),

                    "Fair Odds": fair,

                    "Best Odds": odds,

                    "Edge %": round(edge * 100, 1),

                    "Signal": grade(edge),

                    "Book": odds_data["book"] if odds_data else "Manual"

                })

        rows = sorted(rows, key=lambda x: x["Edge %"], reverse=True)

        st.dataframe(rows, use_container_width=True)

st.warning("Model estimates are not guaranteed. Use bankroll control.")
