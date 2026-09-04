import random

import pytest

import berth_constants as C
from berth_evaluation import check_feasible, evaluate
from berth_heuristic import fcfs_construction, greedy_and_polish, local_search, priority_construction
from berth_scenario import generate_instance


def _random_instance_params(rng):
    return dict(
        n_ships=rng.randint(*C.N_SHIPS_RANGE),
        quay_length=rng.randint(*C.QUAY_LENGTH_RANGE),
        deep_zone_fraction=rng.uniform(*C.DEEP_ZONE_FRACTION_RANGE),
        deep_draft_limit=rng.uniform(*C.DEEP_DRAFT_LIMIT_RANGE),
        length_avg=rng.randint(*C.LENGTH_AVG_RANGE),
        length_variability=rng.uniform(*C.LENGTH_VARIABILITY_RANGE),
        draft_avg=rng.uniform(*C.DRAFT_AVG_RANGE),
        draft_variability=rng.uniform(*C.DRAFT_VARIABILITY_RANGE),
        handling_avg=rng.randint(*C.HANDLING_AVG_RANGE),
        handling_variability=rng.uniform(*C.HANDLING_VARIABILITY_RANGE),
        arrival_spread=rng.randint(*C.ARRIVAL_SPREAD_RANGE),
        mainliner_fraction=rng.uniform(*C.MAINLINER_FRACTION_RANGE),
        safety_margin=rng.randint(*C.SAFETY_MARGIN_RANGE),
        seed=rng.randint(0, 10**6),
    )


@pytest.mark.parametrize("trial_seed", range(60))
def test_heuristics_stay_feasible_across_random_scenarios(trial_seed):
    rng = random.Random(trial_seed)
    params = _random_instance_params(rng)
    inst = generate_instance(*params.values())
    if inst.is_trivially_infeasible():
        pytest.skip("Szenario selbst unlösbar - kein Fall für die Heuristiken.")

    for construct in (fcfs_construction, priority_construction):
        plan = construct(inst)
        ok, violations = check_feasible(inst, plan)
        assert ok, violations

    polished = greedy_and_polish(inst, seed=params["seed"], max_moves=100)
    ok, violations = check_feasible(inst, polished)
    assert ok, violations


def test_presets_produce_feasible_plans():
    for name, p in C.PRESETS.items():
        inst = generate_instance(
            p["n_ships"], p["quay_length"], p["deep_zone_fraction"], p["deep_draft_limit"],
            p["length_avg"], p["length_variability"], p["draft_avg"], p["draft_variability"],
            p["handling_avg"], p["handling_variability"], p["arrival_spread"], p["mainliner_fraction"],
            p["safety_margin"], p["seed"],
        )
        for construct in (fcfs_construction, priority_construction):
            ok, violations = check_feasible(inst, construct(inst))
            assert ok, f"{name}: {violations}"
        ok, violations = check_feasible(inst, greedy_and_polish(inst, seed=p["seed"]))
        assert ok, f"{name}: {violations}"


def test_local_search_never_regresses():
    inst = generate_instance(7, 700, 0.4, 16.0, 200, 0.15, 12.0, 0.15, 16, 0.3, 24, 0.5, 15, 1)
    start_order = sorted(range(len(inst.ships)), key=lambda i: inst.ships[i].arrival)

    def score(order):
        from berth_heuristic import _build

        return evaluate(inst, _build(inst, order))["total_weighted_wait"]

    start_score = score(start_order)
    polished_order = local_search(inst, start_order, random.Random(0), max_moves=200)
    assert score(polished_order) <= start_score + 1e-9


def test_greedy_and_polish_at_least_as_good_as_either_construction():
    inst = generate_instance(9, 600, 0.5, 15.0, 180, 0.25, 10.0, 0.2, 14, 0.3, 30, 0.3, 15, 7)
    fcfs_score = evaluate(inst, fcfs_construction(inst))["total_weighted_wait"]
    priority_score = evaluate(inst, priority_construction(inst))["total_weighted_wait"]
    polished_score = evaluate(inst, greedy_and_polish(inst, seed=7))["total_weighted_wait"]
    assert polished_score <= min(fcfs_score, priority_score) + 1e-9
