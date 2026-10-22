# Lab Talk Speaker Selector

A Streamlit app that randomly picks one speaker for each Monday lab talk
(10:00–11:00 SAST, February–November, skipping South African public holidays),
tracks confirmations and swaps, and keeps your Google Calendar up to date.

## Run it

```powershell
uv sync                 # or: pip install -r requirements.txt
uv run python -m streamlit run app.py   # or: python -m streamlit run app.py
```

## Branding

Colours follow the RAIL Lab website (coral `#E85A4F`) and are set in
`.streamlit/config.toml` and `ui.py`. To show the lab logo in the sidebar, save it as
`assets/logo.png`.

## Speakers CSV

`data/speakers.csv` (or upload one in the **Speakers** tab):

```csv
name,email,active
Jane Doe,jane@students.wits.ac.za,true
```

Only `name` is required. Set `active` to `false` to leave someone out of the draw.

## Google Calendar setup (one time)

1. Go to https://console.cloud.google.com/ and create a project (e.g. "Speaker Selector").
2. **APIs & Services → Library** → enable **Google Calendar API**.
3. **APIs & Services → OAuth consent screen** → choose *External*, fill in the app name
   and your email, and add your Google account under **Test users**.
4. **APIs & Services → Credentials → Create credentials → OAuth client ID** →
   application type **Desktop app** → **Download JSON**.
5. Save the downloaded file in this folder as `credentials.json`.
6. In the app, open the **Calendar** tab and click **Connect Google Calendar**.
   A browser window opens; sign in and allow access. A `token.json` is saved so
   you only do this once.

`credentials.json` and `token.json` are in `.gitignore`. Never commit them.

## How it works

- **Generate**: draws speakers for every free Monday in the chosen year.
  Nobody speaks twice until everyone has spoken once, and nobody speaks two
  weeks in a row. Talks already Confirmed/Swapped/Done are kept when you redraw.
- **Schedule**: mark a talk Confirmed/Done, swap two speakers' dates, or hand a
  talk to someone else. Changes update the calendar event automatically.
- **Calendar**: sync pending talks, re-sync everything, or download an `.ics`.

Data lives in `data/speakers.csv` and `data/schedule.csv`.
