"""Defaults, Regler-Grenzen, Farben und Beispielszenarien."""

N_SHIPS_DEFAULT = 6
N_SHIPS_RANGE = (3, 10)

QUAY_LENGTH_DEFAULT = 600
QUAY_LENGTH_RANGE = (300, 1200)

DEEP_ZONE_FRACTION_DEFAULT = 0.5
DEEP_ZONE_FRACTION_RANGE = (0.2, 0.8)

DEEP_DRAFT_LIMIT_DEFAULT = 15.0
DEEP_DRAFT_LIMIT_RANGE = (10.0, 20.0)

LENGTH_AVG_DEFAULT = 180
LENGTH_AVG_RANGE = (80, 320)

LENGTH_VARIABILITY_DEFAULT = 0.25
LENGTH_VARIABILITY_RANGE = (0.0, 0.6)

DRAFT_AVG_DEFAULT = 10.0
DRAFT_AVG_RANGE = (5.0, 16.0)

DRAFT_VARIABILITY_DEFAULT = 0.2
DRAFT_VARIABILITY_RANGE = (0.0, 0.5)

HANDLING_AVG_DEFAULT = 14
HANDLING_AVG_RANGE = (4, 30)

HANDLING_VARIABILITY_DEFAULT = 0.3
HANDLING_VARIABILITY_RANGE = (0.0, 0.6)

ARRIVAL_SPREAD_DEFAULT = 36
ARRIVAL_SPREAD_RANGE = (0, 96)

MAINLINER_FRACTION_DEFAULT = 0.3
MAINLINER_FRACTION_RANGE = (0.0, 0.7)

SAFETY_MARGIN_DEFAULT = 15
SAFETY_MARGIN_RANGE = (0, 40)

RANDOM_SEED_DEFAULT = 7
RANDOM_SEED_RANGE = (0, 2_000_000_000)

EXACT_SOLVE_TIME_LIMIT_SECONDS = 10

PRIORITY_COLORS = {"Mainliner": "#d62728", "Feeder": "#1f77b4", "Tramp": "#7f7f7f"}
ZONE_COLORS = {"Tiefwasser": "rgba(31,119,180,0.08)", "Flachwasser": "rgba(255,127,14,0.10)"}

PRESETS = {
    "Ruhiger Feederhafen": dict(
        n_ships=5, quay_length=500, deep_zone_fraction=0.4, deep_draft_limit=13.0,
        length_avg=140, length_variability=0.2, draft_avg=8.0, draft_variability=0.15,
        handling_avg=10, handling_variability=0.25, arrival_spread=48, mainliner_fraction=0.1,
        safety_margin=12, seed=3,
    ),
    "Mainliner-Stoßzeit trifft Tiefwasser-Engpass": dict(
        n_ships=7, quay_length=700, deep_zone_fraction=0.4, deep_draft_limit=16.0,
        length_avg=200, length_variability=0.15, draft_avg=12.0, draft_variability=0.15,
        handling_avg=16, handling_variability=0.3, arrival_spread=24, mainliner_fraction=0.5,
        safety_margin=15, seed=1,
    ),
    "Volle Kaikapazität": dict(
        n_ships=9, quay_length=600, deep_zone_fraction=0.5, deep_draft_limit=15.0,
        length_avg=180, length_variability=0.25, draft_avg=10.0, draft_variability=0.2,
        handling_avg=14, handling_variability=0.3, arrival_spread=30, mainliner_fraction=0.3,
        safety_margin=15, seed=7,
    ),
}
