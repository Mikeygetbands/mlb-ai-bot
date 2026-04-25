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

TEAM_HITTERS = {
    "NYY": ["Aaron Judge","Giancarlo Stanton","Anthony Volpe","Gleyber Torres"],

    "BOS": ["Rafael Devers","Triston Casas","Trevor Story","Jarren Duran"],

    "LAD": ["Shohei Ohtani","Mookie Betts","Freddie Freeman","Max Muncy","Will Smith"],

    "CHC": ["Seiya Suzuki","Cody Bellinger","Ian Happ","Dansby Swanson"],

    "ATL": ["Ronald Acuna Jr.","Matt Olson","Austin Riley","Marcell Ozuna","Ozzie Albies"],

    "PHI": ["Kyle Schwarber","Bryce Harper","Trea Turner","Nick Castellanos"],

    "NYM": ["Pete Alonso","Francisco Lindor","Brandon Nimmo"],

    "HOU": ["Yordan Alvarez","Jose Altuve","Kyle Tucker","Alex Bregman"],

    "TEX": ["Corey Seager","Adolis Garcia","Marcus Semien","Josh Jung"],

    "TOR": ["Vladimir Guerrero Jr.","Bo Bichette","George Springer"],

    "BAL": ["Gunnar Henderson","Adley Rutschman","Anthony Santander"],

    "SEA": ["Julio Rodriguez","Cal Raleigh","Mitch Haniger"],

    "SD": ["Fernando Tatis Jr.","Manny Machado","Xander Bogaerts"],

    "ARI": ["Corbin Carroll","Christian Walker","Ketel Marte"],

    "CIN": ["Elly De La Cruz","Spencer Steer","Tyler Stephenson"],

    "CLE": ["Jose Ramirez","Josh Naylor","Steven Kwan"],

    "KC": ["Bobby Witt Jr.","Salvador Perez","Vinnie Pasquantino"],

    "DET": ["Spencer Torkelson","Riley Greene","Kerry Carpenter"],

    "MIN": ["Byron Buxton","Carlos Correa","Royce Lewis"],

    "TB": ["Yandy Diaz","Brandon Lowe","Isaac Paredes"],

    "MIL": ["Christian Yelich","Rhys Hoskins","William Contreras"],

    "STL": ["Nolan Arenado","Paul Goldschmidt","Willson Contreras"],

    "PIT": ["Oneil Cruz","Bryan Reynolds","Ke'Bryan Hayes"],

    "MIA": ["Jazz Chisholm Jr.","Josh Bell","Jake Burger"],

    "COL": ["Kris Bryant","Ryan McMahon","Elias Diaz"],

    "SF": ["Matt Chapman","Jorge Soler","Michael Conforto"],

    "LAA": ["Mike Trout","Taylor Ward","Logan O'Hoppe"],

    "WSH": ["CJ Abrams","Lane Thomas","Keibert Ruiz"],

    "OAK": ["Brent Rooker","Shea Langeliers","Zack Gelof"],

    "CWS": ["Luis Robert Jr.","Eloy Jimenez","Andrew Vaughn"]

}

    "

PITCHER_DATA = {

    "Gerrit Cole": {"HR9": 0.9, "HardHit": 0.32},

    "Chris Sale": {"HR9": 1.1, "HardHit": 0.35},

    "Zack Wheeler": {"HR9": 1.0, "HardHit": 0.33},

    "Luis Castillo": {"HR9": 1.2, "HardHit": 0.36},

    "Kevin Gausman": {"HR9": 1.3, "HardHit": 0.37},

    "Blake Snell": {"HR9": 1.1, "HardHit": 0.34},

    "Framber Valdez": {"HR9": 0.7, "HardHit": 0.31}

}

BULLPEN_WEAKNESS = {

    "NYY": 0.95, "BOS": 1.05, "LAD": 0.98, "CHC": 1.07,

    "ATL": 0.97, "PHI": 1.02, "HOU": 0.96, "TEX": 1.08,

    "TOR": 1.03, "BAL": 0.98, "SEA": 0.97, "SD": 1.01,

    "KC": 1.06, "CIN": 1.09, "CLE": 0.96, "LAA": 1.08

}

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

st.caption("HR • RBI • HRR • Team Matchups • Starting Pitcher • Bullpen • Weather • Sportsbook Odds")

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

    hit = len(data[data["events"].isin(["single", "double", "triple", "home_run"])])

    hard_hit = len(batted[batted["launch_speed"] >= 95]) / max(len(batted), 1)

    fly_ball = len(batted[(batted["launch_angle"] >= 20) & (batted["launch_angle"] <= 50)]) / max(len(batted), 1)

    avg_ev = batted["launch_speed"].mean() if not batted.empty else 88

    return {

        "PA": pa,

        "HR": hr,

        "H": hit,

        "HR_PA": hr / pa,

        "H_PA": hit / pa,

        "RBI_PA": 0.22,

        "HardHit": hard_hit,

        "FlyBall": fly_ball,

        "AvgEV": avg_ev

    }

def get_weather_boost():

    st.sidebar.header("Weather Boost")

    temp = st.sidebar.slider("Temperature", 45, 100, 75)

    wind = st.sidebar.slider("Wind Out MPH", 0, 25, 5)

    boost = 1.00

    if temp >= 80:

        boost += 0.06

    elif temp >= 70:

        boost += 0.03

    elif temp <= 55:

        boost -= 0.05

    if wind >= 12:

        boost += 0.08

    elif wind >= 8:

        boost += 0.04

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

