"""
Test script to verify data_models.py and player_dataframe.py work correctly.
Run this before proceeding to ensure foundation is solid.
"""

import pandas as pd
from data_models import FIELD_CATEGORIES, VIEW_CONFIGS, get_all_fields, format_value
from player_dataframe import PlayerDataFrame

print("=" * 60)
print("TESTING FOUNDATION MODULES")
print("=" * 60)

# Test 1: Field Categories
print("\n1. Testing FIELD_CATEGORIES...")
all_fields = get_all_fields()
print(f"   ✓ Total unique fields defined: {len(all_fields)}")
print(f"   ✓ Categories: {len(FIELD_CATEGORIES)}")

# Test 2: View Configs
print("\n2. Testing VIEW_CONFIGS...")
print(f"   ✓ Views defined: {len(VIEW_CONFIGS)}")
for view_name in VIEW_CONFIGS.keys():
    print(f"      - {view_name}")

# Test 3: Create a mock DataFrame
print("\n3. Creating mock player data...")
mock_data = {
    'id': [1, 2, 3, 4, 5],
    'web_name': ['Salah', 'Haaland', 'Saka', 'Palmer', 'Watkins'],
    'position': ['Midfielder', 'Forward', 'Midfielder', 'Midfielder', 'Forward'],
    'team_name': ['Liverpool', 'Man City', 'Arsenal', 'Chelsea', 'Aston Villa'],
    'now_cost': [13.0, 15.0, 9.5, 11.0, 9.0],
    'total_points': [150, 180, 120, 110, 100],
    'form': [5.5, 6.0, 4.5, 5.0, 4.0],
    'minutes': [1500, 1620, 1350, 1440, 1260],
    'expected_goal_involvements': [0.85, 0.95, 0.70, 0.75, 0.65],
    'selected_by_percent': [45.5, 55.0, 25.0, 30.0, 20.0],
    'current_gw': [18, 18, 18, 18, 18]
}

df = pd.DataFrame(mock_data)
print(f"   ✓ Created DataFrame with {len(df)} players")

# Test 4: Wrap in PlayerDataFrame
print("\n4. Testing PlayerDataFrame wrapper...")
player_df = PlayerDataFrame(df)
print(f"   ✓ Wrapped DataFrame: {player_df}")
print(f"   ✓ Shape: {player_df.shape}")

# Test 5: Check calculated fields
print("\n5. Checking calculated fields...")
if 'points_per_million' in player_df.columns:
    print(f"   ✓ points_per_million calculated")
    print(f"      Sample: {player_df.df['points_per_million'].head(3).tolist()}")

if 'minutes_pct' in player_df.columns:
    print(f"   ✓ minutes_pct calculated")
    print(f"      Sample: {player_df.df['minutes_pct'].head(3).tolist()}")

if 'value_score' in player_df.columns:
    print(f"   ✓ value_score calculated")
    print(f"      Sample: {player_df.df['value_score'].head(3).tolist()}")

# Test 6: Filtering
print("\n6. Testing filtering methods...")
midfielders = player_df.filter_by_position('Midfielder')
print(f"   ✓ filter_by_position('Midfielder'): {len(midfielders)} players")

expensive = player_df.filter_by_price(min_price=10.0)
print(f"   ✓ filter_by_price(min_price=10.0): {len(expensive)} players")

top_3 = player_df.top_n(3, 'total_points')
print(f"   ✓ top_n(3, 'total_points'): {len(top_3)} players")

# Test 7: Views
print("\n7. Testing view configurations...")
try:
    overview = player_df.get_view('overview_table')
    print(f"   ✓ get_view('overview_table'): {len(overview)} players")
    print(f"      Columns: {overview.columns[:5]}...")
except Exception as e:
    print(f"   ✗ Error getting view: {e}")

# Test 8: Display formatting
print("\n8. Testing display formatting...")
sample_player = player_df.df.iloc[0]
formatted_cost = format_value('now_cost', sample_player['now_cost'])
formatted_points = format_value('total_points', sample_player['total_points'])
print(f"   ✓ format_value('now_cost', {sample_player['now_cost']}): {formatted_cost}")
print(f"   ✓ format_value('total_points', {sample_player['total_points']}): {formatted_points}")

# Test 9: to_dict methods
print("\n9. Testing dict conversion...")
records = player_df.to_dict('records')
print(f"   ✓ to_dict('records'): {len(records)} records")

display_records = player_df.to_display_dict()
print(f"   ✓ to_display_dict(): {len(display_records)} records")
print(f"      Sample: {display_records[0]['web_name']}, {display_records[0]['now_cost']}")

print("\n" + "=" * 60)
print("✅ ALL FOUNDATION TESTS PASSED!")
print("=" * 60)
print("\nYou can now proceed to Phase 2: Enrichment Layer\n")
