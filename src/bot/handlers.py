"""Bot command, callback query, and Telegram Mini App handlers."""

import json
import logging
from typing import List, Dict, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from src.config import JOB_CATEGORIES, WEBHOOK_URL
from src.db.users import get_or_create_user, update_user_preferences, get_user_preferences
from src.db.jobs import get_matched_jobs_for_user
from src.notifier.runner import match_jobs_with_preferences
from src.bot.formatters import create_job_update_telegraph_page
from src.policy import get_privacy_policy_url

logger = logging.getLogger(__name__)

MAX_PREFERENCES = 15

SECTORS: Dict[str, Dict[str, any]] = {
    "tech": {
        "name": "💻 Tech",
        "full_name": "Technology & Engineering",
        "categories": ["Developer", "Data Science", "Cybersecurity", "IT", "Engineer", "UX/UI Design", "Graphic Design"],
    },
    "finance": {
        "name": "💼 Finance",
        "full_name": "Finance & Banking",
        "categories": ["Finance", "Bank", "Accounting", "Auditor", "Insurance", "Analyst"],
    },
    "creative": {
        "name": "🎨 Creative",
        "full_name": "Creative & Media",
        "categories": ["Design", "Media", "Communications", "Content Creation", "Public Relations"],
    },
    "sales": {
        "name": "📢 Sales",
        "full_name": "Sales & Marketing",
        "categories": ["Marketing", "Sales", "Product Management", "Salesforce"],
    },
    "ops": {
        "name": "🏢 Ops",
        "full_name": "Operations & Leadership",
        "categories": ["Director", "Manager", "Coordinator", "Operations", "Project Management", "Logistics", "Supply Chain", "Administrative", "Assistant"],
    },
    "services": {
        "name": "🌐 Services",
        "full_name": "NGO, Legal & Services",
        "categories": ["NGO", "Human Resources", "Lawyer", "Legal", "Consultant", "Customer Service", "Research", "Teacher", "Hospitality", "Event Planning"],
    },
}


def get_web_app_url() -> Optional[str]:
    """Return the HTTPS URL for the Telegram Mini App if configured and not a placeholder."""
    if not WEBHOOK_URL:
        return None
    if "your-domain" in WEBHOOK_URL or "example.com" in WEBHOOK_URL or "<" in WEBHOOK_URL:
        return None
    base_url = WEBHOOK_URL.replace("/api/webhook", "").replace("/webhook", "").rstrip("/")
    if base_url.startswith("https://"):
        return f"{base_url}/app"
    return None


def build_apple_style_keyboard(
    selected_preferences: List[str], active_sector: str = "tech"
) -> InlineKeyboardMarkup:
    """Build an Apple-inspired grouped keyboard with sector tabs, chips, and actions."""
    keyboard = []

    # 1. Prominent Action Header (Mini App + On-Demand Jobs)
    top_actions = []
    app_url = get_web_app_url()
    if app_url:
        top_actions.append(InlineKeyboardButton("📱 Open Interactive App", web_app=WebAppInfo(url=app_url)))
    top_actions.append(InlineKeyboardButton("⚡ Latest Matches", callback_data="action_get_jobs"))
    keyboard.append(top_actions)

    # 2. Sector Switcher Tabs (2 rows of 3 sectors)
    sector_keys = list(SECTORS.keys())
    row1 = []
    row2 = []
    for i, key in enumerate(sector_keys):
        info = SECTORS[key]
        is_active = key == active_sector
        label = f"• {info['name']} •" if is_active else info['name']
        btn = InlineKeyboardButton(label, callback_data=f"sec_{key}")
        if i < 3:
            row1.append(btn)
        else:
            row2.append(btn)
    keyboard.append(row1)
    keyboard.append(row2)

    # 3. Category Chips for Active Sector (Clean 2-column layout)
    sector_info = SECTORS.get(active_sector, SECTORS["tech"])
    categories = sector_info["categories"]

    chip_row = []
    for i, category in enumerate(categories, 1):
        is_selected = category in selected_preferences
        icon = "✓ " if is_selected else "+ "
        slug = category.lower().replace(" ", "_").replace("/", "_")
        btn = InlineKeyboardButton(f"{icon}{category}", callback_data=f"pref_{slug}_{active_sector}")
        chip_row.append(btn)

        if len(chip_row) == 2 or i == len(categories):
            keyboard.append(chip_row)
            chip_row = []

    # 4. Action Bar (Clear & Save)
    count = len(selected_preferences)
    save_label = f"💾 Save Preferences ({count})" if count > 0 else "💾 Save Preferences"
    keyboard.append([
        InlineKeyboardButton("🗑 Clear All", callback_data=f"pref_clear_{active_sector}"),
        InlineKeyboardButton(save_label, callback_data="pref_submit"),
    ])

    return InlineKeyboardMarkup(keyboard)


