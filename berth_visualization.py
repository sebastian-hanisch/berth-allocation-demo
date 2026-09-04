"""Plotly-Visualisierungen: Kaibelegung im Zeit-Position-Raum (Kernvisual) und Methodenvergleich."""

import berth_constants as C


def build_berth_chart(instance, result, title=""):
    import plotly.graph_objects as go

    fig = go.Figure()
    plan = result["plan"]
    max_time = max((p["start"] + instance.ships[idx].handling_time for idx, p in plan.items()), default=1)
    max_time = max(max_time, 1)

    for zone in instance.zones:
        fig.add_shape(
            type="rect", x0=0, x1=max_time, y0=zone.start, y1=zone.end,
            fillcolor=C.ZONE_COLORS.get(zone.name, "rgba(0,0,0,0.05)"), line=dict(width=0), layer="below",
        )
        fig.add_annotation(
            x=0, y=zone.end - 2, text=f"{zone.name} (max. {zone.max_draft:.1f} m Tiefgang)",
            showarrow=False, xanchor="left", yanchor="top", font=dict(size=10, color="#666"), xshift=4,
        )

    for idx, info in plan.items():
        ship = instance.ships[idx]
        start, pos, wait = info["start"], info["pos"], info["wait"]
        color = C.PRIORITY_COLORS.get(ship.priority, "#888888")

        fig.add_shape(
            type="rect", x0=start, x1=start + ship.handling_time, y0=pos, y1=pos + ship.length,
            fillcolor=color, opacity=0.75, line=dict(color="white", width=1),
        )
        fig.add_trace(
            go.Scatter(
                x=[start + ship.handling_time / 2],
                y=[pos + ship.length / 2],
                mode="markers",
                marker=dict(size=1, color=color),
                showlegend=False,
                hovertemplate=(
                    f"<b>{ship.name}</b> ({ship.priority})<br>"
                    f"Ankunft: {ship.arrival} h &nbsp;|&nbsp; Anlegebeginn: {start} h "
                    f"&nbsp;|&nbsp; Wartezeit: {wait} h<br>"
                    f"Liegezeit: {start}-{start + ship.handling_time} h<br>"
                    f"Position: {pos}-{pos + ship.length} m &nbsp;|&nbsp; Tiefgang: {ship.draft} m"
                    "<extra></extra>"
                ),
            )
        )

    # Eigene Legenden-Einträge statt der (bei marker-size=1 kaum sichtbaren) automatischen
    # Punkt-Swatches der Hover-Traces oben: EIN unsichtbarer Dummy-Punkt je tatsächlich
    # vorkommender Prioritätsklasse, in fester fachlicher Reihenfolge (Mainliner > Feeder >
    # Tramp) statt in der zufälligen Einfüge-Reihenfolge der Heuristik - mit einem großen,
    # quadratischen Marker, der wie ein Farbfeld aussieht (vgl. dieselbe Dummy-Trace-Technik in
    # quaycrane_visualization.py für dessen "Wartezeit"-Legendeneintrag).
    present_priorities = {instance.ships[idx].priority for idx in plan}
    for priority in ("Mainliner", "Feeder", "Tramp"):
        if priority not in present_priorities:
            continue
        fig.add_trace(
            go.Scatter(
                x=[None], y=[None], mode="markers",
                marker=dict(size=14, symbol="square", color=C.PRIORITY_COLORS.get(priority, "#888888")),
                name=priority,
            )
        )

    fig.update_layout(
        title=title,
        xaxis_title="Zeit (Stunden)",
        yaxis_title="Kai-Position (Meter)",
        template="plotly_white",
        height=480,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        margin=dict(t=60),
    )
    fig.update_xaxes(range=[0, max_time * 1.02], fixedrange=True)
    fig.update_yaxes(range=[0, instance.quay_length], fixedrange=True)
    return fig


def build_comparison_chart(results):
    import plotly.graph_objects as go

    labels = [r["label"] for r in results]
    fig = go.Figure()
    fig.add_trace(
        go.Bar(x=labels, y=[r["total_weighted_wait"] for r in results], name="Gewichtete Wartezeit (Score)", marker_color="#d62728")
    )
    fig.add_trace(
        go.Bar(x=labels, y=[r["total_wait"] for r in results], name="Wartezeit gesamt (h)", marker_color="#1f77b4")
    )
    fig.update_layout(
        barmode="group", yaxis_title="Stunden bzw. Score", template="plotly_white", height=380,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def build_priority_wait_chart(results):
    import plotly.graph_objects as go

    priorities = ["Mainliner", "Feeder", "Tramp"]
    fig = go.Figure()
    for r in results:
        fig.add_trace(
            go.Bar(
                x=priorities,
                y=[r["avg_wait_by_priority"].get(p, 0.0) for p in priorities],
                name=r["label"],
            )
        )
    fig.update_layout(
        barmode="group", yaxis_title="Ø Wartezeit (h)", template="plotly_white", height=360,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig
