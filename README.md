# Library Management System — Cloud-Native Deployment on Amazon EKS

A small Flask web application for managing a library, deployed end-to-end with
Docker, Amazon ECR, Amazon EKS, GitHub Actions (OIDC) and Argo CD (GitOps).

## Features

1. **Add books**: title and author
2. **Search** books by title or author
3. **Issue and return** books, with a 7-day due date
4. **Overdue list**: books past their due date
5. **Delete** books
6. **Health endpoint** at `/health`, used by Kubernetes probes, which reports the app version

## Tech stack

| Layer | Tool |
|---|---|
| App | Python 3.12, Flask, SQLite |
| Tests | pytest |
| Container | Docker, gunicorn |
| Registry | Amazon ECR |
| Orchestration | Amazon EKS (Kubernetes) |
| CI | GitHub Actions with AWS OIDC |
| CD (GitOps) | Argo CD |

## Project structure

```
library-management-eks/
├── app.py               # Flask application
├── templates/           # HTML pages
├── tests/test_app.py    # pytest tests
├── requirements.txt
├── Dockerfile
└── README.md
```

## Run locally

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://localhost:5000

## Run tests

```bash
pytest -v
```

## Run with Docker

```bash
docker build -t library-app .
docker run -p 5000:5000 library-app
```

Open http://localhost:5000

## Deployment workflow

```
Developer → GitHub → GitHub Actions → Docker Image → Amazon ECR
          → Git Deployment Config (k8s/) → Argo CD → Amazon EKS → Running App
```

> Note: data is stored in SQLite inside the container, so it resets whenever a pod restarts.
> This is fine for the demo. A production setup would use Amazon RDS.
