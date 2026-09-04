"""Wiederverwendbares Panel zur Darstellung einer Methode im Methodenvergleich."""

import streamlit as st

from berth_pdf_export import generate_berth_plan_pdf
from berth_visualization import build_berth_chart


def render_berth_panel(prefix, label, instance, result):
    m1, m2, m3 = st.columns(3)
    m1.metric("Gewichtete Wartezeit (Score)", f"{result['total_weighted_wait']:.1f}")
    m2.metric("Wartezeit gesamt", f"{result['total_wait']:.0f} h")
    m3.metric("Letzte Abfahrt", f"{result['last_departure']:.0f} h")

    fig = build_berth_chart(instance, result, title=label)
    st.plotly_chart(fig, use_container_width=True, key=f"{prefix}_berth_chart")

    pdf_bytes = generate_berth_plan_pdf(label, instance, result)
    st.download_button(
        "📄 Belegungsplan als PDF herunterladen",
        data=pdf_bytes,
        file_name=f"kaiplan_{prefix}.pdf",
        mime="application/pdf",
        key=f"{prefix}_pdf_download",
    )

    return result