# Backwards compatibility alias
build_preference_keyboard = build_apple_style_keyboard


def format_preference_message(selected_preferences: List[str], active_sector: str = "tech") -> str:
    """Format an elegant status card showing selected preferences."""
    count = len(selected_preferences)
    sector_title = SECTORS.get(active_sector, {}).get("full_name", "All Categories")

    if count == 0:
        selected_text = "_None yet. Tap categories below to add._"
    else:
        selected_text = ", ".join(f"*{p}*" for p in selected_preferences)

    return (
        "✨ *Career Fit Job Matching*\n\n"
        f"🎯 *Selected ({count}/{MAX_PREFERENCES}):*\n"
        f"{selected_text}\n\n"
        f"📂 *Browsing Sector:* {sector_title}\n"
        "Tap a category below to toggle. Switch sectors above anytime."
    )


async def send_latest_jobs_to_user(update: Update, user_id: int) -> None:
    """Fetch recent matches for a user and present a Telegraph Instant View bulletin."""
    user_prefs = get_user_preferences(user_id)
    if not user_prefs:
        msg = (
            "🎯 *No Preferences Configured*\n\n"
            "Please select target categories first using /preferences so we can match vacancies for you."
        )
        if update.callback_query:
            await update.callback_query.message.reply_text(msg, parse_mode="Markdown")
        elif update.message:
            await update.message.reply_text(msg, parse_mode="Markdown")
        return

    matches = get_matched_jobs_for_user(user_prefs, limit=40)
    if not matches:
        prefs_str = ", ".join(f"*{p}*" for p in user_prefs)
        msg = (
            "✨ *No Current Matches Found*\n\n"
            f"No recent postings match your selected categories ({prefs_str}).\n"
            "We scrape monitored channels 3 times daily. You will be alerted as soon as new roles arrive!"
        )
        if update.callback_query:
            await update.callback_query.message.reply_text(msg, parse_mode="Markdown")
        elif update.message:
            await update.message.reply_text(msg, parse_mode="Markdown")
        return

    matched_dict = match_jobs_with_preferences(matches, user_prefs)
    telegraph_url = create_job_update_telegraph_page(matched_dict)

    text = (
        f"✨ *Latest Career Fit Matches*\n\n"
        f"Found *{len(matches)}* active vacancies matching your categories:\n"
    )
    for cat, jobs in matched_dict.items():
        text += f"• *{cat}*: {len(jobs)} role(s)\n"

    text += "\n⚡ *Tap Instant View below to view the full curated bulletin:*"

    buttons = []
    if telegraph_url:
        buttons.append([InlineKeyboardButton("⚡ Open Instant View", url=telegraph_url)])

    app_url = get_web_app_url()
    row = []
    if app_url:
        row.append(InlineKeyboardButton("📱 Browse in App", web_app=WebAppInfo(url=app_url)))
    row.append(InlineKeyboardButton("⚙️ Edit Preferences", callback_data="sec_tech"))
    buttons.append(row)

    markup = InlineKeyboardMarkup(buttons)
    if update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=markup, parse_mode="Markdown")
    elif update.message:
        await update.message.reply_text(text, reply_markup=markup, parse_mode="Markdown")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command: register user and present sleek preference menu."""
    user = update.effective_user
    if not user:
        return

    get_or_create_user(user.id)
    privacy_url = get_privacy_policy_url()

    current_prefs = get_user_preferences(user.id)
    text = format_preference_message(current_prefs, active_sector="tech")
    text += f"\n\n🔒 [Privacy Policy]({privacy_url})"

    keyboard = build_apple_style_keyboard(current_prefs, active_sector="tech")
    await update.message.reply_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="Markdown",
        disable_web_page_preview=True,
    )


async def jobs_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /jobs command: generate Instant View bulletin of recent matches on demand."""
    user = update.effective_user
    if not user:
        return
    await send_latest_jobs_to_user(update, user.id)


