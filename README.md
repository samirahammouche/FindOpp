# FindOpp

FindOpp is a web platform that helps students discover events and opportunities published by organizers.
Visitors can search and browse approved events without an account, organizers publish and manage their
own events, and administrators validate accounts and moderate content.

The project is built with a **microservices architecture**: independent Django REST services, a React
frontend, and an infrastructure layer (Traefik, Consul, RabbitMQ).

> University project: UMBB, Faculty of Sciences, ING4 GL, WAMS 2026.
> Supervisor: Mr. Yahiaten

## Table of contents

1. [Actors and features](#actors-and-features)
2. [Architecture](#architecture)
3. [Project structure](#project-structure)
4. [Getting started](#getting-started)
5. [Configuration](#configuration)
6. [Git workflow](#git-workflow)
7. [Documentation](#documentation)
8. [Team](#team)

## Actors and features

| Actor | Description | Main features |
|---|---|---|
| Visitor (student) | Browses the platform, no account needed | Search by keywords, get suggestions, view event details |
| Organizer | Registered user, must be validated by an admin | Log in and out, reset password, manage profile, create, edit and delete events |
| Administrator | Internal user who supervises the platform | Validate or reject organizer accounts, moderate events, suspend accounts, read the activity log |

### Event lifecycle

```
BROUILLON  ->  EN_ATTENTE  ->  APPROUVEE
                           ->  REJETEE
```

Only events with the status `APPROUVEE` are visible to visitors.

## Architecture

### Services

| Service | Folder | Port | Responsibility |
|---|---|---|---|
| Auth | `backend/auth-service` | 8001 | Registration, JWT login, password reset, roles and permissions, refuses login for unvalidated organizers |
| Admin | `backend/admin-service` | 8002 | Validate or reject organizers and events, suspend accounts, activity log |
| Event | `backend/event-service` | 8003 | Events, categories, statuses, public search (keywords, filters, sorting, pagination) |
| Organizer | `backend/organizer-service` | 8004 | Organizer profile (name, description, logo, contacts) and their publications |
| Frontend | `frontend` | 3000 | React website consuming the APIs |

Each service is an independent Django project with its **own database** and its own `requirements.txt`.
Services never share a database: they communicate through REST calls or RabbitMQ messages, and refer to
each other's data by id only (for example, an event stores `organizerId`).

### Infrastructure

| Component | Folder | Role |
|---|---|---|
| Traefik | `infra/traefik` | Reverse proxy and load balancer in front of all services |
| Consul | `infra/consul` | Service registry and discovery |
| RabbitMQ | `infra/rabbitmq` | Asynchronous messaging between services |

### Routes (through Traefik)

| Route | Target |
|---|---|
| `/api/auth` | auth-service |
| `/api/organizers` | organizer-service |
| `/api/events` | event-service |
| `/api/admin` | admin-service |
| `/` | frontend |

### Main flows

1. The user logs in from the frontend and receives a JWT from the auth service.
2. The frontend sends the token with each API request, and services validate it.
3. When an organizer submits an event, a message is published to RabbitMQ and the admin service
   consumes it to create a pending validation and an activity log entry.
4. Services register themselves in Consul, and Traefik routes requests to them.

## Project structure

```
FindOpp/
├── backend/
│   ├── auth-service/
│   ├── admin-service/
│   ├── event-service/
│   └── organizer-service/
├── frontend/
├── infra/
│   ├── traefik/
│   ├── consul/
│   └── rabbitmq/
├── deploy/            # one docker-compose file per server
├── docs/              # UML design document, project spec, technical report
├── .gitignore
└── README.md
```

## Getting started

### Prerequisites

- Python 3.10 or newer
- Node.js 18 or newer
- Git
- Docker (for deployment)

### 1. Clone the repository

```bash
git clone https://github.com/samirahammouche/FindOpp.git
cd FindOpp
```

### 2. Run a backend service

Example with the auth service (use the port from the table above for the others):

```bash
cd backend/auth-service
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac / Linux
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8001
```

### 3. Run the frontend

```bash
cd frontend
npm install
npm start
```

The website is then available at http://localhost:3000.


## Git workflow

1. Run `git pull` before starting to work.
2. Create a branch for each feature: `git checkout -b feature/short-name`.
3. Commit small and often, with clear messages.
4. Push your branch and open a pull request into `main`.
5. Another team member reviews and merges the pull request.
6. Never commit `.env` files, databases, `venv/` or `node_modules/`.

Each member works inside the folder of their own service to avoid merge conflicts.

## Documentation

The `docs/` folder contains:

- cahier de charge fonctionnel
- cahier de charge technique
- conception UML

## Team


| Hammouche Samira 
| Kouachi Kenza Sirine 
| Gougache Mellissa 
| Toudji Yousra 
| Dziri Nafila 

Supervisor: Mr. Yahiaten