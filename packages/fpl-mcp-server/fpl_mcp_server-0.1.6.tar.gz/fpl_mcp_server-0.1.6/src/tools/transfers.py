"""FPL Transfer Tools - MCP tools for transfer statistics and live trends."""

from pydantic import BaseModel, ConfigDict, Field

from ..client import FPLClient
from ..constants import CHARACTER_LIMIT
from ..state import store
from ..utils import (
    ResponseFormat,
    check_and_truncate,
    format_json_response,
    format_player_price,
    handle_api_error,
)
from . import mcp


class GetPlayerTransfersByGameweekInput(BaseModel):
    """Input model for getting player transfer statistics."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    player_name: str = Field(
        ...,
        description="Player name (e.g., 'Haaland', 'Salah')",
        min_length=2,
        max_length=100,
    )
    gameweek: int = Field(..., description="Gameweek number (1-38)", ge=1, le=38)


class GetTopTransferredPlayersInput(BaseModel):
    """Input model for getting top transferred players."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    limit: int = Field(default=10, description="Number of players to return (1-50)", ge=1, le=50)
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'",
    )


class GetManagerTransfersByGameweekInput(BaseModel):
    """Input model for getting manager transfers."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    team_id: int = Field(..., description="Manager's team ID (entry ID) from FPL", ge=1)
    gameweek: int = Field(..., description="Gameweek number (1-38)", ge=1, le=38)


async def _create_client():
    """Create an unauthenticated FPL client for public API access and ensure data is loaded."""
    client = FPLClient(store=store)
    await store.ensure_bootstrap_data(client)
    await store.ensure_fixtures_data(client)
    return client


@mcp.tool(
    name="fpl_get_player_transfers_by_gameweek",
    annotations={
        "title": "Get FPL Player Transfer Statistics",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def fpl_get_player_transfers_by_gameweek(
    params: GetPlayerTransfersByGameweekInput,
) -> str:
    """
    Get transfer statistics for a specific player in a specific gameweek.

    Shows transfers in, transfers out, net transfers, ownership data, and performance.
    Useful for understanding how manager sentiment towards a player changed during a
    specific gameweek and correlation with performance.

    Args:
        params (GetPlayerTransfersByGameweekInput): Validated input parameters containing:
            - player_name (str): Player name (e.g., 'Haaland', 'Salah')
            - gameweek (int): Gameweek number between 1-38

    Returns:
        str: Transfer statistics and performance for the gameweek

    Examples:
        - Check Haaland GW20: player_name="Haaland", gameweek=20
        - Salah transfers: player_name="Salah", gameweek=15

    Error Handling:
        - Returns error if player not found
        - Suggests using fpl_find_player if name ambiguous
        - Returns error if no data for gameweek
    """
    try:
        client = await _create_client()

        # Find player by name
        matches = store.find_players_by_name(params.player_name, fuzzy=True)
        if not matches:
            return f"No player found matching '{params.player_name}'. Use fpl_search_players to find the correct name."

        if len(matches) > 1 and matches[0][1] < 0.95:
            return f"Ambiguous player name. Use fpl_find_player to see all matches for '{params.player_name}'"

        player = matches[0][0]
        player_id = player.id

        # Fetch detailed summary from API
        summary_data = await client.get_element_summary(player_id)
        history = summary_data.get("history", [])

        # Find the specific gameweek in history
        gw_data = next((gw for gw in history if gw.get("round") == params.gameweek), None)

        if not gw_data:
            return f"No transfer data found for {player.web_name} in gameweek {params.gameweek}. The gameweek may not have started yet or data is unavailable."

        # Enrich with team name
        enriched_history = store.enrich_gameweek_history([gw_data])
        if enriched_history:
            gw_data = enriched_history[0]

        output = [
            f"**{player.web_name}** ({player.first_name} {player.second_name})",
            f"Team: {player.team_name} | Position: {player.position} | Price: {format_player_price(player.now_cost)}",
            "",
            f"**Gameweek {params.gameweek} Transfer Statistics:**",
            "",
            f"├─ Transfers In: {gw_data.get('transfers_in', 0):,}",
            f"├─ Transfers Out: {gw_data.get('transfers_out', 0):,}",
            f"├─ Net Transfers: {gw_data.get('transfers_balance', gw_data.get('transfers_in', 0) - gw_data.get('transfers_out', 0)):+,}",
            f"├─ Ownership at GW: {gw_data.get('selected', 0):,} teams",
            "",
            f"**Performance in GW{params.gameweek}:**",
            f"├─ Points: {gw_data.get('total_points', 0)}",
            f"├─ Minutes: {gw_data.get('minutes', 0)}",
            f"├─ xGoal: {gw_data.get('expected_goals', '0.00')} | Goals: {gw_data.get('goals_scored', 0)}",
            f"├─ xAssist: {gw_data.get('expected_assists', '0.00')} | Assists: {gw_data.get('assists', 0)}",
            f"├─ Clean Sheets: {gw_data.get('clean_sheets', 0)} | Bonus: {gw_data.get('bonus', 0)}",
        ]

        opponent_name = gw_data.get("opponent_team_short", "Unknown")
        home_away = "H" if gw_data.get("was_home") else "A"
        output.append(f"├─ Opponent: vs {opponent_name} ({home_away})")

        result = "\n".join(output)
        truncated, _ = check_and_truncate(result, CHARACTER_LIMIT)
        return truncated

    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="fpl_get_top_transferred_players",
    annotations={
        "title": "Get Top Transferred FPL Players",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def fpl_get_top_transferred_players(params: GetTopTransferredPlayersInput) -> str:
    """
    Get the most transferred in and out players for the current gameweek.

    Shows live transfer trends to identify popular moves happening right now. Uses
    real-time data from bootstrap for instant response. Essential for understanding
    the current template and finding differentials.

    Args:
        params (GetTopTransferredPlayersInput): Validated input parameters containing:
            - limit (int): Number of players to return, 1-50 (default: 10)
            - response_format (ResponseFormat): 'markdown' or 'json' (default: markdown)

    Returns:
        str: Top transferred in and out players with net transfers

    Examples:
        - Top 10: limit=10
        - Top 20: limit=20
        - Get as JSON: limit=15, response_format="json"

    Error Handling:
        - Returns error if no transfer data available
        - Returns formatted error message if current gameweek unavailable
    """
    try:
        await _create_client()
        if not store.bootstrap_data:
            return "Error: Player data not available. Please try again later."

        # Get current gameweek
        current_gw = store.get_current_gameweek()
        if not current_gw:
            return "Error: Could not determine current gameweek. Data may be unavailable."

        gameweek = current_gw.id

        # Use bootstrap data directly - instant, no API calls!
        players_with_transfers = []

        for player in store.bootstrap_data.elements:
            transfers_in = getattr(player, "transfers_in_event", 0)
            transfers_out = getattr(player, "transfers_out_event", 0)

            # Only include players with transfer activity
            if transfers_in > 0 or transfers_out > 0:
                players_with_transfers.append(
                    {
                        "player": player,
                        "transfers_in": transfers_in,
                        "transfers_out": transfers_out,
                        "net_transfers": transfers_in - transfers_out,
                        "points": getattr(player, "event_points", 0),
                    }
                )

        if not players_with_transfers:
            return f"No transfer data available for gameweek {gameweek}. The gameweek may not have started yet."

        # Sort by transfers in and out
        most_transferred_in = sorted(
            players_with_transfers, key=lambda x: x["transfers_in"], reverse=True
        )[: params.limit]
        most_transferred_out = sorted(
            players_with_transfers, key=lambda x: x["transfers_out"], reverse=True
        )[: params.limit]

        if params.response_format == ResponseFormat.JSON:
            result = {
                "gameweek": gameweek,
                "transferred_in": [
                    {
                        "rank": i + 1,
                        "player_name": data["player"].web_name,
                        "team": data["player"].team_name,
                        "position": data["player"].position,
                        "price": format_player_price(data["player"].now_cost),
                        "transfers_in": data["transfers_in"],
                        "net_transfers": data["net_transfers"],
                        "points": data["points"],
                    }
                    for i, data in enumerate(most_transferred_in)
                ],
                "transferred_out": [
                    {
                        "rank": i + 1,
                        "player_name": data["player"].web_name,
                        "team": data["player"].team_name,
                        "position": data["player"].position,
                        "price": format_player_price(data["player"].now_cost),
                        "transfers_out": data["transfers_out"],
                        "net_transfers": data["net_transfers"],
                        "points": data["points"],
                    }
                    for i, data in enumerate(most_transferred_out)
                ],
            }
            return format_json_response(result)
        else:
            output = [
                f"**Gameweek {gameweek} - Live Transfer Trends** 🔥",
                "",
                f"**Most Transferred IN (Top {min(params.limit, len(most_transferred_in))}):**",
                "",
            ]

            for i, data in enumerate(most_transferred_in, 1):
                player = data["player"]
                price = format_player_price(player.now_cost)
                output.append(
                    f"{i:2d}. {player.web_name:20s} ({player.team_name:15s} {player.position}) | "
                    f"{price} | In: {data['transfers_in']:,} | "
                    f"Net: {data['net_transfers']:+,} | {data['points']}pts"
                )

            output.extend(
                [
                    "",
                    f"**Most Transferred OUT (Top {min(params.limit, len(most_transferred_out))}):**",
                    "",
                ]
            )

            for i, data in enumerate(most_transferred_out, 1):
                player = data["player"]
                price = format_player_price(player.now_cost)
                output.append(
                    f"{i:2d}. {player.web_name:20s} ({player.team_name:15s} {player.position}) | "
                    f"{price} | Out: {data['transfers_out']:,} | "
                    f"Net: {data['net_transfers']:+,} | {data['points']}pts"
                )

            result = "\n".join(output)
            truncated, _ = check_and_truncate(result, CHARACTER_LIMIT)
            return truncated

    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="fpl_get_manager_transfers_by_gameweek",
    annotations={
        "title": "Get Manager's FPL Transfers",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def fpl_get_manager_transfers_by_gameweek(
    params: GetManagerTransfersByGameweekInput,
) -> str:
    """
    Get all transfers made by a specific manager in a specific gameweek.

    Shows which players were transferred in and out, transfer costs, and timing.
    Useful for analyzing manager strategy and understanding when/why they made moves.
    Requires manager's team ID (entry ID) which can be found in the FPL URL.

    Args:
        params (GetManagerTransfersByGameweekInput): Validated input parameters containing:
            - team_id (int): Manager's team ID (entry ID)
            - gameweek (int): Gameweek number (1-38)

    Returns:
        str: Complete transfer history for the gameweek with costs

    Examples:
        - View transfers: team_id=123456, gameweek=20
        - Check costs: team_id=789012, gameweek=15

    Error Handling:
        - Returns error if team ID invalid
        - Returns message if no transfers in gameweek
        - Returns formatted error message if API fails
    """
    try:
        client = await _create_client()

        # Fetch manager entry info to get team name
        try:
            manager_entry = await client.get_manager_entry(params.team_id)
            manager_name = f"{manager_entry.get('player_first_name', '')} {manager_entry.get('player_last_name', '')}".strip()
            team_name = manager_entry.get("name", f"Team {params.team_id}")
        except Exception:
            manager_name = f"Manager {params.team_id}"
            team_name = f"Team {params.team_id}"

        # Fetch all transfer history
        transfers_data = await client.get_manager_transfers(params.team_id)

        # Filter transfers for the specific gameweek
        gw_transfers = [t for t in transfers_data if t.get("event") == params.gameweek]

        if not gw_transfers:
            return f"No transfers found for {manager_name} in gameweek {params.gameweek}. They may have used their free transfers or rolled them over."

        output = [
            f"**{team_name}** - {manager_name}",
            f"Gameweek {params.gameweek} Transfers",
            "",
        ]

        total_cost = 0
        for i, transfer in enumerate(gw_transfers, 1):
            # Get player details
            player_in_id = transfer.get("element_in")
            player_out_id = transfer.get("element_out")

            player_in_name = store.get_player_name(player_in_id)
            player_out_name = store.get_player_name(player_out_id)

            # Get player info for prices
            player_in_info = next(
                (p for p in store.bootstrap_data.elements if p.id == player_in_id), None
            )
            player_out_info = next(
                (p for p in store.bootstrap_data.elements if p.id == player_out_id),
                None,
            )

            price_in = format_player_price(player_in_info.now_cost) if player_in_info else "£0.0m"
            price_out = (
                format_player_price(player_out_info.now_cost) if player_out_info else "£0.0m"
            )

            # Transfer details
            transfer_time = transfer.get("time", "Unknown")
            cost = transfer.get("event_cost", 0)
            total_cost += cost

            output.append(f"**Transfer {i}:**")
            output.append(
                f"OUT: {player_out_name} ({player_out_info.team_name if player_out_info else 'Unknown'} "
                f"{player_out_info.position if player_out_info else 'UNK'}) - {price_out}"
            )
            output.append(
                f"IN:  {player_in_name} ({player_in_info.team_name if player_in_info else 'Unknown'} "
                f"{player_in_info.position if player_in_info else 'UNK'}) - {price_in}"
            )
            if cost > 0:
                output.append(f"Cost: -{cost} points")
            output.append(
                f"Time: {transfer_time[:19] if transfer_time != 'Unknown' else 'Unknown'}"
            )
            output.append("")

        output.extend(
            [
                "**Summary:**",
                f"├─ Total Transfers: {len(gw_transfers)}",
                f"├─ Total Cost: -{total_cost} points"
                if total_cost > 0
                else "├─ Free Transfers Used",
            ]
        )

        result = "\n".join(output)
        truncated, _ = check_and_truncate(result, CHARACTER_LIMIT)
        return truncated

    except Exception as e:
        return handle_api_error(e)


class GetManagerChipsInput(BaseModel):
    """Input model for getting manager chip usage."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    team_id: int = Field(..., description="Manager's team ID (entry ID) from FPL", ge=1)
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'",
    )


