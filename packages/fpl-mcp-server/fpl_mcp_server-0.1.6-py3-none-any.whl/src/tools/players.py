"""FPL Player Tools - MCP tools for player search, analysis, and comparison."""

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..client import FPLClient
from ..constants import CHARACTER_LIMIT, PlayerPosition
from ..formatting import format_player_details
from ..state import store
from ..utils import (
    ResponseFormat,
    check_and_truncate,
    format_json_response,
    format_player_price,
    format_player_status,
    format_status_indicator,
    handle_api_error,
)
from . import mcp


class SearchPlayersInput(BaseModel):
    """Input model for searching players by name."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    name_query: str = Field(
        ...,
        description="Player name to search for (e.g., 'Salah', 'Haaland', 'Son')",
        min_length=2,
        max_length=100,
    )
    limit: int | None = Field(
        default=10, description="Maximum number of results to return", ge=1, le=50
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable",
    )


class SearchPlayersByTeamInput(BaseModel):
    """Input model for searching players by team."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    team_name: str = Field(
        ...,
        description="Team name to search for (e.g., 'Arsenal', 'Liverpool', 'Man City')",
        min_length=2,
        max_length=50,
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable",
    )


class FindPlayerInput(BaseModel):
    """Input for finding a player with fuzzy matching."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    player_name: str = Field(
        ...,
        description="Player name with fuzzy matching support (e.g., 'Haalnd' will match 'Haaland')",
        min_length=2,
        max_length=100,
    )


class GetPlayerDetailsInput(BaseModel):
    """Input model for getting player details."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    player_name: str = Field(
        ...,
        description="Player name (e.g., 'Mohamed Salah', 'Erling Haaland')",
        min_length=2,
        max_length=100,
    )


class ComparePlayersInput(BaseModel):
    """Input model for comparing multiple players."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    player_names: list[str] = Field(
        ...,
        description="List of 2-5 player names to compare (e.g., ['Salah', 'Saka', 'Palmer'])",
        min_length=2,
        max_length=5,
    )

    @field_validator("player_names")
    @classmethod
    def validate_player_names(cls, v: list[str]) -> list[str]:
        if len(v) < 2:
            raise ValueError("Must provide at least 2 players to compare")
        if len(v) > 5:
            raise ValueError("Cannot compare more than 5 players at once")
        return v


class GetTopPlayersByMetricInput(BaseModel):
    """Input model for getting top players by various metrics over last N gameweeks."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    num_gameweeks: int = Field(
        default=5,
        description="Number of recent gameweeks to analyze (1-10)",
        ge=1,
        le=10,
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable",
    )


async def _create_client():
    """Create an unauthenticated FPL client for public API access and ensure data is loaded."""
    client = FPLClient(store=store)
    # Ensure bootstrap data is loaded
    await store.ensure_bootstrap_data(client)
    # Ensure fixtures data is loaded
    await store.ensure_fixtures_data(client)
    return client


