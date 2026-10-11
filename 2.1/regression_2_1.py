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

#Setting column range and width for display
pd.set_option("display.max_columns", 14)
pd.set_option("display.width", 200)


#Read the World Cup csv file and check the data
wc_data = pd.read_csv("../data/raw/2026 World Cup Scores&Fixtures.xls.csv")
print("Check World Cup Data")
print(wc_data.info())

#Get the needed columns, remove blank rows and change the date format
wc_data = wc_data[["Date", "Home", "Score", "Away"]].dropna()
wc_data["Date"] = pd.to_datetime(wc_data["Date"])
print("World Cup Rows and Columns:", wc_data.shape)


#Read the friendlies csv file and check the data
fr_data = pd.read_csv("../data/raw/2026 International Friendlies Scores & Fixtures.xls.csv")
print("Check Friendlies Data")
print(fr_data.info())

#Remove suspended matches and matches without any scores
fr_data = fr_data[fr_data["Notes"] != "Match Suspended"]
fr_data = fr_data[["Date", "Home", "Score", "Away"]].dropna()
fr_data["Date"] = pd.to_datetime(fr_data["Date"])

#Keep only the friendlies played before the World Cup started (11th of June 2026)
fr_data = fr_data[fr_data["Date"] < "2026-06-11"]
print("Friendlies Rows and Columns:", fr_data.shape)


#Read the qualification csv file and check the data
qual_data = pd.read_csv("../data/raw/2026 World Cup Qualifications.xls.csv")
print("Check Qualification Data")
print(qual_data.info())

#Remove the repeated qualification records for Congo DR and Iraq
qual_data = qual_data[qual_data["Method"] != "Defeated ng Nigeria"]
qual_data = qual_data[qual_data["Method"] != "Defeated ae United Arab Emirates"]
qual_data = qual_data.fillna("")


#Store each team's host, confederation and playoff details in dictionaries
host = {}
strong_conf = {}
playoff = {}
for i in range(len(qual_data)):
    #Splits country code from country
    team = " ".join(qual_data["Squad"].iloc[i].split(" ")[1:])
    #Changing names to match other country data
    if team == "Bosnia and Herzegovina":
        team = "Bosnia–Herz"
    if team == "United States":
        team = "USA"
    conf = qual_data["Confederation"].iloc[i]
    comp = qual_data["Comp"].iloc[i]

    host[team] = 0
    if qual_data["Method"].iloc[i] == "Competition Host":
        host[team] = 1
    #Give 1 to UEFA and CONMEBOL teams and 0 to the other teams since these two have stronger confederation teams
    strong_conf[team] = 0
    if conf == "UEFA" or conf == "CONMEBOL":
        strong_conf[team] = 1
    playoff[team] = 0
    #Teams that go through extra play off round to qualify gets one
    if "Second round" in comp or "Fourth round" in comp or "Fifth round" in comp or "Inter-confederation" in comp:
        playoff[team] = 1


#Store each match as two rows to get the stats for both teams separately
team_tables = []
for table in [fr_data, wc_data]:
    team_list = []
    opp_list = []
    date_list = []
    gf_list = []
    ga_list = []
    points_list = []
    for i in range(len(table)):
        #Changing names to match other country data and get the match scores
        team1 = " ".join(table["Home"].iloc[i].split(" ")[:-1])
        team2 = " ".join(table["Away"].iloc[i].split(" ")[1:])
        score = table["Score"].iloc[i]
        #Remove the penalty shootout scores if they are present
        if "(" in score:
            score = score.split(") ")[1].split(" (")[0]
        goals1 = int(score.split("–")[0])
        goals2 = int(score.split("–")[1])

        #Give 3 points for a win, 1 for a draw and 0 for a loss
        if goals1 > goals2:
            points = [3, 0]
        elif goals1 == goals2:
            points = [1, 1]
        else:
            points = [0, 3]

        #Add the match results for both teams into their separate lists
        team_list = team_list + [team1, team2]
        opp_list = opp_list + [team2, team1]
        date_list = date_list + [table["Date"].iloc[i], table["Date"].iloc[i]]
        gf_list = gf_list + [goals1, goals2]
        ga_list = ga_list + [goals2, goals1]
        points_list = points_list + points

    team_tables.append(pd.DataFrame({"Team": team_list, "Opponent": opp_list, "Date": date_list,
                                     "GF": gf_list, "GA": ga_list, "Points": points_list}))
