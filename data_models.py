import pandas as pd

"""
data_models.py

Schema definitions and view configurations for FPL player data.
This is the single source of truth for all field definitions.
"""

# ============================================================================
# FIELD CATEGORIES
# ============================================================================
# Organizes all 80+ CSV fields into logical groups

FIELD_CATEGORIES = {
    # Basic identification
    'identity': [
        'id', 'web_name', 'first_name', 'second_name', 
        'team_name', 'position', 'status'
    ],
    
    # Pricing and cost changes
    'pricing': [
        'now_cost', 'cost_change_event', 'cost_change_start',
        'cost_change_event_fall', 'cost_change_start_fall'
    ],
    
    # Selection and transfers
    'selection': [
        'selected_by_percent', 'selected_rank', 'selected_rank_type',
        'transfers_in', 'transfers_out', 'transfers_in_event', 
        'transfers_out_event', 'dreamteam_count'
    ],
    
    # Core performance metrics
    'performance': [
        'total_points', 'event_points', 'points_per_game', 
        'points_per_game_rank', 'points_per_game_rank_type',
        'form', 'form_rank', 'form_rank_type',
        'bonus', 'bps', 'value_form', 'value_season'
    ],
    
    # Advanced metrics (ICT)
    'advanced_metrics': [
        'ict_index', 'ict_index_rank', 'ict_index_rank_type',
        'influence', 'influence_rank', 'influence_rank_type',
        'creativity', 'creativity_rank', 'creativity_rank_type',
        'threat', 'threat_rank', 'threat_rank_type'
    ],
    
    # Expected stats
    'expected_stats': [
        'expected_goals', 'expected_assists', 'expected_goal_involvements',
        'expected_goals_conceded', 'expected_goals_per_90', 
        'expected_assists_per_90', 'expected_goal_involvements_per_90',
        'expected_goals_conceded_per_90', 'ep_next', 'ep_this'
    ],
    
    # Goalkeeper specific
    'goalkeeper': [
        'saves', 'saves_per_90', 'save_value_per_million', 'penalties_saved'
    ],
    
    # Defensive stats
    'defensive': [
        'clean_sheets', 'clean_sheets_per_90', 'goals_conceded',
        'goals_conceded_per_90', 'defensive_contribution',
        'defensive_contribution_per_90', 'tackles',
        'clearances_blocks_interceptions', 'recoveries'
    ],
    
    # Playing time
    'minutes': [
        'minutes', 'starts', 'starts_per_90'
    ],
    
    # Attacking stats
    'attacking': [
        'goals_scored', 'assists'
    ],
    
    # Discipline
    'discipline': [
        'yellow_cards', 'red_cards', 'own_goals', 'penalties_missed'
    ],
    
    # Set pieces
    'set_pieces': [
        'corners_and_indirect_freekicks_order', 'direct_freekicks_order',
        'penalties_order', 'set_piece_threat',
        'corners_and_indirect_freekicks_text', 'direct_freekicks_text',
        'penalties_text'
    ],
    
    # News and availability (from CSV)
    'news_csv': [
        'news', 'news_added'
    ],
    
    # FPL API live data (added during enrichment)
    'fpl_live': [
        'chance_of_playing_next_round', 'chance_of_playing_this_round',
        'is_in_my_team', 'my_team_position', 'is_captain', 
        'is_vice_captain', 'bench_position'
    ],
    
    # Calculated fields (computed by PlayerDataFrame)
    'calculated': [
        'points_per_million', 'minutes_pct', 'value_score'
    ],
    
    # Risk flags (computed by RiskAnalyzer)
    'risk_flags': [
        'rotation_risk', 'rotation_severity', 'dead_wood',
        'form_concern', 'injury_risk', 'injury_severity',
        'value_concern', 'total_risk_flags'
    ],
    
    # Metadata
    'metadata': [
        'gw', 'current_gw', 'stats_gw', 'gw_status'
    ]
}

# ============================================================================
# VIEW CONFIGURATIONS
# ============================================================================
# Defines which columns to show for different pages/tables

