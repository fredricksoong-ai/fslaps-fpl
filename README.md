# FPL Planning Tool

A data-driven Fantasy Premier League transfer planning tool that helps you make better transfer decisions through comprehensive player analysis, fixture difficulty ratings, and rotation risk assessment.

## Features

**Current (v0.2):**
- Player search and filtering
- Top performers by position
- Differential players finder
- Smart caching with automatic updates (5am/5pm UTC)
- Data from FPL-Elo-Insights (updates 2x daily)

**In Development:**
- FPL API integration (import your team)
- Problem detection (rotation risk, bad fixtures)
- Smart replacement suggestions
- Fixture difficulty analysis
- Transfer trends tracking

## Documentation

- [Product Roadmap](ROADMAP.md) - Development phases and vision
- [Feature Backlog](BACKLOG.md) - Prioritized feature list
- [Technical Notes](TECHNICAL.md) - Architecture and decisions

## Quick Start

### Prerequisites
```bash
python 3.8+
pip install flask pandas requests apscheduler
```

### Run Locally
```bash
git clone https://github.com/YOUR_USERNAME/FPL-Transfer-Tool.git
cd FPL-Transfer-Tool
python app.py
```

Open browser to: `http://127.0.0.1:5000`

## Data Sources

- **Primary:** [FPL-Elo-Insights](https://github.com/olbauday/FPL-Elo-Insights) (player stats, Elo ratings)
- **Secondary:** FPL Official API (live data, transfers, prices)

## Tech Stack

- **Backend:** Flask, Python, Pandas
- **Frontend:** Jinja2 templates, HTML/CSS
- **Caching:** APScheduler, time-based cache
- **Data:** CSV files from GitHub, FPL API

## Development Status

**Phase:** Early Development  
**Version:** 0.2.0  
**Focus:** Building transfer assistant features

## Contributing

This is a personal learning project, but suggestions and feedback are welcome via Issues.

## License

MIT License - see LICENSE file

## Acknowledgments

- Data provided by [FPL-Elo-Insights](https://github.com/olbauday/FPL-Elo-Insights)
- Inspired by the FPL community
```

Replace `YOUR_USERNAME` with your actual GitHub username.

Commit message: "Update README with project overview"

---

### **5. Upload Your Code (Optional Now, Do Later)**

You have two options:

**Option A: Simple Upload (For Now)**
1. In your repo, click **"Add file"** → **"Upload files"**
2. Drag and drop your `app.py` file
3. Commit message: "Add Flask application"
4. Click **"Commit changes"**

Then create templates folder:
1. Click **"Add file"** → **"Create new file"**
2. In filename box type: `templates/base.html`
3. Paste your base.html content
4. Commit
5. Repeat for all template files

**Option B: Use Git (Better Long-term)**
I can walk you through this later when you're ready to learn Git commands.

---

### **6. Your Repository is Now Live**

Your documentation is now at:
```
https://github.com/YOUR_USERNAME/FPL-Transfer-Tool
