# Technical Documentation

## 🏗️ Architecture

### Tech Stack
- **Backend:** Flask 3.x (Python)
- **Frontend:** Jinja2 templates, HTML/CSS, vanilla JavaScript
- **Data:** Pandas for processing
- **Scheduler:** APScheduler for background jobs
- **HTTP:** Requests library

### Project Structure
```
FPL-Tool/
├── app.py                 # Main Flask application
├── templates/
│   ├── base.html         # Master template
│   ├── home.html         # Homepage
│   ├── search.html       # Search page
│   ├── differentials.html
│   ├── position.html
│   └── error.html
├── static/ (future)
│   ├── css/
│   └── js/
├── ROADMAP.md
├── BACKLOG.md
└── TECHNICAL.md (this file)
```

---

## 📊 Data Sources

### Primary: FPL-Elo-Insights
**Repo:** https://github.com/olbauday/FPL-Elo-Insights

**Update Schedule:** 5:00 AM & 5:00 PM UTC daily

**Files Used:**
```
/data/2025-2026/
├── players.csv           # Master player list
├── teams.csv            # Team data with Elo ratings
└── By Gameweek/
    └── GW{N}/
        └── playerstats.csv  # Weekly player stats
```

**Access Method:**
```python
BASE_URL = "https://raw.githubusercontent.com/olbauday/FPL-Elo-Insights/main/data/2025-2026"
```

**Key Fields:**
- `player_id`, `web_name`, `team_code`, `position`
- `now_cost`, `total_points`, `points_per_game`
- `expected_goal_involvements` (xGI)
- `selected_by_percent`, `transfers_in`, `transfers_out`

---

### Secondary: FPL Official API
**Base URL:** `https://fantasy.premierleague.com/api/`

**Endpoints Used:**

1. **Bootstrap Static** (General game data):
```
   GET /api/bootstrap-static/
```
   Returns: All players, teams, gameweeks, events
   Update frequency: Real-time
   
2. **User Team** (Specific manager):
```
   GET /api/entry/{TEAM_ID}/
```
   Returns: Manager info, team value, total points
   
3. **Team Picks** (Current squad):
```
   GET /api/entry/{TEAM_ID}/event/{GW}/picks/
```
   Returns: 15 players, captain, bench order
   
4. **Live Gameweek**:
```
   GET /api/event/{GW}/live/
```
   Returns: Live scores during matches

**Rate Limits:**
- No official limits documented
- Best practice: Cache responses for 5+ minutes
- Avoid rapid successive calls

---

### Future: European Fixtures
**Options Under Consideration:**

1. **UEFA Official API** (if available)
2. **Scraping from UEFA.com**
3. **Manual CSV updates**
4. **Third-party fixture APIs**

**Decision:** TBD

---

## ⚙️ Key Technical Decisions

### 1. Caching Strategy

**Implementation:** Time-based cache with background refresh

**Rationale:**
- Data updates at predictable times (5am/5pm UTC)
- No need to check for updates constantly
- Background scheduler ensures data is always fresh
- Users never wait for data fetch

**Code Pattern:**
```python
class SmartDataCache:
    def should_refresh(self):
        # Check if update time (5am or 5pm) passed since last fetch
        
scheduler = BackgroundScheduler(timezone="UTC")
scheduler.add_job(refresh_data, trigger="cron", hour=5)
scheduler.add_job(refresh_data, trigger="cron", hour=17)
```

**Alternatives Considered:**
- ❌ No caching - too slow
- ❌ Fixed 30-min expiry - wasteful
- ❌ Check GitHub for updates - adds latency

---

### 2. Gameweek Detection

**Implementation:** Smart estimation + nearby search

**Algorithm:**
```python
1. Calculate weeks since season start
2. Estimate current GW (weeks_passed)
3. Search order: [estimated, estimated+1, estimated-1, estimated+2, estimated-2, ...]
4. Check file size > 1000 bytes (avoid placeholder files)
5. Return first valid GW found
```

**Rationale:**
- Much faster than checking GW38 → GW1
- Usually finds correct GW in 1-3 attempts
- Handles delays in GitHub repo updates

**Alternatives Considered:**
- ❌ Hardcode GW - requires manual updates
- ❌ Always start from GW38 - slow (35 checks early season)
- ❌ User input - extra friction

---

### 3. Frontend Framework Choice

**Decision:** Stick with Jinja2 templates (no React/Vue/Svelte)

**Rationale:**
- App is primarily data display
- Server-side rendering is fast
- Simpler to deploy (one app, not two)
- SEO-friendly
- Faster iteration during development
- Can always add frameworks later if needed

**When to Reconsider:**
- Heavy client-side interactivity needed (e.g., drag-drop team builder)
- Want to learn frontend frameworks for job skills
- Building a "product" vs. "tool"

---

### 4. Data Processing

**Library:** Pandas

**Why:**
- Excellent for CSV manipulation
- Built-in DataFrame merge/join operations
- Easy aggregation and filtering
- Good performance for this data size

**Typical Operations:**
```python
# Merge player master data with weekly stats
analysis_df = current_players.merge(
    players_master[['player_id', 'team_code', 'position']], 
    left_on='id', 
    right_on='player_id'
)

# Calculate derived metrics
analysis_df['points_per_million'] = analysis_df['total_points'] / analysis_df['now_cost']

# Filter and sort
top_forwards = df[df['position'] == 'Forward'].nlargest(10, 'expected_goal_involvements')
```

