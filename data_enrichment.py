"""
data_enrichment.py

Handles merging of GitHub CSV data with live FPL API data.
Enriches player data with team information, availability, and live stats.
"""

from player_dataframe import PlayerDataFrame
import logging

logger = logging.getLogger(__name__)


class DataEnricher:
    """
    Handles merging of GitHub CSV data with live FPL API data.
    """
    
    def __init__(self, fpl_client):
        """
        Initialize with an FPL API client.
        
        Args:
            fpl_client: Instance of FPLApiClient
        """
        self.fpl_client = fpl_client
    
    def enrich_with_my_team(self, player_df, team_id):
        """
        Enrich player data with "My Team" information.
        Marks which players are in the user's team and adds team structure.
        
        Args:
            player_df: PlayerDataFrame with all players
            team_id: FPL team ID
        
        Returns:
            PlayerDataFrame with team enrichment
        """
        logger.info(f"Enriching data with team {team_id} information...")
        
        # Get team data from FPL API
        team_data = self.fpl_client.get_my_team_data(team_id)
        if not team_data:
            logger.warning(f"Could not fetch team data for team {team_id}")
            return player_df  # Return unchanged if API fails
        
        # Create a set of player IDs in the team
        my_team_ids = {p['id'] for p in team_data['team']}
        logger.info(f"Found {len(my_team_ids)} players in team {team_id}")
        
        # Create mappings for team structure
        position_map = {p['id']: p['position_order'] for p in team_data['team']}
        captain_id = next((p['id'] for p in team_data['team'] if p['is_captain']), None)
        vice_id = next((p['id'] for p in team_data['team'] if p['is_vice_captain']), None)
        
        # Mark players in team
        player_df.df['is_in_my_team'] = player_df.df['id'].isin(my_team_ids)
        
        # Add team position (1-15, where 1-11 are starters, 12-15 are bench)
        player_df.df['my_team_position'] = player_df.df['id'].map(position_map)
        
        # Mark bench players
        player_df.df['bench_position'] = (
            player_df.df['my_team_position'].notna() & 
            (player_df.df['my_team_position'] > 11)
        )
        
        # Mark captain and vice captain
        player_df.df['is_captain'] = player_df.df['id'] == captain_id
        player_df.df['is_vice_captain'] = player_df.df['id'] == vice_id
        
        logger.info(f"✓ Team enrichment complete")
        logger.info(f"  - Captain: {player_df.df[player_df.df['is_captain']]['web_name'].values[0] if captain_id else 'None'}")
        logger.info(f"  - Vice: {player_df.df[player_df.df['is_vice_captain']]['web_name'].values[0] if vice_id else 'None'}")
        
        # Store team metadata
        player_df.df.attrs['team_data'] = {
            'team_id': team_id,
            'manager_name': team_data['manager']['name'],
            'team_value': team_data['team_value'],
            'bank': team_data['bank'],
            'gameweek': team_data['gameweek']
        }
        
        return player_df
    
    def enrich_with_live_status(self, player_df, force_refresh=False):
        """
        Enrich with live availability data from FPL API bootstrap.
        Updates chance_of_playing, news, etc for ALL players.
        
        Args:
            player_df: PlayerDataFrame with all players
            force_refresh: Force refresh of bootstrap cache
        
        Returns:
            PlayerDataFrame with live status enrichment
        """
        logger.info("Enriching data with live player status...")
        
        # Get bootstrap data (uses FPL API's internal cache)
        bootstrap = self.fpl_client.get_bootstrap_data()
        if not bootstrap:
            logger.warning("Could not fetch bootstrap data")
            return player_df
        
        # Create lookup for live status
        live_data = {}
        for p in bootstrap['elements']:
            live_data[p['id']] = {
                'chance_of_playing_next_round': p.get('chance_of_playing_next_round', 100),
                'chance_of_playing_this_round': p.get('chance_of_playing_this_round', 100),
                'news': p.get('news', ''),
                'news_added': p.get('news_added'),
                'status': p.get('status', 'a'),  # a = available, d = doubtful, i = injured, etc.
                'fpl_selected_by': float(p.get('selected_by_percent', 0))
            }
        
        logger.info(f"Retrieved live status for {len(live_data)} players")
        
        # Update DataFrame with live data
        for field in ['chance_of_playing_next_round', 'chance_of_playing_this_round', 
                      'news', 'status', 'fpl_selected_by']:
            player_df.df[field] = player_df.df['id'].map(
                lambda x: live_data.get(x, {}).get(field, None)
            )
        
        # Fill NaN values with defaults
        player_df.df['chance_of_playing_next_round'] = player_df.df['chance_of_playing_next_round'].fillna(100)
        player_df.df['chance_of_playing_this_round'] = player_df.df['chance_of_playing_this_round'].fillna(100)
        player_df.df['news'] = player_df.df['news'].fillna('')
        player_df.df['status'] = player_df.df['status'].fillna('a')
        
        logger.info("✓ Live status enrichment complete")
        
        # Log injury/doubt concerns if any
        injured = len(player_df.df[player_df.df['chance_of_playing_next_round'] < 100])
        if injured > 0:
            logger.info(f"  - {injured} players flagged with availability concerns")
        
        return player_df
    
    def enrich_full(self, player_df, team_id=None, include_live_status=True):
        """
        Full enrichment pipeline: team data + live status.
        
        Args:
            player_df: PlayerDataFrame with all players
            team_id: Optional team ID to enrich with team data
            include_live_status: Whether to include live availability data
        
        Returns:
            Fully enriched PlayerDataFrame
        """
        logger.info("Starting full enrichment pipeline...")
        
        # Add team data if team_id provided
        if team_id:
            player_df = self.enrich_with_my_team(player_df, team_id)
        
        # Add live status
        if include_live_status:
            player_df = self.enrich_with_live_status(player_df)
        
        logger.info("✓ Full enrichment complete")
        return player_df
    
    def update_team_cache(self, player_df, team_id, cache):
        """
        Helper to update the cache with enriched team data.
        
        Args:
            player_df: Enriched PlayerDataFrame
            team_id: Team ID
            cache: SmartDataCache instance
        """
        team_cache_key = f'team_{team_id}'
        
        # Extract just the team's players
        my_team_df = player_df.get_my_team()
        
        # Store in cache
        cache.set(team_cache_key, my_team_df)
        logger.info(f"✓ Cached enriched data for team {team_id}")
