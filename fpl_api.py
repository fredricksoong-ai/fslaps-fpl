# fpl_api.py

import requests
from datetime import datetime, timedelta

FPL_API_BASE = "https://fantasy.premierleague.com/api"

class FPLApiClient:
    def __init__(self):
        self.session = requests.Session()
        self.bootstrap_cache = None
        self.bootstrap_cache_time = None
        self.cache_duration = timedelta(minutes=5)
    
    def get_bootstrap_data(self):
        """Get general FPL data (players, teams, gameweeks) with caching"""
        now = datetime.now()
        
        # Check cache
        if (self.bootstrap_cache and 
            self.bootstrap_cache_time and 
            now - self.bootstrap_cache_time < self.cache_duration):
            print("✓ Using cached FPL bootstrap data")
            return self.bootstrap_cache
        
        try:
            print("📥 Fetching FPL bootstrap data...")
            response = self.session.get(f"{FPL_API_BASE}/bootstrap-static/")
            response.raise_for_status()
            data = response.json()
            
            # Update cache
            self.bootstrap_cache = data
            self.bootstrap_cache_time = now
            print("✅ FPL bootstrap data loaded")
            
            return data
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching bootstrap data: {e}")
            return None
    
    def get_current_gameweek(self):
        """Get the current gameweek number from FPL API"""
        bootstrap = self.get_bootstrap_data()
        if not bootstrap:
            return None
        
        # Find current gameweek
        for gw in bootstrap['events']:
            if gw['is_current']:
                return gw['id']
        
        # If no current, find the next one
        for gw in bootstrap['events']:
            if gw['is_next']:
                return gw['id'] - 1 # Use the one before next
        
        return None
    
    def get_manager_info(self, team_id):
        """Get manager/team basic info"""
        try:
            print(f"📥 Fetching manager info for team {team_id}...")
            response = self.session.get(f"{FPL_API_BASE}/entry/{team_id}/")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching manager info: {e}")
            return None
    
    def get_team_picks(self, team_id, gameweek=None):
        """Get the current team selection for a manager"""
        if gameweek is None:
            gameweek = self.get_current_gameweek()
            if not gameweek:
                return None
        
        try:
            print(f"📥 Fetching team picks for GW{gameweek}...")
            response = self.session.get(
                f"{FPL_API_BASE}/entry/{team_id}/event/{gameweek}/picks/"
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching team picks: {e}")
            return None
    
    def get_my_team_data(self, team_id):
        """
        Get complete team data with player details
        Returns enriched team data ready for display
        """
        # Get bootstrap data for player details
        bootstrap = self.get_bootstrap_data()
        if not bootstrap:
            return None
        
        # Create lookup dictionaries
        players_dict = {p['id']: p for p in bootstrap['elements']}
        teams_dict = {t['id']: t for t in bootstrap['teams']}
        positions = {1: 'GKP', 2: 'DEF', 3: 'MID', 4: 'FWD'}
        
        # Get manager info
        manager_info = self.get_manager_info(team_id)
        if not manager_info:
            return None
        
        # Get current gameweek
        current_gw = self.get_current_gameweek()
        if not current_gw:
            return None
            
        # Get current team
        team_picks = self.get_team_picks(team_id, current_gw)
        if not team_picks:
            return None
        
        # Enrich player data
        enriched_team = []
        for pick in team_picks['picks']:
            player = players_dict.get(pick['element'])
            if player:
                team = teams_dict.get(player['team'])
                
                # --- Fixed Minutes Percentage Calculation ---
                minutes_pct = 0
                # Use current_gw as the max number of games played (90 mins each)
                # Note: If FPL is mid-season, this will use the correct GW.
                max_minutes_possible = current_gw * 90 
                
                if player['minutes'] > 0 and max_minutes_possible > 0:
                    minutes_pct = (player['minutes'] / max_minutes_possible) * 100
                
                enriched_player = {
                    'id': player['id'],
                    'web_name': player['web_name'],
                    'first_name': player['first_name'],
                    'second_name': player['second_name'],
                    'position': positions[player['element_type']],
                    'position_full': ['Goalkeeper', 'Defender', 'Midfielder', 'Forward'][player['element_type']-1],
                    'team': team['short_name'] if team else 'Unknown',
                    'team_code': team['code'] if team else None,
                    'price': player['now_cost'] / 10,
                    'selected_by': float(player['selected_by_percent']),
                    'total_points': player['total_points'],
                    'form': float(player['form']) if player['form'] else 0,
                    'points_per_game': float(player['points_per_game']) if player['points_per_game'] else 0,
                    'minutes': player['minutes'],
                    'minutes_pct': round(minutes_pct, 1),
                    'is_captain': pick['is_captain'],
                    'is_vice_captain': pick['is_vice_captain'],
                    'multiplier': pick['multiplier'],
                    'position_order': pick['position'],
                    'bench_position': pick['position'] > 11,
                    'transfers_in': player['transfers_in_event'],
                    'transfers_out': player['transfers_out_event'],
                    'news': player['news'] if player['news'] else '',
                    'chance_of_playing': player['chance_of_playing_next_round']
                }
                enriched_team.append(enriched_player)
        
        # Sort by position order (1-11 are starters, 12-15 are bench)
        enriched_team.sort(key=lambda x: x['position_order'])
        
        return {
            'manager': {
                'name': manager_info['name'],
                'team_name': manager_info['player_first_name'] + ' ' + manager_info['player_last_name'],
                'overall_rank': manager_info['summary_overall_rank'],
                'overall_points': manager_info['summary_overall_points']
            },
            'gameweek': current_gw,
            'team': enriched_team,
            'team_value': team_picks['entry_history']['value'] / 10,
            'bank': team_picks['entry_history']['bank'] / 10,
            'total_points': team_picks['entry_history']['total_points'],
            'gameweek_points': team_picks['entry_history']['points'],
            'transfers_made': team_picks['entry_history']['event_transfers'],
            'transfer_cost': team_picks['entry_history']['event_transfers_cost']
        }
