def get_my_team_data(self, team_id):
    """
    Get complete team data with player details.
    Returns team structure for enrichment (no calculations).
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
    
    # Build simple team structure (no calculations)
    enriched_team = []
    for pick in team_picks['picks']:
        player = players_dict.get(pick['element'])
        if player:
            team = teams_dict.get(player['team'])
            
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
                'is_captain': pick['is_captain'],
                'is_vice_captain': pick['is_vice_captain'],
                'multiplier': pick['multiplier'],
                'position_order': pick['position'],
                'bench_position': pick['position'] > 11,
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
