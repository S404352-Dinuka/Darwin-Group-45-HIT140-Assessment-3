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

