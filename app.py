"""
Kaiplatz-Zuteilung (Berth Allocation) – interaktive Fall-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Speculative Portfolio-Demo, Fortsetzung des Container-Terminal-Themas aus quaycrane-demo (dort:
WELCHE Containerbrücke bearbeitet welche Bay EINES Schiffs; hier eine Ebene darüber: WANN und WO
entlang des Kais legt JEDES Schiff überhaupt an). Siehe README für die Modell-Abgrenzung zu
quaycrane-demo und dock-demo.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import berth_constants as C
from berth_cp_solver import solve_exact
from berth_evaluation import comparison_table, evaluate
from berth_heuristic import fcfs_construction, greedy_and_polish, priority_construction
from berth_pdf_export import generate_berth_plan_pdf
from berth_presets import (
    apply_preset,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sync_query_params,
)
from berth_scenario import generate_instance
from berth_ui_panel import render_berth_panel
from berth_visualization import build_berth_chart, build_comparison_chart, build_priority_wait_chart

st.set_page_config(page_title="Kaiplatz-Zuteilung – Sebastian Hanisch", layout="wide")

SCENARIO_KEYS = [
    "n_ships_slider", "quay_length_slider", "deep_zone_fraction_slider", "deep_draft_limit_slider",
    "length_avg_slider", "length_variability_slider", "draft_avg_slider", "draft_variability_slider",
    "handling_avg_slider", "handling_variability_slider", "arrival_spread_slider",
    "mainliner_fraction_slider", "safety_margin_slider", "seed_input",
]


@st.cache_data(show_spinner=False)
def _compute_heuristics(scenario_key):
    instance = generate_instance(*scenario_key)
    if instance.is_trivially_infeasible():
        return instance, None

    fcfs_plan = fcfs_construction(instance)
    priority_plan = priority_construction(instance)
    polished_plan = greedy_and_polish(instance, seed=scenario_key[-1])

    results = [
        evaluate(instance, fcfs_plan, label="FCFS (Ankunftsreihenfolge)"),
        evaluate(instance, priority_plan, label="Prioritätsbasiert"),
        evaluate(instance, polished_plan, label="Prioritätsbasiert + lokale Suche"),
    ]
    return instance, results


@st.cache_data(show_spinner=False)
def _compute_exact(scenario_key, hint_plan):
    """Getrennt von `_compute_heuristics`, damit der exakte Löser nicht automatisch bei jeder
    Regler-Änderung mitläuft (kann bei größeren Szenarien mehrere Sekunden dauern) - nur auf
    Klick. `hint_plan` (die beste Heuristik-Lösung) gibt CP-SAT sofort einen gültigen
    Startpunkt statt bei null zu suchen."""
    instance = generate_instance(*scenario_key)
    solve = solve_exact(instance, time_limit_seconds=C.EXACT_SOLVE_TIME_LIMIT_SECONDS, hint_plan=hint_plan)
    if not solve.feasible:
        return None
    exact_label = "Exakt (OR-Tools)" if solve.optimal else "Exakt (OR-Tools, Zeitlimit)"
    exact_eval = evaluate(instance, solve.plan, label=exact_label)
    return {"eval": exact_eval, "optimal": solve.optimal, "wall_time_ms": solve.wall_time_ms}


st.title("⚓ Kaiplatz-Zuteilung (Berth Allocation)")
st.markdown(
    """