def model_probability(stats, prop_type, boost, pitcher=None, opponent_team=None):

    hard_hit = 1 + stats["HardHit"] * 0.35

    fly_ball = 1 + stats["FlyBall"] * 0.30

    pitcher_boost = 1.0

    if pitcher and pitcher in PITCHER_DATA:

        p = PITCHER_DATA[pitcher]

        pitcher_boost = 1 + ((p["HR9"] - 1.0) * 0.6) + ((p["HardHit"] - 0.33) * 0.5)

    bullpen_boost = 1.0

    if opponent_team and opponent_team in BULLPEN_WEAKNESS:

        bullpen_boost = BULLPEN_WEAKNESS[opponent_team]

    if prop_type == "HR":

        base = max(stats["HR_PA"], 0.035)

        adj = base * hard_hit * fly_ball * pitcher_boost * bullpen_boost * boost

        prob = 1 - (1 - adj) ** 4

    elif prop_type == "RBI":

        base = max(stats["RBI_PA"], 0.18)

        adj = base * (1 + stats["HardHit"] * 0.20) * bullpen_boost * boost

        prob = 1 - (1 - min(adj, 0.45)) ** 4

    else:

        base = max(stats["H_PA"] + stats["RBI_PA"], 0.35)

        adj = min(base * (1 + stats["HardHit"] * 0.15) * bullpen_boost * boost, 0.65)

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

boost = get_weather_boost()

tab1, tab2, tab3 = st.tabs(["🔎 Single Player", "🏆 Top 30 Board", "⚾ Game Matchup"])

with tab1:

    st.subheader("Single Player Prop Simulator")

    prop = st.selectbox("Choose Prop", ["HR", "RBI", "HRR"])

    player = st.text_input("Enter Player Name", placeholder="Aaron Judge")

    pitcher = st.text_input("Starting Pitcher Optional", placeholder="Chris Sale")

    opponent = st.text_input("Opponent Team Code Optional", placeholder="BOS")

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

                prob = model_probability(stats, prop, boost, pitcher=pitcher, opponent_team=opponent.upper())

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

                st.write("Recent HR:", stats["HR"])

                st.write("Hard Hit %:", f"{stats['HardHit']*100:.1f}%")

                st.write("Fly Ball %:", f"{stats['FlyBall']*100:.1f}%")

                st.write("Avg EV:", f"{stats['AvgEV']:.1f} mph")

with tab2:

    st.subheader("Top 30 MLB Board")

    prop2 = st.selectbox("Board Prop", ["HR", "RBI", "HRR"], key="boardprop")

    manual_board_odds = st.number_input("Default Manual Odds If Missing", value=300, step=5)

    if st.button("Run Top 30 Board"):

        rows = []

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

with tab3:

    st.subheader("Game Matchup HR Finder")

    st.write("Use team codes like NYY, BOS, LAD, CHC, ATL, PHI, HOU, TEX.")

    team1 = st.text_input("Team 1", placeholder="NYY")

    team2 = st.text_input("Team 2", placeholder="BOS")

    pitcher_vs_team1 = st.text_input("Pitcher Facing Team 1", placeholder="Chris Sale")

    pitcher_vs_team2 = st.text_input("Pitcher Facing Team 2", placeholder="Gerrit Cole")

    matchup_manual_odds = st.number_input("Default Manual HR Odds If Live Odds Missing", value=300, step=5, key="matchup_manual")

    if st.button("Find Best HR Plays In This Game"):

        t1 = team1.upper().strip()

        t2 = team2.upper().strip()

        players_t1 = TEAM_HITTERS.get(t1, [])

        players_t2 = TEAM_HITTERS.get(t2, [])

        if not players_t1 or not players_t2:

            st.error("Team code not found or missing hitters.")

        else:

            matchup_rows = []

            with st.spinner("Running matchup HR simulations..."):

                for p in players_t1:

                    pid = get_player_id(p)

                    if not pid:

                        continue

                    stats = get_stats(pid)

                    if not stats:

                        continue

                    odds_data = get_best_odds(p, MARKETS["HR"])

                    odds = odds_data["odds"] if odds_data else matchup_manual_odds

                    prob = model_probability(stats, "HR", boost, pitcher=pitcher_vs_team1, opponent_team=t2)

                    fair = prob_to_american(prob)

                    implied = american_to_prob(odds)

                    edge = prob - implied

                    matchup_rows.append({

                        "Player": p,

                        "Team": t1,

                        "Opponent": t2,

                        "HR Prob %": round(prob * 100, 1),

                        "Fair Odds": fair,

                        "Best Odds": odds,

                        "Edge %": round(edge * 100, 1),

                        "Signal": grade(edge),

                        "Book": odds_data["book"] if odds_data else "Manual"

                    })

                for p in players_t2:

                    pid = get_player_id(p)

                    if not pid:

                        continue

                    stats = get_stats(pid)

                    if not stats:

                        continue

                    odds_data = get_best_odds(p, MARKETS["HR"])

                    odds = odds_data["odds"] if odds_data else matchup_manual_odds

                    prob = model_probability(stats, "HR", boost, pitcher=pitcher_vs_team2, opponent_team=t1)

                    fair = prob_to_american(prob)

                    implied = american_to_prob(odds)

                    edge = prob - implied

                    matchup_rows.append({

                        "Player": p,

                        "Team": t2,

                        "Opponent": t1,

                        "HR Prob %": round(prob * 100, 1),

                        "Fair Odds": fair,

                        "Best Odds": odds,

                        "Edge %": round(edge * 100, 1),

                        "Signal": grade(edge),

                        "Book": odds_data["book"] if odds_data else "Manual"

                    })

            matchup_rows = sorted(matchup_rows, key=lambda x: x["Edge %"], reverse=True)

            st.dataframe(matchup_rows, use_container_width=True)

            if matchup_rows:

                st.success(f"Top HR Play: {matchup_rows[0]['Player']} — {matchup_rows[0]['Signal']}")

st.warning("Model estimates are not guarantees. Use bankroll control.")
