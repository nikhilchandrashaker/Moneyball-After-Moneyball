import pandas as pd
import numpy as np

panel = pd.read_csv('csv/team_panel_2003_2016_v3.csv')
teams = pd.read_csv('csv/Teams.csv')

# ---- 1. Year-by-year summary: payroll-wins correlation, actual vs counterfactual ----
rows = []
for year, sub in panel.groupby('yearID'):
    sub = sub.dropna(subset=['actual_payroll','W','cf_expected_wins'])
    corr_actual = sub['actual_payroll'].corr(sub['W'])
    corr_cf = sub['actual_payroll'].corr(sub['cf_expected_wins'])
    small = sub.nsmallest(10, 'actual_payroll')
    big = sub.nlargest(10, 'actual_payroll')
    rows.append(dict(
        yearID=year,
        corr_payroll_actual_wins=corr_actual,
        corr_payroll_cf_wins=corr_cf,
        small_market_mean_gain=small['moneyball_gain_wins'].mean(),
        big_market_mean_gain=big['moneyball_gain_wins'].mean(),
        std_actual_wins=sub['W'].std(),
        std_cf_wins=sub['cf_expected_wins'].std(),
    ))
summary = pd.DataFrame(rows)
summary.to_csv('csv/yearly_summary_2003_2016.csv', index=False)
print(summary.round(3).to_string(index=False))

# ---- 2. Moneyball Index: team-year value-efficiency score, out-of-sample predictive test ----
# Index = actual roster WAR per $100M spent (a simple, interpretable acquisition-efficiency score)
panel['moneyball_index'] = panel['actual_roster_WAR'] / (panel['actual_payroll']/1e8)
mi = panel[['yearID','teamID','moneyball_index','W']].copy()
mi_next = mi.copy()
mi_next['yearID'] = mi_next['yearID'] - 1  # shift to align team's index in year t with wins in year t+1
mi_next = mi_next.rename(columns={'W':'W_next'})
mi_test = mi.merge(mi_next[['yearID','teamID','W_next']], on=['yearID','teamID'], how='inner')
# train/test split by year (train <=2011, test 2012-2015) to avoid in-sample leakage
train = mi_test[mi_test.yearID <= 2011]
test = mi_test[(mi_test.yearID > 2011) & (mi_test.yearID <= 2015)]
train_corr = train['moneyball_index'].corr(train['W_next'])
test_corr = test['moneyball_index'].corr(test['W_next'])
print(f"\nMoneyball Index -> next-year wins correlation: train(2003-11)={train_corr:.3f}  test(2012-15)={test_corr:.3f}")

# ---- 3. Competitive balance 2003-2025, salary-free (Noll-Scully ratio) ----
bal_rows = []
for year in range(2003, 2026):
    yr = teams[teams.yearID == year].copy()
    if yr.empty:
        continue
    yr['win_pct'] = yr['W']/(yr['W']+yr['L'])
    actual_std = yr['win_pct'].std()
    n_teams = len(yr)
    avg_g = yr['G'].mean()
    idealized_std = 0.5/np.sqrt(avg_g)  # standard deviation under pure-chance (50% talent) league
    noll_scully = actual_std/idealized_std
    bal_rows.append(dict(yearID=year, n_teams=n_teams, std_win_pct=actual_std,
                          idealized_std=idealized_std, noll_scully_ratio=noll_scully))
balance = pd.DataFrame(bal_rows)
balance.to_csv('csv/competitive_balance_2003_2025.csv', index=False)
print("\nCompetitive balance (Noll-Scully ratio, 1.0 = pure chance, higher = less balanced):")
print(balance.round(3).to_string(index=False))
