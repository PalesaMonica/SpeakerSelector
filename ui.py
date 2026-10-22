"""Look and feel: RAIL Lab colours, page styling and small HTML components."""
from __future__ import annotations

import html
from pathlib import Path

import streamlit as st

# RAIL Lab brand (raillab.org theme colour) + neutrals
CORAL = "#E85A4F"
CORAL_DARK = "#C9443A"
CORAL_TINT = "#FDEEEC"
INK = "#1F2328"
MUTED = "#6B7280"
LINE = "#E7E3E1"
SURFACE = "#FAF8F7"

STATUS_STYLE = {
    "Scheduled": ("#F1F2F4", "#4B5563"),
    "Confirmed": ("#E6F4EA", "#1E7B3A"),
    "Swapped": ("#FFF4E0", "#9A5B00"),
    "Done": ("#ECEEF2", "#5B6575"),
}

LOGO = Path(__file__).resolve().parent / "assets" / "logo.png"

CSS = f"""
<style>
#MainMenu, footer {{visibility: hidden;}}
.block-container {{padding-top: 2rem; padding-bottom: 3rem; max-width: 1200px;}}

/* Header band */
.rail-hero {{
  background: linear-gradient(120deg, {INK} 0%, #2E3238 60%, {CORAL_DARK} 140%);
  color: #fff; border-radius: 14px; padding: 28px 32px; margin-bottom: 1.5rem;
  border-bottom: 4px solid {CORAL};
}}
.rail-hero .eyebrow {{font-size: .78rem; letter-spacing: .14em; text-transform: uppercase;
  color: #FFB4AD; font-weight: 600;}}
.rail-hero h1 {{color: #fff; margin: .25rem 0 .35rem 0; font-size: 2rem; padding: 0;}}
.rail-hero p {{color: #D6D9DE; margin: 0; font-size: .98rem;}}

/* Stat cards */
.rail-cards {{display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: 14px; margin-bottom: 1.25rem;}}
.rail-card {{background: #fff; border: 1px solid {LINE}; border-radius: 12px; padding: 16px 18px;}}
.rail-card.accent {{border-left: 4px solid {CORAL};}}
.rail-card .k {{font-size: .75rem; text-transform: uppercase; letter-spacing: .08em;
  color: {MUTED}; font-weight: 600;}}
.rail-card .v {{font-size: 1.35rem; font-weight: 700; color: {INK}; margin-top: 4px;
  line-height: 1.25;}}
.rail-card .s {{font-size: .85rem; color: {MUTED}; margin-top: 2px;}}

/* Talk table */
.rail-table {{width: 100%; border-collapse: separate; border-spacing: 0; background: #fff;
  border: 1px solid {LINE}; border-radius: 12px; overflow: hidden; font-size: .95rem;}}
.rail-table th {{background: {SURFACE}; color: {MUTED}; text-align: left; font-weight: 600;
  font-size: .75rem; text-transform: uppercase; letter-spacing: .07em; padding: 10px 16px;
  border-bottom: 1px solid {LINE};}}
.rail-table td {{padding: 12px 16px; border-bottom: 1px solid {LINE}; color: {INK};}}
.rail-table tr:last-child td {{border-bottom: none;}}
.rail-table tr.next td {{background: {CORAL_TINT};}}
.rail-table .date {{font-weight: 600; white-space: nowrap;}}
.rail-table .sub {{color: {MUTED}; font-size: .82rem;}}
.pill {{display: inline-block; padding: 3px 10px; border-radius: 999px; font-size: .78rem;
  font-weight: 600;}}
.month-row td {{background: {SURFACE}; color: {CORAL_DARK}; font-weight: 700; font-size: .8rem;
  text-transform: uppercase; letter-spacing: .1em; padding: 8px 16px;}}

/* Section headings */
.rail-scroll {{max-height: 560px; overflow-y: auto; border-radius: 12px;}}
.rail-scroll th {{position: sticky; top: 0; z-index: 1;}}
.rail-h {{font-size: 1.05rem; font-weight: 700; color: {INK}; margin: 1.4rem 0 .6rem 0;
  padding-left: 10px; border-left: 4px solid {CORAL};}}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {{gap: 6px; border-bottom: 1px solid {LINE};}}
.stTabs [data-baseweb="tab"] {{padding: 10px 16px; font-weight: 600;}}
.stTabs [aria-selected="true"] {{color: {CORAL};}}

/* Sidebar */
[data-testid="stSidebar"] {{background: {SURFACE}; border-right: 1px solid {LINE};}}
.rail-brand {{font-weight: 800; font-size: 1.35rem; color: {INK}; letter-spacing: -.01em;}}
.rail-brand span {{color: {CORAL};}}
.rail-brand-sub {{color: {MUTED}; font-size: .82rem; margin-top: -2px;}}
.dot {{display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:6px;}}
</style>
"""


