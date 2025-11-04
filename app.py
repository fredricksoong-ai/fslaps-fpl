from flask import Flask, render_template, request
import pandas as pd
import requests
from datetime import datetime, timedelta, timezone
import time

app = Flask(__name__)

GITHUB_BASE = "https://raw.githubusercontent.com/olbauday/FPL-Elo-Insights/main/data/2025-2026"

# ==================
# SMART TIME-BASED CACHING
# ==================
class SmartDataCache:
    def __init__(self):
        self.data = None
        self.last_updated = None
        self.current_gw = None
        # Update times: 5:00 AM and 5:00 PM UTC
        self.update_hours = [5, 17]  # 5am and 5pm in 24-hour format
    
    def get_next_update_time(self):
        """
        Calculate when the next data update will happen.
        Returns the next 5am or 5pm UTC after now.
        """
        now = datetime.now(timezone.utc)
        
        # Check if next update is today or tomorrow
        for hour in self.update_hours:
            next_update = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            
            if next_update > now:
                # This update time hasn't happened yet today
                return next_update
        
        # If we're past both update times today, next update is 5am tomorrow
        tomorrow = now + timedelta(days=1)
        next_update = tomorrow.replace(hour=self.update_hours[0], minute=0, second=0, microsecond=0)
        return next_update
    
    def should_refresh(self):
        """
        Check if we should fetch fresh data.
        Only refresh if:
        1. Cache is empty (first load)
        2. An update time (5am or 5pm) has passed since last fetch
        """
        if self.last_updated is None:
            print("❓ Cache is empty - need to fetch data")
            return True
        
        now = datetime.now(timezone.utc)
        
        # Check if any update time occurred between last_updated and now
        for hour in self.update_hours:
            update_time_today = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            
            # Was there an update time between our last fetch and now?
            if self.last_updated < update_time_today <= now:
                print(f"⏰ Update time passed ({hour}:00 UTC) - fetching fresh data")
                return True
        
        # Check yesterday's update times too (in case we cached at 4pm and it's now 6am next day)
        yesterday = now - timedelta(days=1)
        for hour in self.update_hours:
            update_time_yesterday = yesterday.replace(hour=hour, minute=0, second=0, microsecond=0)
            
            if self.last_updated < update_time_yesterday <= now:
                print(f"⏰ Update time passed ({hour}:00 UTC yesterday) - fetching fresh data")
                return True
        
        # Cache is still fresh
        next_update = self.get_next_update_time()
        time_until_next = next_update - now
        hours = int(time_until_next.total_seconds() // 3600)
        minutes = int((time_until_next.total_seconds() % 3600) // 60)
        print(f"✓ Using cached data - next update in {hours}h {minutes}m")
        return False
    
    def update(self, data, gw):
        """Update the cache with new data"""
        self.data = data
        self.current_gw = gw
        self.last_updated = datetime.now(timezone.utc)
        
        next_update = self.get_next_update_time()
        print(f"✓ Cache updated at {self.last_updated.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"  Next scheduled update: {next_update.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    
    def get(self):
        """Get cached data if still valid"""
        if not self.should_refresh() and self.data is not None:
            return self.data, self.current_gw
        return None, None

# Initialize smart cache
cache = SmartDataCache()

# ==================
# IMPROVED GW DETECTION
# ==================
def get_latest_gameweek():
    """Detect the latest available gameweek efficiently"""
    try:
        # Estimate current GW based on season start
        season_start = datetime(2025, 8, 16)  # Adjust to actual season start
        weeks_since_start = (datetime.now() - season_start).days // 7
        estimated_gw = max(1, min(weeks_since_start, 38))
        
        print(f"📍 Estimated current GW: {estimated_gw}")
        
        # Search strategy: Check estimated GW, then nearby weeks
        search_order = [estimated_gw]
        for offset in range(1, 10):
            if estimated_gw + offset <= 38:
                search_order.append(estimated_gw + offset)
            if estimated_gw - offset >= 1:
                search_order.append(estimated_gw - offset)
        
        # Check each GW in our smart order
        for gw in search_order:
            url = f"{GITHUB_BASE}/By%20Gameweek/GW{gw}/playerstats.csv"
            
            try:
                response = requests.head(url, timeout=3, allow_redirects=True)
                
                if response.status_code == 200:
                    content_length = response.headers.get('Content-Length')
                    
                    if content_length and int(content_length) > 1000:
                        print(f"✓ Found GW{gw} (Size: {content_length} bytes)")
                        return gw
                        
            except requests.exceptions.RequestException:
                continue
        
        print("⚠️ Could not detect gameweek, defaulting to GW1")
        return 1
        
    except Exception as e:
        print(f"❌ Error in get_latest_gameweek: {e}")
        return 1

# ==================
# SMART CACHED DATA LOADING
# ==================
def load_fpl_data():
    """Load FPL data with smart time-based caching"""
    # Check if we have valid cached data
    cached_data, cached_gw = cache.get()
    
    if cached_data is not None:
        return cached_data
    
    # Cache needs refresh - fetch fresh data
    print("🔄 Fetching fresh data from GitHub...")
    
    try:
        latest_gw = get_latest_gameweek()
        
        # Construct URLs
        players_url = f"{GITHUB_BASE}/players.csv"
        teams_url = f"{GITHUB_BASE}/teams.csv"
        current_players_url = f"{GITHUB_BASE}/By%20Gameweek/GW{latest_gw}/playerstats.csv"
        
        print(f"📥 Loading data from GW{latest_gw}...")
        start_time = time.time()
        
        # Load data from GitHub
        players_master = pd.read_csv(players_url)
        teams_df = pd.read_csv(teams_url)
        current_players = pd.read_csv(current_players_url)
        
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
        
        # Calculate points per million
        analysis_df['points_per_million'] = analysis_df['total_points'] / analysis_df['now_cost']
        
        # Store the current gameweek
        analysis_df['current_gw'] = latest_gw
        
        load_time = time.time() - start_time
        print(f"✅ Data loaded in {load_time:.2f} seconds")
        
        # Update cache
        cache.update(analysis_df, latest_gw)
        
        return analysis_df
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return pd.DataFrame()

@app.route('/')
def home():
    """Home page with basic player analysis"""
    df = load_fpl_data()
    
    if df.empty:
        return render_template('error.html', message="Could not load FPL data from GitHub")
    
    # Get current gameweek for display
    current_gw = df['current_gw'].iloc[0] if 'current_gw' in df.columns else 'Unknown'
    
    # Get top players by position
    analysis_data = {}
    positions = ['Goalkeeper', 'Defender', 'Midfielder', 'Forward']
    
    for pos in positions:
        pos_players = df[df['position'] == pos]
        if len(pos_players) > 0:
            if pos == 'Goalkeeper':
                top_players = pos_players.nlargest(5, 'total_points')
            else:
                top_players = pos_players.nlargest(8, 'expected_goal_involvements')
            
            # Convert to list of dictionaries for template
            analysis_data[pos] = top_players[[
                'web_name', 'team_name', 'now_cost', 'selected_by_percent', 
                'total_points', 'expected_goal_involvements', 'points_per_million'
            ]].round(2).to_dict('records')
    
    return render_template('home.html', analysis_data=analysis_data, current_gw=current_gw)

@app.route('/position/<position_name>')
def position_analysis(position_name):
    """Detailed analysis for a specific position"""
    df = load_fpl_data()
    
    if df.empty:
        return render_template('error.html', message="Could not load FPL data from GitHub")
    
    # Get current gameweek for display
    current_gw = df['current_gw'].iloc[0] if 'current_gw' in df.columns else 'Unknown'
    
    # Filter by position
    pos_players = df[df['position'] == position_name]
    
    if len(pos_players) == 0:
        return render_template('error.html', message=f"No players found for position: {position_name}")
    
    # Sort appropriately by position
    if position_name == 'Goalkeeper':
        pos_players = pos_players.sort_values('total_points', ascending=False)
        key_metric = 'total_points'
    else:
        pos_players = pos_players.sort_values('expected_goal_involvements', ascending=False)
        key_metric = 'expected_goal_involvements'
    
    # Get top 15 players
    top_players = pos_players.head(15)
    
    player_data = top_players[[
        'web_name', 'team_name', 'position', 'now_cost', 'selected_by_percent',
        'total_points', 'expected_goal_involvements', 'points_per_game', 'points_per_million'
    ]].round(2).to_dict('records')
    
    return render_template('position.html', 
                         position=position_name, 
                         players=player_data, 
                         key_metric=key_metric,
                         current_gw=current_gw)

@app.route('/differentials')
def differentials():
    """Show differential players (low ownership, high performance)"""
    df = load_fpl_data()
    
    if df.empty:
        return render_template('error.html', message="Could not load FPL data from GitHub")
    
    # Get current gameweek for display
    current_gw = df['current_gw'].iloc[0] if 'current_gw' in df.columns else 'Unknown'
    
    # Find differentials by position
    differentials_data = {}
    positions = ['Goalkeeper', 'Defender', 'Midfielder', 'Forward']
    
    for pos in positions:
        pos_players = df[df['position'] == pos]
        
        if pos == 'Goalkeeper':
            diff_players = pos_players[
                (pos_players['selected_by_percent'] < 5) & 
                (pos_players['total_points'] > 5)
            ].nlargest(5, 'total_points')
        else:
            min_xgi = 0.3 if pos == 'Defender' else 0.5
            diff_players = pos_players[
                (pos_players['selected_by_percent'] < 10) & 
                (pos_players['expected_goal_involvements'] > min_xgi)
            ].nlargest(5, 'expected_goal_involvements')
        
        if len(diff_players) > 0:
            differentials_data[pos] = diff_players[[
                'web_name', 'team_name', 'now_cost', 'selected_by_percent',
                'total_points', 'expected_goal_involvements', 'points_per_million'
            ]].round(2).to_dict('records')
    
    return render_template('differentials.html', differentials_data=differentials_data, current_gw=current_gw)

@app.route('/search')
def search():
    """Search for players by name"""
    df = load_fpl_data()
    
    if df.empty:
        return render_template('error.html', message="Could not load FPL data from GitHub")
    
    # Get current gameweek for display
    current_gw = df['current_gw'].iloc[0] if 'current_gw' in df.columns else 'Unknown'
    
    # Get the search query from URL parameters
    query = request.args.get('q', '').strip()
    
    if not query:
        # If no search query, show the search page with no results
        return render_template('search.html', query='', results=[], current_gw=current_gw)
    
    # Search for players whose name contains the query (case-insensitive)
    results = df[df['web_name'].str.contains(query, case=False, na=False)]
    
    # Sort by total points
    results = results.sort_values('total_points', ascending=False)
    
    # Convert to list of dictionaries for the template
    player_results = results[[
        'web_name', 'team_name', 'position', 'now_cost', 'selected_by_percent',
        'total_points', 'expected_goal_involvements', 'points_per_game', 'points_per_million'
    ]].head(20).round(2).to_dict('records')
    
    return render_template('search.html', query=query, results=player_results, current_gw=current_gw)

if __name__ == '__main__':
    app.run(debug=True) 
