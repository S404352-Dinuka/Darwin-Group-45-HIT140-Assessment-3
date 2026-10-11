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

#hosts have NaN in Comp, so replace NaN with an empty string
qualification = qualification.fillna("")

"""
Store the strong confederation and play off info of each team in dictionaries
Strong confederation = UEFA (Europe) or CONMEBOL (South America)
"""
strong_conf = {}
playoff = {}
for i in range(len(qualification)):
    team = " ".join(qualification["Squad"].iloc[i].split(" ")[1:])
    #These 2 team names are written differently in this file, so that the match them to the match tables
    if team == "Bosnia and Herzegovina":
        team = "Bosnia–Herz"
    if team == "United States":
        team = "USA"
    confederation = qualification["Confederation"].iloc[i]
    competition = qualification["Comp"].iloc[i]

    strong_conf[team] = 0
    if confederation == "UEFA" or confederation == "CONMEBOL":
        strong_conf[team] = 1
    playoff[team] = 0
    if "Second round" in competition or "Fourth round" in competition or "Fifth round" in competition or "Inter-confederation" in competition:
        playoff[team] = 1


#Friendly results of each World Cup team before the World Cup
#Games = number of friendly_matches played, GF = average goals scored, GA = average goals conceded, PPG = average points
fr_games = {}
fr_gf = {}
fr_ga = {}
fr_ppg = {}
total_goals = 0
total_games = 0
for team in strong_conf:
    team_games = fr_results[fr_results["Team"] == team]
    total_goals = total_goals + team_games["GF"].sum()
    total_games = total_games + len(team_games)
    fr_games[team] = len(team_games)
    fr_gf[team] = team_games["GF"].mean()
    fr_ga[team] = team_games["GA"].mean()
    fr_ppg[team] = team_games["Points"].mean()

"""
Build the modelling dataset: one row per team per match (104 x 2 = 208 rows). 
Columns starting with Opponent describe the opponent, the others describe the team. 
All values come from qualification or friendlies, so they are known before kickoff here
"""
rows = []
for i in range(len(wc_results)):
    team = wc_results["Team"].iloc[i]
    opp = wc_results["Opponent"].iloc[i]
    rows.append([wc_results["Match_ID"].iloc[i], team,
                 strong_conf[team], strong_conf[opp],
                 playoff[team], playoff[opp],
                 fr_games[team], fr_games[opp],
                 fr_gf[team], fr_ga[opp],
                 fr_ppg[team], fr_ppg[opp],
                 wc_results["GF"].iloc[i]])

data = pd.DataFrame(rows, columns=["Match_ID", "Team", "Strong_Conf", "Opp_Strong_Conf",
                                   "Playoff", "Opp_Playoff", "Fr_Games", "Opp_Fr_Games",
                                   "Fr_GF", "Opp_Fr_GA", "Fr_PPG", "Opp_Fr_PPG", "Goals"])
print(data.info())
print(data.head())
print("Rows and Columns:", data.shape)

#Descriptive statistics: count, mean, std, min, quartiles and max, plus median and mode of Goals
goals = data["Goals"]
print(data.drop(["Match_ID"], axis=1).describe())
print("Median:", statistics.median(goals))
print("Mode:", statistics.mode(goals))

#Find the outliers of the goals using the IQR rule
q1 = np.percentile(goals, 25)
q3 = np.percentile(goals, 75)
iqr = q3 - q1
lower = q1 - 1.5 * iqr
upper = q3 + 1.5 * iqr
print("Number of outliers:", len(goals[goals < lower]) + len(goals[goals > upper]))

#95% confidence interval of the mean goals scored by a team in a World Cup match
goals_mean = stats.tmean(goals)
goals_error = stats.tstd(goals) / math.sqrt(len(goals))
goals_low, goals_high = statsm._zconfint_generic(goals_mean, goals_error, alpha=0.05, alternative="two-sided")
print("Goals Mean:", goals_mean, " 95% Confidence Interval:", goals_low, "to", goals_high)
