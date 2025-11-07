from flask import Flask, render_template, request, redirect, url_for, make_response
import pandas as pd
from datetime import datetime, timezone
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import time
import requests
import json
import random

# NEW IMPORTS
from cache_module import SmartDataCache
from github_data import load_fpl_data, scheduled_data_refresh, GITHUB_BASE 
from fpl_api import FPLApiClient
from player_dataframe import PlayerDataFrame
from data_enrichment import DataEnricher
from risk_analyzer import RiskAnalyzer
from data_models import POSITION_MAP, VIEW_CONFIGS

# NOTE: 'github_data' is now 'github_data_refactored' but we keep the old import name
# assuming the module file was renamed/aliased to maintain compatibility.
from cache_module import SmartDataCache
from github_data import load_fpl_data, scheduled_data_refresh, GITHUB_BASE 
from fpl_api import FPLApiClient

app = Flask(__name__)

# Add this to your app.py near the top, after creating the app
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True

# --- LLM API Configuration ---
API_KEY = "AIzaSyCWycMOAs3o75Kaql_M0EJG7tQ_Csg5Nhw"
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent"

# ==================
# INITIALIZE GLOBAL OBJECTS
# ==================
cache = SmartDataCache() 
fpl_client = FPLApiClient()
enricher = DataEnricher(fpl_client)  # NEW: Initialize enricher

# ==================
# UPDATED: GEMINI API HELPER (Now generates 3 headlines via structured JSON)
# ==================