Welches Schiff legt **wann** und **wo entlang des Kais** an? Ein klassisches Terminalproblem:
Schiffe haben eine physische **Länge** und belegen einen zusammenhängenden Kai-Abschnitt - zwei
Schiffe dürfen sich nie gleichzeitig überlappen (inkl. Sicherheitsabstand), tiefgängige Schiffe
brauchen zusätzlich eine ausreichend tiefe **Wasserzone**, und nicht jedes Schiff ist gleich
wichtig: **Mainliner** mit Anschlussverkehr haben Vorrang vor **Feedern** und **Tramp**-Schiffen.
Ziel ist minimale, **prioritätsgewichtete Wartezeit**. Wie das Modell und die drei Verfahren im
Detail funktionieren, steht im Expander "Wie funktioniert diese Demo?" weiter unten, die formale
Herleitung im Expander "📐 Mathematische Formulierung".
"""
)

st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
PRESET_HELP = {
    "Ruhiger Feederhafen": "Wenige, überwiegend kleine Schiffe, viel Zeitpuffer - Priorität spielt kaum eine Rolle.",
    "Mainliner-Stoßzeit trifft Tiefwasser-Engpass": "Viele Mainliner treffen eng gestaffelt ein, während die "
    "Tiefwasserzone knapp ist - hier zeigt sich, was Priorität wirklich kostet.",
    "Volle Kaikapazität": "Viele Schiffe relativ zur Kailänge - der Kai ist über weite Strecken der Zeit fast voll.",
}
preset_cols = st.columns(len(C.PRESETS))
for i, name in enumerate(C.PRESETS.keys()):
    with preset_cols[i]:
        st.button(name, use_container_width=True, on_click=apply_preset, args=(name,), help=PRESET_HELP[name])

st.caption(
    "🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, "
    "um ein Szenario zu teilen."
)

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    n_ships = st.slider("Anzahl Schiffe", *bounds("n_ships_slider"), key="n_ships_slider")
    seed = st.number_input("Zufalls-Seed", *bounds("seed_input"), key="seed_input", step=1)

    st.markdown("**Kai & Tiefe**")
    quay_length = st.slider("Kailänge (m)", *bounds("quay_length_slider"), step=10, key="quay_length_slider")
    deep_zone_fraction = st.slider(
        "Anteil Tiefwasserzone", *bounds("deep_zone_fraction_slider"), key="deep_zone_fraction_slider",
        help="Welcher Anteil des Kais zur tiefen Zone gehört - der Rest ist die flachere Zone "
        "(Tiefgang-Limit = 60% des Tiefwasser-Limits).",
    )
    deep_draft_limit = st.slider(
        "Max. Tiefgang Tiefwasserzone (m)", *bounds("deep_draft_limit_slider"), key="deep_draft_limit_slider"
    )

    st.markdown("**Schiffe**")
    length_avg = st.slider("Ø Schiffslänge (m)", *bounds("length_avg_slider"), key="length_avg_slider")
    length_variability = st.slider("Streuung der Länge", *bounds("length_variability_slider"), key="length_variability_slider")
    draft_avg = st.slider("Ø Tiefgang (m)", *bounds("draft_avg_slider"), key="draft_avg_slider")
    draft_variability = st.slider("Streuung des Tiefgangs", *bounds("draft_variability_slider"), key="draft_variability_slider")

    st.markdown("**Zeiten**")
    handling_avg = st.slider("Ø Liegezeit je Schiff (h)", *bounds("handling_avg_slider"), key="handling_avg_slider")
    handling_variability = st.slider("Streuung der Liegezeit", *bounds("handling_variability_slider"), key="handling_variability_slider")
    arrival_spread = st.slider(
        "Ankunftsfenster (h)", *bounds("arrival_spread_slider"), key="arrival_spread_slider",
        help="Über welchen Zeitraum die Ankünfte der Schiffe gestreut sind - klein = alle kommen fast "
        "gleichzeitig (Stoßzeit), groß = entzerrte Ankünfte.",
    )

    st.markdown("**Priorität**")
    mainliner_fraction = st.slider(
        "Anteil Mainliner", *bounds("mainliner_fraction_slider"), key="mainliner_fraction_slider",
        help="Anteil der Schiffe mit höchster Priorität (Gewicht 3×) - der Rest verteilt sich zufällig "
        "auf Feeder (1,5×) und Tramp (1×).",
    )

    st.markdown("**Physische Randbedingung**")
    safety_margin = st.slider(
        "Sicherheitsabstand zwischen Schiffen (m)", *bounds("safety_margin_slider"), key="safety_margin_slider",
        help="Mindestabstand in Metern, den zwei gleichzeitig liegende Schiffe zueinander einhalten müssen "
        "(Festmacher, Fender).",
    )

    st.button(
        "🎲 Neue Schiffe generieren", use_container_width=True, on_click=randomize_seed,
        help="Würfelt einen neuen Zufalls-Seed für die Schiffsflotte.",
    )

current_values = {key: st.session_state[key] for key in SCENARIO_KEYS}
sync_query_params(current_values)

scenario_key = (
    int(n_ships), int(quay_length), deep_zone_fraction, deep_draft_limit, int(length_avg),
    length_variability, draft_avg, draft_variability, int(handling_avg), handling_variability,
    int(arrival_spread), mainliner_fraction, int(safety_margin), int(seed),
)

with st.spinner("Berechne Kaibelegung..."):
    instance, results = _compute_heuristics(scenario_key)

if results is None:
    st.error(
        "🚫 Für diese Kombination gibt es **kein Szenario mit gültiger Lösung**: mindestens ein "
        "Schiff (Länge inkl. Sicherheitsabstand oder Tiefgang) passt in keine der beiden Zonen. "
        "Bitte Kailänge/Tiefgang-Limits erhöhen, Schiffslänge verringern oder Sicherheitsabstand "
        "reduzieren."
    )
    st.stop()

best = min(results, key=lambda r: r["total_weighted_wait"])
baseline = max(results, key=lambda r: r["total_weighted_wait"])
score_saved = baseline["total_weighted_wait"] - best["total_weighted_wait"]
pct_saved = (score_saved / baseline["total_weighted_wait"] * 100) if baseline["total_weighted_wait"] > 0 else 0.0

st.markdown("## 🎯 Ihre beste Kaibelegung")
st.caption(f"Methode: **{best['label']}** - wird bei jedem Lauf neu anhand der gewichteten Wartezeit bestimmt.")

m1, m2, m3 = st.columns(3)
m1.metric(
    "Gewichtete Wartezeit (Score)", f"{best['total_weighted_wait']:.1f}",
    delta=f"-{score_saved:.1f} ggü. {baseline['label']}", delta_color="inverse",
)
m2.metric("Wartezeit gesamt", f"{best['total_wait']:.0f} h")
m3.metric("Letzte Abfahrt", f"{best['last_departure']:.0f} h")

if score_saved > 0.5:
    st.success(
        f"⏱️ **{best['label']}** spart hier ca. **{score_saved:.1f} Punkte** ({pct_saved:.1f}%) "
        f"gewichtete Wartezeit gegenüber '{baseline['label']}'."
    )

fig_best = build_berth_chart(instance, best, title=best["label"])
st.plotly_chart(fig_best, use_container_width=True, key="primary_berth_chart")

pdf_bytes_best = generate_berth_plan_pdf(best["label"], instance, best)
st.download_button(
    "📄 Belegungsplan als PDF herunterladen", data=pdf_bytes_best, file_name="kaiplan_optimiert.pdf",
    mime="application/pdf", key="primary_pdf_download",
)

st.caption(
    "Ermittelt mit der besten von drei eigenen Verfahren für dieses Szenario. Details zu allen "
    "Verfahren und dem Vergleich mit Google OR-Tools unten."
)

st.markdown("---")

st.subheader("📐 Was kostet Mainliner-Priorität die anderen Schiffe?")
st.markdown(
    """
