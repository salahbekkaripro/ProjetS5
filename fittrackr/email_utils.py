from __future__ import annotations

from typing import Any, Iterable

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

BRAND_CONTEXT = {
    "name": "FitTrackR",
    "primary": "#e6392f",
    "secondary": "#2563eb",
    "accent": "#12b886",
    "text": "#0f172a",
}


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

    ctx = {"brand": BRAND_CONTEXT}
    if context:
        ctx.update(context)

    html_body = render_to_string(template_name, ctx)
    if text_template:
        text_body = render_to_string(text_template, ctx)
    else:
        text_body = strip_tags(html_body)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=to_list,
        reply_to=reply_to,
    )
    msg.attach_alternative(html_body, "text/html")
    return msg.send(fail_silently=False)