def generate_analysis_headlines(data_list, position_name):
    """
    Calls Gemini API to generate 3 compelling headlines based on the top 10 data.
    The function requests a structured JSON response.
    """
    if not data_list:
        return [f"No top 10 data available for {position_name}.", "Data still loading...", "Check back after refresh."]

    # Convert the list of player dictionaries (data_list) to a JSON string
    data_json = json.dumps(data_list)
    
    # Define the System Instruction for the LLM
    system_prompt = (
        "You are an elite Fantasy Premier League (FPL) analyst. "
        "Analyze the provided JSON data containing the top 10 players by points for a specific category. "
        "Generate a **list of three (3) distinct, compelling, and insightful headlines**. "
        "Focus on points, form, value (Pts/£m), and ownership. "
        "Each headline must be a maximum of 15 words. The response MUST be a JSON array of strings."
    )

    # Define the User Query
    user_query = (
        f"Generate three headlines for the top players in the '{position_name}' category. "
        "Analyze this data and focus on key standouts or trends: "
        f"DATA: {data_json}"
    )

    # Construct the payload, requesting JSON output structure
    payload = {
        "contents": [{"parts": [{"text": user_query}]}],
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "ARRAY",
                "items": {"type": "STRING"}
            }
        }
    }

    # Exponential Backoff Retry Logic
    max_retries = 3
    initial_delay = 1 # seconds

    for attempt in range(max_retries):
        try:
            headers = {'Content-Type': 'application/json'}
            response = requests.post(f"{API_URL}?key={API_KEY}", headers=headers, json=payload, timeout=15)
            response.raise_for_status() 
            
            result = response.json()
            
            # Safely extract the generated JSON string from the response
            json_text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '').strip()
            
            if json_text:
                # Attempt to parse the JSON array
                try:
                    headlines_list = json.loads(json_text)
                    # Ensure the result is actually a list of strings and has 3 items
                    if isinstance(headlines_list, list) and len(headlines_list) == 3 and all(isinstance(h, str) for h in headlines_list):
                        return headlines_list
                except json.JSONDecodeError:
                    print(f"LLM API returned unparsable JSON: {json_text}")

            # If parsing failed or result was empty, retry or break
            print(f"LLM API returned empty or invalid response on attempt {attempt + 1}.")
            time.sleep(random.uniform(initial_delay, initial_delay * 2))
            initial_delay *= 2
        
        except requests.exceptions.RequestException as e:
            print(f"Request failed on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(random.uniform(initial_delay, initial_delay * 2))
                initial_delay *= 2
            else:
                break
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            break

    # Fallback message (3 items) if all attempts or processing fail
    return [
        f"Quick Analysis: Top {position_name} players are performing well.",
        "Check points, form, and ownership carefully.",
        "Data loading error or API connection issue."
    ]

# ==================
# CONTEXT PROCESSOR (Existing Code)
# ==================
@app.context_processor
def inject_global_data():
    """
    Makes current_gw available to ALL Jinja templates (base.html, home.html, etc.).
    """
    gw = cache.current_gw if cache.current_gw else None
    return dict(current_gw=gw)

# ==================
# BACKGROUND SCHEDULER (UPDATED: Removed LLM cache clear)
# ==================
scheduler = BackgroundScheduler(timezone="UTC")
scheduler.add_job(
    # LLM cache is now only cleared manually via /llm-refresh-now
    func=lambda: scheduled_data_refresh(cache), 
    trigger="cron",
    hour=5,
    minute=0,
    id='morning_update',
    name='Morning Data Update (5:00 AM UTC)'
)
scheduler.add_job(
    # LLM cache is now only cleared manually via /llm-refresh-now
    func=lambda: scheduled_data_refresh(cache),
    trigger="cron",
    hour=17,
    minute=0,
    id='evening_update',
    name='Evening Data Update (5:00 PM UTC)'
)
scheduler.start()
print("🚀 Background scheduler started")
atexit.register(lambda: scheduler.shutdown())

# Load initial data on startup (UPDATED: Removed LLM cache clear)
print("\n🔄 Loading initial data on startup...")
try:
    initial_data = load_fpl_data(cache) 
    # Removed: cache.set('llm_headlines', None)
    if not initial_data.empty:
        print("✅ Initial data loaded successfully")
except Exception as e:
    print(f"⚠️ Could not load initial data: {e}. App will retry on first user request.")

# ==================
# FLASK ROUTES
# ==================

@app.route('/')
def home():
    """
    New Homepage. Checks for a cached team ID and redirects to the My Team page, 
    otherwise, it redirects to the form page.
    """
    # 1. Check for the cached team ID in the user's browser cookies
    cached_team_id = request.cookies.get('fpl_team_id')
    
    if cached_team_id:
        # If the ID is found, redirect directly to the My Team view
        print(f"🏠 Found cached team ID: {cached_team_id}. Redirecting to My Team.")
        # NOTE: Using a hard-coded redirect string for simplicity, but url_for is often preferred.
        return redirect(f'/my-team/{cached_team_id}')
    else:
        # If no ID is found, render the team ID input form (which currently lives at /my-team)
        return redirect('/my-team') # Or alternatively: return my_team_form()

@app.route('/analysis-overview')
def analysis_overview():
    """
    Analysis Overview page with player analysis.
    Uses the new data layer with PlayerDataFrame and view configs.
    """
    
    # Initialize empty data structures
    analysis_data = {}
    overall_top_10_list = []
    top_10_defensive_contribution = [] 
    
    # Check for cached headlines
    cached_headlines = cache.get('llm_headlines')
    if cached_headlines is not None:
        headlines = cached_headlines
        print("🧠 Using cached LLM headlines.")
    else:
        headlines = {}
        print("🔄 Generating new LLM headlines...")

    # Load data (now returns PlayerDataFrame)
    player_df = load_fpl_data(cache)
    
    # Check if data is empty
    if len(player_df) == 0:
        fallback_max = {
            'max_points': 1, 'max_ownership': 1, 'max_form': 1, 
            'max_cs': 1, 'max_xgi': 1, 'max_saves_pm': 1, 
            'max_ppm': 1, 'max_value_metric': 1, 
            'max_def_cont': 1, 'max_def_cont_p90': 1
        }
        global_max_values = fallback_max
        positional_max_values = {
            'Goalkeeper': fallback_max, 
            'Defender': fallback_max, 
            'Midfielder': fallback_max, 
            'Forward': fallback_max
        }
        
        if not headlines:
            headlines = {
                'Overall': ["Data not loaded.", "Please check back later.", "Error: Data source empty."], 
                'Goalkeeper': ["...", "...", "..."], 
                'Defender': ["...", "...", "..."], 
                'Midfielder': ["...", "...", "..."], 
                'Forward': ["...", "...", "..."],
                'Defensive': ["...", "...", "..."]
            }
                          
        return render_template('analysis_overview.html',
                               message="Could not load FPL data from GitHub.",
                               global_max_values=global_max_values,
                               positional_max_values=positional_max_values,
                               headlines=headlines)

    # Extract GW info
    if hasattr(player_df.df, 'attrs') and 'gw_info' in player_df.df.attrs:
        gw_info = player_df.df.attrs['gw_info']
        current_gw = gw_info.get('current_gw', 'Unknown')
        gw_status = gw_info.get('gw_status', '')
        stats_gw = gw_info.get('stats_gw', current_gw)
    else:
        current_gw = player_df.df['current_gw'].iloc[0] if 'current_gw' in player_df.df.columns else 'Unknown'
        gw_status = ''
        stats_gw = current_gw
    
    # ----------------------------------------------------
    # Overall Top 10 - Using new system
    # ----------------------------------------------------
    overall_top_10 = player_df.top_n(10, 'total_points')
    overall_top_10_list = overall_top_10.to_display_dict(format_values=False)

    # Apply position mapping and rounding - USE .get() FOR SAFETY
    for player in overall_top_10_list:
        # **These lines are correct (inside the loop)**
        player['position'] = POSITION_MAP.get(player.get('position', ''), 'N/A')
        player['now_cost'] = player.get('now_cost', 0)
        
        # **Move rounding logic INSIDE the loop**
        if 'expected_goal_involvements' in player and player['expected_goal_involvements'] is not None:
            player['expected_goal_involvements'] = round(player['expected_goal_involvements'], 2)
        
        if 'save_value_per_million' in player and player['save_value_per_million'] is not None:
            player['save_value_per_million'] = round(player['save_value_per_million'], 2)
        
        if 'points_per_million' in player and player['points_per_million'] is not None:
            player['points_per_million'] = round(player['points_per_million'], 2)
        
        # Ensure 'form' key exists before using float(), then round
        if 'form' in player and player['form'] is not None:
            # Added protection: ensure it's convertible to float, then round
            try:
                player['form'] = round(float(player['form']), 1)
            except ValueError:
                player['form'] = 0.0 # Fallback on error

    # Generate headline for Overall if not cached
    if 'Overall' not in headlines:
        headlines['Overall'] = generate_analysis_headlines(overall_top_10_list, "Overall Top 10")
    
    # ----------------------------------------------------
    # Defensive Contribution (if available)
    # ----------------------------------------------------
    if 'defensive_contribution' in player_df.df.columns:
        # Filter to players with points
        players_with_points = PlayerDataFrame(
            player_df.df[player_df.df['total_points'] > 0].copy()
        )
        defensive_top_10 = players_with_points.top_n(10, 'defensive_contribution')
        top_10_defensive_contribution = defensive_top_10.to_display_dict(format_values=False)
        
        for player in top_10_defensive_contribution:
            player['position'] = POSITION_MAP.get(player.get('position', ''), 'N/A')
            player['now_cost'] = player.get('now_cost', 0)
            
            if 'defensive_contribution' in player and player['defensive_contribution'] is not None:
                player['defensive_contribution'] = round(player['defensive_contribution'], 1)
            
            if 'defensive_contribution_per_90' in player and player['defensive_contribution_per_90'] is not None:
                player['defensive_contribution_per_90'] = round(player['defensive_contribution_per_90'], 2)
        
        if 'Defensive' not in headlines:
            headlines['Defensive'] = generate_analysis_headlines(top_10_defensive_contribution, "Defensive Contribution")
    else:
        if 'Defensive' not in headlines:
            headlines['Defensive'] = ["Defensive stat column missing.", "Update your data module.", "Table data will be empty."]
    
    # ----------------------------------------------------
    # Calculate Max Values for visualization
    # ----------------------------------------------------
    df = player_df.df  # Get underlying DataFrame for calculations
    
    global_max_values = {
        'max_points': df['total_points'].max() if 'total_points' in df.columns else 1,
        'max_ownership': df['selected_by_percent'].astype(float).max() if 'selected_by_percent' in df.columns else 1,
        'max_form': df['form'].max() if 'form' in df.columns else 1,
        'max_cs': df['clean_sheets'].max() if 'clean_sheets' in df.columns else 1,
        'max_xgi': df[df['position'] != 'Goalkeeper']['expected_goal_involvements'].max() if 'expected_goal_involvements' in df.columns else 1,
        'max_saves_pm': df[df['position'] == 'Goalkeeper']['save_value_per_million'].max() if 'save_value_per_million' in df.columns else 1,
        'max_ppm': df['points_per_million'].max() if 'points_per_million' in df.columns else 1,
        'max_def_cont': df['defensive_contribution'].max() if 'defensive_contribution' in df.columns else 1,
        'max_def_cont_p90': df['defensive_contribution_per_90'].max() if 'defensive_contribution_per_90' in df.columns else 1,
    }
    
    # Calculate positional max values
    positional_max_values = {}
    positions_list = ['Goalkeeper', 'Defender', 'Midfielder', 'Forward']
    
    for pos in positions_list:
        pos_df = df[df['position'] == pos]
        if not pos_df.empty:
            pos_maxes = {
                'max_points': pos_df['total_points'].max() if 'total_points' in pos_df.columns else 1,
                'max_ownership': pos_df['selected_by_percent'].astype(float).max() if 'selected_by_percent' in pos_df.columns else 1,
                'max_form': pos_df['form'].max() if 'form' in pos_df.columns else 1,
                'max_cs': pos_df['clean_sheets'].max() if 'clean_sheets' in pos_df.columns else 1,
                'max_ppm': pos_df['points_per_million'].max() if 'points_per_million' in pos_df.columns else 1,
            }
            if pos == 'Goalkeeper':
                pos_maxes['max_value_metric'] = pos_df['save_value_per_million'].max() if 'save_value_per_million' in pos_df.columns else 1
            else:
                pos_maxes['max_value_metric'] = pos_df['expected_goal_involvements'].max() if 'expected_goal_involvements' in pos_df.columns else 1
                
            positional_max_values[pos] = pos_maxes
        else:
            positional_max_values[pos] = {
                'max_points': 1, 'max_ownership': 1, 'max_form': 1, 
                'max_cs': 1, 'max_ppm': 1, 'max_value_metric': 1
            }

    # ----------------------------------------------------
    # Process position sections
    # ----------------------------------------------------
    positions = ['Goalkeeper', 'Defender', 'Midfielder', 'Forward']

    for pos in positions:
        pos_players = player_df.filter_by_position(pos)
        
        if len(pos_players) > 0:
            # Get appropriate view
            if pos == 'Goalkeeper':
                view_data = pos_players.get_view('goalkeeper_analysis')
            else:
                view_data = pos_players.get_view('outfield_analysis')
            
            # Get top 10
            top_10 = view_data.head(10)
            player_list = top_10.to_display_dict(format_values=False)
            
            # Apply formatting - USE .get() FOR SAFETY
            for player in player_list:
                player['position'] = POSITION_MAP.get(player.get('position', ''), 'N/A')
                player['now_cost'] = player.get('now_cost', 0)
                
                if 'expected_goal_involvements' in player and player['expected_goal_involvements'] is not None:
                    player['expected_goal_involvements'] = round(player['expected_goal_involvements'], 2)
                
                if 'save_value_per_million' in player and player['save_value_per_million'] is not None:
                    player['save_value_per_million'] = round(player['save_value_per_million'], 2)
                
                if 'points_per_million' in player and player['points_per_million'] is not None:
                    player['points_per_million'] = round(player['points_per_million'], 2)
                
                if 'form' in player and player['form'] is not None:
                    player['form'] = round(float(player['form']), 1)

            analysis_data[pos] = player_list
            
            # Generate headline if not cached
            if pos not in headlines:
                headlines[pos] = generate_analysis_headlines(player_list, pos)
        else:
            if pos not in headlines:
                headlines[pos] = [f"No data for {pos} yet.", "Waiting for FPL data...", "Try a manual refresh."]
    
    # Cache the newly generated headlines
    if cached_headlines is None:
        cache.set('llm_headlines', headlines)
        print("✅ New LLM headlines cached.")

    # Render template
    return render_template('analysis_overview.html', 
        analysis_data=analysis_data,
        overall_top_10=overall_top_10_list,  
        top_10_defensive_contribution=top_10_defensive_contribution,
        global_max_values=global_max_values, 
        positional_max_values=positional_max_values,
        headlines=headlines,
        current_gw=current_gw,
        gw_status=gw_status,
        stats_gw=stats_gw
    )

@app.route('/position/<position_name>')
def position_analysis(position_name):
    """Detailed analysis for a specific position - using new data layer"""
    
    player_df = load_fpl_data(cache)
    
    if len(player_df) == 0:
        return render_template('error.html', message="Could not load FPL data from GitHub")
    
    current_gw = player_df.df['current_gw'].iloc[0] if 'current_gw' in player_df.df.columns else 'Unknown'
    
    # Position name mapping
    position_map_route = {
        'Goalkeepers': 'Goalkeeper',
        'Defenders': 'Defender',
        'Midfielders': 'Midfielder',
        'Forwards': 'Forward',
        'Goalkeeper': 'Goalkeeper',
        'Defender': 'Defender',
        'Midfielder': 'Midfielder',
        'Forward': 'Forward',
    }
    
    normalized_position_name = position_map_route.get(position_name, position_name)
    
    # Filter by position
    pos_players = player_df.filter_by_position(normalized_position_name)
    
    if len(pos_players) == 0:
        return render_template('error.html', message=f"No players found for position: {position_name}")
    
    # Determine sort metric
    if normalized_position_name == 'Goalkeeper':
        key_metric = 'save_value_per_million'
    else:
        key_metric = 'expected_goal_involvements'
    
    # Get top 15
    top_players = pos_players.top_n(15, key_metric)
    
    # Convert to display format
    player_data = top_players.to_display_dict(format_values=False)
    
    # In position_analysis() - the formatting section:
    for player in player_data:
        player['position'] = POSITION_MAP.get(player.get('position', ''), 'N/A')
        player['now_cost'] = player.get('now_cost', 0)
        
        if 'expected_goal_involvements' in player and player['expected_goal_involvements'] is not None:
            player['expected_goal_involvements'] = round(player['expected_goal_involvements'], 2)
        
        if 'save_value_per_million' in player and player['save_value_per_million'] is not None:
            player['save_value_per_million'] = round(player['save_value_per_million'], 2)
        
        if 'points_per_million' in player and player['points_per_million'] is not None:
            player['points_per_million'] = round(player['points_per_million'], 2)
        
        if 'points_per_game' in player and player['points_per_game'] is not None:
            player['points_per_game'] = round(player['points_per_game'], 1)
    
    # Calculate max values for this position
    pos_df = pos_players.df
    max_values = {
        'max_points': pos_df['total_points'].max() if 'total_points' in pos_df.columns else 1,
        'max_ownership': pos_df['selected_by_percent'].astype(float).max() if 'selected_by_percent' in pos_df.columns else 1,
        'max_form': pos_df['form'].max() if 'form' in pos_df.columns else 1,
        'max_cs': pos_df['clean_sheets'].max() if 'clean_sheets' in pos_df.columns else 1,
    }

    if normalized_position_name == 'Goalkeeper':
        max_values['max_value_metric'] = pos_df['save_value_per_million'].max() if 'save_value_per_million' in pos_df.columns else 1
    else:
        max_values['max_value_metric'] = pos_df['expected_goal_involvements'].max() if 'expected_goal_involvements' in pos_df.columns else 1
    
    return render_template('position.html', 
                         position_name=normalized_position_name, 
                         players=player_data, 
                         key_metric=key_metric,
                         max_values=max_values, 
                         current_gw=current_gw)

@app.route('/differentials')
def differentials():
    """Show differential players using new data layer"""
    
    player_df = load_fpl_data(cache)
    
    if len(player_df) == 0:
        return render_template('error.html', message="Could not load FPL data from GitHub")
    
    current_gw = player_df.df['current_gw'].iloc[0] if 'current_gw' in player_df.df.columns else 'Unknown'
    
    differentials_data = {}
    positions = ['Goalkeeper', 'Defender', 'Midfielder', 'Forward']
    
    for pos in positions:
        pos_players = player_df.filter_by_position(pos)
        
        if len(pos_players) == 0:
            continue
        
        # Apply differential filters
        df = pos_players.df
        
        if pos == 'Goalkeeper':
            # GK: Low ownership, decent points
            diff_df = df[
                (df['selected_by_percent'] < 5) & 
                (df['total_points'] > 5)
            ].nlargest(5, 'total_points')
            
            # For GK, value_metric is save_value_per_million
            value_metric_col = 'save_value_per_million'
        else:
            # Outfield: Low ownership, good xGI
            min_xgi = 0.3 if pos == 'Defender' else 0.5
            diff_df = df[
                (df['selected_by_percent'] < 10) & 
                (df['expected_goal_involvements'] > min_xgi)
            ].nlargest(5, 'expected_goal_involvements')
            
            # For outfield, value_metric is expected_goal_involvements
            value_metric_col = 'expected_goal_involvements'
        
        if len(diff_df) > 0:
            # Convert to PlayerDataFrame and get display format
            diff_players = PlayerDataFrame(diff_df)
            player_list = diff_players.to_display_dict(format_values=False)
            
            # Apply formatting and ADD value_metric field
            for player in player_list:
                player['position'] = POSITION_MAP.get(player.get('position', ''), 'N/A')
                player['now_cost'] = player.get('now_cost', 0)
                
                # Add the appropriate value_metric based on position
                if pos == 'Goalkeeper':
                    player['value_metric'] = round(player.get('save_value_per_million', 0), 2)
                else:
                    player['value_metric'] = round(player.get('expected_goal_involvements', 0), 2)
                
                # Format all fields
                if 'expected_goal_involvements' in player and player['expected_goal_involvements'] is not None:
                    player['expected_goal_involvements'] = round(player['expected_goal_involvements'], 2)
                
                if 'save_value_per_million' in player and player['save_value_per_million'] is not None:
                    player['save_value_per_million'] = round(player['save_value_per_million'], 2)
                
                if 'points_per_million' in player and player['points_per_million'] is not None:
                    player['points_per_million'] = round(player['points_per_million'], 2)
            
            differentials_data[pos] = player_list
    
    return render_template('differentials.html', 
                         differentials_data=differentials_data, 
                         current_gw=current_gw)

@app.route('/search')
def search():
    """Search for players by name"""
    df = load_fpl_data(cache) 
    
    if df.empty:
        return render_template('error.html', message="Could not load FPL data from GitHub")
    
    current_gw = df['current_gw'].iloc[0] if 'current_gw' in df.columns else 'Unknown'
    
    query = request.args.get('q', '').strip()
    
    if not query:
        return render_template('search.html', query='', results=[], current_gw=current_gw)
    
    results = df[df['web_name'].str.contains(query, case=False, na=False)]
    
    results = results.sort_values('total_points', ascending=False)
    
    columns_to_select = [
        'web_name', 'team_name', 'position', 'now_cost', 'selected_by_percent',
        'total_points', 'expected_goal_involvements', 'points_per_game', 
        'points_per_million', 'save_value_per_million' 
    ]
    
    player_results = results[columns_to_select].head(20).to_dict('records')
    
    for player in player_results:
        player['now_cost'] = player.get('now_cost', 0) 
        player['expected_goal_involvements'] = round(player.get('expected_goal_involvements', 0), 2)
        player['save_value_per_million'] = round(player.get('save_value_per_million', 0), 2)
        player['points_per_million'] = round(player.get('points_per_million', 0), 2)
        player['points_per_game'] = round(player.get('points_per_game', 0), 1)
        player['position'] = POS_MAP.get(player.get('position', ''), 'N/A')
    
    return render_template('search.html', query=query, results=player_results, current_gw=current_gw)

@app.route('/my-team')
def my_team_form():
    """
    Show form to enter team ID or handle form submission.
    This is the target of the redirect from the homepage (/) when no cookie is found.
    """
    team_id = request.args.get('team_id')
    
    # This block handles the submission of the form itself (e.g., /my-team?team_id=1234)
    if team_id:
        return redirect(f'/my-team/{team_id}')
    
    # If no ID is provided, just show the blank form
    return render_template('my_team_form.html')

@app.route('/my-team/<int:team_id>')
def my_team(team_id):
    """
    Display user's FPL team with problem detection, using a perpetual cache.
    The data is refreshed only via the manual refresh button or if not found.
    """
    team_cache_key = f'team_{team_id}'
    team_data = cache.get(team_cache_key) # Check the cache first
    
    # --- 1. Data Fetch and Caching Logic ---
    if team_data is None:
        print(f"🔄 Cache miss for team {team_id}. Fetching from FPL API.")
        team_data = fpl_client.get_my_team_data(team_id) 
        
        if not team_data:
            # If data fetch fails, no cookie is set, and render an error
            return render_template('error.html', 
                                 message=f"Could not load team {team_id}. Please check the ID and try again.")
        
        # Store the raw team data perpetually (max_age=None or a very large number)
        # We will use the SmartDataCache's default setting for perpetual storage if max_age is not passed
        cache.set(team_cache_key, team_data) 
        print(f"✅ Team data for {team_id} successfully cached.")
    else:
        print(f"🧠 Using cached data for team {team_id}.")

    # --- 2. Processing and Rendering Logic (Remains the same) ---
    starters = [p for p in team_data['team'] if not p['bench_position']]
    bench = [p for p in team_data['team'] if p['bench_position']]
    
    # ... (Rest of processing logic for team_by_position, problems, etc.) ...
    
    team_by_position = {
        'GKP': [p for p in starters if p['position'] == 'GKP'],
        'DEF': [p for p in starters if p['position'] == 'DEF'],
        'MID': [p for p in starters if p['position'] == 'MID'],
        'FWD': [p for p in starters if p['position'] == 'FWD']
    }
    
    problems = []
    
    for player in team_data['team']:
        player_problems = []
        
        # Dead Wood: < 2 pts/game AND < 60% minutes
        if player['points_per_game'] < 2 and player['minutes_pct'] < 60:
            player_problems.append({
                'type': 'dead_wood',
                'severity': 'urgent',
                'message': f"Dead wood: {player['points_per_game']:.1f} pts/game, {player['minutes_pct']:.0f}% minutes"
            })
        
        # Rotation Risk: < 70% minutes in last 5
        elif player['minutes_pct'] < 70 and player['minutes_pct'] > 0:
            player_problems.append({
                'type': 'rotation_risk',
                'severity': 'warning',
                'message': f"Rotation risk: Only {player['minutes_pct']:.0f}% minutes"
            })
        
        # Injury concern
        if player['chance_of_playing'] and player['chance_of_playing'] < 100:
            player_problems.append({
                'type': 'injury',
                'severity': 'urgent' if player['chance_of_playing'] < 75 else 'warning',
                'message': f"Injury concern: {player['chance_of_playing']}% chance of playing"
            })
        
        # Poor form
        if player['form'] < 2 and player['total_points'] > 0:
            player_problems.append({
                'type': 'poor_form',
                'severity': 'warning',
                'message': f"Poor form: {player['form']} form rating"
            })
        
        if player_problems:
            player['problems'] = player_problems
            problems.append({
                'player': player,
                'issues': player_problems
            })
    
    problems.sort(key=lambda x: 0 if any(p['severity'] == 'urgent' for p in x['issues']) else 1)
    
    # 3. Render and Set Cookie (Existing Logic)
    rendered_template = render_template('my_team.html', 
                                         team_data=team_data,
                                         team_by_position=team_by_position,
                                         bench=bench,
                                         problems=problems,
                                         team_id=team_id)
    
    response = make_response(rendered_template)
    
    # Set the cookie to remember the team ID for 30 days
    response.set_cookie('fpl_team_id', str(team_id), max_age=30 * 24 * 3600)
    # The print statement is optional but good for debugging:
    # print(f"✅ Successfully set cookie for team ID: {team_id}")

    return response

@app.route('/my-team/refresh/<int:team_id>')
def refresh_my_team(team_id):
    """
    Clears the cached team data for the given team ID using the new cache.delete() 
    and redirects to the team view, triggering a fresh API call.
    """
    team_cache_key = f'team_{team_id}'

    # 🔥 FIX: Use the new dedicated delete method
    if cache.delete(team_cache_key): 
        print(f"🔥 Team data for ID {team_id} cleared from cache. Forcing API refresh.")
    else:
        print(f"⚠️ Team data for ID {team_id} was not found in cache.")

    # Redirect back to the main team viewing page
    return redirect(f'/my-team/{team_id}')

@app.route('/refresh-now')
def manual_refresh():
    """
    Manual FPL Data refresh endpoint. 
    NOTE: LLM headlines must be refreshed via /llm-refresh-now
    """
    print("\n🔄 Manual FPL Data refresh requested by user")
    scheduled_data_refresh(cache) 
    return "FPL Data refresh triggered! Check console for details.", 200

@app.route('/llm-refresh-now')
def manual_llm_refresh():
    """
    Clears the cached LLM headlines, forcing a regeneration of new headlines
    on the next visit to the analysis page.
    """
    llm_key = 'llm_headlines'
    
    if cache.delete(llm_key):
        message = "✅ LLM headlines cache cleared. New analysis will be generated on next page view."
        print(f"\n{message}")
    else:
        message = "⚠️ LLM headlines were not in the cache, no action taken."
        print(f"\n{message}")
        
    # Redirect to the analysis page to immediately trigger regeneration
    return redirect(url_for('analysis_overview'))

@app.route('/cache-status')
def cache_status():
    """Show cache status for debugging"""
    if cache.is_empty(): 
        return {
            "status": "empty",
            "message": "Cache is empty"
        }
    
    next_update = cache.get_next_update_time()
    now = datetime.now(timezone.utc)
    time_until = next_update - now
    
    return {
        "status": "active",
        "current_gw": cache.current_gw,
        "last_updated": cache.last_updated.strftime('%Y-%m-%d %H:%M:%S UTC') if cache.last_updated else None,
        "next_update": next_update.strftime('%Y-%m-%d %H:%M:%S UTC'),
        "time_until_next_update": f"{int(time_until.total_seconds() // 3600)}h {int((time_until.total_seconds() % 3600) // 60)}m",
        "headlines_cached": 'llm_headlines' in cache.cache_items
    }

if __name__ == '__main__':
    app.run(debug=True)
