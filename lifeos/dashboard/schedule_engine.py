"""
dashboard/schedule_engine.py
────────────────────────────
Life OS Schedule Rule Engine v1.0

Validates any proposed ScheduleBlock against the full constraint set
before it is persisted to the database.

Usage:
    from dashboard.schedule_engine import ScheduleEngine, ValidationError

    engine = ScheduleEngine()
    result = engine.validate(block_data)   # dict or ScheduleBlock instance
    if not result.is_valid:
        print(result.errors)
    else:
        result.save()   # saves the block
"""

from __future__ import annotations

import dataclasses
from datetime import time, timedelta
from typing import Any


# ── Constraint constants ────────────────────────────────────────────────────

# Deep work window: 10:30–13:00 (midday block)
DEEP_WORK_START = time(10, 30)
DEEP_WORK_END   = time(13, 0)

# Afternoon block: 14:00–16:00
AFTERNOON_START = time(14, 0)
AFTERNOON_END   = time(16, 0)

# Evening physical (Muay Thai): 16:00–18:00
EVENING_START   = time(16, 0)
EVENING_END     = time(18, 0)

# Morning physical-only window: 08:00–10:00
MORNING_START   = time(8, 0)
MORNING_END     = time(10, 0)

# Muay Thai anchor days (weekday index: 0=Mon … 6=Sun)
MUAY_THAI_DAYS = {'TUE', 'THU', 'SAT'}

# Recovery day
RECOVERY_DAY = 'FRI'

# Duration rules (in minutes)
DURATION_RULES = {
    'deep_work_min':  120,
    'deep_work_max':  150,
    'dog_training_min': 60,
    'dog_training_max': 90,
    'muay_thai_min':  90,
    'muay_thai_max':  120,
    'business_max':   90,
    'tools_max':      90,
}

# AI domain categories that cannot coexist on the same day
AI_DOMAIN_CATEGORIES = {'Core', 'macOS', 'Business', 'Tools'}

# Priority ordering (lower number = higher priority)
PRIORITY_ORDER = {
    'Core':     1,
    'macOS':    2,
    'Physical': 3,
    'Business': 4,
    'Tools':    5,
    'Meta':     6,
    'Recovery': 7,
}


# ── Data structures ──────────────────────────────────────────────────────────

@dataclasses.dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str]
    warnings: list[str]
    block_data: dict[str, Any]

    def __bool__(self):
        return self.is_valid

    def save(self):
        """Persist the block to the database. Raises if invalid."""
        if not self.is_valid:
            raise ValidationError(self.errors)
        from dashboard.models import ScheduleBlock
        b = self.block_data
        return ScheduleBlock.objects.create(
            day_of_week=b['day_of_week'],
            activity=b['activity'],
            start_time=b['start_time'],
            end_time=b['end_time'],
            duration_min=b['duration_min'],
            category=b['category'],
            is_anchor=b.get('is_anchor', False),
            notes=b.get('notes', ''),
        )

    def report(self) -> str:
        lines = ['━━ SCHEDULE VALIDATION REPORT ━━']
        lines.append(f"Status : {'✅ VALID' if self.is_valid else '❌ INVALID'}")
        if self.errors:
            lines.append(f"Errors ({len(self.errors)}):")
            for e in self.errors:
                lines.append(f"  ✗ {e}")
        if self.warnings:
            lines.append(f"Warnings ({len(self.warnings)}):")
            for w in self.warnings:
                lines.append(f"  ⚠ {w}")
        return '\n'.join(lines)


