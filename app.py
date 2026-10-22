"""RAIL Lab talk speaker selector.

Run with:  python -m streamlit run app.py
"""
from __future__ import annotations

import datetime as dt
from collections import Counter

import pandas as pd
import streamlit as st

import calendar_sync as cal
import scheduler
import storage
import ui
from storage import DONE, LOCKED, SCHEDULED, SWAPPED

st.set_page_config(page_title="RAIL Lab · Talk Schedule", page_icon=":material/campaign:",
                   layout="wide")
ui.apply_styles()

today = dt.date.today()

# ---------- sidebar ----------
with st.sidebar:
    ui.sidebar_brand()
    st.divider()
    st.markdown("**Google Calendar**")
    if not cal.has_credentials():
        ui.status_line(False, "Not set up")
    elif cal.is_connected():
        ui.status_line(True, "Connected")
    else:
        ui.status_line(False, "Not connected")
    with st.expander("Calendar settings", icon=":material/settings:"):
        calendar_id = st.text_input("Calendar ID", value="primary",
                                    help="'primary' is your main Google calendar.")
        auto_sync = st.toggle("Update calendar automatically", value=True)
        invite = st.toggle("Invite the speaker", value=False,
                           help="Adds the speaker's email as a guest on the event.")
        notify = st.toggle("Email guests about changes", value=False, disabled=not invite)
    st.divider()
    st.caption("Talks run every Monday, 10:00–11:00 (SAST), February to November. "
               "South African public holidays are skipped.")


# ---------- helpers ----------
def flash(msg: str, kind: str = "success") -> None:
    st.session_state["flash"] = (kind, msg)


def show_flash() -> None:
    if "flash" in st.session_state:
        kind, msg = st.session_state.pop("flash")
        icon = {"success": ":material/check_circle:", "warning": ":material/warning:"}.get(kind)
        st.toast(msg, icon=icon)


def sync_rows(sched: pd.DataFrame, idxs) -> int:
    """Create/update the calendar events for the given schedule rows."""
    idxs = list(idxs)
    service = cal.get_service()
    for i in idxs:
        r = sched.loc[i]
        body = cal.event_body(r["date"], r["speaker"], r["email"], invite)
        sched.at[i, "event_id"] = cal.upsert_event(
            service, calendar_id, r["event_id"], body, notify=invite and notify)
        sched.at[i, "synced"] = True
    return len(idxs)


def maybe_autosync(sched: pd.DataFrame, idxs) -> str:
    if not (auto_sync and cal.is_connected()):
        return ""
    try:
        n = sync_rows(sched, idxs)
        storage.save_schedule(sched)
        return f" Calendar updated ({n} event{'s' if n != 1 else ''})."
    except Exception as e:  # noqa: BLE001
        return f" Calendar update failed ({e}); retry from the Calendar tab."


def label(r) -> str:
    return f"{r['date']:%a %d %b %Y} · {r['speaker']} · {r['status']}"


speakers = storage.load_speakers()
sched = storage.load_schedule()
active_names = speakers.loc[speakers["active"], "name"].tolist()
email_of = dict(zip(speakers["name"], speakers["email"]))

ui.hero("Lab Talk Schedule", "Weekly research talks · Mondays 10:00–11:00 · February to November")
show_flash()

tab_sched, tab_gen, tab_spk, tab_cal = st.tabs([
    ":material/event: Schedule", ":material/shuffle: Generate",
    ":material/group: Speakers", ":material/calendar_month: Calendar",
])

