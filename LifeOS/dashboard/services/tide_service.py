"""
Tide helpers for Porto de Cabedelo (stored TideEvent rows).
Returns plain dicts/lists for templates and API responses.
"""
from __future__ import annotations

import datetime as dt
import logging
from typing import Any, Optional

from django.utils import timezone

from ..models import TideEvent

logger = logging.getLogger(__name__)

TZ_NAME = 'America/Fortaleza'
PORT_DEFAULT = 'Porto de Cabedelo'

# Kite heuristics (meters)
HEIGHT_FAVORABLE_LOW = 0.6
HEIGHT_FAVORABLE_HIGH = 2.2
HEIGHT_CAUTION_LOW = 0.4
HEIGHT_CAUTION_HIGH = 2.4
WIND_KITE_KNOTS = 15.0


def _as_date(target_date: Optional[dt.date]) -> dt.date:
    if target_date is None:
        return timezone.localdate()
    return target_date


def _event_to_dict(ev: TideEvent) -> dict[str, Any]:
    return {
        'id': ev.pk,
        'port_name': ev.port_name,
        'date': ev.date.isoformat(),
        'weekday': ev.date.strftime('%a'),
        'time': ev.time.strftime('%H:%M'),
        'height_m': ev.height_m,
        'tide_type': ev.tide_type,
        'datetime_local': ev.datetime_local.isoformat(),
        'source': ev.source,
        'timezone': ev.timezone,
    }


def get_today_tides(target_date: Optional[dt.date] = None, port_name: str = PORT_DEFAULT) -> list[dict[str, Any]]:
    """All tide events for a calendar day, ordered by time."""
    d = _as_date(target_date)
    qs = TideEvent.objects.filter(port_name=port_name, date=d).order_by('time')
    return [_event_to_dict(t) for t in qs]


def get_next_tide(now: Optional[dt.datetime] = None, port_name: str = PORT_DEFAULT) -> Optional[dict[str, Any]]:
    """Next strictly future tide event for this port (by datetime_local)."""
    if now is None:
        now = timezone.now()
    if timezone.is_naive(now):
        now = timezone.make_aware(now, timezone.get_current_timezone())
    ev = (
        TideEvent.objects.filter(port_name=port_name, datetime_local__gt=now)
        .order_by('datetime_local')
        .first()
    )
    if not ev:
        return None
    return _event_to_dict(ev)


def classify_tide_event(
    previous: Optional[dict[str, Any]],
    current: dict[str, Any],
    next_event: Optional[dict[str, Any]],
) -> str:
    """
    Trend label using heights at prev / current / next (dicts with height_m).
    """
    h0 = previous['height_m'] if previous else None
    h1 = current['height_m']
    h2 = next_event['height_m'] if next_event else None

    if h0 is not None and h2 is not None:
        if h1 >= h0 and h1 >= h2:
            return 'HIGH_PEAK'
        if h1 <= h0 and h1 <= h2:
            return 'LOW_PEAK'
        if h1 > h0 and h1 < h2:
            return 'RISING'
        if h1 < h0 and h1 > h2:
            return 'FALLING'
    if h0 is not None:
        return 'RISING' if h1 > h0 else 'FALLING'
    if h2 is not None:
        return 'RISING' if h1 < h2 else 'FALLING'
    return 'UNKNOWN'


def _interpolated_height_at(now: dt.datetime, day_events: list[TideEvent]) -> Optional[float]:
    """Linear interpolation between bracketing tide points on the same day."""
    if not day_events:
        return None
    if timezone.is_naive(now):
        now = timezone.make_aware(now, timezone.get_current_timezone())
    times = [(e.datetime_local, e.height_m) for e in day_events]
    times.sort(key=lambda x: x[0])
    if now <= times[0][0]:
        return times[0][1]
    if now >= times[-1][0]:
        return times[-1][1]
    for i in range(len(times) - 1):
        t0, h0 = times[i]
        t1, h1 = times[i + 1]
        if t0 <= now <= t1:
            span = (t1 - t0).total_seconds()
            if span <= 0:
                return h0
            frac = (now - t0).total_seconds() / span
            return h0 + (h1 - h0) * frac
    return None


def get_tide_window(target_date: Optional[dt.date] = None, port_name: str = PORT_DEFAULT) -> dict[str, Any]:
    """
    Heuristic 'best water' text from same-day events (no ocean model — discrete table only).
    """
    d = _as_date(target_date)
    events = list(TideEvent.objects.filter(port_name=port_name, date=d).order_by('time'))
    if not events:
        return {'label': 'No tide data', 'windows': [], 'detail': ''}

    windows: list[str] = []
    for i in range(len(events) - 1):
        a, b = events[i], events[i + 1]
        lo = min(a.height_m, b.height_m)
        hi = max(a.height_m, b.height_m)
        if lo >= HEIGHT_FAVORABLE_LOW and hi <= HEIGHT_FAVORABLE_HIGH:
            windows.append(f"{a.time.strftime('%H:%M')}–{b.time.strftime('%H:%M')}")

    if windows:
        label = ' / '.join(windows[:3])
        if len(windows) > 3:
            label += ' …'
        detail = 'Segments where tide stays roughly 0.6–2.2 m between successive table points.'
    else:
        label = 'Check heights — no full segment in ideal 0.6–2.2 m band'
        detail = 'Use chart and next tide; table is sparse between extrema.'

    return {'label': label, 'windows': windows, 'detail': detail}


