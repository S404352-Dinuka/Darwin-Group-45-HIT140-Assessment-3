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
plt.figure(figsize=(8, 4.5))
plt.hist(goals, bins=np.arange(-0.5, goals.max() + 1.5, 1), edgecolor="black")
plt.plot([goals_mean, goals_mean], [0, 75], color="red", linestyle="--", label="Mean = " + str(round(goals_mean, 2)))
plt.annotate("3 IQR outliers (6-7 goals)\nare real results, kept", xy=(6.5, 3), xytext=(4.3, 40),
             arrowprops={"facecolor": "black", "shrink": 0.05})
plt.title("Goals Scored by a Team in World Cup 2026 Matches (n = 208)")
plt.xlabel("Goals")
plt.ylabel("No. of Team-Matches (rows)")
plt.legend()
plt.tight_layout()
plt.savefig("../figures/2.2_histogram.png", dpi=300)
plt.show()

#Scatter plot of each candidate variable against goals and its Pearson correlation
columns = data.keys()[2:-1]
for i in range(len(columns)):
    r, p_value = stats.pearsonr(data[columns[i]], goals)
    print(columns[i], " r =", r, " p-value =", p_value)

#Scatter plot of each numeric candidate against goals with a simple linear regression line to check linearity
numeric_columns = ["Fr_Games", "Opp_Fr_Games", "Fr_GF", "Opp_Fr_GA", "Fr_PPG", "Opp_Fr_PPG"]
plt.figure(figsize=(14, 7.5))
for i in range(len(numeric_columns)):
    r, p_value = stats.pearsonr(data[numeric_columns[i]], goals)
    line_model = LinearRegression()
    line_model.fit(data[[numeric_columns[i]]], goals)
    plt.subplot(2, 3, i + 1)
    plt.scatter(data[numeric_columns[i]], goals)
    plt.plot(data[numeric_columns[i]], line_model.predict(data[[numeric_columns[i]]]), color="red")
    plt.title(numeric_columns[i] + "  (r = " + str(round(r, 2)) + ", p = " + str(round(p_value, 4)) + ")")
    plt.xlabel(numeric_columns[i])
    plt.ylabel("Goals")
plt.tight_layout()
plt.savefig("../figures/2.2_scatter.png", dpi=300)
plt.show()

#Mean goals with 95% confidence intervals for each yes/no variable, with a two sample (Welch) t test p-value
binary_columns = ["Strong_Conf", "Opp_Strong_Conf", "Playoff", "Opp_Playoff"]
fig, axes = plt.subplots(1, 4, figsize=(13, 4.5))
for i in range(len(binary_columns)):
    yes = goals[data[binary_columns[i]] == 1]
    no = goals[data[binary_columns[i]] == 0]
    means = [stats.tmean(no), stats.tmean(yes)]
    errors = [1.96 * stats.tstd(no) / math.sqrt(len(no)), 1.96 * stats.tstd(yes) / math.sqrt(len(yes))]
    t_stats, p_val = stats.ttest_ind_from_stats(stats.tmean(yes), stats.tstd(yes), len(yes),
                                                stats.tmean(no), stats.tstd(no), len(no), equal_var=False)
    axes[i].bar(["No (0)", "Yes (1)"], means, yerr=errors)
    axes[i].text(-0.15, 0.1, str(round(means[0], 2)), color="white")
    axes[i].text(0.85, 0.1, str(round(means[1], 2)), color="white")
    axes[i].set_title(binary_columns[i] + "\n(two-sided t test p = " + str(round(p_val, 3)) + ")")
    axes[i].set_ylabel("Mean goals (95% CI)")
fig.tight_layout()
plt.savefig("../figures/2.2_binary_ttests.png", dpi=300)
plt.show()

#Heatmap of the correlation matrix to check collinearity
corr = data.drop(["Match_ID", "Team"], axis=1).corr()
plt.figure(figsize=(11, 9))
sns.heatmap(corr, vmin=-1, vmax=1, center=0, cmap=sns.diverging_palette(20, 220, n=200), annot=True)
plt.xticks(rotation=45, horizontalalignment="right")
plt.title("Correlation Matrix of the 10 Candidate Variables and Goals")
plt.tight_layout()
plt.savefig("../figures/2.2_heatmap.png", dpi=300)
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
std_coef = [round(value, 2) for value in model.params[1:]]
colours = []
for value in std_coef:
    if value > 0:
        colours.append("tab:blue")
    else:
        colours.append("tab:red")
