.PHONY: run migrate seed bot shell static superuser

run:
	python manage.py runserver

migrate:
	python manage.py makemigrations
	python manage.py migrate

seed:
	python manage.py seed_schedule

bot:
	python -c "from reminders.tasks import start_scheduler; start_scheduler()" &
	python -c "from reminders.bot import run_bot; run_bot()"

shell:
	python manage.py shell

static:
	python manage.py collectstatic --noinput

superuser:
	python manage.py createsuperuser

setup: migrate seed superuser static
	@echo "✅ LIFE OS is ready! Run: make run"
