# Minerva Fetcher

Automated pipeline for collecting and storing articles from RSS feeds.

## 📋 Description

Minerva Fetcher is an automated monitoring system that:
- Retrieves articles from multiple configurable RSS feeds
- Extracts full article content (optional)
- Eliminates duplicates
- Stores new articles in Google Sheets and Supabase
- Provides detailed logs for monitoring

## 🏗️ Architecture

```
minerva-fetcher/
├── src/
│   ├── config/
│   │   └── settings.py          # Centralized configuration
│   ├── services/
│   │   ├── rss_fetcher.py       # RSS feed retrieval
│   │   ├── article_processor.py # Article processing and filtering
│   │   ├── gsheet_service.py    # Google Sheets integration
│   │   └── supabase_service.py  # Supabase integration
│   ├── exporters/
│   │   └── markdown_exporter.py # Markdown export (if needed)
│   ├── utils/
│   │   ├── logger.py            # Logging system
│   │   └── helpers.py           # Utility functions
│   └── main.py                  # Pipeline entry point
├── credentials/
│   └── service_account.json     # Google credentials (not versioned)
├── requirements.txt             # Python dependencies
└── .env                         # Environment variables (not versioned)
```

## 🔄 Data Flow

1. **Configuration**: Read RSS feeds from a Google Sheet (published CSV)
2. **Collection**: Fetch articles from each RSS feed
3. **Extraction**: Extract full content (if enabled for the feed)
4. **Deduplication**: 
   - Compare with existing articles in Google Sheets
   - Compare with existing articles in Supabase
5. **Storage**:
   - Add new articles to Google Sheets
   - Add new articles to Supabase

## 🚀 Installation

### Prerequisites

- Python 3.8+
- Google Cloud account with Google Sheets API enabled
- Google Service Account with access to sheets
- Configured Supabase instance

### Installing Dependencies

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
.\venv\Scripts\activate   # On Windows

# Install dependencies
pip install -r requirements.txt
```

## ⚙️ Configuration

### 1. Environment Variables

Create a `.env` file at the project root:

```env
# Google Sheets
RSS_FEEDS_CSV_URL=https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/export?format=csv
ARTICLES_SHEET_ID=your_articles_sheet_id
ARTICLES_WORKSHEET_NAME=Articles
GOOGLE_SERVICE_ACCOUNT_FILE=credentials/service_account.json

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_key
SUPABASE_TABLE_NAME=articles

# Export (optional)
EXPORT_BASE_PATH=data

# Logging
LOG_LEVEL=INFO
```

### 2. Google Service Account

1. Create a Service Account in Google Cloud Console
2. Download the JSON credentials file
3. Place the file in `credentials/service_account.json`
4. Share your Google Sheets with the service account email

### 3. RSS Feeds Configuration

The RSS feeds CSV file must have the following columns:
- `url`: RSS feed URL
- `name`: Feed name
- `description`: Description (optional)
- `extract_articles`: "true" or "false" to extract full content

### 4. Supabase Table

Structure of the `articles` table:

```sql
CREATE TABLE articles (
  id BIGSERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  url TEXT UNIQUE NOT NULL,
  summary TEXT,
  author TEXT,
  published_date TEXT,
  feed_name TEXT,
  domain TEXT,
  extracted_at TIMESTAMP,
  has_full_content BOOLEAN DEFAULT false,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_articles_url ON articles(url);
CREATE INDEX idx_articles_published_date ON articles(published_date);
```

## 🎯 Utilisation

### Exécution manuelle

```bash
python -m src.main
```

### Exécution avec logs détaillés

```bash
LOG_LEVEL=DEBUG python -m src.main
```

### Automatisation (cron)

```bash
# Exemple : Exécution toutes les heures
0 * * * * cd /path/to/minerva-fetcher && /path/to/venv/bin/python -m src.main >> logs/cron.log 2>&1
```

## 📊 Fonctionnalités

### Récupération RSS
- Support de multiples formats RSS/Atom
- Extraction des métadonnées (titre, auteur, date, résumé)
- Gestion des erreurs par flux

### Extraction de contenu
- Extraction du contenu complet via Readability
- Conversion HTML vers Markdown
- Nettoyage et formatage du texte
- Rate limiting pour respecter les serveurs

### Déduplication intelligente
- Détection des doublons par URL
- Comparaison avec Google Sheets (sources de configuration)
- Comparaison avec Supabase (stockage persistant)
- Gestion séparée pour éviter les conflits

### Stockage multi-destination
- **Google Sheets** : Interface visuelle pour revue manuelle
- **Supabase** : Base de données PostgreSQL pour analyses et requêtes
- Gestion des erreurs de duplication (contrainte unique sur URL)

### Logging
- Structured logs with timestamps
- Configurable levels (DEBUG, INFO, WARNING, ERROR)
- Detailed tracking of each pipeline step

## 🔒 Security

✅ **Implemented best practices**:
- All credentials are in environment variables
- `.env` file and `credentials/` excluded from versioning
- Service Account with minimal permissions
- No hardcoded credentials in the code

## 📦 Main Dependencies

- `feedparser`: RSS/Atom feed parsing
- `readability-lxml`: Main content extraction
- `beautifulsoup4`: HTML parsing
- `gspread`: Google Sheets API
- `supabase`: Supabase Python client
- `html2text`: HTML to Markdown conversion
- `python-dotenv`: Environment variable management

## 🐛 Troubleshooting

### Google Authentication Error
Check that:
- The service_account.json file is present and valid
- The service account has access to the sheets
- Google APIs are enabled

### Supabase Error
Check that:
- SUPABASE_URL and SUPABASE_SERVICE_KEY are correct
- The table exists with the correct structure
- RLS permissions are configured

### No Articles Retrieved
Check that:
- The RSS feeds CSV is accessible and properly formatted
- RSS URLs are valid
- Feeds contain articles

## 📈 Future Improvements

- [ ] Optional Markdown export for archiving
- [ ] Webhook for notifications
- [ ] Web monitoring interface
- [ ] Article sentiment analysis
- [ ] Automatic categorization
- [ ] Support for non-RSS sources (API, scraping)

## 📝 License

MIT License

Copyright (c) 2026 Binarii - Andrea DELRE

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## 👤 Author

Andrea - Binarii
