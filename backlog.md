# Feature Backlog

**Priority Levels:**
- **P0:** Must have (blocking other features)
- **P1:** Should have (high value)
- **P2:** Nice to have
- **P3:** Future consideration

**Status:**
- 🔴 Not Started
- 🟡 In Progress
- 🟢 Complete
- 🔵 Blocked

---

## 🚨 P0 Features (Critical Path)

### 1. FPL API Integration - Import My Team
**Status:** 🔴 Not Started  
**Priority:** P0  
**Effort:** Medium (4-6 hours)  
**Dependencies:** None

**Description:**
Connect to FPL Official API to fetch user's current team.

**Requirements:**
- User inputs their team ID
- Fetch current 15 players from API
- Display team with formation
- Show team value, total points
- Cache API responses (5 min)

**API Endpoints Needed:**
```
https://fantasy.premierleague.com/api/entry/{TEAM_ID}/
https://fantasy.premierleague.com/api/entry/{TEAM_ID}/event/{GW}/picks/
```

**Acceptance Criteria:**
- [ ] User can enter team ID
- [ ] Team loads in < 5 seconds
- [ ] Shows all 15 players with names, positions, prices
- [ ] Displays captain and vice-captain
- [ ] Shows team value and total points

**Blockers:** None

---

### 2. Problem Detection System
**Status:** 🔴 Not Started  
**Priority:** P0  
**Effort:** Medium (4-6 hours)  
**Dependencies:** Feature #1 (Import My Team)

**Description:**
Automatically identify players in the team who are underperforming or risky.

**Detection Rules:**
| Issue | Criteria | Flag |
|-------|----------|------|
| Dead Wood | < 2 pts/game AND < 60 min/game | 🚨 URGENT |
| Rotation Risk | < 70% minutes last 5 games | ⚠️ WARNING |
| Bad Fixtures | Next 5 FDR > 3.5 | ⚠️ WARNING |
| Fixture Congestion | 3+ games in 7 days | ⚠️ WARNING |
| Falling Price | Transfer out > transfer in | 💸 LOSING VALUE |

**Acceptance Criteria:**
- [ ] Scans all 15 players automatically
- [ ] Displays issues in priority order
- [ ] Shows specific metric that triggered flag
- [ ] Groups by urgency (urgent vs. watch list)

**Blockers:** 
- Need FPL API for minutes data
- Need fixture data with difficulty ratings

---

### 3. Replacement Suggestion Engine
**Status:** 🔴 Not Started  
**Priority:** P0  
**Effort:** Large (8-10 hours)  
**Dependencies:** Feature #1, #2

**Description:**
When user wants to transfer out a player, suggest ranked replacements.

**Filtering Logic:**
- Same position
- Price ≤ (current player + budget available)
- Better fixtures (FDR)
- More minutes
- Better form

**Sorting Options:**
- Points per million
- Total points
- xGI (expected goal involvements)
- Next 5 fixture difficulty
- Transfer trend (hot picks)

**Acceptance Criteria:**
- [ ] Click "Find Replacement" on any player
- [ ] See top 10 ranked alternatives
- [ ] Can adjust filters (price, fixtures, minutes %)
- [ ] Shows comparison metrics side-by-side
- [ ] Indicates if replacement is "template" (>30% ownership)

**Blockers:**
- Need FDR calculation method
- Need transfer trend data from FPL API

---

## 📊 P1 Features (High Value)

### 4. Enhanced Search & Filtering
**Status:** 🔴 Not Started  
**Priority:** P1  
**Effort:** Medium (4-6 hours)  
**Dependencies:** None

**Description:**
Improve search page with comprehensive filters and sorting.

**Filters to Add:**
- Position (multi-select)
- Price range (slider)
- Team (multi-select)
- Min/max total points
- Min xGI
- Min minutes %
- Ownership range (for differentials)
- "No Europe" toggle

**Sorting Options:**
- Total points
- Points per million
- xGI
- Form (last 5)
- Price
- Ownership %

**Acceptance Criteria:**
- [ ] All filters work independently and together
- [ ] URL reflects filter state (shareable links)
- [ ] Clear all filters button
- [ ] Show result count
- [ ] Filters persist across page refreshes

---

### 5. Fixture Difficulty Rating (FDR) System
**Status:** 🔴 Not Started  
**Priority:** P1  
**Effort:** Medium (4-6 hours)  
**Dependencies:** None

**Description:**
Calculate and display fixture difficulty for next 5 gameweeks.

**Approach Options:**
- **Option A:** Use Elo ratings from FPL-Elo-Insights
- **Option B:** Use official FPL FDR
- **Option C:** Custom algorithm (Elo + home/away + form)

**Visual Display:**
```
Next 5: ■■■□□ (2.8 avg)
GW13: LIV(A) ■■■■■ 5/5
GW14: BOU(H) ■■□□□ 2/5
GW15: CRY(H) ■■□□□ 2/5
```