async def preferences_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /preferences command: display the interactive category picker."""
    user = update.effective_user
    if not user:
        return

    get_or_create_user(user.id)
    current_prefs = get_user_preferences(user.id)
    text = format_preference_message(current_prefs, active_sector="tech")
    keyboard = build_apple_style_keyboard(current_prefs, active_sector="tech")

    await update.message.reply_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command: explain commands, schedules, and usage."""
    help_text = (
        "✨ *Career Fit Jobs Bot*\n\n"
        "🔍 *Available Commands:*\n"
        "• /start — Welcome dashboard & preferences\n"
        "• /jobs — Fetch latest matching job bulletin with Instant View\n"
        "• /preferences — Update your target job categories\n"
        "• /help — Show this guide\n\n"
        "📬 *Delivery Schedule:*\n"
        "Automatic alerts arrive 3 times daily (05:00, 11:00, 17:00 UTC) with Telegram Instant View.\n\n"
        "💡 *Tips:*\n"
        "Use /jobs anytime if you want to see the latest vacancies on demand."
    )
    if update.message:
        await update.message.reply_text(help_text, parse_mode="Markdown")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline button clicks for category toggling, sector tabs, and saving."""
    query = update.callback_query
    if not query:
        return

    # Acknowledge immediately to kill UI latency (Apple Design Principle 1)
    await query.answer()

    user_id = query.from_user.id
    data = query.data or ""

    # On-demand jobs button
    if data == "action_get_jobs":
        await send_latest_jobs_to_user(update, user_id)
        return

    # 1. Save preferences
    if data == "pref_submit":
        user_prefs = get_user_preferences(user_id)
        if not user_prefs:
            await query.answer("Please select at least one category before saving.", show_alert=True)
            return

        summary = "\n".join(f"• {pref}" for pref in user_prefs)
        await query.edit_message_text(
            f"✅ *Preferences Saved!*\n\n"
            f"You will receive alerts for:\n{summary}\n\n"
            "Whenever top channels post matching vacancies, you will be notified.\n"
            "You can also run /jobs anytime to view current matches!",
            parse_mode="Markdown",
        )
        return

    # 2. Switch Sector Tab
    if data.startswith("sec_"):
        active_sector = data[4:]
        if active_sector not in SECTORS:
            active_sector = "tech"
        current_prefs = get_user_preferences(user_id)
        text = format_preference_message(current_prefs, active_sector=active_sector)
        keyboard = build_apple_style_keyboard(current_prefs, active_sector=active_sector)
        await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="Markdown")
        return

    # 3. Clear All
    if data.startswith("pref_clear"):
        parts = data.split("_")
        active_sector = parts[2] if len(parts) > 2 else "tech"
        update_user_preferences(user_id, [])
        text = format_preference_message([], active_sector=active_sector)
        keyboard = build_apple_style_keyboard([], active_sector=active_sector)
        await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="Markdown")
        return

    # 4. Toggle Category Chip
    if data.startswith("pref_"):
        parts = data.split("_")
        active_sector = parts[-1] if parts[-1] in SECTORS else "tech"
        slug = "_".join(parts[1:-1]) if parts[-1] in SECTORS else "_".join(parts[1:])

        category_map = {
            cat.lower().replace(" ", "_").replace("/", "_"): cat
            for cat in JOB_CATEGORIES
        }
        category = category_map.get(slug)
        if not category:
            return

        current_prefs = get_user_preferences(user_id)
        if category in current_prefs:
            current_prefs.remove(category)
        else:
            if len(current_prefs) >= MAX_PREFERENCES:
                await query.answer(f"Maximum {MAX_PREFERENCES} categories allowed.", show_alert=True)
                return
            current_prefs.append(category)

        # Save to database
        update_user_preferences(user_id, current_prefs)

        text = format_preference_message(current_prefs, active_sector=active_sector)
        keyboard = build_apple_style_keyboard(current_prefs, active_sector=active_sector)
        await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="Markdown")


async def web_app_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle data sent back from the Telegram Mini App."""
    if not update.effective_message or not update.effective_message.web_app_data:
        return

    user_id = update.effective_user.id
    raw_data = update.effective_message.web_app_data.data

    try:
        payload = json.loads(raw_data)
        preferences = payload.get("preferences", [])
        if isinstance(preferences, list):
            update_user_preferences(user_id, preferences)
            summary = "\n".join(f"• {p}" for p in preferences) if preferences else "_None_"
            await update.effective_message.reply_text(
                f"✅ *Preferences updated via Mini App!*\n\n"
                f"Selected categories:\n{summary}\n\n"
                "Use /jobs to fetch current matching vacancies anytime!",
                parse_mode="Markdown",
            )
    except Exception as e:
        logger.error(f"Error handling web app data: {e}")


def register_handlers(application: Application) -> None:
    """Register all bot command, callback, and Mini App handlers on the application."""
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("jobs", jobs_command))
    application.add_handler(CommandHandler("preferences", preferences_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data_handler))
