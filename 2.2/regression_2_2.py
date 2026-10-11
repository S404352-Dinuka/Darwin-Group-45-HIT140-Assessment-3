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
    rows.append([wc_results["Match_ID"].iloc[i], team, strong_conf[team], strong_conf[opp], playoff[team], playoff[opp],
                 fr_games[team], fr_games[opp], fr_gf[team], fr_ga[opp], fr_ppg[team], fr_ppg[opp], wc_results["GF"].iloc[i]])

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

#One sample t test: is the mean World Cup goals different from the mean friendly goals?
friendly_mean = total_goals / total_games
print("Average goals per game of the World Cup teams in friendly matches:", friendly_mean)
t_stats, p_val = stats.ttest_1samp(goals, friendly_mean)
print("One sample t test  T Stats:", t_stats, " P-Val:", p_val)
if p_val < 0.05:
    print("Reject Hypothesis")
else:
    print("Do not reject Hypothesis")

"""
Two-sample Welch’s t-test (unequal variances, one-sided). 
H0: UEFA/CONMEBOL teams do not score more goals than other teams
"""
strong = goals[data["Strong_Conf"] == 1]
others = goals[data["Strong_Conf"] == 0]
t_stats, p_val = stats.ttest_ind_from_stats(stats.tmean(strong), stats.tstd(strong), len(strong),
                                            stats.tmean(others), stats.tstd(others), len(others),
                                            equal_var=False, alternative="greater")
print("Two sample t test  T Stats:", t_stats, " P-Val:", p_val)
if p_val < 0.05:
    print("Reject Hypothesis")
else:
    print("Do not reject Hypothesis")

#Histogram of Goals to check the shape of the distribution
plt.hist(goals, bins=int(goals.max() + 1), edgecolor="black")
plt.title("Goals Scored by a Team in World Cup 2026 Matches")
plt.xlabel("Goals")
plt.ylabel("No. of Team-Matches (rows)")
plt.savefig("../figures/2.2_histogram.png", dpi=150)
plt.show()

#Scatter plot of each candidate variable against goals and its Pearson correlation
columns = data.keys()[2:-1]
plt.figure(figsize=(16, 7))
for i in range(len(columns)):
    r, p_value = stats.pearsonr(data[columns[i]], goals)
    print(columns[i], " r =", r, " p-value =", p_value)
    plt.subplot(2, 5, i + 1)
    plt.scatter(data[columns[i]], goals)
    plt.xlabel(columns[i])
    plt.ylabel("Goals")
plt.tight_layout()
plt.savefig("../figures/2.2_scatter.png", dpi=150)
plt.show()

#Heatmap of the correlation matrix to check collinearity
corr = data.drop(["Match_ID", "Team"], axis=1).corr()
plt.figure(figsize=(11, 9))
sns.heatmap(corr, vmin=-1, vmax=1, center=0, cmap=sns.diverging_palette(20, 220, n=200), annot=True)
plt.xticks(rotation=45, horizontalalignment="right")
plt.tight_layout()
plt.savefig("../figures/2.2_heatmap.png", dpi=150)
plt.show()

#Fr_PPG is highly correlated (r > 0.7) with Fr_GF and Opp_Fr_PPG is strongly correlated with Opp_Fr_GA
#Friendly points per game is also already used in 2.1 and only 4 variables can be shared with 2.1
#So drop Fr_PPG and Opp_Fr_PPG and keep the goal based friendly variables
print("Fr_PPG vs Fr_GF:", corr["Fr_PPG"]["Fr_GF"])
print("Opp_Fr_PPG vs Opp_Fr_GA:", corr["Opp_Fr_PPG"]["Opp_Fr_GA"])
data = data.drop(["Fr_PPG", "Opp_Fr_PPG"], axis=1)
data.to_csv("../data/processed/regression_2_2_dataset.csv", index=False)

#Divide the x and y variables and show the 8 used variables
var_x = data.drop(["Match_ID", "Team", "Goals"], axis=1)
var_y = data["Goals"]
print("Explanatory variables:", var_x.keys())

#Model 1 with all 8 variables using all the rows
model = sm.OLS(var_y, sm.add_constant(var_x)).fit()
print("Model 1 summary:")
print(model.summary())

#Model 2 with z score standardisation to see which variables have the biggest effect
std_x = pd.DataFrame(StandardScaler().fit_transform(var_x), columns=var_x.columns)
model = sm.OLS(var_y, sm.add_constant(std_x)).fit()
print("Model 2 summary:")
print(model.summary())

#Creating the bar chart of the standardised coefficients
plt.figure(figsize=(10, 5))
plt.bar(var_x.keys(), model.params[1:])
plt.ylabel("Standardised coefficient")
plt.title("Effect of Each Variable on Goals Scored (bigger bar = stronger effect)")
plt.xticks(rotation=20, horizontalalignment="right")
plt.tight_layout()
plt.savefig("../figures/2.2_coefficients.png", dpi=150)
plt.show()

#Model 3 with the Yeo-Johnson transformation
#It is only used on the variables with many values, not on the yes/no variables (0 and 1)
yj_columns = ["Fr_Games","Opp_Fr_Games","Fr_GF","Opp_Fr_GA"]
power_x = var_x.copy()
power_x[yj_columns] = PowerTransformer().fit_transform(var_x[yj_columns])
model = sm.OLS(var_y, sm.add_constant(power_x)).fit()
print("Model 3 summary:")
print(model.summary())