# ---------- Schedule ----------
with tab_sched:
    upcoming = sched[sched["date"] >= today]
    if sched.empty:
        st.info("No talks scheduled yet. Add speakers in the **Speakers** tab, then draw a "
                "schedule in **Generate**.", icon=":material/info:")
    else:
        this_year = upcoming[pd.Series([d.year == today.year for d in upcoming["date"]],
                                       index=upcoming.index, dtype=bool)]
        nxt = upcoming.iloc[0] if not upcoming.empty else None
        days = (nxt["date"] - today).days if nxt is not None else None
        when = ("Today" if days == 0 else "Tomorrow" if days == 1 else f"In {days} days") \
            if nxt is not None else ""
        ui.cards([
            ("Next talk", nxt["speaker"] if nxt is not None else "None scheduled",
             f"{nxt['date']:%A %d %B} · {when}" if nxt is not None else "Draw a new schedule"),
            ("Status", nxt["status"] if nxt is not None else "—",
             "Needs confirmation" if nxt is not None and nxt["status"] == SCHEDULED else "Ready"),
            ("Talks remaining", str(len(upcoming)), f"{len(this_year)} left in {today.year}"),
            ("Active speakers", str(len(active_names)),
             f"{int((~upcoming['synced']).sum())} talk(s) not in calendar"),
        ])

        head_l, head_r = st.columns([3, 1], vertical_alignment="bottom")
        with head_l:
            ui.section("Talks")
        with head_r:
            show_all = st.toggle("Include past talks", value=False)
        view = sched if show_all else upcoming
        if view.empty:
            st.caption("No upcoming talks.")
        else:
            ui.talk_table(view.to_dict("records"),
                          next_date=nxt["date"] if nxt is not None else None)

        ui.section("Manage a talk")
        choices = view.index.tolist()
        if choices:
            i = st.selectbox("Choose a talk", choices, format_func=lambda k: label(sched.loc[k]),
                             label_visibility="collapsed")
            row = sched.loc[i]
            a, b, c = st.columns(3)

            with a, st.container(border=True):
                st.markdown("**:material/task_alt: Update status**")
                st.caption("Confirm the speaker or mark the talk as done.")
                new_status = st.selectbox(
                    "Status", storage.STATUSES, key=f"status_{i}",
                    index=storage.STATUSES.index(row["status"])
                    if row["status"] in storage.STATUSES else 0)
                if st.button("Save status", key=f"save_status_{i}", type="primary",
                             width="stretch"):
                    sched.at[i, "status"] = new_status
                    storage.save_schedule(sched)
                    flash(f"{row['speaker']} marked {new_status} for {row['date']:%d %b}.")
                    st.rerun()

            with b, st.container(border=True):
                st.markdown("**:material/swap_horiz: Swap dates**")
                st.caption("Exchange this talk with another speaker's date.")
                others = [k for k in sched.index if k != i and sched.at[k, "status"] != DONE]
                j = st.selectbox("Swap with", others, key=f"swap_{i}",
                                 format_func=lambda k: label(sched.loc[k]))
                if st.button("Swap", key=f"do_swap_{i}", disabled=j is None, width="stretch"):
                    a_name, b_name = sched.at[i, "speaker"], sched.at[j, "speaker"]
                    for k, new, old in ((i, b_name, a_name), (j, a_name, b_name)):
                        sched.at[k, "speaker"] = new
                        sched.at[k, "email"] = email_of.get(new, "")
                        sched.at[k, "swapped_with"] = old
                        sched.at[k, "status"] = SWAPPED
                        sched.at[k, "synced"] = False
                    storage.save_schedule(sched)
                    flash(f"Swapped {a_name} and {b_name}.{maybe_autosync(sched, [i, j])}")
                    st.rerun()

            with c, st.container(border=True):
                st.markdown("**:material/person_add: Hand over**")
                st.caption("Give this talk to someone who isn't on that date.")
                cands = [n for n in active_names if n != row["speaker"]]
                who = st.selectbox("New speaker", cands, key=f"replace_{i}")
                if st.button("Replace speaker", key=f"do_replace_{i}", disabled=who is None,
                             width="stretch"):
                    old = row["speaker"]
                    sched.at[i, "speaker"] = who
                    sched.at[i, "email"] = email_of.get(who, "")
                    sched.at[i, "swapped_with"] = old
                    sched.at[i, "status"] = SWAPPED
                    sched.at[i, "synced"] = False
                    storage.save_schedule(sched)
                    flash(f"{who} now speaks on {row['date']:%d %b} instead of {old}."
                          f"{maybe_autosync(sched, [i])}")
                    st.rerun()

        past_open = sched[(sched["date"] < today) & (sched["status"] != DONE)]
        if not past_open.empty:
            if st.button(f"Mark {len(past_open)} past talk(s) as Done",
                         icon=":material/done_all:"):
                sched.loc[past_open.index, "status"] = DONE
                storage.save_schedule(sched)
                flash("Past talks marked as Done.")
                st.rerun()

