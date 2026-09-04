import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot API credentials
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
TOKEN: str = TELEGRAM_BOT_TOKEN
TELEGRAM_API_ID_RAW = os.getenv("TELEGRAM_API_ID")
TELEGRAM_API_ID: int = int(TELEGRAM_API_ID_RAW) if TELEGRAM_API_ID_RAW and TELEGRAM_API_ID_RAW.isdigit() else 0
API_ID: int = TELEGRAM_API_ID
TELEGRAM_API_HASH: str = os.getenv("TELEGRAM_API_HASH", "")
API_HASH: str = TELEGRAM_API_HASH
TELEGRAM_PHONE_NUMBER: str = os.getenv("TELEGRAM_PHONE_NUMBER", "")
PHONE_NUMBER: str = TELEGRAM_PHONE_NUMBER

# Telethon session string for stateless scraping
TELETHON_SESSION_STRING: str = os.getenv("TELETHON_SESSION_STRING", "")

# Supabase credentials (REST API)
SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
# Accept either SUPABASE_KEY or SUPABASE_ANON_KEY for convenience
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_DB_URL: str = os.getenv("SUPABASE_DB_URL", "")

# Webhook configuration
WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "")
WEBHOOK_SECRET: str = os.getenv("WEBHOOK_SECRET", "")

# Monitored Telegram channels
CHANNELS: List[str] = [
    "@Maroset",
    "@freelance_ethio",
    "@addis_ababa_jobs",
    "@ethio_job_vacancy1",
    "@jobs_in_ethio",
    "@josad_software",
    "@hahujobs",
    "@effoyjobs",
    "@harmeejobs",
    "@Elelanjobs",
    "@shegarjob",
    "@vacancyforallethio",
    "@fanajobs",
    "@DagmawiBabiJobs",   
]

# Supported job categories
JOB_CATEGORIES: List[str] = [
    "Finance", "Bank", "Insurance", "NGO", "Marketing", "Sales", "Director",
    "Human Resources", "Lawyer", "Design", "Media", "Hospitality", "Analyst",
    "Administrative", "Developer", "Engineer", "Accountant", "Auditor", "Teacher",
    "Consultant", "Manager", "Coordinator", "Operations", "Customer Service",
    "Supply Chain", "Legal", "Research", "Product Management", "Data Science",
    "Cybersecurity", "Project Management", "Logistics", "IT", "Graphic Design",
    "UX/UI Design", "Communications", "Assistant", "Salesforce", "Event Planning",
    "Content Creation", "Public Relations",
]
