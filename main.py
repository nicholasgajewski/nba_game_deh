from html import escape
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from nba_api.stats.endpoints.scheduleleaguev2 import ScheduleLeagueV2

today = datetime.now(ZoneInfo("America/New_York")).date()
season_start_year = today.year if today.month >= 7 else today.year - 1
season = f"{season_start_year}-{str(season_start_year + 1)[-2:]}"
schedule = ScheduleLeagueV2(season=season).get_dict()["leagueSchedule"]
games_today = []

for schedule_date in schedule["gameDates"]:
    scheduled_day = datetime.strptime(schedule_date["gameDate"], "%m/%d/%Y %H:%M:%S").date()
    if scheduled_day != today:
        continue

    for game in sorted(schedule_date["games"], key=lambda item: item["gameDateTimeEst"]):
        home_team = f"{game['homeTeam']['teamCity']} {game['homeTeam']['teamName']}"
        away_team = f"{game['awayTeam']['teamCity']} {game['awayTeam']['teamName']}"
        ca_broadcasters = []

        for group in ("homeTvBroadcasters", "awayTvBroadcasters", "nationalBroadcasters"):
            for broadcaster in game.get("broadcasters", {}).get(group, []):
                name = broadcaster.get("broadcasterDisplay", "")
                if name in ("SN/SN+", "TSN/TSN+", "Spectrum SportsNet", "Prime Video") and name not in ca_broadcasters:
                    ca_broadcasters.append(name)

        network_info = ", ".join(ca_broadcasters)
        if network_info:
            games_today.append({
                "matchup": f"{away_team} @ {home_team}",
                "time": game["gameStatusText"],
                "network": network_info
            })

# Print today's games
for game in games_today:
    print(f"{game['matchup']} - {game['time']} - {game['network']}")

game_rows = "\n".join(
    f"""<article class="game">
        <div>
            <h2>{escape(game['matchup'])}</h2>
            <p class="time">{escape(game['time'])}</p>
        </div>
        <p class="network">{escape(game['network'])}</p>
    </article>"""
    for game in games_today
)

if not game_rows:
    game_rows = '<p class="empty">No games scheduled today.</p>'

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Today's NBA Games</title>
    <style>
        :root {{ color-scheme: light; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
        body {{ margin: 0; background: #f4f6f8; color: #17212b; }}
        main {{ width: min(760px, calc(100% - 40px)); margin: 48px auto; }}
        header {{ border-bottom: 3px solid #d64545; margin-bottom: 24px; padding-bottom: 16px; }}
        h1 {{ margin: 0; font-family: Georgia, serif; font-size: 2rem; }}
        .eyebrow {{ margin: 0 0 8px; color: #52616b; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.08em; }}
        .game {{ display: flex; justify-content: space-between; gap: 24px; align-items: center; padding: 20px 0; border-bottom: 1px solid #d5dce1; }}
        h2 {{ margin: 0; font-size: 1.1rem; }}
        .time, .network {{ margin: 8px 0 0; color: #52616b; }}
        .network {{ max-width: 45%; text-align: right; }}
        .empty {{ padding: 24px 0; color: #52616b; }}
        @media (max-width: 520px) {{ main {{ margin: 28px auto; }} .game {{ align-items: flex-start; flex-direction: column; gap: 4px; }} .network {{ max-width: 100%; text-align: left; }} }}
    </style>
</head>
<body>
    <main>
        <header>
            <p class="eyebrow">NBA | CANADIAN BROADCASTS</p>
            <h1>Today's Games</h1>
        </header>
        {game_rows}
    </main>
</body>
</html>
"""

output_path = Path(__file__).with_name("index.html")
output_path.write_text(html, encoding="utf-8")
print(f"HTML schedule saved to {output_path}")