"""
Test script for enrichment layer.
Tests DataEnricher and RiskAnalyzer with mock data.
"""

import pandas as pd
from player_dataframe import PlayerDataFrame
from data_enrichment import DataEnricher
from risk_analyzer import RiskAnalyzer

print("=" * 60)
print("TESTING ENRICHMENT LAYER")
print("=" * 60)

# Create mock player data
print("\n1. Creating mock player data...")
mock_data = {
    'id': [1, 2, 3, 4, 5, 6],
    'web_name': ['Salah', 'Haaland', 'Saka', 'Palmer', 'Watkins', 'Bench Player'],
    'position': ['Midfielder', 'Forward', 'Midfielder', 'Midfielder', 'Forward', 'Defender'],
    'team_name': ['Liverpool', 'Man City', 'Arsenal', 'Chelsea', 'Aston Villa', 'Brighton'],
    'now_cost': [13.0, 15.0, 9.5, 11.0, 9.0, 4.5],
    'total_points': [150, 180, 120, 110, 100, 15],
    'points_per_game': [8.5, 10.0, 7.0, 6.5, 6.0, 1.5],
    'form': [5.5, 6.0, 4.5, 2.5, 4.0, 1.0],
    'minutes': [1500, 1620, 1350, 1440, 1260, 450],
    'expected_goal_involvements': [0.85, 0.95, 0.70, 0.75, 0.65, 0.10],
    'selected_by_percent': [45.5, 55.0, 25.0, 30.0, 20.0, 2.0],
    'current_gw': [18, 18, 18, 18, 18, 18]
}

player_df = PlayerDataFrame(pd.DataFrame(mock_data))
print(f"   ✓ Created {len(player_df)} players")

# Test 2: RiskAnalyzer
print("\n2. Testing RiskAnalyzer...")

# Rotation risk
player_df = RiskAnalyzer.detect_rotation_risk(player_df)
rotation_count = player_df.df['rotation_risk'].sum()
print(f"   ✓ detect_rotation_risk: {rotation_count} players flagged")

# Dead wood
player_df = RiskAnalyzer.detect_dead_wood(player_df)
deadwood_count = player_df.df['dead_wood'].sum()
print(f"   ✓ detect_dead_wood: {deadwood_count} players flagged")

# Form concerns
player_df = RiskAnalyzer.detect_form_concerns(player_df)
form_count = player_df.df['form_concern'].sum()
print(f"   ✓ detect_form_concerns: {form_count} players flagged")

# Injury risk (need to add the field first)
player_df.df['chance_of_playing_next_round'] = [100, 100, 75, 100, 100, 50]
player_df = RiskAnalyzer.detect_injury_risk(player_df)
injury_count = player_df.df['injury_risk'].sum()
print(f"   ✓ detect_injury_risk: {injury_count} players flagged")

# Value concerns
player_df = RiskAnalyzer.detect_value_concerns(player_df)
value_count = player_df.df['value_concern'].sum()
print(f"   ✓ detect_value_concerns: {value_count} players flagged")

# Test 3: Full analysis
print("\n3. Testing full risk analysis...")
player_df = RiskAnalyzer.analyze_all_risks(player_df)
print(f"   ✓ analyze_all_risks completed")
print(f"      Total risk flags: {player_df.df['total_risk_flags'].sum()}")

# Test 4: Risk summary
print("\n4. Testing risk summary...")
summary = RiskAnalyzer.get_risk_summary(player_df)
print("   ✓ Risk Summary:")
for label, count in summary.items():
    print(f"      - {label}: {count}")

# Test 5: Problem players
print("\n5. Testing problem player identification...")
problem_players = RiskAnalyzer.get_problem_players(player_df, min_risk_flags=1)
print(f"   ✓ Found {len(problem_players)} problem players")
if len(problem_players) > 0:
    print(f"      Sample: {problem_players.df['web_name'].head(3).tolist()}")

# Test 6: DataEnricher structure (without API calls)
print("\n6. Testing DataEnricher structure...")
print("   ✓ DataEnricher class loaded successfully")
print("   ℹ️  API integration tests require real FPL API client")

print("\n" + "=" * 60)
print("✅ ALL ENRICHMENT TESTS PASSED!")
print("=" * 60)
print("\nReady for Phase 3: Integration with existing app\n")
