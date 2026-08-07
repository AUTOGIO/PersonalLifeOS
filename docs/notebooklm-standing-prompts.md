# STANDING PROMPTS — Cursor / Analyst rules

Operating rules for every answer in this notebook:

1. Answer only from uploaded sources. Cite sources. If a figure is missing, write `n/v` — never invent metrics.
2. Prefer repo canonical docs (`AGENTS.md`, `README.md`, architecture brief) over chat memory when they conflict.
3. Match depth to the question. Short question → short answer.
4. Do not invent secrets, credentials, or production URLs not present in sources.
5. When advising code changes, respect PersonalLifeOS layout rules in `AGENTS.md`: app code lives in `LifeOS/`; do not invent empty top-level folders; do not revive the retired Django/Telegram stack from `archive/`.

## Smoke test

Ask: *Which standing rules bind a short question about folder layout?* — the answer should cite this source.
