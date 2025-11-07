import pandas as pd
import requests
from datetime import datetime
import logging
from typing import Tuple, Optional
from player_dataframe import PlayerDataFrame

# --- Configuration ---

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# GitHub repo base URL (Constant)
GITHUB_BASE = "https://raw.githubusercontent.com/olbauday/FPL-Elo-Insights/main/data/2025-2026"

# --- Gameweek Detection ---

def check_gw_file_exists(gw: int) -> bool:
    """
    Check if a valid playerstats.csv file exists for a given gameweek.
    A file is "valid" if it exists and has a content length > 1000 bytes.
    """
    if not (1 <= gw <= 38):
        return False
        
    url = f"{GITHUB_BASE}/By%20Gameweek/GW{gw}/playerstats.csv"
    try:
        response = requests.head(url, timeout=3, allow_redirects=True)
        
        if response.status_code == 200:
            content_length = response.headers.get('Content-Length')
            if content_length and int(content_length) > 1000:
                logging.debug(f"✓ Found valid GW{gw} file (Size: {content_length} bytes)")
                return True
        logging.debug(f"✗ No valid GW{gw} file found (Status: {response.status_code})")
        return False
        
    except requests.exceptions.RequestException as e:
        logging.warning(f"Network error checking GW{gw}: {e}")
        return False

def find_latest_gw_file() -> int:
    """
    Find the latest gameweek number that has a valid, non-empty data file.
    
    This is the most robust way to find the "current" GW data, as it relies
    on the data's existence, not on fixture times.
    """
    try:
        # Estimate current GW based on season start (Aug 16, 2025)
        # This is just an optimization to start our search
        season_start = datetime(2025, 8, 16)
        weeks_since_start = (datetime.now() - season_start).days // 7
        estimated_gw = max(1, min(weeks_since_start + 1, 38)) # +1 to check current
        
        logging.info(f"📍 Estimated GW: {estimated_gw}. Starting search...")
        
        # Search strategy: Check estimated GW, then search outwards
        search_order = [estimated_gw]
        for offset in range(1, 10): # Search 10 GWs in either direction
            if estimated_gw + offset <= 38:
                search_order.append(estimated_gw + offset)
            if estimated_gw - offset >= 1:
                search_order.append(estimated_gw - offset)
        
        # Check in smart order, but keep track of the *highest* one found
        latest_found_gw = 0
        for gw in search_order:
            if check_gw_file_exists(gw):
                latest_found_gw = max(latest_found_gw, gw)
        
        if latest_found_gw > 0:
            logging.info(f"✓ Found latest available GW file: {latest_found_gw}")
            return latest_found_gw

        # If smart search fails, fall back to a full reverse scan (slower)
        logging.warning("Smart search failed, starting full reverse scan...")
        for gw in range(38, 0, -1):
            if check_gw_file_exists(gw):
                logging.info(f"✓ Found latest available GW file: {gw} (full scan)")
                return gw
        
        logging.error("Could not detect any gameweek data. Defaulting to GW1.")
        return 1
        
    except Exception as e:
        logging.error(f"❌ Error in find_latest_gw_file: {e}")
        return 1

def determine_gw_info() -> dict:
    """
    Determine which GW files to use for stats and transfers.
    
    - `transfers_gw` (N): The latest file available. This has the
      most up-to-date prices, transfers, and selection stats.
    - `stats_gw` (N-1): The previous GW. We use this file to get the
      *completed* points and stats for players.
    """
    
    # Find the latest available GW file (e.g., GW20 file)
    latest_file_gw = find_latest_gw_file()
    
    # This file has the latest transfers/prices FOR GW20
    transfers_gw = latest_file_gw
    
    # The stats (points) IN this file are from GW19
    # So, we need the GW19 file to get GW19 points
    # And the GW20 file to get GW20 prices/transfers
    stats_gw = max(1, latest_file_gw - 1)
    
    # If we are in GW1, both stats and transfers come from GW1 file
    if latest_file_gw == 1:
        stats_gw = 1
    
    gw_info = {
        'current_gw': latest_file_gw,
        'stats_gw': stats_gw,
        'transfers_gw': transfers_gw,
        'gw_status': 'unknown' # We no longer need to know this
    }
    
    logging.info(f"📊 Using GW{gw_info['stats_gw']} for player stats")
    logging.info(f"📈 Using GW{gw_info['transfers_gw']} for transfer data")
    
    return gw_info

