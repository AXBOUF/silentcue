# SilentCue

SilentCue is a real-time web application for sending simple silent prompts between two devices. One device acts as the controller and sends cues such as **NEXT / BACK**, while the second device acts as the receiver and displays the latest cue in a clear, high-visibility interface.

This project is designed for situations where spoken instructions are distracting or impossible, such as presentations, filming, live production, or any environment that needs low-friction non-verbal coordination.

## What the project does

- Creates a private room with a unique 8-character code
- Lets a second device join instantly with that room code
- Opens a live WebSocket connection between both devices
- Sends cues from the controller to the receiver in real time
- Supports preset modes like presentation, film shooting, and yes/no signals
- Allows custom two-command setups for flexible workflows
- Automatically expires stale rooms and closes sessions when the controller leaves

## What was built to achieve that

### Frontend

- Built a React single-page interface focused on speed, readability, and large touch targets
- Added separate controller and receiver experiences so each device sees only the actions it needs
- Implemented room creation, room joining, room-code copy, connection state, and session-expiry warnings
- Added multiple cue modes, including editable custom commands
- Styled the app for strong visibility and fast use on phones and laptops

### Backend

- Built a Django backend to create rooms, validate join requests, and serve the real-time session flow
- Used Django Channels to handle persistent WebSocket connections
- Added role-based behavior so only the controller can send cues
- Protected controller access with a generated controller token
- Added room cleanup rules for expired sessions, disconnected controllers, and stale rooms
- Included heartbeat and session monitoring logic to keep sessions reliable

## Architecture

- **React + Vite** powers the client application in `frontend/web`
- **Django** handles room lifecycle and HTTP endpoints in `backend`
- **Django Channels + Daphne** handle real-time messaging over WebSockets
- **SQLite/Django ORM** stores active room records and metadata

## Key implementation highlights

- Room creation and join flow backed by Django endpoints
- Real-time cue delivery through a shared WebSocket room group
- Controller/receiver role separation for safer signaling
- Automatic room teardown when the controlling device exits
- Session retention rules to remove inactive or expired rooms
- Development proxy in Vite so the React app talks to Django locally without CORS setup

## Why this project matters

SilentCue shows practical full-stack engineering work across:

- real-time communication
- frontend interaction design
- backend session management
- WebSocket lifecycle handling
- lightweight security controls
- product thinking around a focused user workflow

For recruiters, this project demonstrates the ability to turn a simple product idea into a working system with a clear user flow, live synchronization, and thoughtful operational safeguards.

## Tech stack

- React 19
- Vite
- Tailwind CSS
- Django 5
- Django Channels
- Daphne
- Python 3.11+

## Repository structure

```text
backend/        Django app, models, views, WebSocket consumers
frontend/web/   React interface and Vite development setup
docs/           Project notes and design references
```

## Running locally

From the repository root:

### Backend

```bash
uv sync
cd backend
uv run manage.py migrate
uv run manage.py runserver 127.0.0.1:8000
```

### Frontend

```bash
cd frontend/web
npm install
npm run dev
```

Then open `http://localhost:5173`.

## Current status

The repository contains both:

- a modern React frontend for the main user experience
- a Django template-based prototype that documents the earlier room flow

The current product direction is centered on the React client backed by Django and WebSockets.