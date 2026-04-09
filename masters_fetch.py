"""
Masters Pool - ESPN Data Fetcher
Run this in Jupyter Lab to fetch live Masters scores and save to scores.json
Place scores.json in the same folder as index.html (your GitHub Pages repo)
"""

import requests
import json
from datetime import datetime

# ESPN undocumented golf API
# tournamentId for Masters 2026 — update this each year if needed
# To find the ID: go to espn.com/golf/leaderboard, click Masters, grab the ID from the URL
MASTERS_TOURNAMENT_ID = "401811941"  # Update each year - this is the 2026 Masters ID

ESPN_URL = f"https://site.api.espn.com/apis/site/v2/sports/golf/leaderboard?event={MASTERS_TOURNAMENT_ID}"

def fetch_masters_scores():
    """Fetch live Masters leaderboard from ESPN API"""
    print(f"Fetching Masters data from ESPN... ({datetime.now().strftime('%H:%M:%S')})")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    resp = requests.get(ESPN_URL, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    
    players = []
    
    try:
        competitions = data["events"][0]["competitions"][0]["competitors"]
    except (KeyError, IndexError) as e:
        print(f"Error parsing ESPN response: {e}")
        print("Raw response keys:", list(data.keys()))
        return None
    
    for comp in competitions:
        try:
            athlete = comp.get("athlete", {})
            name = athlete.get("displayName", "Unknown")
            
            status = comp.get("status", {})
            position = comp.get("sortOrder", 999)
            pos_display = comp.get("status", {}).get("position", {}).get("displayName", "--")
            
            # Score to par (overall)
            score_value = comp.get("score", {}).get("value", 0)
            score_display = comp.get("score", {}).get("displayValue", "E")
            
            # Check if missed cut
            missed_cut = False
            line_score = comp.get("linescores", [])
            status_type = comp.get("status", {}).get("type", {}).get("name", "")
            if "CUT" in status_type.upper() or "WD" in status_type.upper() or "DQ" in status_type.upper():
                missed_cut = True
            
            # Round scores
            rounds = {}
            for i, ls in enumerate(line_score[:4]):
                r_val = ls.get("value", None)
                r_display = ls.get("displayValue", "--")
                # ESPN gives round scores as strokes, convert to +/- par (par 72)
                if r_val is not None and r_display not in ("--", "", "WD", "DQ"):
                    try:
                        strokes = int(r_display)
                        rounds[f"r{i+1}"] = strokes
                    except:
                        rounds[f"r{i+1}"] = None
                else:
                    rounds[f"r{i+1}"] = None
            
            # Fill missing rounds
            for r in ["r1", "r2", "r3", "r4"]:
                if r not in rounds:
                    rounds[r] = None
            
            # Total strokes
            total_strokes = None
            strokes_val = comp.get("statistics", [])
            # Try to get total from linescores sum
            round_vals = [v for v in [rounds["r1"], rounds["r2"], rounds["r3"], rounds["r4"]] if v is not None]
            if round_vals:
                total_strokes = sum(round_vals)
            
            # Score to par for display
            try:
                score_to_par = int(score_display.replace("E", "0").replace("+", ""))
            except:
                score_to_par = 0
            
            players.append({
                "name": name,
                "pos": pos_display,
                "sortOrder": position,
                "scoreToPar": score_to_par,
                "scoreDisplay": score_display,
                "r1": rounds["r1"],
                "r2": rounds["r2"],
                "r3": rounds["r3"],
                "r4": rounds["r4"],
                "totalStrokes": total_strokes,
                "missedCut": missed_cut,
                "statusType": status_type
            })
        
        except Exception as e:
            print(f"  Skipping player due to error: {e}")
            continue
    
    # Sort by position
    players.sort(key=lambda x: x["sortOrder"])
    
    output = {
        "tournament": "2026 Masters Tournament",
        "lastUpdated": datetime.now().isoformat(),
        "round": detect_current_round(players),
        "players": players
    }
    
    print(f"  ✅ Fetched {len(players)} players")
    return output


def detect_current_round(players):
    """Detect which round is currently in progress or most recently completed"""
    for p in players[:10]:  # Check top 10
        if p["r4"] is not None:
            return 4
        elif p["r3"] is not None:
            return 3
        elif p["r2"] is not None:
            return 2
        elif p["r1"] is not None:
            return 1
    return 1


def save_scores(output, path="scores.json"):
    """Save scores to JSON file"""
    with open(path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"  💾 Saved to {path}")


def fetch_and_save(path="scores.json"):
    """Main function — call this from Jupyter to refresh scores"""
    data = fetch_masters_scores()
    if data:
        save_scores(data, path)
        print(f"\n📊 Round {data['round']} | {len(data['players'])} players")
        print(f"🕐 Last updated: {data['lastUpdated']}")
        # Preview top 5
        print("\n🏆 Current Top 5:")
        for p in data["players"][:5]:
            cut_flag = " ✂️ MISSED CUT" if p["missedCut"] else ""
            print(f"  {p['pos']:5} {p['name']:<25} {p['scoreDisplay']:>5}{cut_flag}")
        return data
    else:
        print("❌ Failed to fetch data")
        return None


# ── JUPYTER USAGE ──────────────────────────────────────────────
# In a Jupyter cell, run:
#
#   from masters_fetch import fetch_and_save
#   data = fetch_and_save("scores.json")
#
# This saves scores.json — commit/push it to your GitHub Pages repo
# and the web app will pick it up automatically.
#
# To auto-refresh every 5 minutes inside Jupyter:
#
#   import time
#   while True:
#       fetch_and_save("scores.json")
#       time.sleep(300)  # 5 minutes
# ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    fetch_and_save("scores.json")
