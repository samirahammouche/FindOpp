"""Custom template tags of the organizer space.

    {% load findopp_tags %}
    {% doodle "book" "blue" %}        hand-drawn style icon on a colored blob
    {% icon "search" %}               simple line icon
    {{ 24860|spaced }}                -> "24 860"
    {{ publication.status|status_class }}
    {{ "/organizer-media/x.jpg"|media }}
"""
from datetime import date

from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()

# 24x24 line icons
ICONS = {
    "overview": "M3 5h18v11H3z M8 20h8 M12 16v4 M7 12.5l3-3 3 2 4-4",
    "book": "M3 5.5c3-1.2 6-1.2 9 .8 3-2 6-2 9-.8V19c-3-1.2-6-1.2-9 .8-3-2-6-2-9-.8z M12 6.3v13.5 "
            "M5.5 9h4 M5.5 12h4 M14.5 9h4 M14.5 12h4",
    "code": "M8 7l-5 5 5 5 M16 7l5 5-5 5 M14 4l-4 16",
    "cap": "M2 9l10-5 10 5-10 5z M6 11v5c3 2.5 9 2.5 12 0v-5 M22 9v5",
    "puzzle": "M10 3h4v2.2a1.8 1.8 0 1 0 3.6 0V3H21v5.5h-2.2a1.8 1.8 0 1 0 0 3.6H21V21h-5.5v-2.2a1.8 1.8 0 1 0-3.6 "
              "0V21H3v-5.5h2.2a1.8 1.8 0 1 0 0-3.6H3V3h7",
    "globe": "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18z M3 12h18 M12 3c2.5 2.7 3.8 5.7 3.8 9s-1.3 6.3-3.8 9"
             "c-2.5-2.7-3.8-5.7-3.8-9S9.5 5.7 12 3z",
    "medal": "M12 3a6 6 0 1 0 0 12 6 6 0 0 0 0-12z M9.5 9l2 2 3.5-3.5 M8.5 14l-1.5 7 5-2.5 5 2.5-1.5-7",
    "calendar": "M4 6h16v14H4z M4 10h16 M8 3v4 M16 3v4 M7.5 13.5h2 M11 13.5h2 M7.5 16.5h2 "
                "M17 14.5a3 3 0 1 0 0 6 3 3 0 0 0 0-6z M17 16v1.5l1 .8",
    "bell": "M6 16v-5a6 6 0 0 1 12 0v5l1.5 2h-15z M10 21h4",
    "search": "M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14z M20 20l-4-4",
    "image": "M3 5h18v14H3z M3 16l5-5 4 4 3-3 6 6 M15.5 8.5h.01",
    "pin": "M12 21s-7-6-7-11.5a7 7 0 0 1 14 0C19 15 12 21 12 21z M12 7a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5z",
    "link": "M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1 M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1",
    "logout": "M15 4h4v16h-4 M10 8l-4 4 4 4 M6 12h10",
    "check": "M5 12l5 5 9-10",
    "plus": "M12 5v14 M5 12h14",
    "mail": "M3 6h18v12H3z M3 7l9 6 9-6",
    "lock": "M6 11h12v9H6z M8.5 11V8a3.5 3.5 0 0 1 7 0v3",
    "arrow": "M5 12h14 M13 6l6 6-6 6",
    "external": "M7 17L17 7 M9 7h8v8",
}

# blob color, line color
COLORS = {
    "blue": ("#A9C6F0", "#1E4E8C"),
    "mint": ("#A8E3D2", "#1D6B4C"),
    "yellow": ("#F6D58A", "#7A5200"),
    "pink": ("#F4A7B9", "#9C3550"),
    "lavender": ("#CFC6F2", "#4B3E75"),
}
BLOB = "M12 1.6c5.2 0 10.4 2.7 10.4 8.6 0 6.9-4.8 12.4-10.8 12.4C5.4 22.6 1.6 18 1.6 12.2 1.6 6.1 6.5 1.6 12 1.6z"

CATEGORY_STYLE = {
    "hackathon": ("code", "blue"),
    "scholarship": ("medal", "mint"),
    "event": ("calendar", "yellow"),
    "club": ("puzzle", "pink"),
}


@register.simple_tag
def doodle(name, color="blue", size=44):
    blob, stroke = COLORS.get(color, COLORS["blue"])
    return format_html(
        '<svg class="doodle" width="{s}" height="{s}" viewBox="0 0 24 24" aria-hidden="true">'
        '<path d="{blob}" fill="{fill}" transform="translate(-1 1)"/>'
        '<path d="{path}" fill="none" stroke="{stroke}" stroke-width="1.5" '
        'stroke-linecap="round" stroke-linejoin="round"/></svg>',
        s=size, blob=BLOB, fill=blob, path=ICONS.get(name, ""), stroke=stroke,
    )


@register.simple_tag
def category_doodle(category, size=44):
    name, color = CATEGORY_STYLE.get(category, ("book", "blue"))
    return doodle(name, color, size)


@register.simple_tag
def icon(name, size=18):
    return format_html(
        '<svg class="icon" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        '<path d="{p}"/></svg>', s=size, p=ICONS.get(name, ""),
    )


@register.inclusion_tag("partials/_logo.html")
def logo(variant="dark", size=40):
    return {"variant": variant, "size": size}


@register.filter
def spaced(value):
    """24860 -> "24 860" (French style thousands, like the design)."""
    try:
        return mark_safe(f"{int(value):,}".replace(",", "&#8239;"))
    except (TypeError, ValueError):
        return value


@register.filter
def status_class(status):
    return f"status status--{status or 'draft'}"


@register.filter
def category_class(category):
    return f"badge badge--{category or 'hackathon'}"


@register.filter
def media(url):
    """Image URL from the serializer (same service, so it is used as it is)."""
    return url or ""


@register.filter
def short_date(value):
    """'2027-01-15' -> '15 Jan 2027'"""
    if not value:
        return "—"
    try:
        day = date.fromisoformat(str(value)[:10])
    except ValueError:
        return value
    return f"{day.day} {day.strftime('%b %Y')}"


@register.simple_tag(takes_context=True)
def query(context, **changes):
    """Keeps the current filters when changing page or tab: ?{% query page=2 %}"""
    params = context["request"].GET.copy()
    for key, value in changes.items():
        if value in (None, ""):
            params.pop(key, None)
        else:
            params[key] = value
    return params.urlencode()