# ---------- Generate ----------
with tab_gen:
    ui.section("Draw a schedule")
    st.caption("One speaker per Monday. Everyone speaks once before anyone speaks twice, and "
               "nobody speaks two weeks in a row. Confirmed, swapped and finished talks are kept.")
    with st.container(border=True):
        default_year = today.year if today.month < 11 else today.year + 1
        c1, c2, c3 = st.columns(3)
        year = int(c1.number_input("Year", min_value=2024, max_value=2100, value=default_year))
        start_default = max(dt.date(year, 2, 1), today) if year == today.year \
            else dt.date(year, 2, 1)
        start = c2.date_input("Start from", value=start_default, format="DD/MM/YYYY")
        seed = c3.text_input("Random seed (optional)",
                             help="The same seed and speaker list always give the same draw.")
        skip_hol = st.checkbox("Skip South African public holidays", value=True)

        dates = scheduler.talk_mondays(year, start=start, skip_holidays=skip_hol)
        locked_dates = set(sched.loc[sched["status"].isin(LOCKED), "date"])
        free_dates = [d for d in dates if d not in locked_dates]
        ui.cards([
            ("Mondays in range", str(len(dates)), f"{start:%d %b} – 30 Nov {year}"),
            ("Already confirmed", str(len(dates) - len(free_dates)), "Kept as they are"),
            ("To be drawn", str(len(free_dates)), f"From {len(active_names)} active speakers"),
        ])
        if not active_names:
            st.warning("Add at least one active speaker first.", icon=":material/warning:")
        if st.button("Draw speakers", type="primary", icon=":material/shuffle:",
                     disabled=not active_names or not free_dates):
            kept = sched[~sched["date"].isin(free_dates)]
            before = kept[kept["date"] < free_dates[0]]
            picks = scheduler.draw_speakers(
                active_names, len(free_dates),
                past_counts=Counter(kept["speaker"]),
                last_speaker=before.iloc[-1]["speaker"] if not before.empty else None,
                seed=seed or None,
            )
            st.session_state["preview"] = pd.DataFrame({"date": free_dates, "speaker": picks})

    preview = st.session_state.get("preview")
    if preview is not None:
        ui.section("Preview")
        st.caption("Nothing is saved until you click **Save schedule**.")
        ui.talk_table(preview.assign(status="Draft", swapped_with="", synced=False)
                      .to_dict("records"))
        st.write("")
        b1, b2, _ = st.columns([1, 1, 3])
        if b1.button("Save schedule", type="primary", icon=":material/save:", width="stretch"):
            replaced = sched[sched["date"].isin(preview["date"])]
            msg = ""
            to_delete = [e for e in replaced["event_id"] if e]
            if to_delete and cal.is_connected():
                try:
                    service = cal.get_service()
                    for e in to_delete:
                        cal.delete_event(service, calendar_id, e)
                except Exception as e:  # noqa: BLE001
                    msg += f" Could not remove old events ({e})."
            new = preview.assign(
                email=preview["speaker"].map(email_of).fillna(""),
                status=SCHEDULED, swapped_with="", event_id="", synced=False)
            sched = pd.concat([sched[~sched["date"].isin(preview["date"])], new],
                              ignore_index=True)
            sched = sched.sort_values("date").reset_index(drop=True)
            storage.save_schedule(sched)
            idxs = sched.index[sched["date"].isin(preview["date"])]
            msg = maybe_autosync(sched, idxs) + msg
            del st.session_state["preview"]
            flash(f"Saved {len(preview)} talks.{msg}")
            st.rerun()
        if b2.button("Discard", icon=":material/close:", width="stretch"):
            del st.session_state["preview"]
            st.rerun()

