"""
Cito API Client
"""

import requests
from typing import Optional, Dict, Any, List


class CitoAPI:
    """
    Python client for Cito API - Esports data for Call of Duty and Fortnite.

    Get your API key at https://citoapi.com

    Example:
        >>> from cito_api import CitoAPI
        >>> api = CitoAPI("your-api-key")
        >>> players = api.cod.get_players(limit=10)
    """

    BASE_URL = "https://api.citoapi.com/api/v1"

    def __init__(self, api_key: str, base_url: Optional[str] = None):
        """
        Initialize the Cito API client.

        Args:
            api_key: Your Cito API key from https://citoapi.com
            base_url: Optional custom base URL
        """
        self.api_key = api_key
        self.base_url = base_url or self.BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            "x-api-key": api_key,
            "Content-Type": "application/json"
        })

        # Initialize sub-clients
        self.cod = CodClient(self)
        self.fortnite = FortniteClient(self)

    def _request(self, method: str, endpoint: str, params: Optional[Dict] = None, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make an API request."""
        url = f"{self.base_url}{endpoint}"
        response = self.session.request(method, url, params=params, json=data)
        response.raise_for_status()
        return response.json()

    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a GET request."""
        return self._request("GET", endpoint, params=params)

    def post(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a POST request."""
        return self._request("POST", endpoint, data=data)


class CodClient:
    """Call of Duty esports API client."""

    def __init__(self, client: CitoAPI):
        self._client = client

    # Players
    def get_players(self, limit: int = 50, offset: int = 0, nationality: Optional[str] = None, team: Optional[str] = None, search: Optional[str] = None) -> Dict[str, Any]:
        """Get list of COD players."""
        params = {"limit": limit, "offset": offset}
        if nationality:
            params["nationality"] = nationality
        if team:
            params["team"] = team
        if search:
            params["search"] = search
        return self._client.get("/cod/players", params)

    def get_player(self, player_id: str) -> Dict[str, Any]:
        """Get player details by ID or IGN."""
        return self._client.get(f"/cod/players/{player_id}")

    def get_player_earnings(self, player_id: str, limit: int = 50, game: Optional[str] = None, year: Optional[int] = None) -> Dict[str, Any]:
        """Get player earnings history."""
        params = {"limit": limit}
        if game:
            params["game"] = game
        if year:
            params["year"] = year
        return self._client.get(f"/cod/players/{player_id}/earnings", params)

    def get_player_stats(self, player_id: str, season: Optional[str] = None) -> Dict[str, Any]:
        """Get player season stats."""
        params = {}
        if season:
            params["season"] = season
        return self._client.get(f"/cod/players/{player_id}/stats", params)

    # Teams/Organizations
    def get_teams(self, limit: int = 50, offset: int = 0, region: Optional[str] = None, franchise_only: bool = False) -> Dict[str, Any]:
        """Get list of COD teams/organizations."""
        params = {"limit": limit, "offset": offset}
        if region:
            params["region"] = region
        if franchise_only:
            params["franchiseOnly"] = "true"
        return self._client.get("/cod/teams", params)

    def get_team(self, slug: str) -> Dict[str, Any]:
        """Get team details by slug."""
        return self._client.get(f"/cod/teams/{slug}")

    def get_team_roster(self, slug: str, include_former: bool = False) -> Dict[str, Any]:
        """Get team roster."""
        params = {}
        if include_former:
            params["includeFormer"] = "true"
        return self._client.get(f"/cod/teams/{slug}/roster", params)

    def get_team_results(self, slug: str, limit: int = 50, game: Optional[str] = None) -> Dict[str, Any]:
        """Get team tournament results."""
        params = {"limit": limit}
        if game:
            params["game"] = game
        return self._client.get(f"/cod/teams/{slug}/results", params)

    # Tournaments
    def get_tournaments(self, limit: int = 50, offset: int = 0, game: Optional[str] = None, tier: Optional[str] = None, completed: Optional[bool] = None) -> Dict[str, Any]:
        """Get list of COD tournaments."""
        params = {"limit": limit, "offset": offset}
        if game:
            params["game"] = game
        if tier:
            params["tier"] = tier
        if completed is not None:
            params["completed"] = str(completed).lower()
        return self._client.get("/cod/tournaments", params)

    def get_tournament(self, tournament_id: str) -> Dict[str, Any]:
        """Get tournament details."""
        return self._client.get(f"/cod/tournaments/{tournament_id}")

    def get_tournament_results(self, tournament_id: str) -> Dict[str, Any]:
        """Get tournament results."""
        return self._client.get(f"/cod/tournaments/{tournament_id}/results")

    def get_tournament_matches(self, tournament_id: str, limit: int = 50, round: Optional[str] = None) -> Dict[str, Any]:
        """Get tournament matches."""
        params = {"limit": limit}
        if round:
            params["round"] = round
        return self._client.get(f"/cod/tournaments/{tournament_id}/matches", params)

    # Transfers
    def get_transfers(self, limit: int = 50, offset: int = 0, type: Optional[str] = None) -> Dict[str, Any]:
        """Get recent transfers."""
        params = {"limit": limit, "offset": offset}
        if type:
            params["type"] = type
        return self._client.get("/cod/transfers", params)

    # CDL
    def get_cdl_standings(self, season: Optional[str] = None, stage: Optional[str] = None) -> Dict[str, Any]:
        """Get CDL standings."""
        params = {}
        if season:
            params["season"] = season
        if stage:
            params["stage"] = stage
        return self._client.get("/cod/cdl/standings", params)

    def get_cdl_schedule(self, upcoming: bool = True) -> Dict[str, Any]:
        """Get CDL schedule."""
        return self._client.get("/cod/cdl/schedule", {"upcoming": str(upcoming).lower()})

    def get_cdl_live(self) -> Dict[str, Any]:
        """Get live CDL matches."""
        return self._client.get("/cod/cdl/live")

    # Leaderboards
    def get_earnings_leaderboard(self, limit: int = 50, game: Optional[str] = None, year: Optional[int] = None) -> Dict[str, Any]:
        """Get earnings leaderboard."""
        params = {"limit": limit}
        if game:
            params["game"] = game
        if year:
            params["year"] = year
        return self._client.get("/cod/leaderboards/earnings", params)

    def get_leaderboard(self, mode: str, limit: int = 50, season: Optional[str] = None) -> Dict[str, Any]:
        """Get leaderboard by mode (hardpoint, snd, control, kd, kills, damage)."""
        params = {"limit": limit}
        if season:
            params["season"] = season
        return self._client.get(f"/cod/leaderboards/{mode}", params)

    # Search
    def search(self, query: str, type: Optional[str] = None, limit: int = 20) -> Dict[str, Any]:
        """Search COD data."""
        params = {"q": query, "limit": limit}
        if type:
            params["type"] = type
        return self._client.get("/cod/search", params)


class FortniteClient:
    """Fortnite esports API client."""

    def __init__(self, client: CitoAPI):
        self._client = client

    def get_players(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Get list of Fortnite players."""
        return self._client.get("/players", {"limit": limit, "offset": offset})

    def get_player(self, player_id: str) -> Dict[str, Any]:
        """Get player details."""
        return self._client.get(f"/players/{player_id}")

    def get_teams(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Get list of Fortnite organizations."""
        return self._client.get("/orgs", {"limit": limit, "offset": offset})

    def get_team(self, slug: str) -> Dict[str, Any]:
        """Get organization details."""
        return self._client.get(f"/orgs/{slug}")

    def get_tournaments(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Get list of Fortnite tournaments."""
        return self._client.get("/tournaments", {"limit": limit, "offset": offset})

    def get_transfers(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Get Fortnite transfers."""
        return self._client.get("/transfers", {"limit": limit, "offset": offset})

    def search(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """Search Fortnite data."""
        return self._client.get("/search", {"q": query, "limit": limit})
