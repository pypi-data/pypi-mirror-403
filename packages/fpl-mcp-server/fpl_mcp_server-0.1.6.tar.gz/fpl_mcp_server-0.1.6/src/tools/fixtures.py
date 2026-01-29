"""FPL Fixtures Tools - MCP tools for fixture information and analysis."""

from pydantic import BaseModel, ConfigDict, Field

from ..client import FPLClient
from ..constants import CHARACTER_LIMIT
from ..state import store
from ..utils import (
    ResponseFormat,
    check_and_truncate,
    format_json_response,
    handle_api_error,
)
from . import mcp


class GetFixturesForGameweekInput(BaseModel):
    """Input model for getting fixtures for a gameweek."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    gameweek: int = Field(
        ..., description="Gameweek number to get fixtures for (1-38)", ge=1, le=38
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable",
    )


async def _create_client():
    """Create an unauthenticated FPL client for public API access and ensure data is loaded."""
    client = FPLClient(store=store)
    await store.ensure_bootstrap_data(client)
    await store.ensure_fixtures_data(client)
    return client


@mcp.tool(
    name="fpl_get_fixtures_for_gameweek",
    annotations={
        "title": "Get FPL Fixtures for Gameweek",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def fpl_get_fixtures_for_gameweek(params: GetFixturesForGameweekInput) -> str:
    """
    Get all Premier League fixtures for a specific gameweek.

    Returns complete fixture list with team names, kickoff times, scores (if finished),
    and difficulty ratings for both teams. Useful for planning transfers based on
    fixture difficulty and understanding upcoming matches.

    Args:
        params (GetFixturesForGameweekInput): Validated input parameters containing:
            - gameweek (int): Gameweek number between 1-38
            - response_format (ResponseFormat): 'markdown' or 'json' (default: markdown)

    Returns:
        str: Complete fixture list with times and difficulty ratings

    Examples:
        - View GW10 fixtures: gameweek=10
        - Check upcoming matches: gameweek=15
        - Get as JSON: gameweek=20, response_format="json"

    Error Handling:
        - Returns error if gameweek number invalid (must be 1-38)
        - Returns error if no fixtures found for gameweek
        - Returns formatted error message if data unavailable
    """
    try:
        await _create_client()
        if not store.fixtures_data:
            return "Error: Fixtures data not available. Please try again later."

        gw_fixtures = [f for f in store.fixtures_data if f.event == params.gameweek]

        if not gw_fixtures:
            return f"No fixtures found for gameweek {params.gameweek}. This gameweek may not exist or fixtures may not be scheduled yet."

        # Enrich fixtures with team names
        gw_fixtures_enriched = store.enrich_fixtures(gw_fixtures)
        gw_fixtures_sorted = sorted(gw_fixtures_enriched, key=lambda x: x.get("kickoff_time") or "")

        if params.response_format == ResponseFormat.JSON:
            result = {
                "gameweek": params.gameweek,
                "fixture_count": len(gw_fixtures_sorted),
                "fixtures": [
                    {
                        "home_team": fixture.get("team_h_name"),
                        "home_team_short": fixture.get("team_h_short"),
                        "away_team": fixture.get("team_a_name"),
                        "away_team_short": fixture.get("team_a_short"),
                        "kickoff_time": fixture.get("kickoff_time"),
                        "finished": fixture.get("finished"),
                        "home_score": fixture.get("team_h_score")
                        if fixture.get("finished")
                        else None,
                        "away_score": fixture.get("team_a_score")
                        if fixture.get("finished")
                        else None,
                        "home_difficulty": fixture.get("team_h_difficulty"),
                        "away_difficulty": fixture.get("team_a_difficulty"),
                    }
                    for fixture in gw_fixtures_sorted
                ],
            }
            return format_json_response(result)
        else:
            output = [
                f"**Gameweek {params.gameweek} Fixtures ({len(gw_fixtures_enriched)} matches)**\n"
            ]

            for fixture in gw_fixtures_sorted:
                home_name = fixture.get("team_h_short", "Unknown")
                away_name = fixture.get("team_a_short", "Unknown")

                status = "✓" if fixture.get("finished") else "○"
                score = (
                    f"{fixture.get('team_h_score')}-{fixture.get('team_a_score')}"
                    if fixture.get("finished")
                    else "vs"
                )
                kickoff = (
                    fixture.get("kickoff_time", "")[:16].replace("T", " ")
                    if fixture.get("kickoff_time")
                    else "TBD"
                )

                output.append(
                    f"{status} {home_name} {score} {away_name} | "
                    f"Kickoff: {kickoff} | "
                    f"Difficulty: H:{fixture.get('team_h_difficulty')} A:{fixture.get('team_a_difficulty')}"
                )

            result = "\n".join(output)
            truncated, _ = check_and_truncate(result, CHARACTER_LIMIT)
            return truncated

    except Exception as e:
        return handle_api_error(e)
