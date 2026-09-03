# Career Fit Jobs Bot

Career Fit Jobs Bot is an automated job alert service on Telegram. It monitors public employment channels, indexes job posts, matches vacancies against individual user category preferences, and delivers periodic digest alerts.

The system is built on a serverless, zero-maintenance architecture designed to run entirely within free-tier infrastructure limits.

---

## Architecture Overview

The system is decoupled into two independent execution environments sharing a central Supabase database:

```
                  +-----------------------------------+
                  |           Telegram User           |
                  +-----------------+-----------------+
                                    |
                         (Commands / Callbacks)
                                    v
+------------------+      +-------------------+      +-------------------+
|  Monitored TG    |      |  Telegram Webhook |      |     Supabase      |
|     Channels     |      |  (Vercel Function)|<---->|    PostgreSQL     |
+--------+---------+      +-------------------+      +---------+---------+
         |                                                     ^
         | (3x Daily Scrape)                                   |
         v                                                     |
+---------------------------------------------+                |
|           GitHub Actions Runner             |----------------+
|  1. Scrape new posts (src.scraper.runner)   |
|  2. Match & dispatch (src.notifier.runner)  |
+---------------------------------------------+
```

### 1. User-Facing Bot (Serverless Webhook)
- **Runtime:** Vercel Python Function (`api/webhook.py`) powered by FastAPI.
- **Protocol:** HTTPS Webhook (`POST /api/webhook`). Telegram pushes updates directly to the endpoint.
- **State:** Stateless and scales to zero when idle, eliminating idle process crashes and costs.

### 2. Scheduled Scraper and Notifier
- **Runtime:** GitHub Actions scheduled workflow (`.github/workflows/scrape_and_notify.yml`).
- **Frequency:** 3 times daily (05:00, 11:00, 17:00 UTC).
- **Execution:**
  1. `src.scraper.runner`: Connects to Telegram via Telethon, scrapes new messages from configured channels past the recorded watermark, and stores vacancies in Supabase.
  2. `src.notifier.runner`: Reads all active user preferences from Supabase, finds matches, publishes detailed Telegraph summaries, and sends alert messages via Telegram Bot API.
- **Keepalive:** A weekly workflow (`.github/workflows/keepalive.yml`) prevents GitHub from automatically disabling scheduled jobs after 60 days of repository inactivity.

### 3. Database Layer
- **Provider:** Supabase (PostgreSQL).
- **Schema Management:** Checked-in SQL migrations located in `migrations/`.

---

## Repository Structure

```
.
├── api/
│   └── webhook.py                 # FastAPI webhook entry point for Vercel
├── src/
│   ├── bot/
│   │   ├── formatters.py          # Telegraph page generation and Telegram formatting
│   │   └── handlers.py            # Bot command and callback query handlers
│   ├── db/
│   │   ├── client.py              # Supabase client singleton
│   │   ├── jobs.py                # Job listings data access
│   │   ├── scraper_state.py       # Per-channel scrape watermarks
│   │   └── users.py               # User records and preferences data access
│   ├── notifier/
│   │   └── runner.py              # Single-run preference matcher and dispatcher
│   ├── scraper/
│   │   ├── keywords.txt           # Vacancy detection keywords
│   │   └── runner.py              # Single-run Telethon channel scraper
│   ├── config.py                  # Environment variable configuration and constants
│   └── policy.py                  # Privacy policy generator
├── scripts/
│   └── generate_session.py        # Utility to generate Telethon StringSession for CI
├── migrations/
│   └── 001_initial_schema.sql     # Database tables, indexes, and constraints
├── tests/
│   ├── test_db.py
│   ├── test_formatters.py
│   ├── test_matching.py
│   ├── test_scraper.py
│   └── test_webhook.py
├── .github/workflows/
│   ├── keepalive.yml              # Weekly workflow keepalive
│   └── scrape_and_notify.yml      # 3x daily scrape and dispatch workflow
├── .env.example                   # Environment configuration template
├── requirements.txt               # Python package dependencies
└── vercel.json                    # Serverless routing configuration
```