@mcp.tool(
    name="fpl_get_manager_chips",
    annotations={
        "title": "Get Manager's Chip Usage",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def fpl_get_manager_chips(params: GetManagerChipsInput) -> str:
    """
    Get a manager's chip usage showing which chips have been used and which are still available.

    Since the 2025/2026 season, FPL provides 4 chips per half-season.

    Shows used chips with gameweek and timing, plus remaining available chips.
    Essential for strategic chip planning and recommendations.

    Args:
        params (GetManagerChipsInput): Validated input parameters containing:
            - team_id (int): Manager's team ID (entry ID)
            - response_format (ResponseFormat): 'markdown' or 'json' (default: markdown)

    Returns:
        str: Chip usage summary with used and available chips

    Examples:
        - Check chip status: team_id=123456
        - JSON format: team_id=123456, response_format="json"

    Error Handling:
        - Returns error if team ID invalid
        - Returns formatted error message if API fails
    """
    try:
        client = await _create_client()

        # Fetch manager history for used chips
        history_data = await client.get_manager_history(params.team_id)
        used_chips = history_data.get("chips", [])

        # Get all available chips from bootstrap data
        bootstrap_chips = store.bootstrap_data.chips if store.bootstrap_data else []

        # Get current gameweek to determine which chips are available
        current_gw_data = store.get_current_gameweek()
        current_gw = current_gw_data.id if current_gw_data else 1

        # Build chip availability map
        # FPL chip names: "wildcard", "freehit", "bboost", "3xc"
        chip_display_names = {
            "wildcard": "Wildcard",
            "freehit": "Free Hit",
            "bboost": "Bench Boost",
            "3xc": "Triple Captain",
        }

        # Build available chips list
        # Match used chips to specific chip instances based on gameweek used
        available_chips = []
        for chip in bootstrap_chips:
            chip_name = chip.get("name")
            start_gw = chip.get("start_event", 1)
            end_gw = chip.get("stop_event", 38)

            # Check if this specific chip instance was used
            # Match by checking if any used chip has this name and was used within this chip's GW range
            chip_used = any(
                used_chip["name"] == chip_name and start_gw <= used_chip["event"] <= end_gw
                for used_chip in used_chips
            )

            # Chip is available if: within current gameweek range AND not used
            if start_gw <= current_gw <= end_gw and not chip_used:
                available_chips.append(
                    {
                        "name": chip_name,
                        "display_name": chip_display_names.get(chip_name, chip_name.title()),
                        "start_event": start_gw,
                        "stop_event": end_gw,
                        "half": "First Half" if end_gw <= 19 else "Second Half",
                    }
                )

        if params.response_format == ResponseFormat.JSON:
            result = {
                "team_id": params.team_id,
                "current_gameweek": current_gw,
                "used_chips": [
                    {
                        "name": chip["name"],
                        "display_name": chip_display_names.get(chip["name"], chip["name"].title()),
                        "gameweek": chip["event"],
                        "time": chip["time"],
                    }
                    for chip in used_chips
                ],
                "available_chips": available_chips,
            }
            return format_json_response(result)
        else:
            # Markdown output
            output = [
                f"**Chip Usage Summary** (Team ID: {params.team_id})",
                f"Current Gameweek: {current_gw}",
                "",
                f"**Used Chips ({len(used_chips)}):**",
                "",
            ]

            if used_chips:
                # Group used chips by half
                first_half_used = [c for c in used_chips if c["event"] <= 19]
                second_half_used = [c for c in used_chips if c["event"] >= 20]

                if first_half_used:
                    output.append("  **First Half (GW1-19):**")
                    for chip in first_half_used:
                        display_name = chip_display_names.get(chip["name"], chip["name"].title())
                        gw = chip["event"]
                        time = chip["time"][:10] if chip.get("time") else "Unknown"
                        output.append(f"    ✓ {display_name} - GW{gw} | Used: {time}")
                    output.append("")

                if second_half_used:
                    output.append("  **Second Half (GW20-38):**")
                    for chip in second_half_used:
                        display_name = chip_display_names.get(chip["name"], chip["name"].title())
                        gw = chip["event"]
                        time = chip["time"][:10] if chip.get("time") else "Unknown"
                        output.append(f"    ✓ {display_name} - GW{gw} | Used: {time}")
                    output.append("")
            else:
                output.append("No chips used yet")

            output.extend(
                [
                    "",
                    f"**Available Chips ({len(available_chips)}):**",
                    "",
                ]
            )

            if available_chips:
                # Group by half
                first_half_available = [c for c in available_chips if c["half"] == "First Half"]
                second_half_available = [c for c in available_chips if c["half"] == "Second Half"]

                if first_half_available:
                    output.append("  **First Half (GW1-19):**")
                    for chip in first_half_available:
                        output.append(f"    • {chip['display_name']}")
                    output.append("")

                if second_half_available:
                    output.append("  **Second Half (GW20-38):**")
                    for chip in second_half_available:
                        output.append(f"    • {chip['display_name']}")
            else:
                output.append("All chips have been used")

            result = "\n".join(output)
            truncated, _ = check_and_truncate(result, CHARACTER_LIMIT)
            return truncated

    except Exception as e:
        return handle_api_error(e)
