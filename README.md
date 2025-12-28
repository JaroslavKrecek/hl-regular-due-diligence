# 🏦 Hargreaves Lansdown Due Diligence Monitor

Automated monthly due diligence research on Hargreaves Lansdown using Claude AI with web search. Compares each month's findings against the previous report and emails a summary of changes.

## 🎯 What It Monitors

- **CEO Search & Leadership** - Status of permanent CEO appointment after March 2025 privatisation
- **New Ownership Impact** - How CVC/Nordic Capital/ADIA are changing the company
- **Woodford Litigation** - Progress of the £200m+ group legal action
- **Operational Performance** - AUA, client numbers, platform reliability
- **Regulatory Standing** - FCA status, Consumer Duty compliance
- **Financial Health** - Cash position, debt levels, credit ratings

## 📅 Schedule

Runs automatically on the **1st of every month at 9:00 AM UTC**.

You can also trigger manually: Actions → Monthly HL Due Diligence → Run workflow

## 🚀 Setup

### 1. Fork or Clone This Repository

```bash
git clone https://github.com/YOUR_USERNAME/hl-monitoring.git
```

### 2. Configure GitHub Secrets

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Description |
|--------|-------------|
| `ANTHROPIC_API_KEY` | Your Claude API key (starts with `sk-ant-`) |
| `GMAIL_ADDRESS` | Gmail address to send from |
| `GMAIL_APP_PASSWORD` | Gmail App Password (16 characters) |
| `RECIPIENT_EMAIL` | Where to receive reports |

### 3. Enable Web Search in Anthropic Console

Go to [console.anthropic.com](https://console.anthropic.com) → Settings → Privacy → Enable "Web search"

### 4. Test the Workflow

Go to **Actions → Monthly HL Due Diligence → Run workflow** to test immediately.

## 📧 Email Output

Each email includes:

1. **Changes Summary** - Critical changes, notable developments, positive updates (compared to previous month)
2. **Metrics Comparison Table** - Side-by-side numbers
3. **Recommendation** - Whether any action is needed
4. **Full Report** - Expandable detailed research (click to view)

## 💰 Cost

- **GitHub Actions**: Free (public repo)
- **Claude API**: ~$0.40/month (Sonnet 4.5 with ~15 web searches)
- **Email**: Free (Gmail SMTP)

**Total: ~$0.40/month**

## 📁 Repository Structure

```
hl-monitoring/
├── .github/
│   └── workflows/
│       └── monthly-research.yml    # GitHub Actions workflow
├── src/
│   └── hl_monitor.py               # Main Python script
├── reports/
│   ├── latest_report.json          # Most recent report (for comparison)
│   └── report_YYYY-MM-DD.json      # Archived reports
├── requirements.txt                 # Python dependencies
└── README.md
```

## 🔧 Customisation

### Change Schedule

Edit `.github/workflows/monthly-research.yml`:

```yaml
schedule:
  - cron: '0 9 1 * *'  # Currently: 9 AM UTC on 1st of month
```

Examples:
- Weekly (Monday 9 AM): `'0 9 * * 1'`
- Bi-weekly: `'0 9 1,15 * *'`

### Modify Research Focus

Edit the `get_research_prompt()` function in `src/hl_monitor.py` to adjust what Claude researches.

### Change AI Model

In `src/hl_monitor.py`, change the model in `conduct_research()`:
- `claude-sonnet-4-20250514` - Balanced (recommended)
- `claude-haiku-4-5-20251001` - Cheaper, faster
- `claude-opus-4-5-20251101` - Most thorough

## 🐛 Troubleshooting

### "No module named 'anthropic'"
Ensure `requirements.txt` includes `anthropic>=0.40.0`

### Email not sending
- Check Gmail App Password is correct (16 chars, no spaces)
- Ensure 2FA is enabled on Gmail
- Check spam folder

### Web search not working
- Enable web search in Anthropic Console (Settings → Privacy)
- Ensure your API key has web search permissions

### Workflow not running on schedule
- GitHub Actions schedules can be delayed up to 15 minutes
- Check Actions tab for any errors
- Ensure the repository has recent activity (dormant repos may have Actions paused)

## 📜 License

MIT - Use freely for personal monitoring.

## ⚠️ Disclaimer

This tool provides automated research summaries, not financial advice. Always verify important information from primary sources before making investment decisions.
