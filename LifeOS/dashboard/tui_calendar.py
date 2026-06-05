"""
tui_calendar.py — LifeOS Terminal Calendar
==========================================
Colorful weekly calendar rendered with Python's built-in curses.
Zero extra dependencies required.

Controls:
  ←  /  h   — previous week
  →  /  l   — next week
  r          — refresh from DB
  q / Esc    — quit
"""

from __future__ import annotations

import curses
import os
import sys
import traceback
from datetime import date, timedelta, datetime, time as dtime
from typing import Optional


# ── ANSI / curses color pair IDs ──────────────────────────────────────────────
# Pairs are initialised in _init_colors()
PAIR_DEFAULT   = 0
PAIR_HEADER    = 1
PAIR_DAY_TITLE = 2
PAIR_AI_CORE   = 3
PAIR_AI_MACOS  = 4
PAIR_AI_BIZ    = 5
PAIR_AI_TOOLS  = 6
PAIR_MUAY_THAI = 7
PAIR_DOG       = 8
PAIR_GYM       = 9
PAIR_KITE      = 10
PAIR_SLEEP     = 11
PAIR_CUSTOM    = 12

PAIR_STATUS_PLANNED    = 13
PAIR_STATUS_INPROGRESS = 14
PAIR_STATUS_DONE       = 15
PAIR_STATUS_SKIPPED    = 16
PAIR_STATUS_RESCHEDULED= 17

PAIR_CONFLICT  = 18
PAIR_LOAD_LOW  = 19
PAIR_LOAD_MED  = 20
PAIR_LOAD_HIGH = 21
PAIR_BORDER    = 22
PAIR_DIM       = 23
PAIR_TODAY     = 24

# ── Category → pair mapping ───────────────────────────────────────────────────
CATEGORY_PAIRS = {
    'AI_DEV_CORE':     PAIR_AI_CORE,
    'AI_DEV_MACOS':    PAIR_AI_MACOS,
    'AI_DEV_BUSINESS': PAIR_AI_BIZ,
    'AI_DEV_TOOLS':    PAIR_AI_TOOLS,
    'MUAY_THAI':       PAIR_MUAY_THAI,
    'DOG_TRAINING':    PAIR_DOG,
    'GYM':             PAIR_GYM,
    'KITESURFING':     PAIR_KITE,
    'SLEEP':           PAIR_SLEEP,
    'CUSTOM':          PAIR_CUSTOM,
}

CATEGORY_ICONS = {
    'AI_DEV_CORE':     '🧠',
    'AI_DEV_MACOS':    '🍎',
    'AI_DEV_BUSINESS': '📈',
    'AI_DEV_TOOLS':    '🔧',
    'MUAY_THAI':       '🥊',
    'DOG_TRAINING':    '🐕',
    'GYM':             '🏋',
    'KITESURFING':     '🪁',
    'SLEEP':           '😴',
    'CUSTOM':          '⭐',
}

STATUS_PAIRS = {
    'PLANNED':     PAIR_STATUS_PLANNED,
    'IN_PROGRESS': PAIR_STATUS_INPROGRESS,
    'DONE':        PAIR_STATUS_DONE,
    'SKIPPED':     PAIR_STATUS_SKIPPED,
    'RESCHEDULED': PAIR_STATUS_RESCHEDULED,
}

STATUS_LABELS = {
    'PLANNED':     'PLAN',
    'IN_PROGRESS': 'NOW ',
    'DONE':        'DONE',
    'SKIPPED':     'SKIP',
    'RESCHEDULED': 'RSCH',
}

# Load score weights per category
LOAD_WEIGHTS = {
    'MUAY_THAI':       3,
    'KITESURFING':     3,
    'GYM':             2,
    'DOG_TRAINING':    1,
    'AI_DEV_CORE':     2,
    'AI_DEV_BUSINESS': 2,
    'AI_DEV_MACOS':    2,
    'AI_DEV_TOOLS':    1,
    'SLEEP':           0,
    'CUSTOM':          1,
}

DAYS = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
DAY_FULL = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


# ── Django bootstrap ──────────────────────────────────────────────────────────
def _bootstrap_django() -> bool:
    """Configure Django settings if not already done. Returns True on success."""
    if os.environ.get('DJANGO_SETTINGS_MODULE'):
        try:
            import django
            django.setup()
            return True
        except Exception:
            return False

    # Try to locate manage.py and set settings from there
    candidate = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    manage_py = os.path.join(candidate, 'manage.py')
    if os.path.isfile(manage_py):
        if candidate not in sys.path:
            sys.path.insert(0, candidate)

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lifeos.settings')
    try:
        import django
        django.setup()
        return True
    except Exception:
        return False


