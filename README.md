# Darwin Group 45 – HIT140 Assessment 3

## Project Overview

This repository contains the HIT140 Assessment 3 group project for Darwin Group 45.

The project uses linear regression to predict FIFA World Cup 2026 results using only information available before each match was played:

- **Linear Regression 2.1** predicts the **goal difference** between the two teams in each of the 104 World Cup matches (104 rows, 8 explanatory variables).
- **Linear Regression 2.2** predicts the **number of goals scored by a team** in a match (208 rows – one per team per match, 8 explanatory variables). At most 4 of its variables are shared with 2.1, as required by the brief.

Both tasks include data cleaning, exploratory data analysis (descriptive statistics, outliers, confidence intervals, t-tests, correlation), multiple linear regression with optimisation (standardisation, Yeo-Johnson and log transformations, collinearity removal and backward elimination), and a comparison with competing algorithms (Ridge regression and random forest).

## Group Members

| Student ID | Name |
|---|---|
| S404352 | Dinuka Dhaneshani Mathangaweera |
| S401456 | Sehan Hansaja Udayakantha Panik Mudiyanselage |
| S401680 | BalaTripuraSundari Polineni |
| S401279 | Prabodha Sathsarani Aththanayake Aththanayake Boralage |

## Repository Structure

```text
Darwin-Group-45-HIT140-Assessment-3/
│
├── 2.1/
│   └── regression_2.1.py          # Linear Regression 2.1 – goal difference
│
├── 2.2/
│   └── regression_2_2.py          # Linear Regression 2.2 – goals scored by a team
│
├── data/
│   ├── raw/                       # Original FBref datasets (CSV)
│   └── processed/                 # Final modelling datasets created by the scripts
│
└── figures/                       # Charts and model comparison tables created by the scripts
```

- **2.1/** and **2.2/** – one Python script per task (data cleaning, EDA and modelling)
- **data/raw/** – the three original FBref datasets
- **data/processed/** – `regression_2_1_dataset.csv` (104 rows) and `regression_2_2_dataset.csv` (208 rows)
- **figures/** – all charts (`.png`) and the model comparison tables (`2.1_model_comparison.csv`, `2.2_model_comparison.csv`)

## Data Source

All data was downloaded from [FBref](https://fbref.com/) (one of the recommended sources in the brief):

- 2026 World Cup Scores & Fixtures
- 2026 International Friendlies Scores & Fixtures (only friendlies played before 11 June 2026 are used)
- 2026 World Cup Qualifications

## Requirements

- Python 3.10+
- pandas
- numpy
- scipy
- statsmodels
- matplotlib
- seaborn
- scikit-learn

## Additional References

In addition to the weekly learning materials, the following references were used for Python implementation and visualisation support:

- [Python 3 Documentation](https://docs.python.org/3/)
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [NumPy Documentation](https://numpy.org/doc/stable/)
- [SciPy Documentation](https://docs.scipy.org/doc/scipy/)
- [statsmodels Documentation](https://www.statsmodels.org/stable/)
- [Matplotlib Documentation](https://matplotlib.org/stable/)
- [seaborn Documentation](https://seaborn.pydata.org/)
- [scikit-learn – Ridge](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.Ridge.html)
- [scikit-learn – RandomForestRegressor](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html)
- [scikit-learn – train_test_split](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.train_test_split.html)
- [scikit-learn – Common pitfalls (data leakage)](https://scikit-learn.org/stable/common_pitfalls.html)