fig, ax = plt.subplots(figsize=(10, 5))
rects = ax.bar(var_x.keys(), std_coef, color=colours)
ax.bar_label(rects, padding=3)
ax.set_ylabel("Change in goals for +1 standard deviation")
ax.set_title("Effect of Each Variable on Goals Scored (Model 2, standardised)")
plt.xticks(rotation=20, horizontalalignment="right")
fig.tight_layout()
plt.savefig("../figures/2.2_coefficients.png", dpi=300)
plt.show()

#Model 3 with the Yeo-Johnson transformation
yj_columns = ["Fr_Games","Opp_Fr_Games","Fr_GF","Opp_Fr_GA"]
power_x = var_x.copy()
power_x[yj_columns] = PowerTransformer().fit_transform(var_x[yj_columns])
model = sm.OLS(var_y, sm.add_constant(power_x)).fit()
print("Model 3 summary:")
print(model.summary())

#Model 6 with the log transformation on the same 4 numeric variables
log_x = var_x.copy()
for column in yj_columns:
    log_x[column] = (var_x[column] + 1).apply(np.log)
model = sm.OLS(var_y, sm.add_constant(log_x)).fit()
print("Model 6 summary:")
print(model.summary())

#Model 4: remove the variable with the highest p-value one at a time
x_reduced = var_x
for column in ["Playoff", "Fr_GF", "Opp_Strong_Conf"]:
    x_reduced = x_reduced.drop([column], axis=1)
    model = sm.OLS(var_y, sm.add_constant(x_reduced)).fit()
    print("Model 4 summary after removing", column)
    print(model.summary())

#add Model 5 with Yeo-Johnson transformation and baseline comparison across multiple algorithms
model_names = ["Baseline", "M1: All 8", "M2: Standardised", "M3: Yeo-Johnson",
               "M4: 5 significant", "M5: 5 sig. + Yeo-Johnson", "M6: Log transform",
               "Ridge: All 8", "Random Forest: All 8"]
model_x = [var_x, var_x, var_x, var_x, x_reduced, x_reduced, var_x, var_x, var_x]
model_scale = ["none", "none", "standard", "yeo-johnson", "none", "yeo-johnson", "log", "standard", "none"]
model_algo = ["mean", "linear", "linear", "linear", "linear", "linear", "linear", "ridge", "forest"]
#Round 21 is a forecast test: train on the 72 group stage matches and predict the 32 knockout matches
rmse_lists = [[] for name in model_names]
r2_lists = [[] for name in model_names]
forecast_rmse = []
forecast_r2 = []
for seed in range(21):
    for m in range(len(model_names)):
        if seed < 20:
            train_x, test_x, train_y, test_y = train_test_split(model_x[m], var_y, test_size=0.4, random_state=seed)
        else:
            train_x = model_x[m][data["Match_ID"] <= 72]
            test_x = model_x[m][data["Match_ID"] > 72]
            train_y = var_y[data["Match_ID"] <= 72]
            test_y = var_y[data["Match_ID"] > 72]
        if model_scale[m] == "standard":
            scaler = StandardScaler()
            train_x = scaler.fit_transform(train_x)
            test_x = scaler.transform(test_x)
        if model_scale[m] == "yeo-johnson":
            columns = []
            for column in train_x.keys():
                if column in yj_columns:
                    columns.append(column)
            scaler = PowerTransformer()
            train_x = train_x.copy()
            test_x = test_x.copy()
            train_x[columns] = scaler.fit_transform(train_x[columns])
            test_x[columns] = scaler.transform(test_x[columns])
        if model_scale[m] == "log":
            train_x = train_x.copy()
            test_x = test_x.copy()
            for column in yj_columns:
                train_x[column] = (train_x[column] + 1).apply(np.log)
                test_x[column] = (test_x[column] + 1).apply(np.log)
        if model_algo[m] == "mean":
            pred_y = [np.mean(train_y)] * len(test_y)
        else:
            if model_algo[m] == "linear":
                model = LinearRegression()
            if model_algo[m] == "ridge":
                model = Ridge(alpha=10)
            if model_algo[m] == "forest":
                model = RandomForestRegressor(n_estimators=100, min_samples_leaf=5, random_state=0)
            model.fit(train_x, train_y)
            pred_y = model.predict(test_x)
        rmse = math.sqrt(metrics.mean_squared_error(test_y, pred_y))
        r2 = metrics.r2_score(test_y, pred_y)
        if seed < 20:
            rmse_lists[m].append(rmse)
            r2_lists[m].append(r2)
        else:
            forecast_rmse.append(rmse)
            forecast_r2.append(r2)

