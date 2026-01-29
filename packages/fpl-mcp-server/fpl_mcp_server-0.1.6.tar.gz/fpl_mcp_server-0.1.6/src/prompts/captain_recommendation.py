"""
FPL MCP Prompts - Captain Recommendation.

Prompts guide the LLM in selecting optimal captain choices from the manager's squad
using form, fixtures, xGI metrics, and opponent defensive strength.
"""

from ..tools import mcp


@mcp.prompt()
def recommend_captain(team_id: int, gameweek: int | None = None, response_format: str = "markdown") -> str:
    """
    Recommend optimal captain choices using xGI-based metrics and fixture analysis.

    This prompt guides the LLM to analyze squad players and recommend the top 3
    captain options based on form, fixtures, expected goals, and opponent strength.

    Args:
        team_id: Manager's FPL team ID
        gameweek: Target gameweek (defaults to current/next if None)
        response_format: Output format - 'markdown' (default) or 'json'
    """
    gameweek_text = f"gameweek {gameweek}" if gameweek else "the current/upcoming gameweek"
    gameweek_display = f"{gameweek}" if gameweek else "Current"

    return f"""Analyze captain options for team ID {team_id} in {gameweek_text}.
Act as an FPL Expert Analyst with 10+ years of experience. We do not play it safe; we play for points.

**OBJECTIVE: Identify top 3 captain choices using a weighted Pro-Level scoring model.**

---

## 🚦 **Workflow & Efficiency**

**DO NOT** analyze all 15 players in depth. That is inefficient.
1.  **Get Squad**: Fetch manager's team.
2.  **Shortlist**: Identify **3-5 Candidates** based on:
    *   **Price**: > £7.0m (Premiums usually haul)
    *   **Form**: > 4.0 PPG
    *   **Context**: Key talismen (e.g., Salah, Haaland, Palmer, Saka) even if form is dip.
3.  **Deep Dive**: Only fetch detailed stats (`fpl_compare_players`) for these 3-5 candidates.

---

## 📊 **Pro-Level Scoring Model (Max 100)**

Calculate the **Captain Suitability Score** using this weighted matrix:

### **1. Projected Points (Weight: 40%)**
*The core engine. Can they score specific points this week?*
*   **Metric**: Underlying stats (xG + xA) over last 5 GWs + Historical reliability.
*   **Scoring**:
    *   **40pts**: Elite stats (xGI > 0.9/match) OR consistent returns (returned in 4/5 last).
    *   **30pts**: Good stats (xGI 0.6-0.8) OR decent form.
    *   **20pts**: Average stats but good player class.
    *   **10pts**: Poor underlying stats.

### **2. Fixture Vulnerability (Weight: 30%)**
*Target specific defensive weaknesses, not just generic FDR.*
*   **Metric**: Opponent strength & Home/Away advantage.
*   **Scoring**:
    *   **30pts**: vs Weak Defense (bottom 5) + Home Game.
    *   **20pts**: vs Average Defense (Home) OR Weak Defense (Away).
    *   **10pts**: vs Strong Defense (Home).
    *   **0pts**: vs Elite Defense (Away).

### **3. Nailedness & Minutes (Weight: 20%)**
*Can they hurt us if they don't start?*
*   **Metric**: Minutes played in last 3 weeks + Status.
*   **Scoring**:
    *   **20pts**: Nailed (90 mins every game).
    *   **15pts**: Secure starter (70-80 mins).
    *   **10pts**: Rotation Risk (Pep Roulette / Early Subs).
    *   **5pts**: Returning from injury (Start uncertain).
    *   **0pts**: benched/injured (Exclude).

### **4. Explosiveness Bonus (Weight: 10%)**
*Do they have a 20-point ceiling?*
*   **Metric**: Penalties, Set Pieces, Multi-goal history.
*   **Scoring**:
    *   **10pts**: on Penalties + Hat-trick history.
    *   **5pts**: Goalscorer but no penalties.
    *   **0pts**: Defensive Midfielder / Low ceiling.

**Total Score = Sum of above factors.**

---

## ⚠️ **Critical Rules**

1.  **Risk Flags (Don't auto-exclude):**
    *   If a premium player (Price > £10.0m) has `status != 'a'` (available) or played 0 mins recently, **DO NOT** exclude them automatically.
    *   Instead, apply a **"Risk Flag"**: penalty to their *Nailedness* score but keep them in the ranking if their upside is huge.
    *   *Example:* Haaland returning from injury might play 60 mins but score 2 goals. He is a valid risky captain.

2.  **Differentials:**
    *   If scores are close (<5pts), favor the player with lower ownership (Differential) if chasing rank, or higher ownership (Shield) if protecting rank. Default to *Points Prediction*.

3.  **Ambiguity:**
    *   If stats are missing for a new signing, judge based on *Club Pedigree* and *Fixture* (Assumed 50% "Projected Points" score).

---

## 📝 **Output Format:**

**Top 3 Captain Recommendations for Gameweek {gameweek_display}**

🥇 **1. [Player Name]** (Score: [Score]/100) | Confidence: [High/Medium/Low]
   • **Projected Points**: [High/Med/Low] based on xGI & History
   • **Fixture**: [Opponent] (H/A) - Difficulty: [FDR]/5 [⭐]
   • **Nailedness**: [Secure/Risk] - [Minutes played last 3 GWs]
   • **Explosiveness**: [Penalty Duties? / Haul Potential?]

   **Why**: [2-3 sentence reasoning. Mention specific matchup weaknesses or player form.]
   **Risk**: [Any rotation risk or injury flag? If none, say "None"]

   **Confidence**: [Justification, e.g., "Clear data leader, 15pt gap to #2"]

🥈 **2. [Player Name]** (Score: .../100)
   ...

🥉 **3. [Player Name]** (Score: .../100)
   ...

---
**Confidence Key:**
• High: Complete data, clear leader
• Medium: Close competition
• Low: Uncertain data / Risk factors
```

**Use emojis for FDR:**
- FDR 1: ⭐ (very easy)
- FDR 2: ⭐⭐
- FDR 3: ⭐⭐⭐
- FDR 4: ⭐⭐⭐⭐
- FDR 5: ⭐⭐⭐⭐⭐ (very hard)

---

## 🔧 **Execution Plan**

1.  **Tool**: `fpl_get_manager_by_team_id(team_id={team_id}, gameweek={gameweek})` -> Get squad.
2.  **Tool**: `fpl_get_gameweek_fixtures` -> Scan for easy matchups.
3.  **Process**: Filter squad for Shortlist (Premiums + Form + Easy Fixture).
4.  **Tool**: `fpl_compare_players(player_names=[List of Shortlist Names])` -> Get xGI, Stats, Etc.
5.  **Compute**: Apply Scoring Model.
6.  **Output**: Generate Recommendation.

**Begin Analysis Now.**
"""
