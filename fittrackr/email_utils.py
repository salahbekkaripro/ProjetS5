from __future__ import annotations

import base64
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

BRAND_BASE = {
    "name": "FitTrackR",
    "primary": "#e6392f",
    "secondary": "#2563eb",
    "accent": "#12b886",
    "text": "#0f172a",
}


@lru_cache(maxsize=1)
def _logo_data_uri() -> str | None:
    """
    Load the local logo as a data URI for embedding in emails.
    """
    logo_path = Path(settings.BASE_DIR) / "image.png"
    if not logo_path.exists():
        return None
    data = logo_path.read_bytes()
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _brand_context() -> dict[str, Any]:
    ctx = dict(BRAND_BASE)
    logo_data = _logo_data_uri()
    if logo_data:
        ctx["logo_data"] = logo_data
    return ctx


def send_templated_email(
    subject: str,
    to_emails: str | Iterable[str],
    template_name: str,
    context: dict[str, Any] | None = None,
    *,
    text_template: str | None = None,
    reply_to: list[str] | None = None,
) -> int:
    """
    Envoie un email HTML + texte avec un thème cohérent.
    """
    if isinstance(to_emails, str):
        to_list = [to_emails]
    else:
        to_list = list(to_emails)

    ctx = {"brand": _brand_context()}
    if context:
        ctx.update(context)

    html_body = render_to_string(template_name, ctx)
    if text_template:
        text_body = render_to_string(text_template, ctx)
    else:
        text_body = strip_tags(html_body)

    # Priorité à l'API SendGrid si la clé est fournie (plus fiable que SMTP sur certains hosts)
    sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
    if sendgrid_api_key:
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail

            sg_message = Mail(
                from_email=settings.DEFAULT_FROM_EMAIL,
                to_emails=to_list,
                subject=subject,
                html_content=html_body,
                plain_text_content=text_body,
            )
            if reply_to:
                sg_message.reply_to = reply_to[0]
            sg = SendGridAPIClient(sendgrid_api_key)
            sg.send(sg_message)
            return 1
        except Exception:
            # En cas d'échec SendGrid, on laisse la voie SMTP tenter d'envoyer ou lever l'erreur.
            pass

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=to_list,
        reply_to=reply_to,
    )
    msg.attach_alternative(html_body, "text/html")
    return msg.send(fail_silently=False)
