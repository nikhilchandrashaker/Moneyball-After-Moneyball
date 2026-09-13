# Moneyball After Moneyball
### A counterfactual simulation of leaguewide Moneyball adoption, 2003–2016 (with balance analysis through 2025)

## Data constraint that shaped the scope

The plan called for a full 2003–2025 simulation. That requires team payroll data, and the
only open, non-scraped payroll source available (the USA Today salary data bundled in the
Lahman database) **stops at 2016** — it hasn't been maintained since. There's no reproducible
way to get 2017–2025 player salaries without scraping sites like Spotrac or Cot's Contracts,
which wasn't available here. So the payroll-constrained simulation runs **2003–2016** (14
seasons — still spans the original Moneyball window and its first decade of imitation), and
the salary-free competitive-balance analysis runs the full **2003–2025**.

All underlying stats (batting, pitching, wins, postseason results) come from the Lahman
database through the actual 2025 season.

## Player value model

No external WAR/FIP source was available either, so value is built directly from raw
Lahman batting/pitching lines using public sabermetric formulas:

- **Batting**: linear-weights runs (standard event weights: 1B .47, 2B .78, 3B 1.09, HR 1.40,
  BB/HBP .33, out −.25) converted to runs above the year's league average, then to WAR at
  10 runs/win with a replacement-level baseline of ~2 wins per 600 PA below average.
- **Pitching**: FIP computed from HR/BB/HBP/K/IP with a year-specific constant so league-average
  FIP equals league-average ERA, converted to runs saved vs. league average, then to WAR the
  same way (replacement baseline ~1 win per 180 IP).

Sanity check: the model's top 2002 player is Barry Bonds at 13.7 WAR — consistent with the
real-world consensus that his 2002 season was one of the best in modern history.

## The simulation

For each team-year 2003–2016, an "if everyone adopted Moneyball" roster was built by:

1. Pooling every player-season in MLB that year with value (WAR) and salary attached.
2. Running a **shared-scarcity draft**: teams take turns (snake order) picking the best
   remaining WAR-per-dollar player they can still afford, until each team's real payroll
   and real roster size are exhausted.
3. Draft order was set **ascending by real payroll** — i.e., small-budget teams move first.
   This is a modeling assumption representing "budget-constrained teams are the ones forced
   to get analytically creative first," matching the actual A's origin story. It is not
   observed fact, and it matters a lot: a market where rich teams could simply outbid anyone
   for undervalued players at any point would look different. Treat the specific numbers as
   illustrative of a mechanism, not a precise forecast.

Earlier draft of this simulation (an independent knapsack per team against the full league
pool) was discarded — it let all 30 teams simultaneously "acquire" the same undervalued
players, which is impossible. The shared draft enforces that a player can only go to one team.

## Findings

**1. Payroll stopped predicting wins under the counterfactual.**
In real MLB 2003–2016, payroll and wins correlate positively (r = 0.19 to 0.64, noisy but
consistently positive). Under the simulation, that correlation flips negative every single
year (r = −0.08 to −0.50). Small-payroll teams gain wins in most years; large-payroll teams
lose them — because they draft last in this mechanism and end up paying full price for
whatever value is left.

**2. No clean "death of the advantage" year.**
The hypothesis that the Moneyball edge should visibly erode over the decade doesn't show up
cleanly in the actual payroll-wins correlation — 2012–2015 dip lower (r ≈ 0.19–0.32) but 2016
snaps back to 0.64. The data's too noisy over 14 seasons to call a specific inflection year.

**3. The "Moneyball Index" (roster WAR per $100M spent) is a weak predictor of next
year's wins** — r = 0.01 in-sample (2003–11) and r = 0.14 out-of-sample (2012–15). A
single season's acquisition efficiency, by this simplified measure, doesn't reliably carry
into next year. That's a real negative result, not a modeling failure to paper over — it's
consistent with the idea that year-to-year variance and roster turnover dominate over a
persistent "smart franchise" effect, at least as this index defines it.

**4. Competitive balance (real data, no salary needed) didn't monotonically improve.**
Using the Noll-Scully ratio (actual win-pct spread vs. the spread expected under pure chance)
across all 30 teams, 2003–2025: balance was *tighter* in the mid-2000s to mid-2010s
(ratio ≈ 1.5–1.9) than in 2018–2022 (ratio ≈ 2.1–2.5, the sport's widely-discussed
"tanking era"), before easing back down to ≈1.8–2.0 in 2023–2025. If anything, the league
got *less* competitively balanced as analytics became universal — the opposite of the naive
"shared knowledge equalizes everyone" hypothesis. A more likely story: once every front
office had the same tools, the differentiator became front-office *resources* (analytics
staff size, R&D spend) rather than knowledge itself, which favors large-market teams again.

## What's in the output files

- `csv/player_value.csv` — every player-season 2003–2016(+) with WAR_bat, WAR_pitch, salary
- `csv/team_panel_2003_2016_v3.csv` — team-year actual vs. counterfactual wins/payroll
- `csv/yearly_summary_2003_2016.csv` — correlations and market-size splits by year
- `csv/competitive_balance_2003_2025.csv` — Noll-Scully ratio, full real-data window
- `csv/moneyball_archetypes.csv` — top value/$ outlier players by year
- `moneyball_charts.png` — the four charts above

## Honest limitations

- The batting/pitching value model is a simplified public-formula approximation, not
  Baseball-Reference or FanGraphs WAR — treat magnitudes as directionally right, not exact.
- The draft-order assumption (ascending payroll) is a modeling choice with real influence
  on results; an alternative order (e.g., descending prior-year wins, the real Rule 4 draft
  convention) would tell a different story and is a natural next step.
- No trade/injury/aging dynamics or path dependency across seasons — each year is simulated
  independently from real starting rosters and real payrolls.
- 2017–2025 has no salary-constrained simulation, only the salary-free balance metric.
