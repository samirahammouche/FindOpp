"""Turns the 30-day series of the API into an SVG line chart (no JS library)."""
import math
from datetime import date

WIDTH, HEIGHT = 1000, 260  # drawing area of the SVG


def _nice_step(value):
    """Round step for 3 grid intervals: 233 -> 250, 410 -> 500, 7 -> 10."""
    if value <= 0:
        return 10
    power = 10 ** math.floor(math.log10(value))
    for factor in (1, 2, 2.5, 5, 10):
        if value <= factor * power:
            return int(factor * power) or 1
    return int(10 * power)


def _label(day):
    return f"{day.day} {day.strftime('%b')}"


def build_views_chart(chart):
    """chart = {"from": "2026-10-12", "to": "2026-11-10", "points": [{"date": ..., "views": 12}, ...]}"""
    points = chart.get("points") or []
    days = [p["date"] if isinstance(p["date"], date) else date.fromisoformat(p["date"]) for p in points]
    values = [p["views"] for p in points]
    if not values:
        return None

    step = _nice_step(max(values) / 3)
    top = step * 3
    step_x = WIDTH / max(len(values) - 1, 1)
    coords = [(round(i * step_x, 1), round(HEIGHT - v * HEIGHT / top, 1)) for i, v in enumerate(values)]
    line = " ".join(f"{x},{y}" for x, y in coords)

    ticks = [{"value": step * i, "y": round(HEIGHT - HEIGHT * i / 3, 1)} for i in range(4)]
    label_indexes = sorted({0, len(days) // 3, 2 * len(days) // 3, len(days) - 1})
    labels = [{"text": _label(days[i]), "x": coords[i][0]} for i in label_indexes]

    start, end = days[0], days[-1]
    period = f"{start.day} {start.strftime('%B')} – {end.day} {end.strftime('%B %Y')}"
    return {
        "width": WIDTH, "height": HEIGHT,
        "line": line,
        "area": f"0,{HEIGHT} {line} {WIDTH},{HEIGHT}",
        "ticks": ticks, "labels": labels, "period": period,
        "total": sum(values),
    }
