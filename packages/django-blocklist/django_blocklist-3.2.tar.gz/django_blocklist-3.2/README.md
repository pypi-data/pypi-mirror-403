# Django-blocklist

This is a [Django][] app that implements IP-based blocklisting. Its `BlocklistMiddleware` performs the blocking, and its `clean_blocklist` management command deletes entries which have satisfied the cooldown period. Entries also have a `reason` field, used in reporting. There are utility functions to add/remove IPs, an admin, and several management commands.

This app is primarily for situations where server-level blocking is not available, e.g. on platform-as-a-service hosts like PythonAnywhere or Heroku. Being an application-layer solution, it's not as performant as blocking via firewall or web server process, but is suitable for moderate traffic sites. It also offers better integration with the application stack, for easier management.

## Quick start

1. The [PyPI package name is `django-blocklist`](https://pypi.org/project/django-blocklist/); add that to your `requirements.txt` or otherwise install it into your project's Python environment.

1. Add "django_blocklist" to `settings.INSTALLED_APPS`
1. Add "django_blocklist.middleware.BlocklistMiddleware" to `settings.MIDDLEWARE`
1. Run `python manage.py migrate` to create the `django_blocklist_blockedip` table.
1. Add IPs to the list (via management commands, `utils.update_blocklist`, or the admin).
1. Set up a cron job or equivalent to run `manage.py clean_blocklist` daily.

## Management commands

Django-blocklist includes several management commands:

* `clean_blocklist` — remove entries that have fulfilled their cooldown period
* `import_blocklist` — convenience command for importing IPs from a file
* `print_blocklist` — print list of blocked IPs in plain text or JSON form
* `remove_from_blocklist` — remove one or more IPs
* `report_blocklist` — information on the current entries (see the [sample report][])
* `search_blocklist` — look for an IP in the list; in addition to info on stdout, returns an exit code of 0 if successful
* `update_blocklist` — add/update IPs; `--reason` and `--cooldown` optional; use `--skip-existing` to avoid updating existing records

The `--help` for each of these details its available options.

## Configuration

You can customize the following settings via a `BLOCKLIST_CONFIG` dict in your project settings:

* `cooldown` — Days to expire, for new entries; default 7
* `denial-template` — For the denial response; an f-string with `{ip}` and `{cooldown}` placeholders

## Utility methods

The `utils` module defines some convenience functions:

* `remove_from_blocklist(ip: str)` — removes an entry, returning `True` if successful
* `should_block(request: HttpRequest)` — Checks the request IP and method against the blocklist.
* `update_blocklist(ips: set, reason: str, cooldown: int, last_seen: datetime)` — adds IPs to the blocklist (all args except `ips` are optional)

## Development

* Project hub: [django-blocklist on Gitlab][gitlab project]
* Development is managed with [Poetry](https://python-poetry.org/)
* Quickstart: `python -m venv venv; source venv/bin/activate; poetry install`
* The project's [settings.py][] is minimal, just enough to run the tests and the admin
* Run tests: `tox` in project root to run the full test matrix, or use `pytest`
  to run specific tests under your installed Django
* Linting: `ruff check django_blocklist`
* `manage.py runserver` lets you try out the admin
* Merge requests and issues (tickets) are welcome!

[django]: https://www.djangoproject.com/
[gitlab project]: https://gitlab.com/paul_bissex/django-blocklist/
[sample report]: https://gitlab.com/paul_bissex/django-blocklist/-/blob/trunk/blocklist-report-sample.txt
[settings.py]: https://gitlab.com/paul_bissex/django-blocklist/-/blob/trunk/settings.py
