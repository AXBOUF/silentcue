# SilentCue

A real-time, session-based signaling app built with **Django** and **Django Channels** (WebSockets), paired with a **React** frontend. Two people join a shared room and relay a simple boolean signal (Yes/No) to each other instantly — no chat history, no accounts, no persistence beyond the room's lifetime.

This project was built to demonstrate practical, end-to-end web development: a Python/Django backend exposing both traditional HTTP endpoints and a WebSocket API, a modern React client, and a self-hosted production deployment (nginx + systemd + Cloudflare Tunnel).

## What it demonstrates

- **Django web framework** — models, views, URL routing, the admin site, and the ORM (`ChatRoom` model with expiring rooms via a scheduled cleanup command).
- **API design** — HTTP endpoints (`/create_room/`, `/join_room/`) that create and validate resources server-side before handing off to a real-time channel.
- **Real-time communication** — a full WebSocket API built on **Django Channels** (`ChatConsumer`), including connection lifecycle management (`connect`/`receive`/`disconnect`), group broadcast messaging, and role-based logic (room owner vs. guest).
- **Frontend integration** — a React (Vite) single-page app that talks to the Django backend over both HTTP and WebSockets.
- **Production deployment** — the app is actually deployed: Django runs behind **Daphne** (ASGI server) as a systemd service, **nginx** reverse-proxies HTTP/WebSocket traffic and serves the built frontend, and **Cloudflare Tunnel** exposes it publicly under a custom domain without opening router ports.

## Tech stack

| Layer | Technology |
|---|---|
| Backend framework | Django 5.2 |
| Real-time layer | Django Channels + Daphne (ASGI) |
| Database | SQLite (via Django ORM) |
| Frontend | React + Vite + Tailwind CSS |
| Reverse proxy | nginx |
| Deployment | systemd services + Cloudflare Tunnel |

## How it works

1. A user creates a room (`GET /create_room/`) — the backend generates a unique room code and becomes the room's "root" (owner).
2. A second user joins with that code (`POST /join_room/`).
3. Both clients open a WebSocket connection to `/ws/chat/<room_code>/`. The backend tracks both connections and, once both are present, enables the signaling controls on each client.
4. Pressing "Yes" or "No" sends a signal over the socket; the Django Channels consumer relays it to everyone else in the room's channel group in real time.
5. If the room owner disconnects, the backend broadcasts a dismantle event and the room is deleted — guests are notified and returned home automatically. Expired rooms are also cleaned up periodically via a Django management command.

## Project structure

```
backend/     Django project (app/, core/) — models, views, WebSocket consumers, URL routing
frontend/web/  React + Vite single-page app
deploy/      nginx, systemd, and Cloudflare Tunnel configs used for the live deployment
```

## Running it locally

```bash
# backend
cd backend
uv run manage.py migrate
uv run manage.py runserver

# frontend (separate terminal)
cd frontend/web
npm install
npm run dev
```
