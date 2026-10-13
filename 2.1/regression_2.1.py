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


#Create a heatmap to check the correlations between variables
corr = data.drop(["Match_ID"], axis=1).corr()
plt.figure(figsize=(11, 9))
sns.heatmap(corr, vmin=-1, vmax=1, center=0, cmap=sns.diverging_palette(20, 220, n=200), annot=True)
plt.xticks(rotation=45, horizontalalignment="right")
plt.tight_layout()
plt.savefig("../figures/2.1_heatmap.png", dpi=150)
plt.show()

#Create a histogram to show the different goal differences
plt.hist(goal_diff, bins=int(goal_diff.max() - goal_diff.min() + 1), edgecolor="black")
plt.title("Goal Difference in World Cup 2026 Matches")
plt.xlabel("Goal Difference (Team1 - Team2)")
plt.ylabel("No. of Matches")
plt.savefig("../figures/2.1_histogram.png", dpi=150)
plt.show()

#Create scatter plots to check the relationship of variable and goal difference
columns = data.keys()[1:-1]
plt.figure(figsize=(16, 7))
for i in range(len(columns)):
    r, p_val = stats.pearsonr(data[columns[i]], goal_diff)
    print("Variable:", columns[i])
    print("Correlation:", r)
    print("P-Val:", p_val)
    plt.subplot(2, 5, i + 1)
    plt.scatter(data[columns[i]], goal_diff)
    plt.xlabel(columns[i])
    plt.ylabel("Goal_Diff")
plt.tight_layout()
plt.savefig("../figures/2.1_scatter.png", dpi=150)
plt.show()


#Check t test and say if the hypothesis is rejected
def print_t_test(test_name, t_stats, p_val):
    print(test_name)
    print("T Stats:", t_stats)
    print("P-Val:", p_val)
    if p_val < 0.05:
        print("Reject Hypothesis")
    else:
        print("Do not reject Hypothesis")

#Check one sample t test, if the mean goal difference is different from 0
t_stats, p_val = stats.ttest_1samp(goal_diff, 0)
print_t_test("One Sample T Test:", t_stats, p_val)

#Check two sample t test to compate if goal differences are based on friendly points
better_fr = goal_diff[data["Fr_PPG_Diff"] > 0]
other_fr = goal_diff[data["Fr_PPG_Diff"] <= 0]
t_stats, p_val = stats.ttest_ind_from_stats(stats.tmean(better_fr), stats.tstd(better_fr), len(better_fr),
                                            stats.tmean(other_fr), stats.tstd(other_fr), len(other_fr),
                                            equal_var=False, alternative="greater")
print_t_test("Two Sample T Test:", t_stats, p_val)


#Check the correlation between friendly points, goals scored and goals conceded so keep friendly points and remove the other two variables
print("Friendly Points and Goals Scored Correlation:", corr["Fr_PPG_Diff"]["Fr_GF_Diff"])
print("Friendly Points and Goals Conceded Correlation:", corr["Fr_PPG_Diff"]["Fr_GA_Diff"])
data = data.drop(["Fr_GF_Diff", "Fr_GA_Diff"], axis=1)

#Divide the variables used for prediction and the actual goal difference
x_data = data.drop(["Match_ID", "Goal_Diff"], axis=1)
y_data = data["Goal_Diff"]
print("Variables Used for Prediction:")
print(x_data.keys())

#Make model 1 using all 8 variables
model1 = sm.OLS(y_data, sm.add_constant(x_data)).fit()
print("Model 1 Regression Summary:")
print(model1.summary())

#Make model 2 by standardising the variables to compare their effects
x_std = pd.DataFrame(StandardScaler().fit_transform(x_data), columns=x_data.columns)
model2 = sm.OLS(y_data, sm.add_constant(x_std)).fit()
print("Model 2 Standardised Regression Summary:")
print(model2.summary())

#Create a bar chart to compare the coefficients: model 2
plt.figure(figsize=(10, 5))
plt.bar(x_data.keys(), model2.params[1:])
plt.ylabel("Standardised coefficient")
plt.title("Effect of Each Variable on Goal Difference (bigger bar = stronger effect)")
plt.xticks(rotation=20, horizontalalignment="right")
plt.tight_layout()
plt.savefig("../figures/2.1_coefficients.png", dpi=150)
plt.show()

#Make model 3 using Yeo-Johnson transformation and apply the transformation to the picked variables only
yj_cols = ["Fr_PPG_Diff", "Fr_Opp_Diff", "WC_PPG_Diff", "WC_GF_Diff", "WC_GA_Diff"]
x_yj = x_data.copy()
x_yj[yj_cols] = PowerTransformer().fit_transform(x_data[yj_cols])
model3 = sm.OLS(y_data, sm.add_constant(x_yj)).fit()
print("Model 3 Yeo-Johnson Regression Summary:")
print(model3.summary())

#Select model 4 variables by removing the selected variables one at a time and each removed variable had the highest p-value at that step
x_final = x_data
for column in ["Fr_Opp_Diff", "WC_PPG_Diff", "WC_GF_Diff", "Host_Diff"]:
    x_final = x_final.drop([column], axis=1)
    model4 = sm.OLS(y_data, sm.add_constant(x_final)).fit()
    print("Model 4 Summary After Removing:", column)
    print(model4.summary())

#Creating models with names and variables, how they change, and model types
model_names = ["Baseline", "M1: All 8", "M2: Standardised", "M3: Yeo-Johnson",
               "M4: 4 significant", "M5: 4 sig. + Yeo-Johnson", "Ridge: All 8", "Random Forest: All 8"]
