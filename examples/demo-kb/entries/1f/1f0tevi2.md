---
author: bob
created: '2026-02-10'
id: 1f0tevi2
status: reviewed
tags:
- docker
- devops
- containers
title: Getting Started with Docker Compose
type: guide
---

## Overview

Docker Compose lets you define and run multi-container applications with a
single YAML file. This guide walks through creating a basic web app with a
database backend.

## Prerequisites

- Docker Engine installed (`docker --version`)
- Docker Compose v2 (`docker compose version`)
- Basic familiarity with containers and YAML

## Steps

### Step 1: Create a `compose.yaml`

Define your services in a `compose.yaml` file at the project root:

```yaml
services:
  web:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - db
    environment:
      DATABASE_URL: postgres://user:pass@db:5432/myapp

  db:
    image: postgres:16
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: myapp

volumes:
  pgdata:
```

### Step 2: Write a Dockerfile for the web service

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

### Step 3: Start the stack

```bash
docker compose up -d
docker compose logs -f web
```

### Step 4: Stop and clean up

```bash
docker compose down          # stop containers
docker compose down -v       # also remove volumes
```

## Troubleshooting

- **Port already in use**: Change the host port mapping (e.g., `"9000:8000"`)
- **Database connection refused**: The `db` service may not be ready yet. Add a
  healthcheck or use a wait script.
- **Permission denied on volume**: Check that the container user has write
  access to the mounted volume path.
