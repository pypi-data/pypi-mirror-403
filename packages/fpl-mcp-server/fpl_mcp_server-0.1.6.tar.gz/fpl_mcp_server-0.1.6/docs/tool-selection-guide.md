# Tool Selection Guide

This guide provides a comprehensive reference to all available tools, resources, and prompts in the FPL MCP Server.

## Quick Navigation

- [Tools](#tools) - 22 interactive functions for FPL analysis
- [Resources](#resources) - 4 URI-based data endpoints
- [Prompts](#prompts) - 8 structured analysis templates

---

## Tools

Interactive functions that perform specific FPL analysis tasks. All tools accept structured inputs and return formatted data.

### Player Tools (7 tools)

| Tool Name | Description | Key Parameters |
|-----------|-------------|----------------|
| `fpl_search_players` | Search players by name | `name`, `max_results` |
| `fpl_search_players_by_team` | Get all players from a specific team | `team_name`, `max_results` |
| `fpl_find_player` | Find player with fuzzy name matching | `player_name` |
| `fpl_get_player_details` | Comprehensive player info with fixtures and history | `player_name` |
| `fpl_compare_players` | Compare multiple players side-by-side | `player_names[]` |
| `fpl_get_top_performers` | Top 10 players by goals, xG, assists, xA, xGI | `metric`, `num_gameweeks` |
| `fpl_get_player_transfers_by_gameweek` | Transfer stats for a specific player | `player_name`, `gameweek` |

### Team Tools (3 tools)

| Tool Name | Description | Key Parameters |
|-----------|-------------|----------------|
| `fpl_get_team_info` | Team details and strength ratings | `team_name` |
| `fpl_list_all_teams` | Overview of all 20 Premier League teams | `format` |
| `fpl_analyze_team_fixtures` | Assess upcoming fixtures for a team | `team_name`, `num_gameweeks` |

### Gameweek Tools (4 tools)

| Tool Name | Description | Key Parameters |
|-----------|-------------|----------------|
| `fpl_get_current_gameweek` | Current or upcoming gameweek details | `format` |
| `fpl_get_gameweek_info` | Detailed gameweek stats and top performers | `gameweek`, `format` |
| `fpl_list_all_gameweeks` | Full season gameweek status | `format` |
| `fpl_get_fixtures_for_gameweek` | All matches in a specific gameweek | `gameweek`, `format` |

### League & Manager Tools (6 tools)

| Tool Name | Description | Key Parameters |
|-----------|-------------|----------------|
| `fpl_get_league_standings` | League rankings and points | `league_id`, `page`, `format` |
| `fpl_get_manager_gameweek_team` | Team selection via manager name + league ID | `manager_name`, `league_id`, `gameweek` |
| `fpl_get_manager_squad` | Direct access via team ID | `team_id`, `gameweek` |
| `fpl_get_manager_by_team_id` | Manager profile without league context | `team_id`, `gameweek`, `format` |
| `fpl_compare_managers` | Side-by-side team comparison | `manager1_team_id`, `manager2_team_id`, `gameweek` |
| `fpl_get_manager_chips` | View used and available chips | `team_id` |

### Transfer Tools (3 tools)

| Tool Name | Description | Key Parameters |
|-----------|-------------|----------------|
| `fpl_get_player_transfers_by_gameweek` | Transfer stats for a player | `player_name`, `gameweek` |
| `fpl_get_top_transferred_players` | Most transferred in/out right now | `limit`, `format` |
| `fpl_get_manager_transfers_by_gameweek` | Transfers made by a manager | `team_id`, `gameweek` |

### Fixtures Tools (1 tool)

| Tool Name | Description | Key Parameters |
|-----------|-------------|----------------|
| `fpl_get_fixtures_for_gameweek` | All fixtures in a gameweek | `gameweek`, `format` |

---

## Resources

URI-based resources provide efficient access to FPL data. Use these for quick data retrieval without complex analysis.

### Bootstrap Resources (4 resources)

| Resource URI | Description | Example |
|--------------|-------------|---------|
| `fpl://bootstrap/players` | All players with basic stats | `fpl://bootstrap/players` |
| `fpl://bootstrap/teams` | All teams with metadata | `fpl://bootstrap/teams` |
| `fpl://bootstrap/gameweeks` | All gameweeks with status | `fpl://bootstrap/gameweeks` |
| `fpl://current-gameweek` | Current gameweek information | `fpl://current-gameweek` |

---

## Prompts

Structured templates that guide analysis workflows. Prompts combine multiple tools and resources for comprehensive insights.

| Prompt Name | Description | Parameters | Use Case |
|-------------|-------------|------------|----------|
| `analyze_squad_performance` | Squad performance over recent gameweeks | `team_id`, `num_gameweeks` | Identify underperformers and transfer candidates |
| `analyze_team_fixtures` | Team fixture difficulty analysis | `team_name`, `num_gameweeks` | Find optimal times to invest in team assets |
| `recommend_transfers` | Transfer strategy recommendations | `team_id`, `free_transfers` | Generate transfer in/out suggestions |
| `recommend_chip_strategy` | Chip timing and strategy | `team_id` | Optimize Wildcard, Free Hit, Triple Captain, Bench Boost |
| `recommend_captain` | Top 3 captain picks with Pro-Level scoring (Weighted: xGI 40%, Fixtures 30%, Nailedness 20%, Upside 10%) | `team_id`, `gameweek`, `response_format` | Optimize weekly captain selection with weighted data-driven insights |
| `compare_players` | Side-by-side player comparison | `*player_names` | Choose between transfer targets |
| `compare_managers` | Manager team comparison | `league_name`, `gameweek`, `*manager_names` | Analyze league rivals' strategies |
| `find_league_differentials` | Find low-ownership differentials | `league_id`, `max_ownership` | Gain competitive advantage in mini-leagues |

---

## Quick Decision Guide

### Finding Players

- **Know exact name?** → `fpl_get_player_details` - Comprehensive player info with fixtures, history, and stats
- **Partial name/typos?** → `fpl_find_player` - Fuzzy matching finds players even with spelling variations
- **Search by criteria?** → `fpl_search_players` - Search by name with customizable results limit
- **Want team's squad?** → `fpl_search_players_by_team` - All players from a specific team
- **Want top by metrics?** → `fpl_get_top_performers` - Top 10 players by goals, xG, assists, xA, xGI over recent gameweeks

### Analyzing Teams

- **Basic team info?** → `fpl_get_team_info` - Team details and strength ratings
- **List all teams?** → `fpl_list_all_teams` - Overview of all 20 Premier League teams
- **Fixture difficulty?** → `fpl_analyze_team_fixtures` - Assess upcoming fixtures for a team

### Gameweek Information

- **Current gameweek?** → `fpl_get_current_gameweek` - Current or upcoming gameweek details
- **Specific gameweek stats?** → `fpl_get_gameweek_info` - Detailed stats and top performers
- **All gameweeks overview?** → `fpl_list_all_gameweeks` - Full season gameweek status
- **Gameweek fixtures?** → `fpl_get_fixtures_for_gameweek` - All matches in a specific gameweek

### League & Manager Analysis

- **League standings?** → `fpl_get_league_standings` - Rankings and points (requires league ID)
- **Manager's team (with name)?** → `fpl_get_manager_gameweek_team` - Team selection via manager name + league ID
- **Manager's team (with team ID)?** → `fpl_get_manager_squad` - Direct access via team ID, optional gameweek
- **Compare managers?** → `fpl_compare_managers` - Side-by-side team comparison
- **Manager transfers?** → `fpl_get_manager_transfers_by_gameweek` - Transfers made by a manager

### Transfer Intelligence

- **Player transfer trends?** → `fpl_get_player_transfers_by_gameweek` - Transfer stats for a player
- **Current trends?** → `fpl_get_top_transferred_players` - Most transferred in/out right now
- **Manager chip usage?** → `fpl_get_manager_chips` - View used and available chips (2025/26 half-season system)
