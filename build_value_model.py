"""
Moneyball After Moneyball: player value model
Builds simplified WAR-like batting and pitching value from Lahman data only
(no external scraped WAR/FIP/Statcast source available in this environment).
Formulas are public sabermetric approximations, not proprietary.
"""
import pandas as pd
import numpy as np

bat = pd.read_csv('csv/Batting.csv')
pit = pd.read_csv('csv/Pitching.csv')
sal = pd.read_csv('csv/Salaries.csv')
teams = pd.read_csv('csv/Teams.csv')
people = pd.read_csv('csv/People.csv')

# ---- Aggregate multi-stint player-seasons to one row per player-year-team ----
bat_group_cols = ['playerID','yearID','teamID']
bat_num = ['G','AB','R','H','X2B','X3B','HR','RBI','SB','CS','BB','SO','IBB','HBP','SH','SF','GIDP']
bat = bat.groupby(bat_group_cols, as_index=False)[bat_num].sum()

pit_num = ['W','L','G','GS','CG','SHO','SV','IPouts','H','ER','HR','BB','SO','IBB','HBP','BK','BFP','GF','R','SH','SF','GIDP']
pit = pit.groupby(bat_group_cols, as_index=False)[pit_num].sum()

# ---- Batting value: linear-weights runs above average -> WAR ----
bat['1B'] = bat['H'] - bat['X2B'] - bat['X3B'] - bat['HR']
bat['PA'] = bat['AB'] + bat['BB'].fillna(0) + bat['HBP'].fillna(0) + bat['SH'].fillna(0) + bat['SF'].fillna(0)
bat['HBP'] = bat['HBP'].fillna(0)
bat['SF'] = bat['SF'].fillna(0)

# standard (era-independent) linear weights approximation, runs per event
w = dict(BB=0.33, HBP=0.33, ONE=0.47, TWO=0.78, THREE=1.09, HR=1.40, OUT=-0.25)
bat['outs'] = bat['AB'] - bat['H']
bat['bat_runs'] = (w['BB']*bat['BB'] + w['HBP']*bat['HBP'] + w['ONE']*bat['1B'] +
                   w['TWO']*bat['X2B'] + w['THREE']*bat['X3B'] + w['HR']*bat['HR'] +
                   w['OUT']*bat['outs'])

# league-year average runs/PA to get runs ABOVE AVERAGE (not just raw linear weight runs)
lg_year = bat.groupby('yearID').apply(lambda d: d['bat_runs'].sum()/d['PA'].sum()).rename('lg_rpa').reset_index()
bat = bat.merge(lg_year, on='yearID', how='left')
bat['bat_raa'] = bat['bat_runs'] - bat['lg_rpa']*bat['PA']

RUNS_PER_WIN = 10.0
REPL_WINS_PER_PA = 2.0/600.0   # replacement level ~ -2 wins/600 PA below average
bat['WAR_bat'] = bat['bat_raa']/RUNS_PER_WIN + bat['PA']*REPL_WINS_PER_PA

# ---- Pitching value: FIP-based runs saved -> WAR ----
pit['IP'] = pit['IPouts']/3.0
pit = pit[pit['IP'] > 0].copy()
pit['HBP'] = pit['HBP'].fillna(0)
pit['fip_raw'] = (13*pit['HR'] + 3*(pit['BB']+pit['HBP']) - 2*pit['SO'])/pit['IP']

# league-year FIP constant so league-avg FIP == league-avg ERA (public, standard method)
lg_pit = pit.groupby('yearID').apply(
    lambda d: pd.Series({'lg_era': (d['ER'].sum()*9/d['IP'].sum()),
                          'lg_fip_raw': (d['fip_raw']*d['IP']).sum()/d['IP'].sum()})
).reset_index()
lg_pit['fip_const'] = lg_pit['lg_era'] - lg_pit['lg_fip_raw']
pit = pit.merge(lg_pit[['yearID','lg_era','fip_const']], on='yearID', how='left')
pit['FIP'] = pit['fip_raw'] + pit['fip_const']

pit['runs_saved'] = (pit['lg_era'] - pit['FIP'])*pit['IP']/9.0
REPL_WINS_PER_IP = 1.0/180.0
pit['WAR_pitch'] = pit['runs_saved']/RUNS_PER_WIN + pit['IP']*REPL_WINS_PER_IP

# ---- Combine into one player-value table per player-year (sum across teams if traded) ----
bat_val = bat.groupby(['playerID','yearID'], as_index=False).agg(
    WAR_bat=('WAR_bat','sum'), PA=('PA','sum'))
pit_val = pit.groupby(['playerID','yearID'], as_index=False).agg(
    WAR_pitch=('WAR_pitch','sum'), IP=('IP','sum'))

val = pd.merge(bat_val, pit_val, on=['playerID','yearID'], how='outer').fillna(0)
val['WAR'] = val['WAR_bat'] + val['WAR_pitch']

# player's primary team that year = team with most PA+IP (for roster assignment)
bat_team = bat.groupby(['playerID','yearID','teamID'])['PA'].sum().reset_index()
pit_team = pit.groupby(['playerID','yearID','teamID'])['IP'].sum().reset_index()
bat_team['w'] = bat_team['PA']
pit_team['w'] = pit_team['IP']
team_assign = pd.concat([bat_team[['playerID','yearID','teamID','w']],
                          pit_team[['playerID','yearID','teamID','w']]])
team_assign = team_assign.sort_values('w', ascending=False).drop_duplicates(['playerID','yearID'])
val = val.merge(team_assign[['playerID','yearID','teamID']], on=['playerID','yearID'], how='left')

# ---- Merge salary ----
sal_g = sal.groupby(['playerID','yearID'], as_index=False)['salary'].sum()
val = val.merge(sal_g, on=['playerID','yearID'], how='left')

val.to_csv('csv/player_value.csv', index=False)
print(val.shape)
print(val[(val.yearID==2002)].sort_values('WAR', ascending=False).head(10)[['playerID','yearID','teamID','WAR','salary']])
