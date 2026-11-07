# UniList

UniList is a web-based to do list app built with Django. Create lists, track items, and share lists with other people. Users sign in with a time-limited email link.

## Features

- Create lists and add, complete, or remove items.
- Sign in by email link; no password is required. Links expire after one hour.
- Keep lists private to the owner or share them with another email address.
- Browse public lists and manage lists you own or have been invited to.
- Use PostgreSQL in Docker Compose for local development and production.

## Tech stack

- Python 3.14 and Django 5.2
- PostgreSQL 18
- Gunicorn and Nginx for production
- Docker Compose for local and production deployments

## Run locally with Docker Compose

Requirements: Docker with the Compose plugin.

The development Compose configuration reads its environment from `.env.dev`. Create that file in the repository root with the following values (use a local-only password):

```dotenv
DJANGO_DEBUG=1
DB_HOSTNAME=db
POSTGRES_USER=uni
POSTGRES_PASSWORD=change-me
POSTGRES_DB=uni
```

Start the app and database:

```sh
docker compose up --build
```

In a second terminal, apply database migrations:

```sh
docker compose exec web python manage.py migrate
```

Open <http://localhost:8000>. The development server serves the app, and the database is available on port `5432`. Stop the services with `docker compose down`; the development database is kept in the `db_volume_dev` volume.

## Application routes

- `/` — home page and new-list form
- `/todo/lists/mine/` — lists you own and lists shared with you (sign-in required)
- `/todo/lists/<id>/` — view a list
- `/acc/send_login_email` — request a sign-in link (POST)
- `/acc/logout` — sign out
- `/admin/` — Django administration

## Tests

The Django apps have model, form, and view tests, and `src/functional_tests` contains browser-based functional tests. Run the Django test suite in the development container with:

```sh
docker compose exec web python manage.py test
```

Functional tests use Selenium and require a browser/driver setup; see `requirements/dev.txt` and `src/functional_tests`.

## Production deployment

The production Compose file adds Gunicorn and Nginx with HTTPS termination. It expects:

- A configured `.env.prod` file with Django's `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, and `DB_HOSTNAME` settings.
- `SSL_CERT` and `SSL_KEY` environment variables pointing to the TLS certificate and private key mounted by `docker-compose.prod.yml`.

Start the production stack with:

```sh
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
```

The production entrypoint waits for PostgreSQL, collects static files, and applies migrations before starting Gunicorn. Nginx listens on ports 80 and 443 and redirects HTTP to HTTPS. Keep production secrets and certificate paths out of version control.

## Project layout

```text
src/                 Django project and applications
  acc/               Email-link authentication
  todolist/          Lists, items, and sharing
  functional_tests/  Browser-based functional tests
requirements/        Base and development Python dependencies
nginx/               Nginx configuration
infra/               Ansible deployment and certificate playbooks
```

## License

See [LICENSE](LICENSE).