---

## Setup and Local Development

### Prerequisites
- Python 3.10 or higher
- A Telegram account with API credentials from [my.telegram.org](https://my.telegram.org)
- A Telegram bot created via [@BotFather](https://t.me/BotFather)
- A [Supabase](https://supabase.com) project

### 1. Installation

Clone the repository and install the required dependencies:

```bash
git clone https://github.com/DanielKinnito/Career-Fit-Jobs-Bot.git
cd Career-Fit-Jobs-Bot
pip install -r requirements.txt
```

### 2. Configuration

Copy the example environment configuration:

```bash
cp .env.example .env
```

Populate `.env` with your credentials:

```env
# Telegram Bot API
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=0123456789abcdef0123456789abcdef

# Supabase REST API
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your-supabase-anon-or-service-key

# Direct PostgreSQL Connection (special characters in password must be percent-encoded)
SUPABASE_DB_URL=postgresql://postgres:encoded_password@db.your-project-ref.supabase.co:5432/postgres

# Webhook Secret (arbitrary string used to authenticate Telegram webhook payloads)
WEBHOOK_SECRET=your_custom_secret_token
```

### 3. Database Migration

Execute `migrations/001_initial_schema.sql` inside the Supabase SQL Editor. This provisions:
- `users`: Registered users and their category preferences.
- `user_profiles`: User CV storage paths, skills, and experience.
- `job_listings`: Scraped vacancies.
- `applications`: Job application tracking by link.
- `job_suggestions`: User-suggested jobs for review.
- `scraper_state`: Persistent per-channel scrape watermarks.

### 4. Running Tests

Run the test suite using pytest:

```bash
pytest tests/ -v
```

---

## Running Components Locally

### Running the Webhook Bot Locally

To test webhook handling locally, start the FastAPI server with Uvicorn:

```bash
uvicorn api.webhook:app --reload --port 8000
```

To connect Telegram to your local instance, expose your local port via a reverse proxy (e.g. `ngrok http 8000`) and configure the webhook:

```bash
curl -F "url=https://<your-ngrok-subdomain>.ngrok-free.app/api/webhook" \
     -F "secret_token=your_custom_secret_token" \
     https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook
```

### Running the Scraper Locally

The scraper runs a single pass over configured channels and records its progress in Supabase:

```bash
python -m src.scraper.runner
```

On first run without a session string, Telethon will prompt in the terminal for your phone number and verification code.

### Running the Notifier Locally

To manually trigger preference matching and dispatch updates:

```bash
python -m src.notifier.runner
```

---

## Production Deployment

### 1. Webhook Bot on Vercel
1. Link your repository to a new project on [Vercel](https://vercel.com).
2. Configure environment variables in the Vercel dashboard:
   - `TELEGRAM_BOT_TOKEN`
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `WEBHOOK_SECRET`
3. Deploy the project. Vercel will automatically build `api/webhook.py` using `@vercel/python`.
4. Register the production webhook with Telegram:
   ```bash
   curl -F "url=https://<your-app>.vercel.app/api/webhook" \
        -F "secret_token=<YOUR_WEBHOOK_SECRET>" \
        https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook
   ```

### 2. Scheduled Workflows on GitHub Actions
1. Generate an in-memory Telethon session string:
   ```bash
   python scripts/generate_session.py
   ```
2. In your GitHub repository settings under **Settings > Secrets and variables > Actions**, add:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_API_ID`
   - `TELEGRAM_API_HASH`
   - `TELETHON_SESSION_STRING`
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
3. The `scrape_and_notify.yml` workflow will automatically run on schedule or can be triggered manually via **Actions > Run workflow**.

---

## License

This project is licensed under the MIT License.
