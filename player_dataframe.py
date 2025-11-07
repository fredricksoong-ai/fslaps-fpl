"""
player_dataframe.py

Wrapper class around pandas DataFrame with FPL-specific functionality.
Handles calculated fields, filtering, sorting, and display formatting.
"""

import pandas as pd
from data_models import (
    FIELD_METADATA, VIEW_CONFIGS, POSITION_MAP, 
    get_field_format, format_value
)


class PlayerDataFrame:
    """
    Enhanced DataFrame specifically for FPL player data.
    Knows about field types, display formats, and common operations.
    """
    
    def __init__(self, df, metadata=None):
        """
        Initialize with a pandas DataFrame.
        
        Args:
            df: pandas DataFrame with player data
            metadata: Optional field metadata dict (defaults to FIELD_METADATA)
        """
        self.df = df.copy()  # Make a copy to avoid modifying original
        self.metadata = metadata or FIELD_METADATA
        
        # Ensure required columns exist
        self._ensure_required_columns()
        
        # Calculate derived fields
        self._apply_calculated_fields()
    
    def _ensure_required_columns(self):
        """
        Make sure essential columns exist with sensible defaults.
        This prevents KeyErrors when accessing fields that might not exist.
        """
        # FPL API columns (added during enrichment, default to False/None)
        if 'is_in_my_team' not in self.df.columns:
            self.df['is_in_my_team'] = False
        
        if 'my_team_position' not in self.df.columns:
            self.df['my_team_position'] = None
        
        if 'is_captain' not in self.df.columns:
            self.df['is_captain'] = False
        
        if 'is_vice_captain' not in self.df.columns:
            self.df['is_vice_captain'] = False
        
        if 'bench_position' not in self.df.columns:
            self.df['bench_position'] = False
        
        # Availability (default to 100% available if not present)
        if 'chance_of_playing_next_round' not in self.df.columns:
            self.df['chance_of_playing_next_round'] = 100
        
        if 'chance_of_playing_this_round' not in self.df.columns:
            self.df['chance_of_playing_this_round'] = 100
        
        if 'news' not in self.df.columns:
            self.df['news'] = ''
        
        # Ensure position is string type
        if 'position' in self.df.columns:
            self.df['position'] = self.df['position'].astype(str)
    
    def _apply_calculated_fields(self):
        """
        Calculate derived metrics that aren't in the raw CSV.
        """
        # Points per million
        if 'total_points' in self.df.columns and 'now_cost' in self.df.columns:
            self.df['points_per_million'] = (
                self.df['total_points'] / self.df['now_cost']
            ).where(self.df['now_cost'] > 0, 0).fillna(0)
        
        # Minutes percentage
        if 'minutes' in self.df.columns and 'current_gw' in self.df.columns:
            # Get the current GW (should be the same for all rows)
            if len(self.df) > 0 and not self.df['current_gw'].isna().all():
                current_gw = self.df['current_gw'].iloc[0]
                max_minutes_possible = current_gw * 90
                
                if max_minutes_possible > 0:
                    self.df['minutes_pct'] = (
                        (self.df['minutes'] / max_minutes_possible) * 100
                    ).clip(0, 100).fillna(0)
                else:
                    self.df['minutes_pct'] = 0
            else:
                self.df['minutes_pct'] = 0
        elif 'minutes' not in self.df.columns:
            self.df['minutes_pct'] = 0
        
        # Value score (composite metric: PPM + Form + xGI)
        # This is a weighted combination of key metrics
        if all(col in self.df.columns for col in ['points_per_million', 'form', 'expected_goal_involvements']):
            # Normalize each component to 0-1 scale
            ppm_max = self.df['points_per_million'].max()
            form_max = self.df['form'].astype(float).max()
            xgi_max = self.df['expected_goal_involvements'].max()
            
            ppm_norm = self.df['points_per_million'] / ppm_max if ppm_max > 0 else 0
            form_norm = self.df['form'].astype(float) / form_max if form_max > 0 else 0
            xgi_norm = self.df['expected_goal_involvements'] / xgi_max if xgi_max > 0 else 0
            
            # Weighted average (40% PPM, 30% Form, 30% xGI)
            self.df['value_score'] = (
                ppm_norm * 0.4 + 
                form_norm * 0.3 + 
                xgi_norm * 0.3
            ).fillna(0)
        else:
            self.df['value_score'] = 0
        
        # Map position to short codes if needed
        if 'position' in self.df.columns:
            self.df['position_short'] = self.df['position'].map(
                lambda x: POSITION_MAP.get(x, x)
            )
    
    def get_view(self, view_name):
        """
        Get data formatted for a specific view configuration.
        
        Args:
            view_name: Name of the view from VIEW_CONFIGS
        
        Returns:
            PlayerDataFrame with filtered and sorted data
        """
        config = VIEW_CONFIGS.get(view_name)
        if not config:
            print(f"Warning: View '{view_name}' not found. Returning full dataset.")
            return self
        
        # Start with a copy of the dataframe
        filtered_df = self.df.copy()
        
        # Apply filters
        filters = config.get('filters', {})
        for field, filter_value in filters.items():
            if field not in filtered_df.columns:
                continue
            
            if isinstance(filter_value, tuple):
                # Range filter: (min, max)
                min_val, max_val = filter_value
                filtered_df = filtered_df[
                    (filtered_df[field] >= min_val) & 
                    (filtered_df[field] <= max_val)
                ]
            else:
                # Minimum value filter
                filtered_df = filtered_df[filtered_df[field] >= filter_value]
        
        # Select columns (only include columns that exist)
        columns = config.get('columns', [])
        available_columns = [col for col in columns if col in filtered_df.columns]
        
        if available_columns:
            filtered_df = filtered_df[available_columns]
        
        # Sort
        sort_by = config.get('sort_by')
        ascending = config.get('ascending', False)
        
        if sort_by and sort_by in filtered_df.columns:
            filtered_df = filtered_df.sort_values(sort_by, ascending=ascending)
        
        # Return as new PlayerDataFrame
        return PlayerDataFrame(filtered_df, self.metadata)
    
    def filter_by_position(self, position):
        """
        Filter to a specific position.
        
        Args:
            position: Position name (e.g., 'Midfielder', 'MID', 'Defender')
        
        Returns:
            PlayerDataFrame with only players in that position
        """
        # Handle both full name and short code
        if position in POSITION_MAP:
            # If it's a short code, convert to full name
            if len(position) <= 3:
                position_full = POSITION_MAP[position]
            else:
                position_full = position
        else:
            position_full = position
        
        filtered_df = self.df[self.df['position'] == position_full].copy()
        return PlayerDataFrame(filtered_df, self.metadata)
    
    def filter_by_team(self, team_name):
        """
        Filter to players from a specific team.
        
        Args:
            team_name: Team name (e.g., 'Arsenal', 'ARS')
        
        Returns:
            PlayerDataFrame with only players from that team
        """
        if 'team_name' not in self.df.columns:
            return self
        
        filtered_df = self.df[self.df['team_name'] == team_name].copy()
        return PlayerDataFrame(filtered_df, self.metadata)
    
    def filter_by_price(self, min_price=None, max_price=None):
        """
        Filter by price range.
        
        Args:
            min_price: Minimum price (e.g., 4.5)
            max_price: Maximum price (e.g., 12.0)
        
        Returns:
            PlayerDataFrame with players in price range
        """
        if 'now_cost' not in self.df.columns:
            return self
        
        filtered_df = self.df.copy()
        
        if min_price is not None:
            filtered_df = filtered_df[filtered_df['now_cost'] >= min_price]
        
        if max_price is not None:
            filtered_df = filtered_df[filtered_df['now_cost'] <= max_price]
        
        return PlayerDataFrame(filtered_df, self.metadata)
    
    def get_my_team(self):
        """
        Get only players in the user's team.
        
        Returns:
            PlayerDataFrame with only players where is_in_my_team is True
        """
        filtered_df = self.df[self.df['is_in_my_team'] == True].copy()
        return PlayerDataFrame(filtered_df, self.metadata)
    
    def exclude_my_team(self):
        """
        Get players NOT in the user's team.
        Useful for transfer search.
        
        Returns:
            PlayerDataFrame excluding user's players
        """
        filtered_df = self.df[self.df['is_in_my_team'] == False].copy()
        return PlayerDataFrame(filtered_df, self.metadata)
    
    def get_starters(self):
        """
        Get starting XI (positions 1-11).
        
        Returns:
            PlayerDataFrame with only starters
        """
        if 'my_team_position' not in self.df.columns:
            return self
        
        filtered_df = self.df[
            (self.df['my_team_position'].notna()) & 
            (self.df['my_team_position'] <= 11)
        ].copy()
        return PlayerDataFrame(filtered_df, self.metadata)
    
    def get_bench(self):
        """
        Get bench players (positions 12-15).
        
        Returns:
            PlayerDataFrame with only bench players
        """
        if 'my_team_position' not in self.df.columns:
            return self
        
        filtered_df = self.df[
            (self.df['my_team_position'].notna()) & 
            (self.df['my_team_position'] > 11)
        ].copy()
        return PlayerDataFrame(filtered_df, self.metadata)
    
    def top_n(self, n, sort_by='total_points'):
        """
        Get top N players by a metric.
        
        Args:
            n: Number of players to return
            sort_by: Field to sort by (default: total_points)
        
        Returns:
            PlayerDataFrame with top N players
        """
        if sort_by not in self.df.columns:
            return self
        
        sorted_df = self.df.nlargest(n, sort_by)
        return PlayerDataFrame(sorted_df, self.metadata)
    
    def to_dict(self, orient='records'):
        """
        Convert to dictionary.
        
        Args:
            orient: pandas to_dict orientation (default: 'records')
        
        Returns:
            Dictionary representation
        """
        return self.df.to_dict(orient=orient)
    
    def to_display_dict(self, view_name=None, format_values=True):
        """
        Convert to dictionary with formatted values for display in templates.
        
        Args:
            view_name: Optional view configuration to apply first
            format_values: Whether to format values according to metadata
        
        Returns:
            List of dictionaries with formatted values
        """
        # Apply view if specified
        if view_name:
            df_to_convert = self.get_view(view_name).df
        else:
            df_to_convert = self.df
        
        # Convert to records
        records = df_to_convert.to_dict('records')
        
        # Format values if requested
        if format_values:
            for record in records:
                for field, value in list(record.items()):
                    # Apply formatting based on metadata
                    formatted = format_value(field, value)
                    record[field] = formatted
                    
                    # Also keep raw value for sorting/calculations
                    record[f'{field}_raw'] = value
        
        return records
    
    def __len__(self):
        """Return number of players"""
        return len(self.df)
    
    def __repr__(self):
        """String representation"""
        return f"PlayerDataFrame({len(self)} players)"
    
    def head(self, n=5):
        """Get first n rows"""
        return PlayerDataFrame(self.df.head(n), self.metadata)
    
    def tail(self, n=5):
        """Get last n rows"""
        return PlayerDataFrame(self.df.tail(n), self.metadata)
    
    @property
    def columns(self):
        """Get list of columns"""
        return self.df.columns.tolist()
    
    @property
    def shape(self):
        """Get shape of dataframe"""
        return self.df.shape
