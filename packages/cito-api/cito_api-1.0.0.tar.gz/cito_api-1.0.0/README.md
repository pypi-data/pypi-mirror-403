# Cito API - Python SDK

Official Python SDK for [Cito API](https://citoapi.com) - the esports data API for Call of Duty and Fortnite.

## Installation

```bash
pip install cito-api
```

## Quick Start

```python
from cito_api import CitoAPI

# Initialize with your API key
api = CitoAPI("your-api-key")

# Get COD players
players = api.cod.get_players(limit=10)
print(players)

# Get a specific player
player = api.cod.get_player("Shotzzy")
print(player)

# Get CDL standings
standings = api.cod.get_cdl_standings()
print(standings)
```

## Features

### Call of Duty Esports

- **Players**: Get player profiles, stats, earnings, and career history
- **Teams**: CDL franchises, rosters, tournament results
- **Tournaments**: CDL Majors, Challengers events, match results
- **Transfers**: Roster moves and player transfers
- **CDL Live**: Real-time standings, schedules, live matches
- **Leaderboards**: Earnings, K/D, hardpoint time, S&D stats

### Fortnite Esports

- **Players**: Pro player profiles and earnings
- **Organizations**: Team rosters and results
- **Tournaments**: FNCS, cash cups, and major events
- **Transfers**: Roster changes

## API Reference

### COD Endpoints

```python
# Players
api.cod.get_players(limit=50, nationality="US", team="optic")
api.cod.get_player("player-id")
api.cod.get_player_earnings("player-id")
api.cod.get_player_stats("player-id", season="2024")

# Teams
api.cod.get_teams(limit=50, franchise_only=True)
api.cod.get_team("optic-texas")
api.cod.get_team_roster("optic-texas")
api.cod.get_team_results("optic-texas")

# Tournaments
api.cod.get_tournaments(game="bo6", tier="S")
api.cod.get_tournament("tournament-id")
api.cod.get_tournament_results("tournament-id")
api.cod.get_tournament_matches("tournament-id")

# Transfers
api.cod.get_transfers(type="transfer")

# CDL
api.cod.get_cdl_standings()
api.cod.get_cdl_schedule(upcoming=True)
api.cod.get_cdl_live()

# Leaderboards
api.cod.get_earnings_leaderboard(limit=100)
api.cod.get_leaderboard("hardpoint")
api.cod.get_leaderboard("snd")
api.cod.get_leaderboard("kd")

# Search
api.cod.search("Shotzzy", type="players")
```

### Fortnite Endpoints

```python
api.fortnite.get_players(limit=50)
api.fortnite.get_player("player-id")
api.fortnite.get_teams()
api.fortnite.get_tournaments()
api.fortnite.search("Bugha")
```

## Get Your API Key

Sign up at [citoapi.com](https://citoapi.com) to get your free API key.

## Links

- Website: https://citoapi.com
- Documentation: https://docs.citoapi.com
- RapidAPI: https://rapidapi.com/citoapi

## License

MIT License
