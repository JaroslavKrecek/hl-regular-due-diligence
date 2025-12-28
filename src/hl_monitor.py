#!/usr/bin/env python3
"""
Hargreaves Lansdown Monthly Due Diligence Monitor
Uses Claude API with web search to research HL, compare with previous report,
and email a summary of changes.
"""

import os
import json
import smtplib
import anthropic
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path


# Configuration from environment variables
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
GMAIL_ADDRESS = os.environ["GMAIL_ADDRESS"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
RECIPIENT_EMAIL = os.environ["RECIPIENT_EMAIL"]

# Paths
SCRIPT_DIR = Path(__file__).parent
REPORTS_DIR = SCRIPT_DIR.parent / "reports"
LATEST_REPORT_PATH = REPORTS_DIR / "latest_report.json"


def get_research_prompt() -> str:
    """Returns the prompt for Claude to research Hargreaves Lansdown."""
    return """Conduct comprehensive due diligence research on Hargreaves Lansdown (HL) with focus on recent developments. Search for and analyze:

1. **CEO Search & Leadership**
   - Current status of CEO search (Dan Olley and Amy Stirling departed after acquisition)
   - Any announcements about permanent CEO appointment
   - Changes to executive team or board

2. **New Ownership Impact**
   - How are CVC Capital Partners, Nordic Capital, and ADIA changing the company?
   - Technology investment announcements
   - Strategic direction changes since March 2025 privatisation
   - Any fee structure changes or new product announcements

3. **Woodford Litigation**
   - Current status of the £200m+ group legal action by RGL Management
   - Any court dates, rulings, or settlement discussions
   - Financial provisions or statements about the case
   - Impact on company finances or reputation

4. **Operational Performance**
   - Recent AUA (Assets Under Administration) figures
   - Client numbers and net flows
   - Platform reliability incidents
   - Customer service quality indicators

5. **Regulatory Standing**
   - Any new FCA actions, investigations, or concerns
   - Consumer Duty compliance updates
   - FSCS protection status confirmation

6. **Financial Health**
   - Latest available financial metrics
   - Cash position and debt levels
   - Any credit rating changes

Provide a structured report with clear sections. Include specific dates and sources for all claims. Flag any items that represent significant changes or concerns for a Junior ISA customer with £30,000+ invested.

Today's date: """ + datetime.now().strftime("%d %B %Y")


def get_comparison_prompt(previous_report: str, new_report: str, previous_date: str) -> str:
    """Returns the prompt for Claude to compare two reports."""
    return f"""Compare these two due diligence reports on Hargreaves Lansdown and identify significant changes.

PREVIOUS REPORT ({previous_date}):
{previous_report}

---

NEW REPORT ({datetime.now().strftime("%d %B %Y")}):
{new_report}

---

Provide a structured comparison with these sections:

## 🔴 CRITICAL CHANGES (Immediate attention required)
Items that significantly affect risk for a £30k+ Junior ISA holder

## 🟡 NOTABLE DEVELOPMENTS (Worth monitoring)
Material changes that don't require immediate action

## 🟢 POSITIVE UPDATES
Improvements or reassuring developments

## ℹ️ STATUS UNCHANGED
Key items that remain the same (brief summary)

## 📊 METRICS COMPARISON TABLE
| Metric | Previous | Current | Change |
|--------|----------|---------|--------|
(Include AUA, client numbers, cash position, litigation status where available)

## 💡 RECOMMENDATION
Brief assessment: Should the JISA holder take any action based on these changes?

Be specific about what changed and when. If no significant changes occurred, clearly state that the situation remains stable."""


def conduct_research() -> str:
    """Use Claude API with web search to research Hargreaves Lansdown."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    
    print("Starting research with Claude API + web search...")
    
    # Initial research request
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8192,
        tools=[{
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": 15  # Allow multiple searches for comprehensive research
        }],
        messages=[{
            "role": "user",
            "content": get_research_prompt()
        }]
    )
    
    # Handle potential pause_turn for continued research
    messages = [{"role": "user", "content": get_research_prompt()}]
    
    while response.stop_reason == "pause_turn":
        print("Claude requesting more search time, continuing...")
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": "Please continue your research."})
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8192,
            tools=[{
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 10
            }],
            messages=messages
        )
    
    # Extract text content from response
    report_text = ""
    for block in response.content:
        if hasattr(block, "text"):
            report_text += block.text
    
    print(f"Research complete. Report length: {len(report_text)} characters")
    return report_text


def compare_reports(previous_report: str, new_report: str, previous_date: str) -> str:
    """Use Claude to compare previous and new reports."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    
    print("Comparing reports...")
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": get_comparison_prompt(previous_report, new_report, previous_date)
        }]
    )
    
    comparison_text = ""
    for block in response.content:
        if hasattr(block, "text"):
            comparison_text += block.text
    
    return comparison_text


def load_previous_report() -> tuple[str, str] | None:
    """Load the previous report from file if it exists."""
    if LATEST_REPORT_PATH.exists():
        with open(LATEST_REPORT_PATH, "r") as f:
            data = json.load(f)
            return data.get("report", ""), data.get("date", "Unknown")
    return None


