# FPL Transfer Tool - Product Roadmap

## 🎯 Vision
A comprehensive FPL planning tool that helps make data-driven transfer decisions by analyzing fixtures, form, rotation risk, and transfer trends.

## 📊 Current Status
**Phase:** Early Development  
**Version:** 0.2.0  
**Last Updated:** November 2025

---

## 🚀 Development Phases

### ✅ Phase 0: Foundation (COMPLETE)
**Goal:** Basic web app with data visualization

**Completed:**
- [x] Flask app setup
- [x] GitHub data integration (FPL-Elo-Insights)
- [x] Template inheritance (base.html)
- [x] Home page with top players by position
- [x] Search functionality
- [x] Differentials page
- [x] Smart caching system (5am/5pm UTC updates)
- [x] Background scheduler for automatic data refresh
- [x] Smart gameweek detection

**Key Learnings:**
- Caching dramatically improves performance
- Template inheritance keeps code DRY
- GitHub raw URLs work well for data fetching

---

### 🔄 Phase 1: Transfer Assistant (IN PROGRESS)
**Goal:** Help identify which players to transfer out and suggest replacements

**Priority Features:**
1. **Import My Team** (P0 - Blocker for everything else)
   - Connect to FPL API
   - Fetch user's current 15 players
   - Display team with key metrics
   
2. **Problem Detection** (P0)
   - Flag low performers (< X points/game)
   - Identify rotation risks (< 70% minutes)
   - Highlight bad fixtures (FDR > 3.5)
   - Show fixture congestion (3+ games in 7 days)

3. **Smart Replacement Suggestions** (P0)
   - Filter by position and budget
   - Sort by relevant metrics
   - Show fixture difficulty for next 5
   - Display minutes played %

4. **Enhanced Filtering** (P1)
   - Position filter
   - Price range slider
   - Team selector
   - Minimum points/xGI
   - Fixture difficulty filter
   - Ownership filter (template vs differential)
   - "No Europe" toggle

**Blocked By:**
- Need FPL API integration for live data
- Need to calculate FDR scores
- Need European fixture calendar data

**Success Metrics:**
- Can import team in < 5 seconds
- Identifies 2-3 actionable transfer targets
- Replacement suggestions ranked by value

---

### 📅 Phase 2: Full Team Analyzer (PLANNED)
**Goal:** Comprehensive team analysis and optimization

**Features:**
1. **Automatic Team Review**
   - Scan entire 15-man squad
   - Generate weekly report
   - Prioritize problems
   
2. **Multi-Transfer Planning**
   - Show impact of 2-3 transfers
   - Calculate points hits
   - Optimize for next 3-5 GWs

3. **Fixture Ticker**
   - Next 5 gameweeks analysis
   - Best/worst fixture runs
   - Differential opportunities by fixture

4. **Minutes Played Analysis**
   - Last 5 games breakdown
   - Rotation risk scoring
   - Nailed-on vs. risky picks

**Dependencies:**
- Phase 1 complete
- Historical minutes data
- Fixture difficulty algorithm

---

### 🏗️ Phase 3: Team Builder (PLANNED)
**Goal:** Build and compare dream teams vs. current team

**Features:**
1. **Current vs. Dream Layout**
   - Side-by-side comparison
   - Budget tracker
   - Formation validator

2. **Save Multiple Teams**
   - Wildcard team
   - Chip strategies
   - Future gameweek targets

3. **Transfer Path Calculator**
   - Show how to get from current → dream
   - Minimize points hits
   - Suggest optimal timing

---

### 📈 Phase 4: Advanced Analytics (FUTURE)
**Goal:** Deep statistical insights

**Features:**
1. **Player Deep Dives**
   - Shot maps
   - xG overperformance/underperformance
   - Bonus point probability
   - Historical form charts

2. **Team Strength Analysis**
   - Elo-based predictions
   - Clean sheet probability
   - Expected goals for/against

3. **Differential Finder**
   - Low ownership gems
   - Rising stars
   - Contrarian captain picks

4. **European Fixture Impact**
   - CL/EL fatigue analysis
   - Rotation prediction
   - Rest day tracking

---

### 🌐 Phase 5: Deployment & Sharing (FUTURE)
**Goal:** Make it publicly accessible

**Tasks:**
- Deploy to Render/Railway
- Add user authentication (optional)
- Multi-user support
- Share link with friends

---

## 🎨 UI Improvements (Ongoing)

**Low-Hanging Fruit:**
- [ ] Add table sorting (click headers)
- [ ] Mobile responsive design
- [ ] Loading spinners
- [ ] Better error messages
- [ ] Add charts (Chart.js)

**Nice-to-Have:**
- [ ] Dark mode
- [ ] Keyboard shortcuts
- [ ] Export to CSV
- [ ] Print-friendly views

---

## 🔧 Technical Debt & Improvements

**Performance:**
- [ ] Consider Redis for caching (if needed)
- [ ] Lazy load heavy data
- [ ] Optimize CSV parsing

**Code Quality:**
- [ ] Add unit tests
- [ ] Error handling improvements
- [ ] Logging system
- [ ] Configuration file (don't hardcode URLs)

**Data Quality:**
- [ ] Validate data freshness
- [ ] Handle missing/null values better
- [ ] Data quality checks

---

## 📝 Notes & Decisions

### Why These Priorities?
1. **Transfer Assistant first** - Most immediate value, use weekly
2. **Team Builder later** - Nice to have, use occasionally (wildcards)
3. **Advanced analytics last** - Interesting but not essential

### Key Technical Decisions
- **Data Source:** FPL-Elo-Insights (auto-updates 2x daily)
- **Caching Strategy:** Time-based (5am/5pm UTC)
- **Backend:** Flask (simple, learner-friendly)
- **Frontend:** Jinja2 templates (no framework needed yet)
- **Deployment:** Local → Render (when ready)

### Data Sources
- **Primary:** FPL-Elo-Insights GitHub repo
- **Live Data:** FPL Official API
- **European Fixtures:** TBD (UEFA API or scrape)

---

## 🤔 Open Questions

1. **European fixtures:** Best source? Scrape vs. API?
2. **FDR calculation:** Use Elo? Official FPL FDR? Custom?
3. **Caching strategy:** Is 30min enough? Too much?
4. **User accounts:** Do we need them? Or just team ID input?