#Put the average RMSE, normalised RMSE and R2 of each model in to a table
#One sample t test on the 20 RMSE differences (model - M1): is the model really different from M1?
avg_rmse = []
norm_rmse = []
avg_r2 = []
p_values = []
rmse_table = pd.DataFrame()
for m in range(len(model_names)):
    avg_rmse.append(np.mean(rmse_lists[m]))
    norm_rmse.append(np.mean(rmse_lists[m])/(var_y.max() - var_y.min()))
    avg_r2.append(np.mean(r2_lists[m]))
    rmse_table[model_names[m]] = rmse_lists[m]
    difference = []
    for i in range(20):
        difference.append(rmse_lists[m][i] - rmse_lists[1][i])
    if m == 1 or m == 2:
        p_values.append("same as M1")
    else:
        t_stats, p_val = stats.ttest_1samp(difference, 0)
        p_values.append(round(p_val, 4))
results = pd.DataFrame({"Model": model_names, "Average RMSE": avg_rmse, "RMSE (Normalised)": norm_rmse, "Average R2": avg_r2,
                        "P-Val vs M1": p_values, "Knockout RMSE": forecast_rmse, "Knockout R2": forecast_r2})
print("Average performance over 20 train/test splits and the knockout forecast test:")
print(results)
results.to_csv("../figures/2.2_model_comparison.csv", index=False)

#Count the splits Ridge wins and give a 95% confidence interval of the mean RMSE difference, using the same method as the confidence interval of the goals
ridge = model_names.index("Ridge: All 8")
wins = 0
difference = []
for i in range(20):
    difference.append(rmse_lists[ridge][i] - rmse_lists[1][i])
    if rmse_lists[ridge][i] < rmse_lists[1][i]:
        wins = wins + 1
diff_mean = stats.tmean(difference)
diff_error = stats.tstd(difference) / math.sqrt(len(difference))
diff_low, diff_high = statsm._zconfint_generic(diff_mean, diff_error, alpha=0.05, alternative="two-sided")
print("Ridge had a lower RMSE than M1 in", wins, "of the 20 splits")
print("Ridge - M1 mean RMSE difference:", diff_mean, " 95% Confidence Interval:", diff_low, "to", diff_high)

#Box plot of the RMSE of each model from the 20 splits
plt.figure(figsize=(10, 6))
sns.boxplot(data=rmse_table, orient="h")
plt.title("RMSE of Each Model over 20 Train/Test Splits (lower is better)")
plt.xlabel("RMSE (goals)")
plt.tight_layout()
plt.savefig("../figures/2.2_rmse_boxplot.png", dpi=150)
plt.show()


#Final model: Ridge with all 8 variables, the only model significantly better than M1
#The variables are standardised, so each coefficient is the change in goals for a 1 standard deviation change
scaler = StandardScaler()
final_model = Ridge(alpha=10)
final_model.fit(scaler.fit_transform(var_x), var_y)
print("Final model (Ridge) intercept:", final_model.intercept_)
coefficients = pd.DataFrame({"Variable": var_x.keys(), "Coefficient (per 1 SD)": final_model.coef_})
print(coefficients)

#Plot the actual vs predicted values and the residuals (errors) of the final model on one test split
train_x, test_x, train_y, test_y = train_test_split(var_x, var_y, test_size=0.4, random_state=0)
scaler = StandardScaler()
model = Ridge(alpha=10)
model.fit(scaler.fit_transform(train_x), train_y)
pred_y = model.predict(scaler.transform(test_x))
residuals = test_y - pred_y
plt.figure(figsize=(11, 4.5))
plt.subplot(1, 2, 1)
plt.scatter(test_y, pred_y)
plt.plot([0, 7], [0, 7], color="red")
plt.annotate("Big wins (5-7 goals)\nare under-predicted", xy=(6, 2.2), xytext=(4.7, 0.15),
             arrowprops={"facecolor": "black", "shrink": 0.05})
plt.title("Final Model: Actual vs Predicted Goals")
plt.xlabel("Actual Goals")
plt.ylabel("Predicted Goals")
plt.subplot(1, 2, 2)
plt.scatter(pred_y, residuals)
plt.plot([min(pred_y), max(pred_y)], [0, 0], color="red")
plt.title("Residuals (should be spread evenly around 0)")
plt.xlabel("Predicted Goals")
plt.ylabel("Residual (Actual - Predicted)")
plt.tight_layout()
plt.savefig("../figures/2.2_final_model.png", dpi=300)
plt.show()