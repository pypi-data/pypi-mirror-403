from typing import Optional, Dict, Any, List
from datetime import datetime


def format_slack_message(
    service_name: str,
    environment: str,
    error_type: str,
    error_message: str,
    location: str,
    function_name: str,
    short_traceback: str,
    context: Dict[str, Any],
    first_seen: datetime,
    occurrences: int,
    github_issue_number: Optional[int],
    github_repo: Optional[str]
) -> List[Dict[str, Any]]:
    # Build context string
    context_lines = [f"• {k}: {v}" for k, v in context.items()]
    context_str = "\n".join(context_lines) if context_lines else "No context"

    # GitHub link
    github_link = ""
    github_text = "N/A"
    if github_issue_number and github_repo:
        github_link = f"https://github.com/{github_repo}/issues/{github_issue_number}"
        github_text = f"#{github_issue_number}"

    # Format first seen
    if isinstance(first_seen, datetime):
        time_diff = datetime.utcnow() - first_seen
        if time_diff.total_seconds() < 60:
            first_seen_str = "Just now"
        elif time_diff.total_seconds() < 3600:
            mins = int(time_diff.total_seconds() / 60)
            first_seen_str = f"{mins} min ago"
        elif time_diff.total_seconds() < 86400:
            hours = int(time_diff.total_seconds() / 3600)
            first_seen_str = f"{hours} hours ago"
        else:
            first_seen_str = first_seen.strftime("%Y-%m-%d %H:%M UTC")
    else:
        first_seen_str = str(first_seen)

    # Truncate error message
    if len(error_message) > 200:
        error_message = error_message[:200] + "..."

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"🚨 ERROR - {service_name}",
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*{error_type}:* {error_message}"}
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*📍 Location*\n`{location}` in `{function_name}()`"}
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*📋 Context*\n{context_str}"}
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*📚 Stack Trace (shortened)*\n`{short_traceback}`"}
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*📊 Stats*\n• First seen: {first_seen_str}\n• Occurrences: {occurrences}\n• GitHub: {github_text}"
            }
        },
        {
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": f"{environment} • {datetime.utcnow().strftime('%b %d, %Y %I:%M %p UTC')}"}
            ]
        }
    ]

    if github_link:
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "View Full Details on GitHub", "emoji": True},
                    "url": github_link,
                    "style": "primary"
                }
            ]
        })

    blocks.append({"type": "divider"})
    return blocks