fr_results = team_tables[0]
wc_results = team_tables[1]


#Check if the opponent in each friendly also qualified for the World Cup
opp_wc_list = []
for opponent in fr_results["Opponent"]:
    if opponent in host:
        opp_wc_list.append(1)
    else:
        opp_wc_list.append(0)
fr_results["Opp_WC"] = opp_wc_list


#Calculating the difference between the two teams and get both teams from the two rows stored for each match
rows = []
for i in range(0, len(wc_results), 2):
    team1 = wc_results["Team"].iloc[i]
    team2 = wc_results["Team"].iloc[i + 1]
    date = wc_results["Date"].iloc[i]
    fr1 = fr_results[fr_results["Team"] == team1]
    fr2 = fr_results[fr_results["Team"] == team2]
    #Get only the previous World Cup match results for each team
    wc1 = wc_results[wc_results["Team"] == team1]
    wc1 = wc1[wc1["Date"] < date]
    wc2 = wc_results[wc_results["Team"] == team2]
    wc2 = wc2[wc2["Date"] < date]

    #Calculate the differences 
    row = [len(rows) + 1,
           host[team1] - host[team2],
           strong_conf[team1] - strong_conf[team2],
           playoff[team1] - playoff[team2],
           fr1["Points"].mean() - fr2["Points"].mean(),
           fr1["GF"].mean() - fr2["GF"].mean(),
           fr1["GA"].mean() - fr2["GA"].mean(),
           fr1["Opp_WC"].mean() - fr2["Opp_WC"].mean()]
    #If first world cup, set to 0
    if len(wc1) == 0:
        row = row + [0, 0, 0]
    else:
        row = row + [wc1["Points"].mean() - wc2["Points"].mean(),
                     wc1["GF"].mean() - wc2["GF"].mean(),
                     wc1["GA"].mean() - wc2["GA"].mean()]

    #Calculate the actual goal difference between the two teams
    row.append(wc_results["GF"].iloc[i] - wc_results["GA"].iloc[i])
    rows.append(row)

#Put all match rows into one table with the column names
data = pd.DataFrame(rows, columns=["Match_ID", "Host_Diff", "Conf_Diff", "Playoff_Diff",
                                   "Fr_PPG_Diff", "Fr_GF_Diff", "Fr_GA_Diff", "Fr_Opp_Diff",
                                   "WC_PPG_Diff", "WC_GF_Diff", "WC_GA_Diff", "Goal_Diff"])
print("Check Regression Data")
print(data.info())
print(data.head())
print("Rows and Columns:", data.shape)


#Show descriptive stats for the goal difference and the other variables
goal_diff = data["Goal_Diff"]
print("Goal Difference and Variables Descriptive Stats:")
print(data.drop(["Match_ID"], axis=1).describe())
print("Goal Difference Median:", statistics.median(goal_diff))
print("Goal Difference Mode:", statistics.mode(goal_diff))

#Calculate the mean and 95% confidence interval for the goal difference
gd_mean = stats.tmean(goal_diff)
gd_error = stats.tstd(goal_diff) / math.sqrt(len(goal_diff))
gd_low, gd_high = statsm._zconfint_generic(gd_mean, gd_error, alpha=0.05, alternative="two-sided")
print("Goal Difference Mean:", gd_mean)
print("Goal Difference 95% Confidence Interval:", gd_low, "to", gd_high)

#Find any outliers in the goal difference using the IQR method
q1 = np.percentile(goal_diff, 25)
q3 = np.percentile(goal_diff, 75)
iqr = q3 - q1
low = q1 - 1.5 * iqr
high = q3 + 1.5 * iqr
print("Number of Goal Difference Outliers:", len(goal_diff[goal_diff < low]) + len(goal_diff[goal_diff > high]))