VIEW_CONFIGS = {
    # Analysis Overview - Top 10 overall
    'overview_table': {
        'columns': [
            'web_name', 'team_name', 'position', 'now_cost', 
            'selected_by_percent', 'total_points', 'form', 
            'expected_goal_involvements', 'points_per_million'
        ],
        'sort_by': 'total_points',
        'ascending': False,
        'filters': {
            'minutes': 90  # Minimum 90 minutes played
        }
    },
    
    # Analysis Overview - By Position
    'position_overview': {
        'columns': [
            'web_name', 'team_name', 'now_cost', 'selected_by_percent',
            'total_points', 'form', 'clean_sheets', 'points_per_million'
        ],
        'sort_by': 'total_points',
        'ascending': False,
        'filters': {
            'minutes': 90
        }
    },
    
    # Goalkeeper-specific view
    'goalkeeper_analysis': {
        'columns': [
            'web_name', 'team_name', 'now_cost', 'selected_by_percent',
            'total_points', 'saves_per_90', 'clean_sheets',
            'save_value_per_million', 'points_per_million'
        ],
        'sort_by': 'save_value_per_million',
        'ascending': False,
        'filters': {
            'minutes': 90
        }
    },
    
    # Outfield players (DEF/MID/FWD)
    'outfield_analysis': {
        'columns': [
            'web_name', 'team_name', 'now_cost', 'selected_by_percent',
            'total_points', 'expected_goal_involvements', 
            'clean_sheets', 'form', 'points_per_million'
        ],
        'sort_by': 'expected_goal_involvements',
        'ascending': False,
        'filters': {
            'minutes': 90
        }
    },
    
    # My Team - Detailed view with risk metrics
    'my_team_detailed': {
        'columns': [
            'web_name', 'position', 'team_name', 'now_cost', 
            'total_points', 'form', 'minutes', 'minutes_pct',
            'expected_goal_involvements', 'ict_index',
            'chance_of_playing_next_round', 'news',
            'my_team_position', 'is_captain', 'is_vice_captain'
        ],
        'sort_by': 'my_team_position',
        'ascending': True,
        'filters': {}
    },
    
    # Transfer Search - Finding replacements
    'transfer_search': {
        'columns': [
            'web_name', 'team_name', 'position', 'now_cost', 
            'selected_by_percent', 'total_points', 'form',
            'expected_goal_involvements', 'ict_index',
            'points_per_million', 'value_score',
            'minutes_pct', 'chance_of_playing_next_round'
        ],
        'sort_by': 'value_score',
        'ascending': False,
        'filters': {
            'minutes': 180,  # At least 180 minutes
            'chance_of_playing_next_round': 75  # At least 75% available
        }
    },
    
    # Differentials - Low ownership, high value
    'differentials': {
        'columns': [
            'web_name', 'team_name', 'position', 'now_cost',
            'selected_by_percent', 'total_points', 'form',
            'expected_goal_involvements', 'points_per_million'
        ],
        'sort_by': 'expected_goal_involvements',
        'ascending': False,
        'filters': {
            'selected_by_percent': (0, 10),  # Less than 10% owned
            'minutes': 180
        }
    },
    
    # Defensive Contribution
    'defensive_contribution': {
        'columns': [
            'web_name', 'team_name', 'position', 'now_cost',
            'total_points', 'clean_sheets', 'defensive_contribution',
            'defensive_contribution_per_90'
        ],
        'sort_by': 'defensive_contribution',
        'ascending': False,
        'filters': {
            'minutes': 180
        }
    }
}

# ============================================================================
# FIELD METADATA
# ============================================================================
# Defines display names, data types, and formatting for each field

