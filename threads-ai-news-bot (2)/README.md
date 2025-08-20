# Threads AI News Bot

Автопостинг выжимки новостей про ИИ в Threads (ежедневно в 09:00 МСК).

## Проверка (Preflight + DRY_RUN)
- **preflight.py**: создаёт контейнер (без публикации) — проверка токена/прав.
- **DRY_RUN=true**: workflow прогоняет генерацию и печатает тред в логи, не публикуя в Threads.

## Живой тест
Смените `DRY_RUN=false` и запустите вручную (Actions → Run workflow).

Secrets: `THREADS_USER_ID`, `THREADS_ACCESS_TOKEN`.