Kernfrage dieser Demo: **FCFS** (First-Come-First-Served) plant Schiffe strikt nach Ankunft ein -
fair im Sinne von "wer zuerst da ist", aber ohne Rücksicht auf Anschlussverkehr. **Prioritätsbasiert**
lässt Mainliner sich die besten Slots zuerst sichern. Das senkt ihre Wartezeit - aber auf wessen
Kosten geht das? Hier live für Ihre aktuelle Konfiguration geprüft, nicht nur behauptet.
"""
)

fcfs_result, priority_result = results[0], results[1]
mainliner_wait_fcfs = fcfs_result["avg_wait_by_priority"].get("Mainliner", 0.0)
mainliner_wait_priority = priority_result["avg_wait_by_priority"].get("Mainliner", 0.0)
mainliner_delta = mainliner_wait_priority - mainliner_wait_fcfs

other_wait_fcfs = sum(
    fcfs_result["avg_wait_by_priority"].get(p, 0.0) for p in ("Feeder", "Tramp")
)
other_wait_priority = sum(
    priority_result["avg_wait_by_priority"].get(p, 0.0) for p in ("Feeder", "Tramp")
)
other_delta = other_wait_priority - other_wait_fcfs

if any(s.priority == "Mainliner" for s in instance.ships):
    core_col1, core_col2, core_col3 = st.columns(3)
    core_col1.metric("Ø Wartezeit Mainliner (FCFS)", f"{mainliner_wait_fcfs:.1f} h")
    core_col2.metric(
        "Ø Wartezeit Mainliner (Prioritätsbasiert)", f"{mainliner_wait_priority:.1f} h",
        delta=f"{mainliner_delta:.1f} h ggü. FCFS", delta_color="inverse",
    )
    core_col3.metric(
        "Ø Wartezeit Feeder+Tramp (Prioritätsbasiert)", f"{other_wait_priority:.1f} h",
        delta=f"{other_delta:.1f} h ggü. FCFS", delta_color="inverse",
    )

    if mainliner_delta < -0.5 and other_delta > 0.5:
        st.success(
            f"✅ Priorität wirkt hier klar: Mainliner warten **{-mainliner_delta:.1f} h** weniger, "
            f"auf Kosten von **{other_delta:.1f} h** zusätzlicher Wartezeit bei Feeder/Tramp im Schnitt."
        )
    elif abs(mainliner_delta) <= 0.5:
        st.info(
            "ℹ️ Bei dieser Konfiguration gibt es kaum Konflikte um Kaiplätze - Priorität ändert die "
            "Mainliner-Wartezeit nur unwesentlich, da meist ohnehin genug Platz frei ist."
        )
    else:
        st.warning(
            "⚠️ Ungewöhnliches Ergebnis für diese Konfiguration - prüfen Sie ggf. die Rohdaten im "
            "Methodenvergleich unten."
        )
else:
    st.info("Kein Mainliner in dieser Flotte - erhöhen Sie den Anteil Mainliner im Regler links.")

st.markdown("---")

with st.expander("🔧 Wie wir das erreichen – vollständiger Methodenvergleich"):
    prefixes = ["fcfs", "priority", "polish"]
    tab_labels = [r["label"] for r in results] + ["🧮 Exakt (OR-Tools)", "📊 Vergleich"]
    tabs = st.tabs(tab_labels)

    for tab, r, prefix in zip(tabs[: len(results)], results, prefixes):
        with tab:
            render_berth_panel(prefix, r["label"], instance, r)

    tab_exact, tab_compare = tabs[len(results)], tabs[len(results) + 1]

    exact_eval = None
    with tab_exact:
        st.caption(
            "Löst dasselbe Zuteilungsmodell exakt statt mit unseren eigenen Verfahren - dient als "
            f"Cross-Check. Auf {C.EXACT_SOLVE_TIME_LIMIT_SECONDS}s begrenzt (bei vielen Schiffen manchmal "
            "nur die beste gefundene, nicht bewiesen optimale Lösung - wird dann so gekennzeichnet)."
        )
        solve_clicked = st.button("🧮 Mit OR-Tools lösen", key="exact_solve_btn")
        if solve_clicked:
            st.session_state["exact_scenario_key"] = scenario_key

        if st.session_state.get("exact_scenario_key") == scenario_key:
            hint_plan = {idx: (info["start"], info["pos"]) for idx, info in results[2]["plan"].items()}
            with st.spinner(f"Berechne exakte Lösung (OR-Tools CP-SAT, bis zu {C.EXACT_SOLVE_TIME_LIMIT_SECONDS}s)..."):
                exact_result = _compute_exact(scenario_key, hint_plan)

            if exact_result is None:
                st.error(
                    "🚫 OR-Tools hat innerhalb des Zeitlimits keine gültige Lösung gefunden. Bitte "
                    "Sicherheitsabstand verringern oder Zonen/Kailänge großzügiger einstellen."
                )
            else:
                exact_eval = exact_result["eval"]
                gap = best["total_weighted_wait"] - exact_eval["total_weighted_wait"]
                gap_pct = (gap / exact_eval["total_weighted_wait"] * 100) if exact_eval["total_weighted_wait"] > 0 else 0.0

                if exact_result["optimal"]:
                    if gap < 0.5:
                        st.info(
                            f"✅ Optimal gelöst ({exact_result['wall_time_ms']:.0f} ms): **{best['label']}** "
                            f"erreicht bereits das Optimum ({exact_eval['total_weighted_wait']:.1f})."
                        )
                    else:
                        st.info(
                            f"📐 Optimal gelöst ({exact_result['wall_time_ms']:.0f} ms): Optimum liegt bei "
                            f"{exact_eval['total_weighted_wait']:.1f} - Lücke zur besten Heuristik: "
                            f"{gap:.1f} ({gap_pct:.1f}%)."
                        )
                else:
                    if gap <= 0.5:
                        st.warning(
                            f"⏱️ Zeitlimit erreicht, kein Optimalitätsbeweis ({exact_result['wall_time_ms']:.0f} ms): "
                            f"**{best['label']}** ({best['total_weighted_wait']:.1f}) erreicht oder unterbietet "
                            f"sogar die beste vom Solver gefundene Lösung ({exact_eval['total_weighted_wait']:.1f})."
                        )
                    else:
                        st.warning(
                            f"⏱️ Zeitlimit erreicht, kein Optimalitätsbeweis ({exact_result['wall_time_ms']:.0f} ms): "
                            f"beste bislang gefundene Lösung liegt bei {exact_eval['total_weighted_wait']:.1f} - "
                            f"{gap:.1f} ({gap_pct:.1f}%) unter der besten Heuristik, aber ohne Optimalitätsgarantie."
                        )
                render_berth_panel("exact", exact_eval["label"], instance, exact_eval)
        elif "exact_scenario_key" in st.session_state:
            st.info(
                "ℹ️ Die zuletzt berechnete exakte Lösung bezog sich auf ein anderes Szenario - "
                "Einstellungen geändert? Erneut auf '🧮 Mit OR-Tools lösen' klicken."
            )
        else:
            st.info("Noch keine Lösung berechnet – auf den Button oben klicken.")

    with tab_compare:
        all_results = list(results) + ([exact_eval] if exact_eval is not None else [])
        st.dataframe(comparison_table(all_results), use_container_width=True, hide_index=True)
        st.plotly_chart(build_comparison_chart(all_results), use_container_width=True, key="comparison_chart")
        st.plotly_chart(build_priority_wait_chart(all_results), use_container_width=True, key="priority_wait_chart")

with st.expander("Wie funktioniert diese Demo?"):
    st.markdown(
        """