def _fetch_activities(week_start: date) -> list[dict]:
    """Query Activity objects for the given week. Returns list of plain dicts."""
    week_end = week_start + timedelta(days=6)
    try:
        from dashboard.models import Activity
        qs = (
            Activity.objects
            .filter(scheduled_date__gte=week_start, scheduled_date__lte=week_end)
            .order_by('scheduled_date', 'start_time')
        )
        results = []
        for a in qs:
            results.append({
                'name': a.name,
                'category': a.category,
                'date': a.scheduled_date,
                'start_time': a.start_time,
                'end_time': a.end_time,
                'duration_minutes': a.duration_minutes,
                'status': a.status,
                'notes': a.notes or '',
            })
        return results
    except Exception as exc:
        # Return error sentinel
        return [{'_error': str(exc)}]


# ── Helper: conflict detection ────────────────────────────────────────────────
def _detect_conflicts(activities: list[dict]) -> set[int]:
    """Return indices of activities that overlap with any other on the same day."""
    conflicted: set[int] = set()
    n = len(activities)
    for i in range(n):
        a = activities[i]
        if not a.get('start_time') or not a.get('end_time'):
            continue
        for j in range(i + 1, n):
            b = activities[j]
            if a['date'] != b['date']:
                continue
            if not b.get('start_time') or not b.get('end_time'):
                continue
            # Overlap condition
            if a['start_time'] < b['end_time'] and a['end_time'] > b['start_time']:
                conflicted.add(i)
                conflicted.add(j)
    return conflicted


# ── Helper: load score ────────────────────────────────────────────────────────
def _day_load(activities: list[dict]) -> tuple[int, str, int]:
    """Return (score, label, pair) for the day's activities."""
    score = sum(LOAD_WEIGHTS.get(a.get('category', ''), 0) for a in activities)
    if score <= 3:
        return score, 'LOW', PAIR_LOAD_LOW
    elif score <= 6:
        return score, 'MED', PAIR_LOAD_MED
    else:
        return score, 'HIGH', PAIR_LOAD_HIGH


# ── curses colour init ────────────────────────────────────────────────────────
def _init_colors() -> None:
    curses.start_color()
    curses.use_default_colors()

    bg = -1  # transparent background

    def p(n, fg, bg=bg):
        curses.init_pair(n, fg, bg)

    p(PAIR_HEADER,    curses.COLOR_WHITE,   curses.COLOR_BLUE)
    p(PAIR_DAY_TITLE, curses.COLOR_BLACK,   curses.COLOR_CYAN)
    p(PAIR_TODAY,     curses.COLOR_BLACK,   curses.COLOR_YELLOW)

    # Categories
    p(PAIR_AI_CORE,   curses.COLOR_MAGENTA, bg)
    p(PAIR_AI_MACOS,  curses.COLOR_BLUE,    bg)
    p(PAIR_AI_BIZ,    curses.COLOR_YELLOW,  bg)
    p(PAIR_AI_TOOLS,  curses.COLOR_CYAN,    bg)
    p(PAIR_MUAY_THAI, curses.COLOR_RED,     bg)
    p(PAIR_DOG,       curses.COLOR_GREEN,   bg)
    p(PAIR_GYM,       curses.COLOR_YELLOW,  bg)
    p(PAIR_KITE,      curses.COLOR_CYAN,    bg)
    p(PAIR_SLEEP,     curses.COLOR_WHITE,   bg)
    p(PAIR_CUSTOM,    curses.COLOR_MAGENTA, bg)

    # Statuses
    p(PAIR_STATUS_PLANNED,     curses.COLOR_BLUE,    bg)
    p(PAIR_STATUS_INPROGRESS,  curses.COLOR_YELLOW,  bg)
    p(PAIR_STATUS_DONE,        curses.COLOR_GREEN,   bg)
    p(PAIR_STATUS_SKIPPED,     curses.COLOR_RED,     bg)
    p(PAIR_STATUS_RESCHEDULED, curses.COLOR_MAGENTA, bg)

    # Misc
    p(PAIR_CONFLICT, curses.COLOR_RED,   bg)
    p(PAIR_LOAD_LOW, curses.COLOR_GREEN, bg)
    p(PAIR_LOAD_MED, curses.COLOR_YELLOW,bg)
    p(PAIR_LOAD_HIGH,curses.COLOR_RED,   bg)
    p(PAIR_BORDER,   curses.COLOR_CYAN,  bg)
    p(PAIR_DIM,      curses.COLOR_WHITE, bg)


