---
name: ops
description: Business operations and utility toolkit for claude.ai. Triggers on "find leads", "analyze competitors", "optimize tweet", "domain name", "meeting transcript", "organize invoices", "pick a winner", "send email", "connect to app", "create a Notion page", "update Jira", "post to Slack", or any business-utility request. Routes to web_search/web_fetch for research, places_search for location/business queries, MCP connectors (Slack/Notion/Jira/Asana/HubSpot/Linear/Atlassian/Box/Canva/Figma) for cross-app actions, the bash sandbox for invoice processing or random selection. Single-instance, claude.ai-only — no local Composio install, no n8n, no external orchestrator.
---

# Ops — claude.ai Business Utility

Business-side tasks that aren't software development. Lead research, competitive analysis, social media, domain naming, meeting notes, invoices, draws, app integration. The skill is mostly a router — claude.ai already has good tools for most of this.

The Claude Code original wrapped Composio for app connection and a bunch of standalone scripts. Here we use real MCP connectors plus claude.ai's native research and place tools.

---

## Routing

| Request | Tool stack |
|---|---|
| Find leads / prospects | `web_search` + `web_fetch` for company sites, LinkedIn-listed info, Crunchbase pages |
| Analyze competitor ads / website / positioning | `web_search` for ads/landing pages, `web_fetch` to read them, `image_search` for ad creative |
| Optimize tweet / LinkedIn / social post | claude.ai writes drafts directly; user reviews; iterate |
| Brainstorm domain names | claude.ai generates candidates; for availability, user checks via registrar (we can't query WHOIS reliably from sandbox without API keys) |
| Meeting transcript analysis | user pastes transcript or uploads file → claude.ai summarizes, extracts action items, attributes decisions |
| Organize invoices / receipts | upload PDFs → `pdf-reading` skill extracts → `xlsx` skill produces summary |
| Pick a random winner | `bash_tool` with `python -c "import random; random.choice(...)"` |
| Send email / Slack / Jira / Notion / Asana / Linear / GitHub | `search_mcp_registry` then `suggest_connectors` — let user pick the connector and authorize |
| Local business / restaurant / venue lookup | `places_search` + `places_map_display_v0` |
| Weather for a meeting / trip | `weather_fetch` |
| Compose a hard message (negotiation, decline, follow-up) | `message_compose_v1` |

---

## Lead research

Standard workflow when the user asks for sales/prospecting leads:

1. Ask three questions if not already answered (use `ask_user_input_v0`):
   - What product/service?
   - Who's the ideal customer? (industry, size, role)
   - What's the value prop in one sentence?

2. Search candidate sources:
   - Company directories: `web_search` for "{industry} companies {region} {size}" 
   - Crunchbase / LinkedIn pages: `web_fetch` on specific company URLs the user shares or that come up in search
   - Industry-specific listings (SaaS reviews, B2B databases, trade press)

3. Output: a markdown table with columns the user actually needs (Company / Why fit / Likely contact / How to reach / Source URL). 10–20 rows max for one query.

4. Save the table to `/mnt/user-data/outputs/leads-<tag>.md` and `present_files`.

Don't fabricate contact emails or phone numbers. If you don't have a verified source, leave the field blank or note "find via LinkedIn outreach".

---

## Competitor analysis

```
1. Get the competitor list (user provides, or web_search if "find competitors of X")
2. For each competitor:
   - web_fetch their landing page → positioning, pricing tier, target customer
   - web_search "{competitor} reviews" → what users complain about and praise
   - web_search "{competitor} alternatives" → what else exists in the space
3. Synthesize a comparison matrix (xlsx for data-heavy, md for narrative)
4. Honest gap analysis — where is the user's offering genuinely differentiated, where is it weaker
```

For ad creative analysis specifically: `image_search "{company} ad campaign 2024"` for visual reference of what they're running. Note that ad libraries (Meta Ad Library, TikTok Ad Library) are searchable via web_fetch directly.

---

## App connections (MCP)

When the user wants to take action in another app:

1. Call `search_mcp_registry` with relevant keywords ("notion", "tasks", "calendar", etc.)
2. If a result fits, call `suggest_connectors` so the user can connect/authorize
3. Wait for the user's selection — the chosen connector arrives as their next message
4. Then use the now-loaded MCP tool (which appears as `[third_party_mcp_app]` in tool descriptions)

Already-connected MCPs (per the system context) include: Atlassian (Jira/Confluence), Notion, Slack, Asana, Linear, HubSpot, Intercom, Canva, Figma, Box, monday.com, Hugging Face, Cloudflare. If the user names one of these, just use it — don't re-prompt connector selection.

---

## Invoice / receipt organization

```
1. veritas audit on uploads
2. For each PDF: pdf-reading skill workflow → extract: date, vendor, amount, currency, category
3. For each image (scanned receipt): mention the limitation — claude.ai can read what's visible to it, but doesn't OCR scanned receipts as accurately as a dedicated OCR service. Suggest a tool if accuracy matters.
4. xlsx skill builds the summary spreadsheet
5. present_files on the .xlsx
```

Don't claim accuracy you don't have. If a receipt is faded, blurry, or partially cropped, flag the entry as "needs verification".

---

## Random winner picker

```python
# In bash sandbox
import random
entrants = ["alice", "bob", "carol", ...]  # from user's list
random.seed()  # default to system entropy
winner = random.choice(entrants)
print(winner)
```

For high-stakes draws (something that matters legally / publicly): mention that this isn't cryptographically auditable. For real-money draws, suggest a third-party service that provides a verifiable record (random.org with signed certificate, or a blockchain-based draw).

---

## What got stripped from v1

- **Composio integration** — replaced by claude.ai's MCP connectors. Whatever Composio was bridging (Gmail, Slack, GitHub, Notion), there's a real MCP for it now.
- **n8n / Zapier orchestration** — claude.ai isn't an orchestrator. For multi-step automation, the user runs n8n/Zapier themselves; we draft the workflow definition.
- **YouTube downloader** — bash sandbox can install yt-dlp, but downloading copyrighted video typically violates ToS regardless of skill name. Default to "I won't download this; here's the link to share legally instead." If it's the user's own content or clearly public-domain, yt-dlp works in bash.
- **Connect-apps Composio installer** — replaced by `search_mcp_registry` + `suggest_connectors` flow

---

## Anti-patterns

- **Fabricated contacts**: never invent email addresses, phone numbers, or LinkedIn URLs. If you can't verify, leave blank.
- **Confident pricing**: competitor pricing changes constantly. Always note the date the page was fetched and that it may be stale.
- **OCR overconfidence**: if the source is a low-quality scanned image, say so before extracting. Don't pretend to high accuracy on bad inputs.
- **Connector spam**: don't suggest every connector that vaguely matches. One or two relevant ones, picked by what the user actually needs.

---

## Tool reference

| Need | Tool |
|---|---|
| Web research | `web_search`, `web_fetch` |
| Local business / map | `places_search`, `places_map_display_v0` |
| Weather | `weather_fetch` |
| Cross-app action | `search_mcp_registry` → `suggest_connectors` → wait → use MCP tool |
| Spreadsheet output | `xlsx` skill |
| Word document output | `docx` skill |
| Hard-message draft | `message_compose_v1` |
| User clarification | `ask_user_input_v0` (1–3 tappable questions) |
| Random selection | `bash_tool` with Python `random` |
| Present results | `present_files` |
