# LogoGrid

A lightweight web app that displays a responsive grid of logos from agencies/institutes/government sites.

## Quick Start

1. Install dependencies:
```bash
   pip install -r requirements.txt
```

2. Configure environment:
```bash
   cp .env.example .env
   # Edit .env with your settings
```

3. Run initial scrape:
```bash
   python -m app.refresh
```

4. Start development server:
```bash
   flask run
```

5. Visit http://localhost:5000

## Project Structure
```
logogrid/
├── app/
│   ├── scraper/           # Logo extraction logic
│   ├── templates/         # HTML templates
│   ├── static/            # CSS, cached logos
│   ├── main.py           # Flask application
│   ├── refresh.py        # Scraping & refresh logic
│   └── scheduler.py      # Cron job scheduler
├── config/
│   ├── sites.json        # Website configuration
│   └── config.json       # App configuration
├── tests/                  # Generated data files
```

## Documentation

See PRD.md for complete product requirements and technical specifications.