Ein Kai ist in zwei **Tiefenzonen** unterteilt - eine tiefe (für tiefgängige Schiffe) und eine
flachere. Jedes ankommende **Schiff** hat eine Länge, einen Tiefgang, eine frühestmögliche
Ankunftszeit und eine feste Liegezeit (Umschlagsdauer). Zwei Schiffe dürfen sich zu keinem
Zeitpunkt räumlich überlappen (inkl. **Sicherheitsabstand**), und jedes Schiff muss vollständig
in einer Zone liegen, deren Tiefenlimit seinen Tiefgang zulässt.

Jedes Schiff gehört zu einer **Prioritätsklasse**: Mainliner (Gewicht 3×, meist Anschlussverkehr
mit festen Terminen), Feeder (1,5×) oder Tramp-Schiffe (1×, am flexibelsten). Zielgröße ist die
**gewichtete Wartezeit** - Wartezeit je Schiff (Anlegebeginn minus Ankunft) multipliziert mit
seinem Prioritätsgewicht, aufsummiert über alle Schiffe.

Drei Verfahren stehen zur Auswahl (im Expander "Wie wir das erreichen" alle nebeneinander),
zusätzlich eine **exakte Referenzlösung** (Google OR-Tools CP-SAT):

- **FCFS (Ankunftsreihenfolge)**: Schiffe werden strikt nach Ankunftszeit eingeplant, ohne
  Rücksicht auf Priorität - Referenzpunkt.