async def _aggregate_player_stats_from_fixtures(client: FPLClient, num_gameweeks: int) -> dict:
    """
    Aggregate player statistics from finished fixtures over the last N gameweeks.

    Args:
        client: FPL client instance
        num_gameweeks: Number of recent gameweeks to analyze

    Returns:
        Dictionary with aggregated stats by metric and player info
    """
    import asyncio
    from collections import defaultdict

    # Get current gameweek
    current_gw = store.get_current_gameweek()
    if not current_gw:
        return {}

    current_gw_id = current_gw.id

    # Determine gameweek range
    start_gw = max(1, current_gw_id - num_gameweeks)
    end_gw = current_gw_id - 1  # Only include finished gameweeks

    # Filter fixtures to the target gameweek range and finished status
    if not store.fixtures_data:
        return {}

    target_fixtures = [
        f
        for f in store.fixtures_data
        if f.event is not None and start_gw <= f.event <= end_gw and f.finished
    ]

    if not target_fixtures:
        return {
            "gameweek_range": f"GW {start_gw}-{end_gw}",
            "fixtures_analyzed": 0,
            "error": "No finished fixtures found in the specified gameweek range",
        }

    # Aggregate stats by player
    player_stats = defaultdict(
        lambda: {
            "goals_scored": 0,
            "assists": 0,
            "expected_goals": 0.0,
            "expected_assists": 0.0,
            "expected_goal_involvements": 0.0,
            "defensive_contribution": 0,
            "matches_played": 0,
        }
    )

    # Fetch fixture stats concurrently (with a reasonable limit to avoid overwhelming the API)
    async def fetch_fixture_stats(fixture_id: int):
        try:
            return await client.get_fixture_stats(fixture_id)
        except Exception:
            # Silently skip fixtures that fail to fetch
            return None

    # Fetch fixture stats in batches of 10 to avoid overwhelming the API
    batch_size = 10
    fixture_ids = [f.id for f in target_fixtures]

    for i in range(0, len(fixture_ids), batch_size):
        batch = fixture_ids[i : i + batch_size]
        results = await asyncio.gather(
            *[fetch_fixture_stats(fid) for fid in batch], return_exceptions=True
        )

        for fixture_stats in results:
            if fixture_stats and isinstance(fixture_stats, dict):
                # Process both home ('h') and away ('a') players
                for team_key in ["h", "a"]:
                    for player_stat in fixture_stats.get(team_key, []):
                        element_id = player_stat.get("element")
                        if not element_id or player_stat.get("minutes", 0) == 0:
                            continue

                        stats = player_stats[element_id]
                        stats["goals_scored"] += player_stat.get("goals_scored", 0)
                        stats["assists"] += player_stat.get("assists", 0)
                        stats["expected_goals"] += float(player_stat.get("expected_goals", "0.0"))
                        stats["expected_assists"] += float(
                            player_stat.get("expected_assists", "0.0")
                        )
                        stats["expected_goal_involvements"] += float(
                            player_stat.get("expected_goal_involvements", "0.0")
                        )
                        stats["defensive_contribution"] += player_stat.get(
                            "defensive_contribution", 0
                        )
                        if player_stat.get("minutes", 0) > 0:
                            stats["matches_played"] += 1

    # Enrich with player details and sort by each metric
    metrics = {
        "goals_scored": [],
        "expected_goals": [],
        "assists": [],
        "expected_assists": [],
        "expected_goal_involvements": [],
        "defensive_contribution": [],
    }

    for element_id, stats in player_stats.items():
        player = store.get_player_by_id(element_id)
        if not player:
            continue

        player_data = {
            "element_id": element_id,
            "name": player.web_name,
            "full_name": f"{player.first_name} {player.second_name}",
            "team": player.team_name,
            "position": player.position,
            "matches_played": stats["matches_played"],
        }

        # Add to each metric list with the stat value
        for metric in metrics:
            metric_value = stats[metric]
            if metric_value > 0:  # Only include players with non-zero stats
                metrics[metric].append({**player_data, "value": metric_value})

    # Sort each metric list by value (descending) and take top 10
    for metric in metrics:
        metrics[metric] = sorted(metrics[metric], key=lambda x: x["value"], reverse=True)[:10]

    return {
        "gameweek_range": f"GW {start_gw}-{end_gw}",
        "fixtures_analyzed": len(target_fixtures),
        "metrics": metrics,
    }