---

## 🔒 Security Considerations

### Current Security Posture
- ✅ No user authentication (public data only)
- ✅ No database (no SQL injection risk)
- ✅ No user input executed as code
- ✅ Read-only access to external APIs

### Potential Risks
- **Rate limiting:** GitHub/FPL might throttle requests
- **XSS:** User input in search not sanitized
- **CSRF:** No forms that modify data yet

### When Authentication Is Added
- Use Flask-Login or similar
- Hash passwords (bcrypt)
- HTTPS only (via deployment platform)
- Session management
- CSRF tokens

---

## 📈 Performance Considerations

### Current Performance
- **First load:** 2-4 seconds (fetches from GitHub)
- **Subsequent loads:** <100ms (cached data)
- **Data size:** ~2MB CSV files
- **Concurrent users:** N/A (local development)

### Optimization Opportunities
1. **Lazy loading:** Load position data on-demand
2. **Pagination:** Show 20 results, load more on scroll
3. **Database:** Move from CSV to SQLite for complex queries
4. **Redis:** If deploying for multiple users
5. **CDN:** Serve static assets (CSS/JS) from CDN

### Bottlenecks to Monitor
- Gameweek detection (HTTP requests)
- CSV parsing (Pandas read_csv)
- Template rendering (if data grows)

---

## 🐛 Error Handling

### Current Approach
- Try-except blocks around data fetching
- Return empty DataFrame on failure
- Show error.html template with message
- Print errors to console

### Improvements Needed
- Structured logging (not just print statements)
- Error categorization (network vs. data vs. app)
- Retry logic for transient failures
- User-friendly error messages
- Sentry or similar for production error tracking

---

## 🧪 Testing Strategy

### Current State
- Manual testing only
- No automated tests

### Future Testing Plan
1. **Unit tests:** Test individual functions
   - `get_latest_gameweek()`
   - `load_fpl_data()`
   - FDR calculation (when built)

2. **Integration tests:** Test routes
   - Does /search return 200?
   - Does /differentials show data?

3. **Data validation tests:**
   - Are CSV files valid?
   - Do merges produce expected rows?

**Tools:** pytest, Flask test client

---

## 🚀 Deployment Plan

### Phase 1: Local Development (Current)
- Run on localhost
- SQLite file database (if needed)
- Environment variables in .env file

### Phase 2: Cloud Deployment (Future)
**Platform:** Render (recommended) or Railway

**Steps:**
1. Push code to GitHub
2. Connect Render to repo
3. Configure environment variables
4. Auto-deploy on push to main

**Considerations:**
- Background scheduler works on Render
- Free tier has cold starts (slow first load)
- Upgrade to paid if gets real traffic

---

## 📝 Configuration Management

### Current Approach
- Hardcoded values in app.py

### Better Approach (TODO)
Create `config.py`:
```python
import os

class Config:
    # Data sources
    GITHUB_BASE_URL = "https://raw.githubusercontent.com..."
    FPL_API_BASE_URL = "https://fantasy.premierleague.com/api/"
    
    # Caching
    CACHE_UPDATE_HOURS = [5, 17]  # UTC
    
    # Season config
    SEASON_START_DATE = "2025-08-16"
    
    # App config
    DEBUG = os.getenv("DEBUG", "False") == "True"
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-key-change-in-prod")
```

---

## 🔄 Development Workflow

### Current Workflow
1. Make changes to app.py or templates
2. Stop Flask (Ctrl+C)
3. Restart Flask (`python app.py`)
4. Refresh browser
5. Check console for errors

### Improved Workflow (TODO)
- Use `FLASK_ENV=development` for auto-reload
- Add debugger breakpoints
- Use Flask shell for testing functions
- Git commits for each feature

---

## 💡 Technical Lessons Learned

1. **Caching is crucial** - Reduced load time from 3s to 0.1s
2. **Smart search > brute force** - GW detection 10x faster
3. **Template inheritance** - Saved 100+ lines of duplicate HTML
4. **Background jobs** - Users never wait for data refresh
5. **Start simple** - Jinja2 templates good enough, no framework needed yet

---

## 🤔 Open Technical Questions

1. **How to store historical data?**
   - Option A: SQLite database
   - Option B: Keep CSV files locally
   - Option C: Query GitHub for past GWs on-demand

2. **FDR calculation method?**
   - Option A: Use Elo ratings from FPL-Elo-Insights
   - Option B: Use official FPL FDR
   - Option C: Custom algorithm

3. **European fixture data source?**
   - Need reliable, updateable source

4. **Deployment database needs?**
   - PostgreSQL? SQLite? No DB?

---

## 📚 Resources & References

**Flask Documentation:**
- https://flask.palletsprojects.com/

**FPL API Documentation (Unofficial):**
- https://github.com/vaastav/Fantasy-Premier-League

**APScheduler Docs:**
- https://apscheduler.readthedocs.io/

**Pandas Docs:**
- https://pandas.pydata.org/docs/

**FPL-Elo-Insights Repo:**
- https://github.com/olbauday/FPL-Elo-Insights