- **Prioritätsbasiert**: Schiffe werden nach Prioritätsgewicht (dann Ankunft) eingeplant -
  Mainliner sichern sich zuerst die besten Slots.
- **Prioritätsbasiert + lokale Suche**: startet bei der besseren der beiden Konstruktionen und
  verbessert iterativ durch paarweisen Tausch der Einplanungsreihenfolge - nachweislich nie
  schlechter als der Startpunkt.

Die Primäransicht zeigt **dynamisch** die bei den aktuellen Einstellungen tatsächlich beste
Methode. Die **Kaibelegungs**-Grafik zeigt jedes Schiff als Rechteck im Zeit-Position-Raum:
Breite = Liegezeit, Höhe = Schiffslänge (plus Sicherheitsabstand) - die Rechtecke überlappen sich
nie, und die schattierten Bänder markieren die beiden Tiefenzonen.
        """
    )

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Berth Allocation Problem (BAP)**, hier als kontinuierliches 2D-Packungsproblem im
Zeit-Position-Raum (vgl. Cordeau et al. 2005 für die klassische kontinuierliche BAP-Formulierung
mit disjunktiven Constraints); NP-schwer.

Gegeben Schiffe $i = 0, \dots, n-1$ mit Länge $\ell_i$, Tiefgang $d_i$, Ankunft $a_i$, fester
Liegezeit $h_i$ und Prioritätsgewicht $w_i$, ein Kai der Länge $L$ mit Zonen $z$ (Positions­bereich
$[z_{\text{lo}}, z_{\text{hi}}]$, Tiefenlimit $D_z$) und Sicherheitsabstand $m$.

Entscheidungsvariablen: Startzeit $t_i \ge a_i$ und Kai-Position $p_i$, mit
$p_i \in \bigcup_{z:\, D_z \ge d_i} [z_{\text{lo}}, \, z_{\text{hi}} - \ell_i - m]$ (das Schiff
liegt vollständig in einer tiefgang-kompatiblen Zone).

Für jedes Schiffspaar $i \ne j$ mit zeitlicher Überlappung
($t_i < t_j + h_j \;\wedge\; t_j < t_i + h_i$) muss zusätzlich räumliche Trennung gelten:

$$
p_i + \ell_i + m \le p_j \qquad \text{oder} \qquad p_j + \ell_j + m \le p_i
$$

Gelöst über Google OR-Tools CP-SAT mit `AddNoOverlap2D`: jedes Schiff wird als ein Rechteck im
Zeit-Position-Raum modelliert (Zeit-Intervall $[t_i, t_i+h_i)$ × Positions-Intervall
$[p_i, p_i+\ell_i+m)$), und die eingebaute 2D-Nichtüberlappung übernimmt genau die obige
Fallunterscheidung, ohne sie von Hand als Constraints auszuschreiben.

Zielfunktion: minimiere primär die gewichtete Wartezeit, als lexikografisches
Tie-Breaking-Ziel zusätzlich die ungewichtete Gesamtwartezeit (verhindert, dass der Solver unter
mehreren gleich guten Lösungen eine mit unnötiger Wartezeit auf einem Schiff zurückgibt):

$$
\min \; \Big(\sum_i w_i (t_i - a_i)\Big) \cdot W \;+\; \sum_i (t_i - a_i)
$$

mit einem Gewicht $W$, das groß genug ist, dass eine Verbesserung des Tie-Breaking-Ziels nie eine
Verschlechterung des primären Ziels aufwiegen kann.

Gelöst in [berth_cp_solver.py](berth_cp_solver.py), auf LIMIT_PLACEHOLDERs Rechenzeit begrenzt -
für die in dieser Demo möglichen Größen fast immer das bewiesene Optimum, bei vielen Schiffen und
engem Kai manchmal nur die beste innerhalb des Zeitlimits gefundene Lösung (dann klar als
"Zeitlimit erreicht" gekennzeichnet).
        """.replace("LIMIT_PLACEHOLDER", str(C.EXACT_SOLVE_TIME_LIMIT_SECONDS))
    )

st.markdown("---")

st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning. Interesse an einer maßgeschneiderten Lösung für "
    "Ihr Unternehmen? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html)"
)
