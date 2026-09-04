import berth_constants as C
from berth_cp_solver import solve_exact
from berth_evaluation import check_feasible, evaluate
from berth_heuristic import greedy_and_polish
from berth_scenario import Instance, Ship, Zone, generate_instance

ZONES = (
    Zone(name="Tiefwasser", start=0, end=150, max_draft=15.0),
    Zone(name="Flachwasser", start=150, end=300, max_draft=9.0),
)


def test_solve_exact_two_ships_must_serialize_when_too_wide_for_parallel_berth():
    """Zwei tiefgängige Schiffe (beide nur in der Tiefwasserzone zulässig), die zusammen (inkl.
    Sicherheitsabstand) breiter als diese Zone sind, müssen zeitlich nacheinander abgefertigt
    werden - der Solver muss das erkennen, nicht parallel planen."""
    s0 = Ship(index=0, name="A", length=100, draft=12.0, arrival=0, handling_time=10, priority="Tramp", weight=1.0)
    s1 = Ship(index=1, name="B", length=100, draft=12.0, arrival=0, handling_time=10, priority="Tramp", weight=1.0)
    inst = Instance(quay_length=300, zones=ZONES, ships=(s0, s1), safety_margin=10, horizon=50)
    # occupied_width je Schiff = 110, Tiefwasserzone nur 150 breit, Flachwasser (Limit 9.0) für
    # beide zu flach -> beide passen NICHT gleichzeitig
    res = solve_exact(inst, time_limit_seconds=5)
    assert res.feasible and res.optimal
    ok, violations = check_feasible(inst, res.plan)
    assert ok, violations
    starts = sorted(v[0] for v in res.plan.values())
    assert starts[1] >= starts[0] + 10  # eines muss warten, bis das andere fertig ist


def test_solve_exact_two_ships_can_run_in_parallel_when_zone_wide_enough():
    s0 = Ship(index=0, name="A", length=50, draft=5.0, arrival=0, handling_time=10, priority="Tramp", weight=1.0)
    s1 = Ship(index=1, name="B", length=50, draft=5.0, arrival=0, handling_time=10, priority="Tramp", weight=1.0)
    inst = Instance(quay_length=300, zones=ZONES, ships=(s0, s1), safety_margin=10, horizon=50)
    res = solve_exact(inst, time_limit_seconds=5)
    assert res.feasible and res.optimal
    assert res.total_weighted_wait == 0.0  # beide passen sofort und gleichzeitig
    ok, violations = check_feasible(inst, res.plan)
    assert ok, violations


def test_solve_exact_respects_zone_draft_compatibility():
    deep_ship = Ship(index=0, name="Deep", length=40, draft=12.0, arrival=0, handling_time=5, priority="Tramp", weight=1.0)
    inst = Instance(quay_length=300, zones=ZONES, ships=(deep_ship,), safety_margin=10, horizon=50)
    res = solve_exact(inst, time_limit_seconds=5)
    assert res.feasible
    start, pos = res.plan[0]
    assert pos + deep_ship.length <= 150  # nur in der Tiefwasserzone möglich


def test_solve_exact_prioritizes_higher_weight_ship_for_the_only_early_slot():
    """Zwei Schiffe können nicht gleichzeitig an Bord (eine einzige, schmale Zone lässt nur eines
    zur Zeit zu) - dasjenige mit dem höheren Gewicht muss (bei gleicher Ankunft) den frühen Slot
    bekommen, wenn das die gewichtete Wartezeit minimiert."""
    single_zone = (Zone(name="Nur eine Zone", start=0, end=150, max_draft=15.0),)
    heavy = Ship(index=0, name="Mainliner", length=100, draft=5.0, arrival=0, handling_time=10, priority="Mainliner", weight=3.0)
    light = Ship(index=1, name="Tramp", length=100, draft=5.0, arrival=0, handling_time=10, priority="Tramp", weight=1.0)
    inst = Instance(quay_length=150, zones=single_zone, ships=(heavy, light), safety_margin=10, horizon=50)
    res = solve_exact(inst, time_limit_seconds=5)
    assert res.feasible and res.optimal
    heavy_start = res.plan[0][0]
    light_start = res.plan[1][0]
    assert heavy_start < light_start


def test_solve_exact_matches_heuristic_on_presets_or_beats_it():
    for name, p in C.PRESETS.items():
        inst = generate_instance(
            p["n_ships"], p["quay_length"], p["deep_zone_fraction"], p["deep_draft_limit"],
            p["length_avg"], p["length_variability"], p["draft_avg"], p["draft_variability"],
            p["handling_avg"], p["handling_variability"], p["arrival_spread"], p["mainliner_fraction"],
            p["safety_margin"], p["seed"],
        )
        polished = greedy_and_polish(inst, seed=p["seed"])
        heuristic_score = evaluate(inst, polished)["total_weighted_wait"]
        res = solve_exact(inst, time_limit_seconds=C.EXACT_SOLVE_TIME_LIMIT_SECONDS, hint_plan=polished)
        assert res.feasible, name
        ok, violations = check_feasible(inst, res.plan)
        assert ok, f"{name}: {violations}"
        assert res.total_weighted_wait <= heuristic_score + 1e-6, name
