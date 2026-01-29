"""FPL Team Tools - MCP tools for team information and fixture analysis."""

from pydantic import BaseModel, ConfigDict, Field

from ..client import FPLClient
from ..constants import CHARACTER_LIMIT
from ..formatting import format_difficulty_indicator, format_team_details
from ..state import store
from ..utils import (
    ResponseFormat,
    check_and_truncate,
    format_json_response,
    handle_api_error,
)
from . import mcp


class GetTeamInfoInput(BaseModel):
    """Input model for getting team information."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    team_name: str = Field(
        ...,
        description="Team name or abbreviation (e.g., 'Arsenal', 'MCI', 'Liverpool')",
        min_length=2,
        max_length=50,
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable",
    )


class ListAllTeamsInput(BaseModel):
    """Input model for listing all teams."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable",
    )


class AnalyzeTeamFixturesInput(BaseModel):
    """Input model for analyzing team fixtures."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    team_name: str = Field(
        ...,
        description="Team name to analyze (e.g., 'Arsenal', 'Liverpool')",
        min_length=2,
        max_length=50,
    )
    num_gameweeks: int = Field(
        default=5, description="Number of upcoming gameweeks to analyze", ge=1, le=15
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
    name="fpl_get_team_info",
    annotations={
        "title": "Get FPL Team Information",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def fpl_get_team_info(params: GetTeamInfoInput) -> str:
    """
    Get detailed information about a specific Premier League team.

    Returns team strength ratings for home/away attack/defence, useful for assessing
    which teams have strong defensive or attacking potential.

    Args:
        params (GetTeamInfoInput): Validated input parameters containing:
            - team_name (str): Team name or abbreviation (e.g., 'Arsenal', 'MCI')
            - response_format (ResponseFormat): 'markdown' or 'json' (default: markdown)

    Returns:
        str: Detailed team information with strength ratings

    Examples:
        - Get Arsenal info: team_name="Arsenal"
        - Use abbreviation: team_name="LIV"
        - Get JSON format: team_name="Man City", response_format="json"

    Error Handling:
        - Returns error if no team found
        - Returns error if multiple teams match (asks user to be more specific)
        - Returns formatted error message if data unavailable
    """
    try:
        await _create_client()
        if not store.bootstrap_data:
            return "Error: Team data not available. Please try again later."

        matching_teams = [
            t
            for t in store.bootstrap_data.teams
            if params.team_name.lower() in t.name.lower()
            or params.team_name.lower() in t.short_name.lower()
        ]

        if not matching_teams:
            return f"No team found matching '{params.team_name}'. Try using the full team name or abbreviation."

        if len(matching_teams) > 1:
            team_list = ", ".join([f"{t.name} ({t.short_name})" for t in matching_teams])
            return f"Multiple teams found: {team_list}. Please be more specific."

        team = matching_teams[0]
        team_dict = store.get_team_by_id(team.id)

        if params.response_format == ResponseFormat.JSON:
            return format_json_response(team_dict)
        else:
            # Convert Team object to dict for formatter
            team_dict = {
                "name": team.name,
                "short_name": team.short_name,
                "strength": getattr(team, "strength", None),
                "strength_overall_home": getattr(team, "strength_overall_home", None),
                "strength_overall_away": getattr(team, "strength_overall_away", None),
                "strength_attack_home": getattr(team, "strength_attack_home", None),
                "strength_attack_away": getattr(team, "strength_attack_away", None),
                "strength_defence_home": getattr(team, "strength_defence_home", None),
                "strength_defence_away": getattr(team, "strength_defence_away", None),
            }

            result = format_team_details(team_dict)
            truncated, _ = check_and_truncate(result, CHARACTER_LIMIT)
            return truncated

    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="fpl_list_all_teams",
    annotations={
        "title": "List All FPL Teams",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def fpl_list_all_teams(params: ListAllTeamsInput) -> str:
    """
    List all Premier League teams with their basic information.

    Returns all 20 Premier League teams with their names, abbreviations, and average
    strength ratings. Useful for finding exact team names or comparing team strengths.

    Args:
        params (ListAllTeamsInput): Validated input parameters containing:
            - response_format (ResponseFormat): 'markdown' or 'json' (default: markdown)

    Returns:
        str: List of all teams with strength ratings

    Examples:
        - List all teams: response_format="markdown"
        - Get as JSON: response_format="json"

    Error Handling:
        - Returns error if team data unavailable
        - Returns formatted error message if API fails
    """
    try:
        await _create_client()
        teams = store.get_all_teams()
        if not teams:
            return "Error: Team data not available. Please try again later."

        teams_sorted = sorted(teams, key=lambda t: t["name"])

        if params.response_format == ResponseFormat.JSON:
            return format_json_response({"count": len(teams_sorted), "teams": teams_sorted})
        else:
            output = ["**Premier League Teams:**\n"]

            for team in teams_sorted:
                strength_info = ""
                if team.get("strength_overall_home") and team.get("strength_overall_away"):
                    avg_strength = (
                        team["strength_overall_home"] + team["strength_overall_away"]
                    ) / 2
                    strength_info = f" | Strength: {avg_strength:.0f}"

                output.append(f"{team['name']:20s} ({team['short_name']}){strength_info}")

            result = "\n".join(output)
            truncated, _ = check_and_truncate(result, CHARACTER_LIMIT)
            return truncated

    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="fpl_analyze_team_fixtures",
    annotations={
        "title": "Analyze FPL Team Fixtures",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def fpl_analyze_team_fixtures(params: AnalyzeTeamFixturesInput) -> str:
    """
    Analyze upcoming fixtures for a specific Premier League team to assess difficulty.

    Shows next N gameweeks with opponent strength and home/away status. Includes average
    difficulty rating and assessment. Very useful for identifying good times to bring in
    or sell team assets based on fixture difficulty.

    Args:
        params (AnalyzeTeamFixturesInput): Validated input parameters containing:
            - team_name (str): Team name to analyze (e.g., 'Arsenal', 'Liverpool')
            - num_gameweeks (int): Number of gameweeks to analyze, 1-15 (default: 5)
            - response_format (ResponseFormat): 'markdown' or 'json' (default: markdown)

    Returns:
        str: Fixture difficulty analysis with ratings and assessment

    Examples:
        - Next 5 fixtures: team_name="Arsenal"
        - Next 10 fixtures: team_name="Liverpool", num_gameweeks=10
        - Long-term view: team_name="Man City", num_gameweeks=15

    Error Handling:
        - Returns error if team not found
        - Returns error if no upcoming fixtures
        - Returns formatted error message if data unavailable
    """
    try:
        await _create_client()
        if not store.bootstrap_data or not store.fixtures_data:
            return "Error: Team or fixtures data not available. Please try again later."

        matching_teams = [
            t
            for t in store.bootstrap_data.teams
            if params.team_name.lower() in t.name.lower()
            or params.team_name.lower() in t.short_name.lower()
        ]

        if not matching_teams:
            return f"No team found matching '{params.team_name}'. Try using the full team name."

        if len(matching_teams) > 1:
            team_list = ", ".join([f"{t.name} ({t.short_name})" for t in matching_teams])
            return f"Multiple teams found: {team_list}. Please be more specific."

        team = matching_teams[0]

        current_gw = store.get_current_gameweek()
        if not current_gw:
            return "Error: Could not determine current gameweek. Data may be unavailable."

        start_gw = current_gw.id
        # Fetch extra gameweeks to ensure we get enough after filtering out finished fixtures
        end_gw = start_gw + params.num_gameweeks + 5  # Add buffer

        team_fixtures = [
            f
            for f in store.fixtures_data
            if (f.team_h == team.id or f.team_a == team.id)
            and f.event
            and start_gw <= f.event < end_gw
            and not f.finished
        ]

        if not team_fixtures:
            return f"No upcoming fixtures found for {team.name} in the next {params.num_gameweeks} gameweeks."

        # Enrich and sort fixtures
        team_fixtures_enriched = store.enrich_fixtures(team_fixtures)
        team_fixtures_sorted = sorted(team_fixtures_enriched, key=lambda x: x.get("event") or 999)

        # Limit to requested number of fixtures
        team_fixtures_sorted = team_fixtures_sorted[: params.num_gameweeks]

        if params.response_format == ResponseFormat.JSON:
            total_difficulty = sum(
                f.get(
                    "team_h_difficulty" if f.get("team_h") == team.id else "team_a_difficulty",
                    3,
                )
                for f in team_fixtures_sorted
            )
            avg_difficulty = (
                total_difficulty / len(team_fixtures_sorted) if team_fixtures_sorted else 0
            )

            result = {
                "team": {"name": team.name, "short_name": team.short_name},
                "num_fixtures": len(team_fixtures_sorted),
                "average_difficulty": round(avg_difficulty, 2),
                "assessment": "Favorable"
                if avg_difficulty < 3
                else "Moderate"
                if avg_difficulty < 3.5
                else "Difficult",
                "fixtures": [
                    {
                        "gameweek": f.get("event"),
                        "opponent": f.get("team_a_name")
                        if f.get("team_h") == team.id
                        else f.get("team_h_name"),
                        "home_away": "H" if f.get("team_h") == team.id else "A",
                        "difficulty": f.get("team_h_difficulty")
                        if f.get("team_h") == team.id
                        else f.get("team_a_difficulty"),
                        "kickoff_time": f.get("kickoff_time", "TBD"),
                    }
                    for f in team_fixtures_sorted
                ],
            }
            return format_json_response(result)
        else:
            output = [
                f"**{team.name} ({team.short_name}) - Next {len(team_fixtures_sorted)} Fixtures**\n"
            ]

            total_difficulty = 0
            for fixture in team_fixtures_sorted:
                is_home = fixture.get("team_h") == team.id
                opponent_name = (
                    fixture.get("team_a_name") if is_home else fixture.get("team_h_name", "Unknown")
                )

                difficulty = (
                    fixture.get("team_h_difficulty")
                    if is_home
                    else fixture.get("team_a_difficulty", 3)
                )
                home_away = "H" if is_home else "A"

                total_difficulty += difficulty

                difficulty_indicator = format_difficulty_indicator(difficulty)
                output.append(
                    f"├─ GW{fixture.get('event')}: vs {opponent_name} ({home_away}) | "
                    f"Diff: {difficulty_indicator} ({difficulty}/5)"
                )

            avg_difficulty = total_difficulty / len(team_fixtures_sorted)
            output.extend(
                [
                    "",
                    f"**Average Difficulty:** {avg_difficulty:.1f}/5",
                    f"**Assessment:** {'Favorable' if avg_difficulty < 3 else 'Moderate' if avg_difficulty < 3.5 else 'Difficult'} run of fixtures",
                ]
            )

            result = "\n".join(output)
            truncated, _ = check_and_truncate(result, CHARACTER_LIMIT)
            return truncated

    except Exception as e:
        return handle_api_error(e)