def get_kite_tide_score(target_date: Optional[dt.date] = None, port_name: str = PORT_DEFAULT) -> dict[str, Any]:
    """Score 0–10 + labels from today's table and current interpolated height."""
    d = _as_date(target_date)
    events = list(TideEvent.objects.filter(port_name=port_name, date=d).order_by('time'))
    if not events:
        return {
            'score': 0,
            'label': 'NO DATA',
            'tone': 'muted',
            'height_now_m': None,
            'trend': 'UNKNOWN',
            'cautions': [],
        }

    now = timezone.now()
    h_now = _interpolated_height_at(now, events)
    cautions: list[str] = []

    if h_now is not None:
        if h_now < HEIGHT_CAUTION_LOW:
            cautions.append('Very low water')
        elif h_now > HEIGHT_CAUTION_HIGH:
            cautions.append('Very high water')
        elif h_now < HEIGHT_FAVORABLE_LOW or h_now > HEIGHT_FAVORABLE_HIGH:
            cautions.append('Outside ideal 0.6–2.2 m band')

    prev_ev = (
        TideEvent.objects.filter(port_name=port_name, datetime_local__lte=now)
        .order_by('-datetime_local')
        .first()
    )
    next_ev = (
        TideEvent.objects.filter(port_name=port_name, datetime_local__gt=now)
        .order_by('datetime_local')
        .first()
    )
    trend = 'UNKNOWN'
    if prev_ev and next_ev:
        if next_ev.height_m > prev_ev.height_m:
            trend = 'RISING'
        elif next_ev.height_m < prev_ev.height_m:
            trend = 'FALLING'
        else:
            trend = 'STEADY'

    score = 7
    if h_now is not None:
        if HEIGHT_FAVORABLE_LOW <= h_now <= HEIGHT_FAVORABLE_HIGH:
            score += 2
        if h_now < HEIGHT_CAUTION_LOW or h_now > HEIGHT_CAUTION_HIGH:
            score -= 4
    if 'Very low' in ' '.join(cautions) or 'Very high' in ' '.join(cautions):
        score -= 2
    if trend == 'RISING' and not cautions:
        score += 1
    if trend == 'FALLING':
        score -= 1

    score = max(0, min(10, score))

    if score >= 7 and not cautions:
        label, tone = 'FAVORABLE', 'good'
    elif score >= 4:
        label, tone = 'MIXED', 'warn'
    else:
        label, tone = 'CAUTION', 'bad'

    return {
        'score': score,
        'label': label,
        'tone': tone,
        'height_now_m': round(h_now, 2) if h_now is not None else None,
        'trend': trend,
        'cautions': cautions,
    }


def combined_kite_message(wind_kn: Optional[float], tide_score: dict[str, Any]) -> dict[str, Any]:
    """Merge Open-Meteo wind (knots) with tide score — UI banner text."""
    favorable_tide = tide_score.get('score', 0) >= 6 and not tide_score.get('cautions')
    wind_ok = wind_kn is not None and wind_kn >= WIND_KITE_KNOTS
    wind_weak = wind_kn is not None and wind_kn < WIND_KITE_KNOTS

    if wind_ok and favorable_tide:
        return {'level': 'kite', 'text': 'KITE WINDOW — wind and tide aligned.'}
    if wind_ok and not favorable_tide:
        return {'level': 'wind', 'text': 'Wind OK — tide caution.'}
    if (not wind_ok) and favorable_tide and wind_kn is not None:
        return {'level': 'tide', 'text': 'Tide OK — wind weak.'}
    if wind_kn is None:
        return {'level': 'info', 'text': 'Load weather for wind + tide combo.'}
    return {'level': 'muted', 'text': 'Conditions marginal — check chart.'}


def build_tide_card_payload(
    target_date: Optional[dt.date] = None,
    port_name: str = PORT_DEFAULT,
    wind_kn: Optional[float] = None,
) -> dict[str, Any]:
    """Everything the tide card partial needs (safe if DB empty)."""
    d = _as_date(target_date)
    tides = get_today_tides(d, port_name=port_name)
    nxt = get_next_tide(port_name=port_name)
    window = get_tide_window(d, port_name=port_name)
    tide_score = get_kite_tide_score(d, port_name=port_name)
    combo = combined_kite_message(wind_kn, tide_score)

    highlight_id = None
    highlight_index = None
    if nxt and nxt['date'] == d.isoformat():
        highlight_id = nxt.get('id')
        for i, row in enumerate(tides):
            if row.get('id') == highlight_id:
                highlight_index = i
                break

    prev_d = d - dt.timedelta(days=1)
    next_d = d + dt.timedelta(days=1)

    return {
        'selected_date': d.isoformat(),
        'nav_prev': prev_d.isoformat(),
        'nav_next': next_d.isoformat(),
        'port_name': port_name,
        'tides': tides,
        'next_tide': nxt,
        'tide_window': window,
        'tide_score': tide_score,
        'kite_message': combo,
        'wind_kn': wind_kn,
        'chart': {
            'labels': [t['time'] for t in tides],
            'heights': [t['height_m'] for t in tides],
            'types': [t['tide_type'] for t in tides],
            'highlight_id': highlight_id,
            'highlight_index': highlight_index,
            'next_time': nxt['time'] if nxt else None,
        },
    }


class TideService:
    """Back-compat wrapper; prefer module-level functions."""

    get_today_tides = staticmethod(get_today_tides)
    get_next_tide = staticmethod(get_next_tide)
    get_tide_window = staticmethod(get_tide_window)
    classify_tide_event = staticmethod(classify_tide_event)
    get_kite_tide_score = staticmethod(get_kite_tide_score)
