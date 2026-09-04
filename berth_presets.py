"""SETTING_SPECS-Permalink-Muster, Presets und Zufalls-Seed-Button (Standardmuster aus dem
OR-Demo-Portfolio, siehe z.B. quaycrane_presets.py)."""

import math
import random
from dataclasses import dataclass
from typing import Callable, Optional

import streamlit as st

import berth_constants as C


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: Callable
    default: object
    lo: Optional[float] = None
    hi: Optional[float] = None


SETTING_SPECS = {
    "n_ships_slider": SettingSpec("ns", int, C.N_SHIPS_DEFAULT, *C.N_SHIPS_RANGE),
    "quay_length_slider": SettingSpec("ql", int, C.QUAY_LENGTH_DEFAULT, *C.QUAY_LENGTH_RANGE),
    "deep_zone_fraction_slider": SettingSpec("dzf", float, C.DEEP_ZONE_FRACTION_DEFAULT, *C.DEEP_ZONE_FRACTION_RANGE),
    "deep_draft_limit_slider": SettingSpec("ddl", float, C.DEEP_DRAFT_LIMIT_DEFAULT, *C.DEEP_DRAFT_LIMIT_RANGE),
    "length_avg_slider": SettingSpec("la", int, C.LENGTH_AVG_DEFAULT, *C.LENGTH_AVG_RANGE),
    "length_variability_slider": SettingSpec("lv", float, C.LENGTH_VARIABILITY_DEFAULT, *C.LENGTH_VARIABILITY_RANGE),
    "draft_avg_slider": SettingSpec("da", float, C.DRAFT_AVG_DEFAULT, *C.DRAFT_AVG_RANGE),
    "draft_variability_slider": SettingSpec("dv", float, C.DRAFT_VARIABILITY_DEFAULT, *C.DRAFT_VARIABILITY_RANGE),
    "handling_avg_slider": SettingSpec("ha", int, C.HANDLING_AVG_DEFAULT, *C.HANDLING_AVG_RANGE),
    "handling_variability_slider": SettingSpec("hv", float, C.HANDLING_VARIABILITY_DEFAULT, *C.HANDLING_VARIABILITY_RANGE),
    "arrival_spread_slider": SettingSpec("as_", int, C.ARRIVAL_SPREAD_DEFAULT, *C.ARRIVAL_SPREAD_RANGE),
    "mainliner_fraction_slider": SettingSpec("mf", float, C.MAINLINER_FRACTION_DEFAULT, *C.MAINLINER_FRACTION_RANGE),
    "safety_margin_slider": SettingSpec("sm", int, C.SAFETY_MARGIN_DEFAULT, *C.SAFETY_MARGIN_RANGE),
    "seed_input": SettingSpec("seed", int, C.RANDOM_SEED_DEFAULT, *C.RANDOM_SEED_RANGE),
}


def bounds(state_key):
    spec = SETTING_SPECS[state_key]
    return spec.lo, spec.hi


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = spec.default


def load_permalink_settings():
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param in qp:
            try:
                value = spec.caster(qp[spec.url_param])
                if isinstance(value, float) and not math.isfinite(value):
                    continue
                if spec.lo is not None:
                    value = max(spec.lo, value)
                if spec.hi is not None:
                    value = min(spec.hi, value)
                st.session_state[state_key] = value
            except (ValueError, TypeError):
                pass
    st.session_state["permalink_loaded"] = True


def sync_query_params(values):
    """values: dict state_key -> aktueller Wert (aus den Widgets, nicht aus session_state, damit
    dieselbe Änderung, die gerade gerendert wurde, auch sofort in der Adresszeile landet)."""
    try:
        for state_key, value in values.items():
            spec = SETTING_SPECS[state_key]
            st.query_params[spec.url_param] = str(int(value)) if spec.caster is int else str(value)
    except Exception:
        pass


def apply_preset(name):
    p = C.PRESETS[name]
    st.session_state["n_ships_slider"] = p["n_ships"]
    st.session_state["quay_length_slider"] = p["quay_length"]
    st.session_state["deep_zone_fraction_slider"] = p["deep_zone_fraction"]
    st.session_state["deep_draft_limit_slider"] = p["deep_draft_limit"]
    st.session_state["length_avg_slider"] = p["length_avg"]
    st.session_state["length_variability_slider"] = p["length_variability"]
    st.session_state["draft_avg_slider"] = p["draft_avg"]
    st.session_state["draft_variability_slider"] = p["draft_variability"]
    st.session_state["handling_avg_slider"] = p["handling_avg"]
    st.session_state["handling_variability_slider"] = p["handling_variability"]
    st.session_state["arrival_spread_slider"] = p["arrival_spread"]
    st.session_state["mainliner_fraction_slider"] = p["mainliner_fraction"]
    st.session_state["safety_margin_slider"] = p["safety_margin"]
    st.session_state["seed_input"] = p["seed"]


def randomize_seed():
    st.session_state["seed_input"] = random.randint(0, 2_000_000_000)