# ---------- Speakers ----------
with tab_spk:
    counts = Counter(sched["speaker"])
    left, right = st.columns([2, 1], gap="large")
    with left:
        ui.section("Lab members")
        st.caption("Edit names directly, add rows at the bottom, or untick **Active** to leave "
                   "someone out of future draws.")
        edit_df = speakers.assign(talks=speakers["name"].map(counts).fillna(0).astype(int))
        edited = st.data_editor(
            edit_df, num_rows="dynamic", hide_index=True, width="stretch",
            column_config={
                "name": st.column_config.TextColumn("Name", required=True),
                "email": st.column_config.TextColumn("Email"),
                "active": st.column_config.CheckboxColumn("Active", default=True),
                "talks": st.column_config.NumberColumn("Talks", disabled=True),
            },
        )
        if st.button("Save changes", type="primary", icon=":material/save:"):
            storage.save_speakers(edited.drop(columns=["talks"]))
            flash("Speakers saved.")
            st.rerun()
    with right:
        ui.section("Import from CSV")
        with st.container(border=True):
            st.caption("Needs a **name** column. Optional: **email**, **active**.")
            up = st.file_uploader("Speakers CSV", type="csv", label_visibility="collapsed")
            if up is not None:
                try:
                    new_spk = storage.normalize_speakers(pd.read_csv(up, dtype=str))
                    st.dataframe(new_spk, hide_index=True, width="stretch")
                    if st.button(f"Replace list with {len(new_spk)} speakers",
                                 icon=":material/upload:", width="stretch"):
                        storage.save_speakers(new_spk)
                        flash(f"Loaded {len(new_spk)} speakers.")
                        st.rerun()
                except Exception as e:  # noqa: BLE001
                    st.error(f"Could not read that CSV: {e}")
            st.download_button("Download current list", speakers.to_csv(index=False),
                               file_name="speakers.csv", mime="text/csv",
                               icon=":material/download:", width="stretch")

# ---------- Calendar ----------
with tab_cal:
    left, right = st.columns([2, 1], gap="large")
    with left:
        ui.section("Google Calendar")
        with st.container(border=True):
            if not cal.has_credentials():
                st.markdown("**Not set up yet.** Save your OAuth client file as "
                            "`credentials.json` in the project folder (steps in README.md), "
                            "then reload this page.")
            elif not cal.is_connected():
                st.markdown("Sign in once so the app can add talks to your calendar.")
                if st.button("Connect Google Calendar", type="primary", icon=":material/link:"):
                    try:
                        cal.get_service()
                        flash("Google Calendar connected.")
                        st.rerun()
                    except Exception as e:  # noqa: BLE001
                        st.error(f"Sign-in failed: {e}")
            else:
                pending = sched[(~sched["synced"]) & (sched["date"] >= today)]
                future = sched[sched["date"] >= today]
                ui.status_line(True, f"Connected · {len(future) - len(pending)} of "
                                     f"{len(future)} upcoming talks in your calendar")
                st.write("")
                c1, c2, c3 = st.columns(3)
                if c1.button(f"Sync {len(pending)} pending", type="primary",
                             icon=":material/sync:", disabled=pending.empty, width="stretch"):
                    try:
                        n = sync_rows(sched, pending.index)
                        storage.save_schedule(sched)
                        flash(f"Synced {n} talk(s) to Google Calendar.")
                        st.rerun()
                    except Exception as e:  # noqa: BLE001
                        st.error(f"Sync failed: {e}")
                if c2.button("Re-sync all upcoming", icon=":material/refresh:",
                             disabled=future.empty, width="stretch"):
                    try:
                        n = sync_rows(sched, future.index)
                        storage.save_schedule(sched)
                        flash(f"Re-synced {n} talk(s).")
                        st.rerun()
                    except Exception as e:  # noqa: BLE001
                        st.error(f"Sync failed: {e}")
                if c3.button("Disconnect", icon=":material/link_off:", width="stretch"):
                    cal.disconnect()
                    st.rerun()
    with right:
        ui.section("Export")
        with st.container(border=True):
            st.caption("Download upcoming talks as an .ics file to import into any calendar.")
            st.download_button(
                "Download .ics", data=cal.to_ics(sched[sched["date"] >= today].to_dict("records")),
                file_name="rail_lab_talks.ics", mime="text/calendar", icon=":material/download:",
                disabled=sched.empty, width="stretch",
            )