class ValidationError(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__('; '.join(errors))


# ── Rule Engine ──────────────────────────────────────────────────────────────

class ScheduleEngine:
    """
    Deterministic constraint checker for Life OS schedule blocks.

    Rules enforced:
    1.  NO TIME OVERLAPS on the same day_of_week
    2.  ONE primary AI domain per day
    3.  NO CONTEXT SWITCHING between AI domains in one day
    4.  Muay Thai must be anchored to TUE / THU / SAT
    5.  Dog Training ≤ 90 min daily
    6.  Deep Work: 120–150 min, must start at 10:30 or later
    7.  Muay Thai: 90–120 min, 16:00–18:00 window
    8.  Business / Tools: ≤ 90 min
    9.  No Deep Work (AI domains) in the evening (after 16:00)
    10. Friday is recovery → no deep AI work (Core/macOS)
    """

    def validate(self, block_data: dict[str, Any]) -> ValidationResult:
        """
        Validate a proposed block against all constraints.

        block_data keys:
          day_of_week : str  ('MON' … 'SUN')
          activity    : str
          start_time  : time | str  ('HH:MM')
          end_time    : time | str  ('HH:MM')
          duration_min: int
          category    : str  ('Core'|'macOS'|'Business'|'Tools'|'Physical'|'Meta'|'Recovery')
          is_anchor   : bool  (optional)
          notes       : str   (optional)
        """
        errors: list[str] = []
        warnings: list[str] = []

        # ── Normalise ───────────────────────────────────────────────────────
        b = dict(block_data)
        b['start_time'] = self._to_time(b.get('start_time'))
        b['end_time']   = self._to_time(b.get('end_time'))

        if not b['start_time'] or not b['end_time']:
            errors.append('start_time and end_time are required.')
            return ValidationResult(False, errors, warnings, b)

        # Compute duration if not given
        if not b.get('duration_min'):
            b['duration_min'] = self._minutes_between(b['start_time'], b['end_time'])

        day    = b.get('day_of_week', '').upper()
        cat    = b.get('category', '')
        start  = b['start_time']
        end    = b['end_time']
        dur    = b['duration_min']
        act    = b.get('activity', '')

        if not day:
            errors.append('day_of_week is required.')
        if not cat:
            errors.append('category is required.')
        if not act:
            errors.append('activity name is required.')

        if errors:
            return ValidationResult(False, errors, warnings, b)

        # ── Fetch existing blocks for this day ───────────────────────────
        try:
            existing = self._existing_blocks(day)
        except Exception as exc:
            warnings.append(f'DB unavailable for overlap check: {exc}')
            existing = []

        # ── Rule 1: No time overlaps ─────────────────────────────────────
        for ex in existing:
            if self._overlaps(start, end, ex['start_time'], ex['end_time']):
                errors.append(
                    f'OVERLAP: {act} ({start.strftime("%H:%M")}–{end.strftime("%H:%M")}) '
                    f'conflicts with "{ex["activity"]}" '
                    f'({ex["start_time"].strftime("%H:%M")}–{ex["end_time"].strftime("%H:%M")})'
                )

        # ── Rule 2 & 3: One AI domain per day / no context switching ─────
        if cat in AI_DOMAIN_CATEGORIES:
            other_ai_cats = {
                ex['category'] for ex in existing
                if ex['category'] in AI_DOMAIN_CATEGORIES and ex['category'] != cat
            }
            if other_ai_cats:
                errors.append(
                    f'DOMAIN CONFLICT: Cannot add {cat} — day already has '
                    f'{", ".join(other_ai_cats)}. Only ONE AI domain per day.'
                )

        # ── Rule 4: Muay Thai anchor days ────────────────────────────────
        if 'muay thai' in act.lower() or (cat == 'Physical' and 'muay' in act.lower()):
            if day not in MUAY_THAI_DAYS:
                errors.append(
                    f'ANCHOR VIOLATION: Muay Thai must be on TUE/THU/SAT, got {day}.'
                )
            if not (EVENING_START <= start < EVENING_END):
                warnings.append(
                    f'Muay Thai should start between {EVENING_START.strftime("%H:%M")} '
                    f'and {EVENING_END.strftime("%H:%M")}.'
                )
            if not (DURATION_RULES['muay_thai_min'] <= dur <= DURATION_RULES['muay_thai_max']):
                errors.append(
                    f'DURATION: Muay Thai must be '
                    f'{DURATION_RULES["muay_thai_min"]}–{DURATION_RULES["muay_thai_max"]} min, got {dur}.'
                )

        # ── Rule 5: Dog Training ≤ 90 min ────────────────────────────────
        if 'dog' in act.lower():
            if dur > DURATION_RULES['dog_training_max']:
                errors.append(
                    f'DURATION: Dog Training must be ≤{DURATION_RULES["dog_training_max"]} min, got {dur}.'
                )
            if dur < DURATION_RULES['dog_training_min']:
                warnings.append(
                    f'Dog Training is very short ({dur} min); '
                    f'minimum recommended is {DURATION_RULES["dog_training_min"]} min.'
                )

        # ── Rule 6: Deep Work duration + timing ──────────────────────────
        if cat in ('Core', 'macOS'):
            if not (DURATION_RULES['deep_work_min'] <= dur <= DURATION_RULES['deep_work_max']):
                errors.append(
                    f'DURATION: Deep Work ({cat}) must be '
                    f'{DURATION_RULES["deep_work_min"]}–{DURATION_RULES["deep_work_max"]} min, got {dur}.'
                )
            if start < DEEP_WORK_START:
                errors.append(
                    f'TIMING: Deep Work must start at {DEEP_WORK_START.strftime("%H:%M")} or later, '
                    f'got {start.strftime("%H:%M")}.'
                )

        # ── Rule 8: Business / Tools ≤ 90 min ────────────────────────────
        if cat == 'Business' and dur > DURATION_RULES['business_max']:
            warnings.append(
                f'Business block is {dur} min; recommended max is {DURATION_RULES["business_max"]} min.'
            )
        if cat == 'Tools' and dur > DURATION_RULES['tools_max']:
            warnings.append(
                f'Tools block is {dur} min; recommended max is {DURATION_RULES["tools_max"]} min.'
            )

        # ── Rule 9: No AI deep work in evening ───────────────────────────
        if cat in AI_DOMAIN_CATEGORIES and start >= EVENING_START:
            errors.append(
                f'TIMING: AI Dev blocks must not be placed in the evening '
                f'(after {EVENING_START.strftime("%H:%M")}). Got {start.strftime("%H:%M")}.'
            )

        # ── Rule 10: Friday recovery bias ────────────────────────────────
        if day == RECOVERY_DAY and cat in ('Core', 'macOS'):
            errors.append(
                f'RECOVERY VIOLATION: Friday is a recovery day — no Core/macOS deep work allowed. '
                f'Use Tools or Business instead.'
            )

        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings, b)

    def validate_full_week(self, blocks: list[dict]) -> dict[str, ValidationResult]:
        """Validate an entire week of blocks, returning per-block results."""
        results = {}
        for i, block in enumerate(blocks):
            key = f"{block.get('day_of_week','?')}_{i}"
            results[key] = self.validate(block)
        return results

    def get_available_slots(self, day: str) -> list[dict]:
        """
        Return open time windows for a given day based on existing schedule blocks.
        Useful for suggesting where to place a new block.
        """
        existing = self._existing_blocks(day)
        existing.sort(key=lambda x: x['start_time'])

        windows = []
        cursor = time(8, 0)
        day_end = time(22, 0)

        for block in existing:
            if cursor < block['start_time']:
                gap_mins = self._minutes_between(cursor, block['start_time'])
                if gap_mins >= 30:  # Only meaningful gaps
                    windows.append({
                        'start': cursor,
                        'end': block['start_time'],
                        'duration_min': gap_mins,
                        'day': day,
                    })
            cursor = max(cursor, block['end_time'])

        if cursor < day_end:
            gap_mins = self._minutes_between(cursor, day_end)
            if gap_mins >= 30:
                windows.append({
                    'start': cursor,
                    'end': day_end,
                    'duration_min': gap_mins,
                    'day': day,
                })

        return windows

    # ── Internal helpers ────────────────────────────────────────────────────

    @staticmethod
    def _to_time(value) -> time | None:
        if value is None:
            return None
        if isinstance(value, time):
            return value
        if isinstance(value, str):
            parts = value.split(':')
            try:
                return time(int(parts[0]), int(parts[1]))
            except (IndexError, ValueError):
                return None
        return None

    @staticmethod
    def _minutes_between(start: time, end: time) -> int:
        dummy = __import__('datetime').date(2000, 1, 1)
        from datetime import datetime
        dt_start = datetime.combine(dummy, start)
        dt_end   = datetime.combine(dummy, end)
        diff = dt_end - dt_start
        return max(int(diff.total_seconds() / 60), 0)

    @staticmethod
    def _overlaps(s1: time, e1: time, s2: time, e2: time) -> bool:
        """True if interval [s1,e1) overlaps [s2,e2)."""
        return s1 < e2 and s2 < e1

    @staticmethod
    def _existing_blocks(day: str) -> list[dict]:
        """Fetch all active ScheduleBlocks for the given day_of_week."""
        from dashboard.models import ScheduleBlock
        qs = ScheduleBlock.objects.filter(day_of_week=day.upper(), is_active=True)
        return [
            {
                'activity':   b.activity,
                'start_time': b.start_time,
                'end_time':   b.end_time,
                'category':   b.category,
                'duration_min': b.duration_min,
            }
            for b in qs
        ]