def save_report(report: str) -> None:
    """Save the current report for next month's comparison."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    data = {
        "date": datetime.now().strftime("%d %B %Y"),
        "timestamp": datetime.now().isoformat(),
        "report": report
    }
    
    with open(LATEST_REPORT_PATH, "w") as f:
        json.dump(data, f, indent=2)
    
    # Also save a dated archive copy
    archive_path = REPORTS_DIR / f"report_{datetime.now().strftime('%Y-%m-%d')}.json"
    with open(archive_path, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"Report saved to {LATEST_REPORT_PATH}")


def create_email_html(comparison: str | None, full_report: str, is_first_run: bool) -> str:
    """Create HTML email content."""
    
    # Convert markdown-style formatting to HTML
    def md_to_html(text: str) -> str:
        import re
        # Headers
        text = re.sub(r'^## (.+)$', r'<h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px;">\1</h2>', text, flags=re.MULTILINE)
        text = re.sub(r'^### (.+)$', r'<h3 style="color: #34495e;">\1</h3>', text, flags=re.MULTILINE)
        # Bold
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        # Tables (basic)
        text = re.sub(r'\|(.+)\|', r'<tr><td style="border: 1px solid #ddd; padding: 8px;">\1</td></tr>', text)
        # Line breaks
        text = text.replace('\n\n', '</p><p style="margin: 10px 0;">')
        text = text.replace('\n', '<br>')
        return text
    
    date_str = datetime.now().strftime("%d %B %Y")
    
    if is_first_run:
        subject_line = "🆕 First HL Due Diligence Report"
        intro = """<p style="background: #e8f4f8; padding: 15px; border-radius: 5px;">
            This is your <strong>first automated due diligence report</strong> on Hargreaves Lansdown. 
            Future monthly reports will include a comparison highlighting changes since this baseline.
        </p>"""
        comparison_section = ""
    else:
        subject_line = "📊 Monthly HL Due Diligence Update"
        intro = """<p style="background: #e8f4f8; padding: 15px; border-radius: 5px;">
            Your monthly due diligence report on Hargreaves Lansdown is ready. 
            See the <strong>Changes Summary</strong> below for what's new since last month.
        </p>"""
        comparison_section = f"""
        <div style="background: #fff; border: 1px solid #ddd; border-radius: 5px; padding: 20px; margin: 20px 0;">
            <h2 style="color: #2c3e50; margin-top: 0;">📋 Changes Since Last Report</h2>
            {md_to_html(comparison)}
        </div>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
            h1 {{ color: #1a5276; }}
            h2 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px; }}
            table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background: #3498db; color: white; }}
            .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <h1>🏦 Hargreaves Lansdown Due Diligence Report</h1>
        <p style="color: #666;">Generated: {date_str}</p>
        
        {intro}
        
        {comparison_section}
        
        <details style="margin: 20px 0;">
            <summary style="cursor: pointer; font-weight: bold; font-size: 18px; color: #2c3e50; padding: 10px; background: #f8f9fa; border-radius: 5px;">
                📄 Full Research Report (click to expand)
            </summary>
            <div style="background: #fff; border: 1px solid #ddd; border-radius: 0 0 5px 5px; padding: 20px; margin-top: -5px;">
                {md_to_html(full_report)}
            </div>
        </details>
        
        <div class="footer">
            <p>This report was automatically generated using Claude AI with web search.</p>
            <p>Repository: <a href="https://github.com/YOUR_USERNAME/hl-monitoring">hl-monitoring</a></p>
            <p>Next report scheduled: {(datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1).strftime("%d %B %Y")}</p>
        </div>
    </body>
    </html>
    """
    
    return html, subject_line


def send_email(html_content: str, subject: str) -> None:
    """Send the report via Gmail SMTP."""
    print(f"Sending email to {RECIPIENT_EMAIL}...")
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = RECIPIENT_EMAIL
    
    # Attach HTML content
    html_part = MIMEText(html_content, "html")
    msg.attach(html_part)
    
    # Send via Gmail SMTP
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, RECIPIENT_EMAIL, msg.as_string())
    
    print("Email sent successfully!")


def main():
    """Main execution flow."""
    from datetime import timedelta
    
    print("=" * 60)
    print(f"HL Due Diligence Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    # Step 1: Conduct new research
    new_report = conduct_research()
    
    # Step 2: Load previous report if exists
    previous = load_previous_report()
    
    # Step 3: Compare if we have a previous report
    if previous:
        previous_report, previous_date = previous
        print(f"Found previous report from {previous_date}")
        comparison = compare_reports(previous_report, new_report, previous_date)
        is_first_run = False
    else:
        print("No previous report found - this is the first run")
        comparison = None
        is_first_run = True
    
    # Step 4: Create email
    html_content, subject = create_email_html(comparison, new_report, is_first_run)
    
    # Step 5: Send email
    send_email(html_content, subject)
    
    # Step 6: Save report for next month
    save_report(new_report)
    
    print("=" * 60)
    print("Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