# ==================
# DATA FETCHING
# ==================
def fetch_data_from_github() -> Tuple[Optional[PlayerDataFrame], Optional[int]]:
    """
    Fetch fresh data from GitHub and return as PlayerDataFrame.
    Returns tuple of (PlayerDataFrame, gameweek_number) or (None, None) if failed.
    """
    try:
        # Get gameweek status
        gw_info = determine_gw_info()
        
        # Load base data
        players_url = f"{GITHUB_BASE}/players.csv"
        teams_url = f"{GITHUB_BASE}/teams.csv"
        
        logging.info("📥 Loading base data (players.csv, teams.csv)...")
        players_master = pd.read_csv(players_url)
        teams_df = pd.read_csv(teams_url)
        
        # Load player stats from the STATS GW
        stats_url = f"{GITHUB_BASE}/By%20Gameweek/GW{gw_info['stats_gw']}/playerstats.csv"
        logging.info(f"📥 Loading player stats from GW{gw_info['stats_gw']}...")
        current_players = pd.read_csv(stats_url)
        
        # Load transfer data from the TRANSFERS GW
        transfers_url = f"{GITHUB_BASE}/By%20Gameweek/GW{gw_info['transfers_gw']}/playerstats.csv"
        logging.info(f"📥 Loading transfer data from GW{gw_info['transfers_gw']}...")
        
        try:
            transfer_data = pd.read_csv(transfers_url)
            
            # Update transfer columns in current_players
            transfer_cols = [
                'transfers_in', 'transfers_out', 'transfers_balance', 
                'selected_by_percent', 'now_cost'
            ]
            
            # Use a dictionary for efficient mapping
            transfer_map = transfer_data.set_index('id').to_dict('index')
            
            for col in transfer_cols:
                if col in transfer_data.columns:
                    current_players[col] = current_players['id'].map(
                        lambda x: transfer_map.get(x, {}).get(col)
                    ).fillna(current_players[col])
                    
            logging.info(f"✓ Updated transfer/price data from GW{gw_info['transfers_gw']}")
            
        except (pd.errors.EmptyDataError, FileNotFoundError, Exception) as e:
            logging.warning(f"⚠️ Could not load/merge transfer data from GW{gw_info['transfers_gw']}: {e}")
            # Continue without it; we still have the stats_gw data
        
        # Create team mapping
        team_mapping = teams_df.set_index('code')[['name', 'short_name', 'elo']].to_dict('index')
        
        # Join player data
        analysis_df = current_players.merge(
            players_master[['player_id', 'team_code', 'position']], 
            left_on='id', 
            right_on='player_id', 
            how='left'
        )
        
        # Add team names
        analysis_df['team_name'] = analysis_df['team_code'].map(
            lambda x: team_mapping.get(x, {}).get('short_name', 'Unknown')
        )
        
        # Store the gameweek info in columns (PlayerDataFrame will use this)
        analysis_df['current_gw'] = gw_info['current_gw']
        analysis_df['stats_gw'] = gw_info['stats_gw']
        analysis_df['gw_status'] = gw_info['gw_status']
        
        # Add metadata as attributes
        analysis_df.attrs['gw_info'] = gw_info
        
        logging.info("✅ Data loaded and merged successfully")
        logging.info(f"   Current GW: {gw_info['current_gw']}")
        logging.info(f"   Stats from: GW{gw_info['stats_gw']}")
        logging.info(f"   Transfers from: GW{gw_info['transfers_gw']}")
        
        # CHANGED: Wrap in PlayerDataFrame before returning
        player_df = PlayerDataFrame(analysis_df)
        
        # Copy over the gw_info to the new PlayerDataFrame
        player_df.df.attrs['gw_info'] = gw_info
        
        logging.info(f"✓ Wrapped data in PlayerDataFrame ({len(player_df)} players)")
        
        return player_df, gw_info['current_gw']
        
    except Exception as e:
        logging.error(f"❌ Error in fetch_data_from_github: {e}", exc_info=True)
        return None, None

# ==================
# MAIN DATA LOADING FUNCTION
# ==================
def load_fpl_data(cache):
    """
    Load FPL data with smart caching. Requires a SmartDataCache instance.
    This is the main function to call from your app.
    
    Returns PlayerDataFrame (not raw pandas DataFrame).
    """
    # Try to get cached data first
    cached_data, cached_gw = cache.get()
    
    if cached_data is not None:
        # We have cached data - check if it's still valid
        if not cache.should_refresh():
            logging.info("Cache is fresh, using cached data.")
            return cached_data
        logging.info("Cache is stale, attempting to refresh.")
    
    # Need to fetch fresh data
    logging.info("🔄 Fetching fresh data from GitHub...")
    
    player_df, latest_gw = fetch_data_from_github()
    
    if player_df is not None and len(player_df) > 0:
        logging.info(f"Successfully fetched fresh data for GW{latest_gw}.")
        cache.update(player_df, latest_gw)
        return player_df
    else:
        # If fetch failed but we have old cached data, return that
        if cached_data is not None:
            logging.warning("⚠️ Fetch failed, using stale cached data as fallback.")
            return cached_data
        
        # No fresh data, no cached data. Return empty PlayerDataFrame.
        logging.error("❌ Fetch failed and no cached data available.")
        return PlayerDataFrame(pd.DataFrame())

def scheduled_data_refresh(cache):
    """
    Background job to refresh data.
    Fetches data automatically without user interaction.
    """
    now = datetime.now()
    logging.info(f"\n{'='*60}\n🔄 SCHEDULED REFRESH triggered at {now.strftime('%Y-%m-%d %H:%M:%S')}\n{'='*60}")
    
    player_df, latest_gw = fetch_data_from_github()
    
    if player_df is not None and len(player_df) > 0:
        cache.update(player_df, latest_gw)
        logging.info(f"✅ Scheduled refresh completed successfully for GW{latest_gw}")
    else:
        logging.error(f"❌ Scheduled refresh failed")
    
    logging.info(f"{'='*60}\n")
