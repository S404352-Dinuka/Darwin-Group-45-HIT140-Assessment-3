import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import pandas as pd
import numpy as np
import math
import statistics
import scipy.stats as stats
import statsmodels.stats.weightstats as statsm
import statsmodels.api as sm
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn import metrics
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import PowerTransformer

pd.set_option("display.max_columns", 14)
pd.set_option("display.width", 200)

#Read the three CSV files to ensure that the data was loaded correctly.
world_cup = pd.read_csv("../data/raw/2026 World Cup Scores&Fixtures.xls.csv")
friendly_matches = pd.read_csv("../data/raw/2026 International Friendlies Scores & Fixtures.xls.csv")
qualification = pd.read_csv("../data/raw/2026 World Cup Qualifications.xls.csv")
print(world_cup.info())
print(friendly_matches.info())
print(qualification.info())

#Get the required columns here, removes the empty rows between match weeks and converts Date from text to a date type so we can compare dates
world_cup = world_cup[["Date", "Home", "Score", "Away"]].dropna()
world_cup["Date"] = pd.to_datetime(world_cup["Date"])

#Remove the suspended match and also the unplayed matches. It means did not play yet
friendly_matches = friendly_matches[friendly_matches["Notes"] != "Match Suspended"]
friendly_matches = friendly_matches[["Date", "Home", "Score", "Away"]].dropna()
friendly_matches["Date"] = pd.to_datetime(friendly_matches["Date"])

#Keep only friendly matches before 11 June 2026 (World Cup start), so every variable is pre-match info
friendly_matches = friendly_matches[friendly_matches["Date"] < "2026-06-11"]
print("Matches of World Cup:", world_cup.shape)
print("Friendlies before the World Cup:", friendly_matches.shape)

"""
Reshape the data: each match becomes 2 rows (one per team) with GF (goals for), GA (goals against) and points.
Home like "Mexico mx", Away like "za South Africa", Score like "2–0"
Scores use an en dash, e.g. “2–0”. Shoot-outs look like “(3) 1–1 (4)”. Penalties are not goals, so that we keep only 1–1.
"""
results = []
for match_table in [friendly_matches, world_cup]:
    match_ids = []
    team_list = []
    opponents = []
    goals_for = []
    goals_against = []
    team_points = []
    for i in range(len(match_table)):
        team1 = " ".join(match_table["Home"].iloc[i].split(" ")[:-1])
        team2 = " ".join(match_table["Away"].iloc[i].split(" ")[1:])
        score = match_table["Score"].iloc[i]
        if "(" in score:
            score = score.split(") ")[1].split(" (")[0]
        goals1 = int(score.split("–")[0])
        goals2 = int(score.split("–")[1])

        #points: win = 3, draw = 1, loss = 0
        if goals1 > goals2:
            points = [3, 0]
        elif goals1 == goals2:
            points = [1, 1]
        else:
            points = [0, 3]
             
        #append the home row and the away row (same Match_ID, GF and GA swapped)
        match_ids = match_ids + [i + 1, i + 1]
        team_list = team_list + [team1, team2]
        opponents = opponents + [team2, team1]
        goals_for = goals_for + [goals1, goals2]
        goals_against = goals_against + [goals2, goals1]
        team_points = team_points + points

    results.append(pd.DataFrame({"Match_ID": match_ids, "Team": team_list, "Opponent": opponents,
                                 "GF": goals_for, "GA": goals_against, "Points": team_points}))
fr_results = results[0]
wc_results = results[1]
print("World Cup rows (2 per match):", wc_results.shape)

#Congo DR and Iraq are listed twice, so remove their earlier play-off round
qualification = qualification[qualification["Method"] != "Defeated ng Nigeria"]
qualification = qualification[qualification["Method"] != "Defeated ae United Arab Emirates"]