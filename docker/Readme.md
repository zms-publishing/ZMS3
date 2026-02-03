# Docker (Zope/ZEO) — local development

This project ships a Docker Compose setup to run **Zope** with a **ZEO** backend, plus an optional **debug** profile with code-server and debugger ports.

## Prerequisites

- Docker + Docker Compose (with support for `develop.watch`)
- Free host ports:
  - `80` (default Zope)
  - Debug profile: `8080`, `5678`, `8085`, `8086`

## Services (docker-compose.yml)

- `zeo`: ZEO server (internal port `8090`, not published to host)
- `zope`: main Zope instance (publishes `80:80`)
- `zope-debug` (profile `debug`): code-server + debug ports, depends on `zeo`

## Quickstart

From the repository root:

- Build and run:
  - `docker compose up --build`
- Open Zope:
  - http://localhost/

Stop / remove containers:

- `docker compose down`

## Debug profile (optional)

Starts a container intended for debugging, including VSCode code-server and debugpy port forwarding.

- Run debug profile:
  - `docker compose --profile debug up --build`

Endpoints / ports:

- code-server: http://localhost:8080
- debugpy: `localhost:5678`
- Zope ports exposed by the debug service: `8085`, `8086`

## Volumes and persistence

Bind mounts used by the containers:

- `docker/zope/etc/` → `/home/zope/etc/`
  - Zope/ZEO config files (e.g. `zope.conf`, `zeo.conf`, `zope_debug.conf`)
- `docker/zope/var/` → `/home/zope/var/`
  - persistent data (e.g. `Data.fs`), logs, caches
- `docker/zope/Extensions/` → `/home/zope/Extensions/`
  - shared Zope External Methods folder

Source/test mounts:

- `./tests` → `/home/zope/tests`
- `./test_output` → `/home/zope/test_output`
- `./selenium_tests` → `/home/zope/selenium_tests`

## Configuration notes

- `docker/zope/etc/zope.conf` is configured as a **ZEO client** and connects to `zeo:8090` for both `main` and `temporary` storages.
- `docker/zope/etc/zeo.conf` defines the ZEO server and file storages in `/home/zope/var/`.
- `docker/zope/etc/zope_debug.conf` is a standalone (filestorage) debug config and defaults to HTTP port `8085`.

## Live development workflow

Compose `develop.watch` is configured to:

- `sync+restart` on changes in `./Products` → `/home/zope/Products`
- trigger `rebuild` on changes to `docker/base/Dockerfile*`, `requirements*.txt`, `setup.py`, `setup.cfg`

## Useful commands

- Follow logs:
  - `docker compose logs -f zope`
  - `docker compose logs -f zeo`

## Troubleshooting (short)

- If host port `80` is already in use, change the `ports:` mapping in `docker-compose.yml`.
- To reset the database, remove the contents of `docker/zope/var/` (this deletes `Data.fs`).