**Acceptance Criteria:**
- [ ] Every player shows next 5 fixtures
- [ ] Color-coded difficulty (green = easy, red = hard)
- [ ] Average FDR score calculated
- [ ] Can sort/filter by fixture difficulty

**Decision Needed:** Which approach for FDR calculation?

---

### 6. Minutes Played Analysis
**Status:** 🔴 Not Started  
**Priority:** P1  
**Effort:** Small (2-3 hours)  
**Dependencies:** FPL API integration

**Description:**
Show minutes played for last 5 gameweeks to identify rotation risk.

**Display:**
```
Last 5 Games:
GW12: 90 min ███████████████ 100%
GW11: 78 min ████████████    87%
GW10: 90 min ███████████████ 100%
GW9:  62 min █████████       69%
GW8:  90 min ███████████████ 100%

Average: 82 min (91%)
Status: ✓ NAILED ON
```

**Risk Categories:**
- **Nailed (90%+):** ✓ Green
- **Mostly starts (70-89%):** ⚠️ Yellow  
- **Rotation risk (<70%):** ❌ Red

**Acceptance Criteria:**
- [ ] Shows last 5 games for each player
- [ ] Displays visual bar chart
- [ ] Calculates average minutes %
- [ ] Risk category clearly shown

---

### 7. Transfer Trends Integration
**Status:** 🔴 Not Started  
**Priority:** P1  
**Effort:** Small (2-3 hours)  
**Dependencies:** FPL API integration

**Description:**
Show which players are being heavily transferred in/out.

**Data from FPL API:**
- Transfers in (last 24h)
- Transfers out (last 24h)
- Ownership %
- Price changes

**Display:**
```
📈 TRENDING IN:
1. Salah      +125k (58% → 62%) ⬆️ Price rising tonight
2. Saka       +98k  (42% → 45%)

📉 TRENDING OUT:
1. Son        -156k (25% → 22%) ⬇️ Price falling tonight
```

**Acceptance Criteria:**
- [ ] Shows top 10 transferred in
- [ ] Shows top 10 transferred out
- [ ] Indicates price change risk
- [ ] Updates at least daily

---

## 🎨 P2 Features (Nice to Have)

### 8. Visual Charts & Graphs
**Status:** 🔴 Not Started  
**Priority:** P2  
**Effort:** Medium (4-6 hours)

**Charts to Add:**
- Points trend over season (line chart)
- xG vs actual goals (scatter plot)
- Position value comparison (bar chart)
- Fixture difficulty heatmap

**Library:** Chart.js or Plotly

---

### 9. Team Builder - Current vs Dream
**Status:** 🔴 Not Started  
**Priority:** P2  
**Effort:** Large (10-12 hours)

**Features:**
- Side-by-side team comparison
- Drag-and-drop OR dropdown selection
- Budget tracker
- Formation validation
- Save multiple teams
- Calculate transfer path

---

### 10. European Fixture Integration
**Status:** 🔴 Not Started  
**Priority:** P2  
**Effort:** Medium (6-8 hours)

**Data Needed:**
- Champions League fixtures
- Europa League fixtures
- Domestic cup dates

**Analysis:**
- Identify fixture congestion (3+ games in 7 days)
- Flag rotation risks
- Calculate rest days

**Blocked By:**
- Need data source for European fixtures
- Decision: Scrape vs. API vs. manual entry?

---

## 🔮 P3 Features (Future)

### 11. Historical Performance Comparison
**Status:** 🔴 Not Started  
**Priority:** P3

Compare player/team performance across multiple gameweeks.

---

### 12. Captain Picker Tool
**Status:** 🔴 Not Started  
**Priority:** P3

Suggest optimal captain based on fixtures, form, ownership.

---

### 13. Chip Strategy Advisor
**Status:** 🔴 Not Started  
**Priority:** P3

Advise when to use wildcard, bench boost, triple captain, free hit.

---

### 14. Mini-League Analysis
**Status:** 🔴 Not Started  
**Priority:** P3

Compare your team to mini-league rivals, identify differentials.

---

## 🐛 Bugs & Technical Debt

### Bug #1: None reported yet
*(Will track bugs here as they arise)*

---

## 📋 Completed Features

### ✅ Phase 0 Features

1. **Basic Flask App Setup** 🟢
   - Templates, routes, static files
   
2. **GitHub Data Integration** 🟢
   - Fetch from FPL-Elo-Insights
   
3. **Smart Caching** 🟢
   - Time-based cache (5am/5pm UTC)
   - Background scheduler
   
4. **Template Inheritance** 🟢
   - base.html with blocks
   
5. **Search Functionality** 🟢
   - Basic name search
   
6. **Differentials Page** 🟢
   - Low ownership, high potential players

---

## 💭 Ideas Parking Lot

*Features mentioned but not yet prioritized:*

- [ ] Dark mode toggle
- [ ] Export to CSV
- [ ] Email alerts for price changes
- [ ] Mobile app (React Native?)
- [ ] Social features (share teams)
- [ ] AI-powered predictions
- [ ] Betting odds integration
- [ ] Player news aggregator
