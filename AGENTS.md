# Career Fit Jobs Bot — Rebuild Brief

## Context for the agent

This is a fork of `firaol-d/Career-Fit-Jobs-Bot`, a Telegram bot that scrapes job posts
from Telegram channels, matches them to user preferences, and pushes alerts 3x/day.
The original build ran on Heroku (paid) and briefly on Render free tier, and broke
because it ran polling + an internal scheduler (e.g. APScheduler-style) inside one
long-running process. Free hosts spin down or restart idle processes, which silently
kills the scheduled sends. **We are not repeating that architecture.**

Read the existing repo code first before writing anything. Note especially:
- `session.session` (if present) is a Telethon session file — check if it contains
  real credentials. If so, treat it as a leaked secret: rotate/revoke it, add it to
  `.gitignore`, and never commit a real one again.
- Any hardcoded tokens/keys anywhere in the codebase — move all of them to environment
  variables / GitHub Actions Secrets before touching anything else.

## Target architecture (100% free tier, no host required to stay awake)

Split into two independent pieces. Do not merge them back into one process.

**1. User-facing bot (chat, commands, profile setup, link submission)**
- Convert from long-polling to **webhook mode**.
- Host on a free serverless platform that scales to zero: Cloudflare Workers or
  Vercel Functions (pick whichever fits the language/runtime already in the repo;
  if the repo is Python, Vercel Python functions or a small FastAPI app on
  Cloudflare via Workers Python is fine — confirm compatibility before committing).
- Telegram POSTs updates to this endpoint. Cold starts are fine; this isn't
  latency-sensitive.

**2. Scheduled scraper + notifier (runs 3x/day)**
- Implement as a **GitHub Actions scheduled workflow** (`.github/workflows/*.yml`
  with a `schedule: cron:` trigger), not a background worker.
- Each run: scrape configured Telegram channels → match against user prefs in
  Supabase → call Telegram's `sendMessage` API directly for each match → exit.
- Stateless between runs — all state lives in Supabase, not in the workflow.
- Keep the repo **public** so Actions minutes are unlimited/free. Put all secrets
  (bot token, Supabase keys, Telethon API creds) in GitHub Actions Secrets.
- Add a lightweight keepalive (e.g. a weekly workflow that bumps a timestamp file)
  so the scheduled workflow doesn't get auto-disabled after 60 days of repo
  inactivity.

**Database:** Keep Supabase (free tier). All schema changes go through migration
files checked into the repo, not made ad hoc in the dashboard.

## New features to build (in priority order)

1. **User profile**: CV upload (store in Supabase Storage), experience/skills text
   fields, editable via bot commands.
2. **Application tracking by link**: user sends a job link → bot creates a row
   (user_id, link, status, timestamp) using their existing profile info — no
   re-entry of CV/experience per application.
3. **CV swap**: let user upload a replacement CV that becomes their new default,
   without affecting already-submitted application records (store a reference,
   not a copy-per-application, unless they explicitly attach a different CV to
   one application).
4. **Suggest-a-job-by-link**: user sends a link to a job they want to share → bot
   stores/queues it (same shape as application tracking, different table/flag),
   for either admin review or auto-inclusion in the next alert batch — confirm
   which behavior is wanted before building.

## Working agreement for the agent

- Make small, reviewable commits. Don't refactor unrelated code while adding a
  feature.
- Never commit secrets, tokens, or the real `session.session` file.
- Before starting each session, read `.agents/.AGENT_LOG.md` (create it if missing) to
  see what's already done and what's next.
- At the **end of every chat/edits** (or before running low on context/
  tokens), update `.agents/.AGENT_LOG.md` using the format below. This is how work gets
  handed off between IDE sessions and between different accounts — treat it as
  mandatory, not optional.

### AGENT_LOG.md format

Append a new entry per session, most recent on top:

```md
## [YYYY-MM-DD HH:MM] Session summary

**Done this session:**
- Bullet list of concrete changes (files touched, features completed)

***Done this chat:***
- Short bullet list of concrete changes
***Decisions made:***
- Any architectural/design choice made and why (so it isn't re-litigated later)

**Open questions / blockers:**
- Anything unresolved that needs a human decision or is blocking progress

**Next steps:**
- Concrete next action(s) for the next session, in priority order

**State of the repo:**
- What currently works end-to-end vs. what's partial/untested
```

Keep entries honest — if something is half-done or untested, say so explicitly.
The next session (possibly a different agent/account) should be able to read
the latest entry and continue without re-reading the whole codebase from
scratch.