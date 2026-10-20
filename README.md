# Kavita Chemist - Django pharmacy inventory

Public website (home, about, features, contact) + a login-protected dashboard to manage
medicines, categories and stock, with low-stock / expiry alerts and charts.

## Run locally
```bash
python -m venv venv
venv\Scripts\activate          # Windows   (Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo      # optional sample medicines
python manage.py runserver
```
Open http://127.0.0.1:8000/

## Deploy on Render
- Build command:  `./build.sh`
- Start command:  `gunicorn kavita_chemist.wsgi:application`
- Environment:    `SECRET_KEY` (any long random string)
- Optional env:   `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL`, `DJANGO_SUPERUSER_PASSWORD`, `SEED_DEMO=1`
- SQLite is wiped on each deploy. For permanent data add a Render Postgres, set `DATABASE_URL`
  and uncomment the two lines at the bottom of requirements.txt.

## Edit shop details
Address, phone, email and hours live in `main/context.py`.

## Layout
- `kavita_chemist/` settings, urls, wsgi/asgi
- `main/` models, views, forms, admin, `seed_demo` command
- `templates/` base.html, dashboard_base.html, main/*.html
- `static/css/style.css` (your original stylesheet) + `extras.css`, `static/js/app.js`
