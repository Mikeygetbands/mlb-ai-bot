import os

import streamlit as st

import random

st.title("🔥 MLB HR AI Simulator")

player_name = st.text_input("Enter Player Name")

if player_name:

    hr_prob = random.uniform(0.15, 0.35)

    if hr_prob > 0.5:

        fair_odds = -100 * (hr_prob / (1 - hr_prob))

    else:

        fair_odds = 100 * ((1 - hr_prob) / hr_prob)

    sportsbook_odds = random.randint(200, 400)

    edge = sportsbook_odds - fair_odds

    if edge > 60:

        signal = "🔥 ELITE"

    elif edge > 30:

        signal = "🔥 STRONG"

    elif edge > 10:

        signal = "👍 VALUE"

    else:

        signal = "❌ PASS"

    st.write(f"Player: {player_name}")

    st.write(f"HR Probability: {round(hr_prob*100,2)}%")

    st.write(f"Fair Odds: {round(fair_odds)}")

    st.write(f"Sportsbook Odds: +{sportsbook_odds}")

    st.write(f"Edge: {round(edge)}")

    st.write(f"Signal: {signal}")
