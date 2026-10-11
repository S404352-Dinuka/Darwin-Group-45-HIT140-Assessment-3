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