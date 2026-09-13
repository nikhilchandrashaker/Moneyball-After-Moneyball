import pandas as pd
import numpy as np

val = pd.read_csv('csv/player_value.csv')
teams = pd.read_csv('csv/Teams.csv')
sal = pd.read_csv('csv/Salaries.csv')

YEARS = range(2003, 2017)
REPL_WINS = 48.0

team_payroll = sal.groupby(['yearID','teamID'], as_index=False)['salary'].sum().rename(columns={'salary':'actual_payroll'})
team_actual = val.dropna(subset=['teamID']).groupby(['yearID','teamID']).agg(
    actual_roster_WAR=('WAR','sum'), roster_size=('playerID','nunique')
).reset_index()

panel = teams[teams.yearID.isin(YEARS)][['yearID','teamID','W','L','G']].copy()
panel = panel.merge(team_payroll, on=['yearID','teamID'], how='left')
panel = panel.merge(team_actual, on=['yearID','teamID'], how='left')
panel = panel.dropna(subset=['actual_payroll','roster_size']).copy()
panel['roster_size'] = panel['roster_size'].astype(int)

def run_draft(year_panel, pool):
    """Shared-scarcity snake draft: teams (ordered by ascending real payroll -- the
    'a savvy small-budget team moves first on mispriced value' assumption) take turns
    picking the best-remaining WAR-per-$ player they can still afford, until every
    team's real payroll and real roster-size are used up. This is a modeling choice,
    not observed fact -- documented as such."""
    order = year_panel.sort_values('actual_payroll')['teamID'].tolist()
    budget = year_panel.set_index('teamID')['actual_payroll'].to_dict()
    slots = year_panel.set_index('teamID')['roster_size'].to_dict()
    spent = {t: 0.0 for t in order}
    war_won = {t: 0.0 for t in order}
    filled = {t: 0 for t in order}

    remaining = pool.sort_values('value_per_dollar', ascending=False).to_dict('records')
    remaining_idx = 0
    active_teams = set(order)
    round_num = 0
    forward = True
    while active_teams and remaining_idx < len(remaining):
        seq = order if forward else list(reversed(order))
        forward = not forward
        progressed = False
        for t in seq:
            if t not in active_teams:
                continue
            # find next player this team can afford
            picked = None
            # linear scan from front for best-remaining-value player this team can afford
            for i, p in enumerate(remaining):
                if p is None:
                    continue
                if spent[t] + p['salary'] <= budget[t]:
                    picked = i
                    break
            if picked is None or filled[t] >= slots[t]:
                active_teams.discard(t)
                continue
            p = remaining[picked]
            spent[t] += p['salary']
            war_won[t] += p['WAR']
            filled[t] += 1
            remaining[picked] = None
            progressed = True
            if filled[t] >= slots[t]:
                active_teams.discard(t)
        if not progressed:
            break
        round_num += 1
    return pd.DataFrame({'teamID': order,
                          'cf_roster_WAR': [war_won[t] for t in order],
                          'cf_spend': [spent[t] for t in order],
                          'cf_n_players': [filled[t] for t in order]})

all_results = []
for year in YEARS:
    pool = val[(val.yearID==year) & (val.salary.notna()) & (val.salary>0)].copy()
    pool['value_per_dollar'] = pool['WAR']/(pool['salary']/1e6)
    yr_panel = panel[panel.yearID==year]
    draft_res = run_draft(yr_panel, pool)
    draft_res['yearID'] = year
    all_results.append(draft_res)

cf_df = pd.concat(all_results)
panel = panel.merge(cf_df, on=['yearID','teamID'], how='left')
panel['actual_expected_wins'] = REPL_WINS + panel['actual_roster_WAR']
panel['cf_expected_wins'] = REPL_WINS + panel['cf_roster_WAR']
panel['moneyball_gain_wins'] = panel['cf_expected_wins'] - panel['actual_expected_wins']
panel['payroll_millions'] = panel['actual_payroll']/1e6

panel.to_csv('csv/team_panel_2003_2016_v3.csv', index=False)

pd.set_option('display.width', 140)
print(panel[panel.yearID==2003][['teamID','W','payroll_millions','actual_roster_WAR','cf_roster_WAR',
                                   'actual_expected_wins','cf_expected_wins','moneyball_gain_wins']]
      .sort_values('payroll_millions').to_string(index=False))
