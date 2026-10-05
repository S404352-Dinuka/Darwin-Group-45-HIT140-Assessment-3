import pandas as pd

#Read the match data in the two csv files
world_cup_matches = pd.read_csv("../data/2026 World Cup Scores&Fixtures.xls.csv")
friendlies_matches = pd.read_csv("../data/2026 International Friendlies Scores & Fixtures.xls.csv")

print("World Cup Dataset")
world_cup_matches.info()
print(world_cup_matches.head())
print("Rows and Columns ")