model_data = [x_data, x_data, x_data, x_data, x_final, x_final, x_data, x_data]
model_scale = ["none", "none", "standard", "yeo-johnson", "none", "yeo-johnson", "standard", "none"]
model_type = ["mean", "linear", "linear", "linear", "linear", "linear", "ridge", "forest"]

#Function to train one model to get RSME and R2 on the test data
def test_model(m, train_x, test_x, train_y, test_y):
    #Standardise the variables
    if model_scale[m] == "standard":
        scaler = StandardScaler()
        train_x = scaler.fit_transform(train_x)
        test_x = scaler.transform(test_x)
    #Use yeo johhnson on select variables
    if model_scale[m] == "yeo-johnson":
        columns = []
        for column in train_x.keys():
            if column in yj_cols:
                columns.append(column)
        scaler = PowerTransformer()
        train_x = train_x.copy()
        test_x = test_x.copy()
        train_x[columns] = scaler.fit_transform(train_x[columns])
        test_x[columns] = scaler.transform(test_x[columns])
    #Predict traning average per match to get baseline
    if model_type[m] == "mean":
        pred_y = [np.mean(train_y)] * len(test_y)
    else:
        if model_type[m] == "linear":
            model = LinearRegression()
        if model_type[m] == "ridge":
            model = Ridge(alpha=10)
        if model_type[m] == "forest":
            model = RandomForestRegressor(n_estimators=100, min_samples_leaf=5, random_state=0)
        model.fit(train_x, train_y)
        pred_y = model.predict(test_x)
    #Check how close predictions are to real results
    rmse = math.sqrt(metrics.mean_squared_error(test_y, pred_y))
    r2 = metrics.r2_score(test_y, pred_y)
    return rmse, r2

#Test all the models using 20 random splits 60 to 40
rmse_scores = [[], [], [], [], [], [], [], []]
r2_scores = [[], [], [], [], [], [], [], []]
for seed in range(20):
    for m in range(8):
        train_x, test_x, train_y, test_y = train_test_split(model_data[m], y_data, test_size=0.4, random_state=seed)
        rmse, r2 = test_model(m, train_x, test_x, train_y, test_y)
        rmse_scores[m].append(rmse)
        r2_scores[m].append(r2)

#Test the models using the 72 group stage matches for training and the 32 knockout matches for testing
knock_rmse = []
knock_r2 = []
for m in range(8):
    train_x = model_data[m][data["Match_ID"] <= 72]
    test_x = model_data[m][data["Match_ID"] > 72]
    train_y = y_data[data["Match_ID"] <= 72]
    test_y = y_data[data["Match_ID"] > 72]
    rmse, r2 = test_model(m, train_x, test_x, train_y, test_y)
    knock_rmse.append(rmse)
    knock_r2.append(r2)

#Calculate the average RMSE, normalised RMSE and R2 for each model and using a one sample t test to compare if each model is better than model 1 among the 20 splits
avg_rmse = []
norm_rmse = []
avg_r2 = []
p_vals = []
rmse_data = pd.DataFrame()
for m in range(8):
    avg_rmse.append(np.mean(rmse_scores[m]))
    norm_rmse.append(np.mean(rmse_scores[m]) / (y_data.max() - y_data.min()))
    avg_r2.append(np.mean(r2_scores[m]))
    rmse_data[model_names[m]] = rmse_scores[m]
    difference = []
    for i in range(20):
        difference.append(rmse_scores[m][i] - rmse_scores[1][i])
    if m == 1 or m == 2:
        p_vals.append("same as M1")
    else:
        t_stats, p_val = stats.ttest_1samp(difference, 0)
        p_vals.append(round(p_val, 4))

model_results = pd.DataFrame({"Model": model_names, "Average RMSE": avg_rmse, "RMSE (Normalised)": norm_rmse, "Average R2": avg_r2,
                              "P-Val vs M1": p_vals, "Knockout RMSE": knock_rmse, "Knockout R2": knock_r2})

print("Model Performance from 20 Random Splits and Knockout Test:")
print(model_results)

#Create a box plot to show to compare the RMSE results from all 20 splits
plt.figure(figsize=(10, 6))
sns.boxplot(data=rmse_data, orient="h")
plt.title("RMSE of Each Model over 20 Train/Test Splits")
plt.xlabel("RMSE (goals)")
plt.tight_layout()
plt.savefig("../figures/2.1_rmse_boxplot.png", dpi=150)
plt.show()

#Show the model 4 using the 4 selected variables and all the matches
print("Final Model 4 Regression Summary:")
print(model4.summary())

#Create graphs to show the comparison of the actual and predicted goal differences and show the errors
train_x, test_x, train_y, test_y = train_test_split(x_final, y_data, test_size=0.4, random_state=0)
model = LinearRegression()
model.fit(train_x, train_y)
pred_y = model.predict(test_x)
residuals = test_y - pred_y
plt.figure(figsize=(11, 4.5))
plt.subplot(1, 2, 1)
plt.scatter(test_y, pred_y)
plt.plot([-4, 6], [-4, 6], color="red")
plt.title("Final Model: Actual vs Predicted Goal Difference")
plt.xlabel("Actual Goal Difference")
plt.ylabel("Predicted Goal Difference")
plt.subplot(1, 2, 2)
plt.scatter(pred_y, residuals)
plt.plot([min(pred_y), max(pred_y)], [0, 0], color="red")
plt.title("Residuals (should be spread evenly around 0)")
plt.xlabel("Predicted Goal Difference")
plt.ylabel("Residual (Actual - Predicted)")
plt.tight_layout()
plt.savefig("../figures/2.1_final_model.png", dpi=150)
plt.show()

#Save final data and models figures
data.to_csv("../data/processed/regression_2_1_dataset.csv", index=False)
model_results.to_csv("../figures/2.1_model_comparison.csv", index=False)
print("Cleaned Datasets Saved!")