# ── Safe addstr helper ────────────────────────────────────────────────────────
def _safe_add(win, y: int, x: int, text: str, attr: int = 0) -> None:
    h, w = win.getmaxyx()
    if y < 0 or y >= h or x < 0 or x >= w:
        return
    available = w - x - 1
    if available <= 0:
        return
    try:
        win.addstr(y, x, text[:available], attr)
    except curses.error:
        pass


def _safe_hline(win, y: int, x: int, ch: int, n: int, attr: int = 0) -> None:
    h, w = win.getmaxyx()
    if y < 0 or y >= h or x < 0 or x >= w:
        return
    n = min(n, w - x - 1)
    if n <= 0:
        return
    try:
        win.hline(y, x, ch, n, attr)
    except curses.error:
        pass


# ── Main TUI class ────────────────────────────────────────────────────────────
class TUICalendar:
    def __init__(self, stdscr, django_ok: bool):
        self.stdscr = stdscr
        self.django_ok = django_ok

        # Week anchor: Monday of current week
        today = date.today()
        self.week_start = today - timedelta(days=today.weekday())

        self.activities: list[dict] = []
        self.error_msg: Optional[str] = None
        self.status_msg: str = ''

        _init_colors()
        curses.curs_set(0)
        self.stdscr.keypad(True)
        self.stdscr.timeout(200)

        self._load_data()

    # ── Data loading ──────────────────────────────────────────────────────────
    def _load_data(self) -> None:
        self.status_msg = 'Loading…'
        if not self.django_ok:
            self.error_msg = 'Django not configured — showing empty calendar'
            self.activities = []
            self.status_msg = ''
            return
        raw = _fetch_activities(self.week_start)
        if raw and '_error' in raw[0]:
            self.error_msg = raw[0]['_error']
            self.activities = []
        else:
            self.error_msg = None
            self.activities = raw
        self.status_msg = f'Loaded {len(self.activities)} activities'

    # ── Derived helpers ───────────────────────────────────────────────────────
    def _activities_for_day(self, d: date) -> list[dict]:
        return [a for a in self.activities if a.get('date') == d]

    def _week_dates(self) -> list[date]:
        return [self.week_start + timedelta(days=i) for i in range(7)]

    # ── Drawing ───────────────────────────────────────────────────────────────
    def draw(self) -> None:
        self.stdscr.erase()
        h, w = self.stdscr.getmaxyx()

        row = 0
        row = self._draw_header(row, w)
        row = self._draw_nav_hint(row, w)

        if h - row < 10:
            _safe_add(self.stdscr, row, 2, 'Terminal too small — resize to at least 40 rows.',
                      curses.color_pair(PAIR_CONFLICT) | curses.A_BOLD)
            self.stdscr.refresh()
            return

        row = self._draw_calendar(row, w, h)
        self._draw_footer(h - 1, w)
        self.stdscr.refresh()

    def _draw_header(self, row: int, w: int) -> int:
        week_end = self.week_start + timedelta(days=6)
        label = (
            f'  LifeOS TUI Calendar  '
            f'│  {self.week_start.strftime("%d %b")} – {week_end.strftime("%d %b %Y")}  '
        )
        _safe_add(self.stdscr, row, 0, label.ljust(w), curses.color_pair(PAIR_HEADER) | curses.A_BOLD)
        return row + 1

    def _draw_nav_hint(self, row: int, w: int) -> int:
        hint = '  ◀ ← prev  │  → next ▶  │  r refresh  │  q quit'
        _safe_add(self.stdscr, row, 0, hint.ljust(w), curses.color_pair(PAIR_DIM))
        if self.error_msg:
            msg = f'  ⚠  {self.error_msg}'
            _safe_add(self.stdscr, row + 1, 0, msg[:w], curses.color_pair(PAIR_CONFLICT) | curses.A_BOLD)
            return row + 2
        return row + 1

    def _draw_calendar(self, start_row: int, w: int, h: int) -> int:
        dates = self._week_dates()
        today = date.today()
        conflicts = _detect_conflicts(self.activities)

        row = start_row
        for idx, d in enumerate(dates):
            if row >= h - 2:
                break
            day_acts = self._activities_for_day(d)
            load_score, load_label, load_pair = _day_load(day_acts)
            is_today = (d == today)

            # ── Day header bar ────────────────────────────────────────────────
            day_label = f'  {DAY_FULL[idx]:9s}  {d.strftime("%d/%m")}  '
            load_str = f' [{load_label} {load_score}]'
            act_count = f'  {len(day_acts)} activit{"y" if len(day_acts) == 1 else "ies"} '
            header_line = day_label + act_count + load_str

            header_attr = (
                curses.color_pair(PAIR_TODAY) | curses.A_BOLD
                if is_today else
                curses.color_pair(PAIR_DAY_TITLE) | curses.A_BOLD
            )
            _safe_add(self.stdscr, row, 0, header_line.ljust(w), header_attr)
            # Overlay load score at end of line
            load_disp = load_str.strip()
            lx = max(0, w - len(load_disp) - 3)
            _safe_add(self.stdscr, row, lx, f' {load_disp} ',
                      curses.color_pair(load_pair) | curses.A_BOLD)
            row += 1

            if not day_acts:
                _safe_add(self.stdscr, row, 4, '— no activities —', curses.color_pair(PAIR_DIM))
                row += 1
            else:
                act_indices_on_day = [
                    i for i, a in enumerate(self.activities) if a.get('date') == d
                ]
                for local_i, global_i in enumerate(act_indices_on_day):
                    if row >= h - 2:
                        break
                    a = self.activities[global_i]
                    row = self._draw_activity(row, w, a, global_i in conflicts)

            # Thin separator between days
            _safe_hline(self.stdscr, row, 0, curses.ACS_HLINE, w,
                        curses.color_pair(PAIR_BORDER))
            row += 1

        return row

    def _draw_activity(self, row: int, w: int, a: dict, is_conflict: bool) -> int:
        h, _ = self.stdscr.getmaxyx()
        if row >= h - 2:
            return row

        cat   = a.get('category', 'CUSTOM')
        status = a.get('status', 'PLANNED')
        cat_pair    = curses.color_pair(CATEGORY_PAIRS.get(cat, PAIR_CUSTOM))
        status_pair = curses.color_pair(STATUS_PAIRS.get(status, PAIR_STATUS_PLANNED))

        icon = CATEGORY_ICONS.get(cat, '●')

        # Time range
        def fmt_t(t) -> str:
            if t is None:
                return '-- :--'
            if isinstance(t, dtime):
                return t.strftime('%H:%M')
            return str(t)

        t_start = fmt_t(a.get('start_time'))
        t_end   = fmt_t(a.get('end_time'))
        dur = a.get('duration_minutes')
        dur_str = f'{dur}m' if dur else '  ?  '

        status_lbl = STATUS_LABELS.get(status, status[:4])
        name = a.get('name', 'Unknown')

        # Build line
        conflict_flag = '⚡' if is_conflict else '  '
        line_prefix = f'    {conflict_flag} {t_start}–{t_end} ({dur_str:>5})  '
        line_name   = f'{icon} {name}'
        line_status = f'  [{status_lbl}]'

        # Draw prefix (time/duration)
        _safe_add(self.stdscr, row, 0, line_prefix, curses.color_pair(PAIR_DIM))
        px = len(line_prefix)

        # Draw category-coloured name
        _safe_add(self.stdscr, row, px, line_name, cat_pair | curses.A_BOLD)
        px += len(line_name)

        # Draw status
        _safe_add(self.stdscr, row, px, line_status, status_pair)
        px += len(line_status)

        # If conflict, append warning
        if is_conflict:
            warn = '  ⚠ CONFLICT'
            _safe_add(self.stdscr, row, px, warn,
                      curses.color_pair(PAIR_CONFLICT) | curses.A_BOLD)

        row += 1
        return row

    def _draw_footer(self, row: int, w: int) -> None:
        msg = f'  {self.status_msg}'
        _safe_add(self.stdscr, row, 0, msg.ljust(w), curses.color_pair(PAIR_HEADER))

    # ── Event loop ────────────────────────────────────────────────────────────
    def run(self) -> None:
        while True:
            self.draw()
            try:
                key = self.stdscr.getch()
            except KeyboardInterrupt:
                break

            if key in (ord('q'), ord('Q'), 27):  # q / Esc
                break
            elif key in (curses.KEY_LEFT, ord('h'), ord('H')):
                self.week_start -= timedelta(weeks=1)
                self._load_data()
            elif key in (curses.KEY_RIGHT, ord('l'), ord('L')):
                self.week_start += timedelta(weeks=1)
                self._load_data()
            elif key in (ord('r'), ord('R')):
                self._load_data()


# ── Public entry point ────────────────────────────────────────────────────────
def launch() -> None:
    """Bootstrap Django then launch the TUI inside curses wrapper."""
    django_ok = _bootstrap_django()

    def _main(stdscr):
        tui = TUICalendar(stdscr, django_ok)
        tui.run()

    try:
        curses.wrapper(_main)
    except Exception:
        sys.stdout.write('\033[0m')  # reset terminal colours
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    launch()