FIELD_METADATA = {
    # Identity fields
    'id': {
        'display_name': 'ID',
        'type': 'int',
        'format': None,
        'description': 'Player ID'
    },
    'web_name': {
        'display_name': 'Player',
        'type': 'str',
        'format': None,
        'description': 'Player display name'
    },
    'first_name': {
        'display_name': 'First Name',
        'type': 'str',
        'format': None,
        'description': 'Player first name'
    },
    'second_name': {
        'display_name': 'Last Name',
        'type': 'str',
        'format': None,
        'description': 'Player last name'
    },
    'team_name': {
        'display_name': 'Team',
        'type': 'str',
        'format': None,
        'description': 'Team name'
    },
    'position': {
        'display_name': 'Pos',
        'type': 'str',
        'format': None,
        'description': 'Position'
    },
    
    # Pricing
    'now_cost': {
        'display_name': 'Price',
        'type': 'float',
        'format': '£{:.1f}m',
        'description': 'Current price'
    },
    'cost_change_event': {
        'display_name': 'Price Δ',
        'type': 'float',
        'format': '{:+.1f}',
        'description': 'Price change this GW'
    },
    
    # Performance
    'total_points': {
        'display_name': 'Points',
        'type': 'int',
        'format': '{:,}',
        'description': 'Total points'
    },
    'event_points': {
        'display_name': 'GW Pts',
        'type': 'int',
        'format': '{}',
        'description': 'Gameweek points'
    },
    'points_per_game': {
        'display_name': 'Pts/Game',
        'type': 'float',
        'format': '{:.1f}',
        'description': 'Points per game'
    },
    'form': {
        'display_name': 'Form',
        'type': 'float',
        'format': '{:.1f}',
        'description': 'Form rating'
    },
    'bonus': {
        'display_name': 'Bonus',
        'type': 'int',
        'format': '{}',
        'description': 'Bonus points'
    },
    'bps': {
        'display_name': 'BPS',
        'type': 'int',
        'format': '{}',
        'description': 'Bonus points system score'
    },
    
    # Selection
    'selected_by_percent': {
        'display_name': 'Own %',
        'type': 'float',
        'format': '{:.1f}%',
        'description': 'Ownership percentage'
    },
    'transfers_in': {
        'display_name': 'Transfers In',
        'type': 'int',
        'format': '{:,}',
        'description': 'Total transfers in'
    },
    'transfers_out': {
        'display_name': 'Transfers Out',
        'type': 'int',
        'format': '{:,}',
        'description': 'Total transfers out'
    },
    'transfers_in_event': {
        'display_name': 'GW In',
        'type': 'int',
        'format': '{:,}',
        'description': 'Transfers in this GW'
    },
    'transfers_out_event': {
        'display_name': 'GW Out',
        'type': 'int',
        'format': '{:,}',
        'description': 'Transfers out this GW'
    },
    
    # Advanced metrics
    'ict_index': {
        'display_name': 'ICT',
        'type': 'float',
        'format': '{:.1f}',
        'description': 'ICT Index'
    },
    'influence': {
        'display_name': 'Influence',
        'type': 'float',
        'format': '{:.1f}',
        'description': 'Influence score'
    },
    'creativity': {
        'display_name': 'Creativity',
        'type': 'float',
        'format': '{:.1f}',
        'description': 'Creativity score'
    },
    'threat': {
        'display_name': 'Threat',
        'type': 'float',
        'format': '{:.1f}',
        'description': 'Threat score'
    },
    
    # Expected stats
    'expected_goals': {
        'display_name': 'xG',
        'type': 'float',
        'format': '{:.2f}',
        'description': 'Expected goals'
    },
    'expected_assists': {
        'display_name': 'xA',
        'type': 'float',
        'format': '{:.2f}',
        'description': 'Expected assists'
    },
    'expected_goal_involvements': {
        'display_name': 'xGI',
        'type': 'float',
        'format': '{:.2f}',
        'description': 'Expected goal involvements'
    },
    'expected_goals_per_90': {
        'display_name': 'xG/90',
        'type': 'float',
        'format': '{:.2f}',
        'description': 'Expected goals per 90'
    },
    'expected_assists_per_90': {
        'display_name': 'xA/90',
        'type': 'float',
        'format': '{:.2f}',
        'description': 'Expected assists per 90'
    },
    'expected_goal_involvements_per_90': {
        'display_name': 'xGI/90',
        'type': 'float',
        'format': '{:.2f}',
        'description': 'Expected goal involvements per 90'
    },
    
    # Goalkeeper
    'saves': {
        'display_name': 'Saves',
        'type': 'int',
        'format': '{}',
        'description': 'Total saves'
    },
    'saves_per_90': {
        'display_name': 'Saves/90',
        'type': 'float',
        'format': '{:.1f}',
        'description': 'Saves per 90 minutes'
    },
    'save_value_per_million': {
        'display_name': 'Save Value',
        'type': 'float',
        'format': '{:.2f}',
        'description': 'Save value per million'
    },
    
    # Defensive
    'clean_sheets': {
        'display_name': 'CS',
        'type': 'int',
        'format': '{}',
        'description': 'Clean sheets'
    },
    'goals_conceded': {
        'display_name': 'GC',
        'type': 'int',
        'format': '{}',
        'description': 'Goals conceded'
    },
    'defensive_contribution': {
        'display_name': 'Def Cont',
        'type': 'float',
        'format': '{:.1f}',
        'description': 'Defensive contribution'
    },
    'defensive_contribution_per_90': {
        'display_name': 'Def/90',
        'type': 'float',
        'format': '{:.2f}',
        'description': 'Defensive contribution per 90'
    },
    
    # Minutes
    'minutes': {
        'display_name': 'Mins',
        'type': 'int',
        'format': '{:,}',
        'description': 'Minutes played'
    },
    'starts': {
        'display_name': 'Starts',
        'type': 'int',
        'format': '{}',
        'description': 'Starts'
    },
    
    # Attacking
    'goals_scored': {
        'display_name': 'Goals',
        'type': 'int',
        'format': '{}',
        'description': 'Goals scored'
    },
    'assists': {
        'display_name': 'Assists',
        'type': 'int',
        'format': '{}',
        'description': 'Assists'
    },
    
    # Availability
    'chance_of_playing_next_round': {
        'display_name': 'Avail.',
        'type': 'int',
        'format': '{}%',
        'description': 'Chance of playing next round'
    },
    'news': {
        'display_name': 'News',
        'type': 'str',
        'format': None,
        'description': 'Injury/suspension news'
    },
    
    # Calculated fields
    'points_per_million': {
        'display_name': 'Pts/£',
        'type': 'float',
        'format': '{:.1f}',
        'description': 'Points per million'
    },
    'minutes_pct': {
        'display_name': 'Mins %',
        'type': 'float',
        'format': '{:.0f}%',
        'description': 'Minutes percentage'
    },
    'value_score': {
        'display_name': 'Value',
        'type': 'float',
        'format': '{:.2f}',
        'description': 'Composite value score'
    },
    
    # Team position
    'my_team_position': {
        'display_name': 'Pos',
        'type': 'int',
        'format': '{}',
        'description': 'Team position (1-15)'
    },
    'is_captain': {
        'display_name': 'Captain',
        'type': 'bool',
        'format': None,
        'description': 'Is captain'
    },
    'is_vice_captain': {
        'display_name': 'Vice',
        'type': 'bool',
        'format': None,
        'description': 'Is vice captain'
    }
}

