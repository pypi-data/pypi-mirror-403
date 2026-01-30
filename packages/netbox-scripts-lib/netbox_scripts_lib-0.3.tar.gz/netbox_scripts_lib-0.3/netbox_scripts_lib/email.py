import re
from typing import List, Optional
from django.core.mail import send_mail
from netbox.models import NetBoxModel
from netbox import configuration
from extras.scripts import Script

EMAIL_REGEX = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
SENDER = "noreply@cesnet.cz"


def prepare_and_send_email(
    script: Script, subject: str, emails: str, status: str, all_results: List[str], sender: str = SENDER
) -> Optional[str]:
    if not emails:
        return "No e-mail address provided - no e-mail sent"

    if status == "Success":
        return "No issues found - no e-mail sent"

    recipients = [email.strip() for email in emails.split(";")]
    for recipient in recipients:
        if not is_valid_email(recipient):
            script.log_failure(f"Invalid e-mail address: {recipient}")
            return f"Invalid e-mail address: {recipient} - no e-mail sent"

    # Use script.full_name which is in format "module.ClassName"
    jobs_url = f"{configuration.HOST_URL}/extras/scripts/{script.full_name}/jobs"

    body = f"{status} - Please check {jobs_url} results for latest run.\n"
    body += "\n".join(all_results)

    try:
        send_mail(subject, body, sender, recipients, fail_silently=False)
        script.log_success(f"Sending email successful. Recipients: {recipients}")
        return f"Sending email successful. Recipients: {recipients} Subject: {subject}"
    except Exception as e:
        script.log_failure(f"Sending email failed {e}")
        script.log_failure(f"Subject: {subject} sender: {sender} recipients: {recipients}")
        return f"Sending email failed: {e}"


def is_valid_email(email: str) -> bool:
    return re.fullmatch(EMAIL_REGEX, email) is not None


def get_object_url(object: Optional[NetBoxModel]) -> str:
    return f"{configuration.HOST_URL}{object.get_absolute_url()}" if object else ""


def get_markdown_link(object: Optional[NetBoxModel]) -> str:
    return f"[#{object.id} {object.name}]({get_object_url(object)})" if object else ""