def apply_styles() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def esc(x) -> str:
    return html.escape(str(x))


def pill(status: str) -> str:
    bg, fg = STATUS_STYLE.get(status, ("#F1F2F4", "#4B5563"))
    return f'<span class="pill" style="background:{bg};color:{fg}">{esc(status)}</span>'


def hero(title: str, subtitle: str) -> None:
    st.markdown(
        f'<div class="rail-hero"><div class="eyebrow">RAIL Lab · University of the Witwatersrand</div>'
        f"<h1>{esc(title)}</h1><p>{esc(subtitle)}</p></div>",
        unsafe_allow_html=True,
    )


def section(title: str) -> None:
    st.markdown(f'<div class="rail-h">{esc(title)}</div>', unsafe_allow_html=True)


def cards(items: list[tuple[str, str, str]]) -> None:
    """items: (label, value, subtext). The first card gets the coral accent."""
    parts = []
    for n, (k, v, s) in enumerate(items):
        cls = "rail-card accent" if n == 0 else "rail-card"
        parts.append(f'<div class="{cls}"><div class="k">{esc(k)}</div>'
                     f'<div class="v">{esc(v)}</div><div class="s">{esc(s)}</div></div>')
    st.markdown(f'<div class="rail-cards">{"".join(parts)}</div>', unsafe_allow_html=True)


def talk_table(rows, next_date=None) -> None:
    """rows: iterable of dicts with date, speaker, status, swapped_with, synced."""
    body, month = [], None
    for r in rows:
        m = r["date"].strftime("%B %Y")
        if m != month:
            month = m
            body.append(f'<tr class="month-row"><td colspan="4">{esc(m)}</td></tr>')
        note = f"Swapped with {esc(r['swapped_with'])}" if r.get("swapped_with") else ""
        cal = "In calendar" if r.get("synced") else "Not synced"
        cls = ' class="next"' if next_date is not None and r["date"] == next_date else ""
        body.append(
            f"<tr{cls}><td class='date'>{r['date']:%a %d %b}<div class='sub'>10:00–11:00</div></td>"
            f"<td>{esc(r['speaker'])}<div class='sub'>{note}</div></td>"
            f"<td>{pill(r['status'])}</td><td class='sub'>{cal}</td></tr>"
        )
    st.markdown(
        "<div class='rail-scroll'><table class='rail-table'><thead><tr><th>Date</th><th>Speaker</th><th>Status</th>"
        f"<th>Calendar</th></tr></thead><tbody>{''.join(body)}</tbody></table></div>",
        unsafe_allow_html=True,
    )


def sidebar_brand() -> None:
    if LOGO.exists():
        st.image(str(LOGO), width=150)
    st.markdown('<div class="rail-brand">RAIL <span>Lab</span></div>'
                '<div class="rail-brand-sub">Talk Speaker Selector</div>', unsafe_allow_html=True)


def status_line(ok: bool, text: str) -> None:
    color = "#1E7B3A" if ok else MUTED
    st.markdown(f'<div style="font-size:.88rem;color:{INK}"><span class="dot" '
                f'style="background:{color}"></span>{esc(text)}</div>', unsafe_allow_html=True)