# ============================================================================
# POSITION MAPPING
# ============================================================================

POSITION_MAP = {
    'Goalkeeper': 'GK',
    'Defender': 'DEF',
    'Midfielder': 'MID',
    'Forward': 'FWD',
    # Reverse mapping
    'GK': 'Goalkeeper',
    'DEF': 'Defender',
    'MID': 'Midfielder',
    'FWD': 'Forward'
}

# FPL API position type to full name
POSITION_TYPE_MAP = {
    1: 'Goalkeeper',
    2: 'Defender',
    3: 'Midfielder',
    4: 'Forward'
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_all_fields():
    """Get a flat list of all available fields"""
    all_fields = []
    for category, fields in FIELD_CATEGORIES.items():
        all_fields.extend(fields)
    return list(set(all_fields))  # Remove duplicates

def get_fields_by_category(category):
    """Get fields for a specific category"""
    return FIELD_CATEGORIES.get(category, [])

def get_display_name(field):
    """Get the display name for a field"""
    return FIELD_METADATA.get(field, {}).get('display_name', field)

def get_field_format(field):
    """Get the format string for a field"""
    return FIELD_METADATA.get(field, {}).get('format')

def format_value(field, value):
    """Format a value according to its field metadata"""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return '-'
    
    format_str = get_field_format(field)
    if format_str:
        try:
            return format_str.format(value)
        except (ValueError, TypeError):
            return str(value)
    return str(value)