@mcp.tool(
    name="fpl_search_players",
    annotations={
        "title": "Search FPL Players",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def fpl_search_players(params: SearchPlayersInput) -> str:
    """
    Search for Fantasy Premier League players by name.

    Returns basic player information including price, form, and stats. Use player names
    (not IDs) for all operations. Supports partial name matching.

    Args:
        params (SearchPlayersInput): Validated input parameters containing:
            - name_query (str): Player name to search (e.g., 'Salah', 'Haaland')
            - limit (Optional[int]): Max results to return, 1-50 (default: 10)
            - response_format (ResponseFormat): 'markdown' or 'json' (default: markdown)

    Returns:
        str: Formatted player search results

    Examples:
        - Search for Egyptian players: name_query="Salah"
        - Find strikers named Kane: name_query="Kane"
        - Get top 20 results: name_query="Son", limit=20

    Error Handling:
        - Returns "No players found" if no matches
        - Returns formatted error message if API fails
    """
    try:
        await _create_client()
        if not store.bootstrap_data:
            return "Error: Player data not available. Please try again later."

        # Use bootstrap data which has all attributes
        players = store.bootstrap_data.elements
        matches = [p for p in players if params.name_query.lower() in p.web_name.lower()]

        if not matches:
            return f"No players found matching '{params.name_query}'. Try a different search term."

        # Limit results
        matches = matches[: params.limit]

        if params.response_format == ResponseFormat.JSON:
            result = {
                "query": params.name_query,
                "count": len(matches),
                "players": [
                    {
                        "name": p.web_name,
                        "full_name": f"{p.first_name} {p.second_name}",
                        "team": p.team_name,
                        "position": p.position,
                        "price": format_player_price(p.now_cost),
                        "form": str(p.form),
                        "points_per_game": str(p.points_per_game),
                        "status": p.status,
                        "news": p.news or None,
                    }
                    for p in matches
                ],
            }
            return format_json_response(result)
        else:
            output = [
                f"# Player Search Results: '{params.name_query}'",
                f"\nFound {len(matches)} players:\n",
            ]
            for p in matches:
                price = format_player_price(p.now_cost)
                status_ind = format_status_indicator(p.status, p.news)
                output.append(
                    f"├─ **{p.web_name}** ({p.team_name}) | {price} | Form: {p.form} | PPG: {p.points_per_game}{status_ind}"
                )

            result = "\n".join(output)
            truncated, was_truncated = check_and_truncate(
                result,
                CHARACTER_LIMIT,
                "Use a more specific name_query to narrow results",
            )
            return truncated

    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="fpl_search_players_by_team",
    annotations={
        "title": "Search FPL Players by Team",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def fpl_search_players_by_team(params: SearchPlayersByTeamInput) -> str:
    """
    Search for all Fantasy Premier League players from a specific team.

    Returns all players from the team organized by position, with prices, form, and stats.
    Useful for analyzing team squads or finding budget options from specific teams.

    Args:
        params (SearchPlayersByTeamInput): Validated input parameters containing:
            - team_name (str): Team name (e.g., 'Arsenal', 'Liverpool', 'Man City')
            - response_format (ResponseFormat): 'markdown' or 'json' (default: markdown)

    Returns:
        str: Formatted team squad listing organized by position

    Examples:
        - Get Arsenal squad: team_name="Arsenal"
        - Search by short name: team_name="MCI"
        - Get Liverpool in JSON: team_name="Liverpool", response_format="json"

    Error Handling:
        - Returns error if no team found
        - Returns error if multiple teams match (asks user to be more specific)
        - Returns formatted error message if API fails
    """
    try:
        await _create_client()
        if not store.bootstrap_data:
            return "Error: Player data not available. Please try again later."

        matching_teams = [
            t
            for t in store.bootstrap_data.teams
            if params.team_name.lower() in t.name.lower()
            or params.team_name.lower() in t.short_name.lower()
        ]

        if not matching_teams:
            return f"No teams found matching '{params.team_name}'. Try using the full team name or abbreviation."

        if len(matching_teams) > 1:
            team_list = ", ".join([f"{t.name} ({t.short_name})" for t in matching_teams])
            return f"Multiple teams found: {team_list}. Please be more specific."

        team = matching_teams[0]
        players = [p for p in store.bootstrap_data.elements if p.team == team.id]

        if not players:
            return f"No players found for {team.name}. This may be a data issue."

        # Sort by position and price
        position_order = {
            PlayerPosition.GOALKEEPER.value: 1,
            PlayerPosition.DEFENDER.value: 2,
            PlayerPosition.MIDFIELDER.value: 3,
            PlayerPosition.FORWARD.value: 4,
        }
        players_sorted = sorted(
            players,
            key=lambda p: (position_order.get(p.position or "ZZZ", 5), -p.now_cost),
        )

        if params.response_format == ResponseFormat.JSON:
            result = {
                "team": {"name": team.name, "short_name": team.short_name},
                "player_count": len(players_sorted),
                "players": [
                    {
                        "name": p.web_name,
                        "full_name": f"{p.first_name} {p.second_name}",
                        "position": p.position,
                        "price": format_player_price(p.now_cost),
                        "form": str(p.form),
                        "points_per_game": str(p.points_per_game),
                        "status": p.status,
                        "news": p.news or None,
                    }
                    for p in players_sorted
                ],
            }
            return format_json_response(result)
        else:
            output = [f"**{team.name} ({team.short_name}) Squad:**\n"]

            current_position = None
            for p in players_sorted:
                if p.position != current_position:
                    current_position = p.position
                    output.append(f"\n**{current_position}:**")

                price = format_player_price(p.now_cost)
                status_ind = format_status_indicator(p.status, p.news)

                output.append(
                    f"├─ {p.web_name:20s} | {price} | "
                    f"Form: {p.form:4s} | PPG: {p.points_per_game:4s}{status_ind}"
                )

            result = "\n".join(output)
            truncated, _ = check_and_truncate(result, CHARACTER_LIMIT)
            return truncated

    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="fpl_find_player",
    annotations={
        "title": "Find FPL Player with Fuzzy Matching",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def fpl_find_player(params: FindPlayerInput) -> str:
    """
    Find a Fantasy Premier League player by name with intelligent fuzzy matching.

    Handles variations in spelling, partial names, and common nicknames. If multiple
    players match, returns disambiguation options. More forgiving than exact search.

    Args:
        params (FindPlayerInput): Validated input parameters containing:
            - player_name (str): Player name with fuzzy support (e.g., 'Haalnd' matches 'Haaland')

    Returns:
        str: Player details if unique match, or list of matching players if ambiguous

    Examples:
        - Find with typo: player_name="Haalnd" (finds Haaland)
        - Partial name: player_name="Mo Salah" (finds Mohamed Salah)
        - Surname only: player_name="Son" (finds Son Heung-min)

    Error Handling:
        - Returns helpful message if no players found
        - Returns disambiguation list if multiple matches
        - Returns formatted error message if API fails
    """
    try:
        await _create_client()
        if not store.bootstrap_data:
            return "Error: Player data not available. Please try again later."

        matches = store.find_players_by_name(params.player_name, fuzzy=True)

        if not matches:
            return f"No players found matching '{params.player_name}'. Try a different spelling or use the player's surname."

        if len(matches) == 1 or (
            matches[0][1] >= 0.95 and len(matches) > 1 and matches[0][1] - matches[1][1] > 0.2
        ):
            player = matches[0][0]
            return format_player_details(player)

        # Multiple matches - show disambiguation
        output = [f"Found {len(matches)} players matching '{params.player_name}':\n"]

        for player, _score in matches[:10]:
            price = format_player_price(player.now_cost)
            status_ind = format_status_indicator(player.status, player.news)

            output.append(
                f"├─ {player.first_name} {player.second_name} ({player.web_name}) - "
                f"{player.team_name} {player.position} | {price} | "
                f"Form: {player.form} | PPG: {player.points_per_game}{status_ind}"
            )

        output.append("\nPlease use the full name or be more specific for detailed information.")
        result = "\n".join(output)
        truncated, _ = check_and_truncate(result, CHARACTER_LIMIT)
        return truncated

    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="fpl_get_player_details",
    annotations={
        "title": "Get FPL Player Details",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def fpl_get_player_details(params: GetPlayerDetailsInput) -> str:
    """
    Get comprehensive information about a specific Fantasy Premier League player.

    Returns detailed player information including price, form, team, position,
    upcoming fixtures with difficulty ratings, recent gameweek performance,
    popularity, and season stats. Most comprehensive player tool.

    Args:
        params (GetPlayerDetailsInput): Validated input parameters containing:
            - player_name (str): Player name (e.g., 'Mohamed Salah', 'Erling Haaland')

    Returns:
        str: Comprehensive player information with fixtures, form, and stats

    Examples:
        - Get player info: player_name="Mohamed Salah"
        - Check fixtures: player_name="Bukayo Saka"
        - Review form: player_name="Erling Haaland"

    Error Handling:
        - Returns error if player not found
        - Suggests using fpl_find_player if name is ambiguous
        - Returns formatted error message if API fails
    """
    try:
        client = await _create_client()
        matches = store.find_players_by_name(params.player_name, fuzzy=True)

        if not matches:
            return f"No player found matching '{params.player_name}'. Use fpl_search_players to find the correct name."

        if len(matches) > 1 and matches[0][1] < 0.95:
            return f"Ambiguous player name. Use fpl_find_player to see all matches for '{params.player_name}'"

        player = matches[0][0]
        player_id = player.id

        # Fetch detailed summary from API including fixtures and history
        summary_data = await client.get_element_summary(player_id)

        # Enrich history and fixtures with team names
        history = summary_data.get("history", [])
        history = store.enrich_gameweek_history(history)

        fixtures = summary_data.get("fixtures", [])
        fixtures = store.enrich_fixtures(fixtures)

        # Format with comprehensive data
        result = format_player_details(player, history, fixtures)
        truncated, _ = check_and_truncate(result, CHARACTER_LIMIT)
        return truncated

    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="fpl_compare_players",
    annotations={
        "title": "Compare FPL Players",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def fpl_compare_players(params: ComparePlayersInput) -> str:
    """
    Compare multiple Fantasy Premier League players side-by-side.

    Provides detailed comparison of 2-5 players including their stats, prices, form,
    and other key metrics. Useful for making transfer decisions.

    Args:
        params (ComparePlayersInput): Validated input parameters containing:
            - player_names (list[str]): 2-5 player names to compare

    Returns:
        str: Side-by-side comparison of players in markdown format

    Examples:
        - Compare wingers: player_names=["Salah", "Saka", "Palmer"]
        - Compare strikers: player_names=["Haaland", "Isak"]
        - Compare for transfers: player_names=["Son", "Maddison", "Odegaard"]

    Error Handling:
        - Returns error if fewer than 2 or more than 5 players provided
        - Returns error if any player name is ambiguous
        - Returns formatted error message if API fails
    """
    try:
        await _create_client()
        if not store.bootstrap_data:
            return "Error: Player data not available. Please try again later."

        players_to_compare = []
        ambiguous = []

        for name in params.player_names:
            matches = store.find_players_by_name(name, fuzzy=True)

            if not matches:
                return f"Error: No player found matching '{name}'. Use fpl_search_players to find the correct name."

            if len(matches) == 1 or (
                matches[0][1] >= 0.95 and len(matches) > 1 and matches[0][1] - matches[1][1] > 0.2
            ):
                players_to_compare.append(matches[0][0])
            else:
                ambiguous.append((name, matches[:3]))

        if ambiguous:
            output = ["Cannot compare - ambiguous player names:\n"]
            for name, matches in ambiguous:
                output.append(f"\n'{name}' could be:")
                for player, _score in matches:
                    output.append(
                        f"  - {player.first_name} {player.second_name} ({player.team_name})"
                    )
            output.append("\nPlease use more specific names or full names.")
            return "\n".join(output)

        output = [f"**Player Comparison ({len(players_to_compare)} players)**\n"]
        output.append("=" * 80)

        for player in players_to_compare:
            price = format_player_price(player.now_cost)
            status_ind = format_status_indicator(player.status, player.news)
            full_status = format_player_status(player.status)

            output.extend(
                [
                    f"\n**{player.web_name}** ({player.first_name} {player.second_name})",
                    f"├─ Team: {player.team_name} | Position: {player.position}",
                    f"├─ Price: {price}",
                    f"├─ Form: {player.form} | Points per Game: {player.points_per_game}",
                    f"├─ Total Points: {getattr(player, 'total_points', 'N/A')}",
                    f"├─ Status: {full_status}{status_ind}",
                ]
            )

            if player.news:
                output.append(f"├─ News: {player.news}")

            # Popularity stats
            if hasattr(player, "selected_by_percent"):
                output.append(f"├─ Selected by: {getattr(player, 'selected_by_percent', 'N/A')}%")

            if hasattr(player, "minutes"):
                output.append(f"├─ Minutes: {getattr(player, 'minutes', 'N/A')}")

            # Detailed Season Statistics
            output.extend(
                [
                    f"├─ Goals: {getattr(player, 'goals_scored', 0)} | xG: {getattr(player, 'expected_goals', '0.00')}",
                    f"├─ Assists: {getattr(player, 'assists', 0)} | xA: {getattr(player, 'expected_assists', '0.00')}",
                    f"├─ BPS: {getattr(player, 'bps', 0)} | Bonus: {getattr(player, 'bonus', 0)}",
                    f"├─ Clean Sheets: {getattr(player, 'clean_sheets', 0)}",
                    f"├─ Defensive Contribution: {getattr(player, 'defensive_contribution', 0)}",
                    f"├─ Yellow Cards: {getattr(player, 'yellow_cards', 0)} | Red Cards: {getattr(player, 'red_cards', 0)}",
                ]
            )

            output.append("=" * 80)

        result = "\n".join(output)
        truncated, _ = check_and_truncate(result, CHARACTER_LIMIT)
        return truncated

    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="fpl_get_top_performers",
    annotations={
        "title": "Get Top FPL Performers",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def fpl_get_top_performers(params: GetTopPlayersByMetricInput) -> str:
    """
    Get top 10 Fantasy Premier League performers over recent gameweeks.

    Analyzes player performance over the last N gameweeks and returns the top 10 players for
    each metric: Goals, Expected Goals (xG), Assists, Expected Assists (xA), and
    Expected Goal Involvements (xGI). Perfect for identifying in-form players for transfers.

    Args:
        params (GetTopPlayersByMetricInput): Validated input parameters containing:
            - num_gameweeks (int): Number of recent gameweeks to analyze, 1-10 (default: 5)
            - response_format (ResponseFormat): 'markdown' or 'json' (default: markdown)

    Returns:
        str: Top 10 players for each metric with their stats and team info

    Examples:
        - Last 5 gameweeks: num_gameweeks=5
        - Last 10 gameweeks: num_gameweeks=10
        - Get as JSON: num_gameweeks=5, response_format="json"

    Error Handling:
        - Returns error if no finished fixtures in range
        - Gracefully handles API failures for individual fixtures
        - Returns formatted error message if data unavailable

    Note:
        This tool might take a few seconds to complete due to the number of
        data points it needs to process.
    """
    try:
        client = await _create_client()

        # Aggregate stats from fixtures
        result = await _aggregate_player_stats_from_fixtures(client, params.num_gameweeks)

        if "error" in result:
            return f"Error: {result['error']}\nGameweek range: {result.get('gameweek_range', 'Unknown')}"

        if params.response_format == ResponseFormat.JSON:
            return format_json_response(result)
        else:
            # Format as markdown
            output = [
                f"# Top Performers ({result['gameweek_range']})\n",
            ]

            metric_names = {
                "goals_scored": "⚽ Goals Scored",
                "expected_goals": "📊 Expected Goals (xG)",
                "assists": "🎯 Assists",
                "expected_assists": "📈 Expected Assists (xA)",
                "expected_goal_involvements": "🔥 Expected Goal Involvements (xGI)",
                "defensive_contribution": "🛡️ Defensive Contribution",
            }

            for metric_key, metric_name in metric_names.items():
                players = result["metrics"].get(metric_key, [])
                if not players:
                    continue

                output.append(f"\n## {metric_name}\n")

                for i, player in enumerate(players, 1):
                    value = player["value"]
                    # Format value based on metric type
                    if metric_key in ("goals_scored", "assists", "defensive_contribution"):
                        value_str = f"{int(value)}"
                    else:
                        value_str = f"{value:.2f}"

                    output.append(
                        f"{i}. **{player['name']}** ({player['team']} - {player['position']}) | "
                        f"{value_str} | {player['matches_played']} matches"
                    )

            result_text = "\n".join(output)
            truncated, _ = check_and_truncate(result_text, CHARACTER_LIMIT)
            return truncated

    except Exception as e:
        return handle_api_error(e)
