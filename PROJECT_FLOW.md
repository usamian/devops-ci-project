# Atlas-AI CI/CD Pipeline - Simple Flow

## Visual Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  DEVELOPER PUSHES CODE TO GITHUB                           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  GITHUB WEBHOOK TRIGGERS JENKINS                           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  JENKINS STARTS PIPELINE (3 Stages)                        │
│                                                             │
│  Stage 1: Checkout                                         │
│  ┌──────────────────────────────────────┐                 │
│  │ Git clone from GitHub                 │                 │
│  └──────────────────────────────────────┘                 │
│                                                             │
│  Stage 2: SonarQube Analysis                               │
│  ┌──────────────────────────────────────┐                 │
│  │ Scan code for:                       │                 │
│  │ - Bugs                               │                 │
│  │ - Vulnerabilities                    │                 │
│  │ - Code smells                        │                 │
│  │ - Coverage                           │                 │
│  └──────────────────────────────────────┘                 │
│                                                             │
│  Stage 3: Docker Build                                     │
│  ┌──────────────────────────────────────┐                 │
│  │ Build Docker image                   │                 │
│  │ Push to registry (optional)          │                 │
│  └──────────────────────────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  PIPELINE COMPLETE - DEVELOPER GETS REPORT                 │
└─────────────────────────────────────────────────────────────┘
```

## Services Running

```
┌──────────────────────────────────────────────────────────────┐
│                    DOCKER HOST                               │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Jenkins    │  │  SonarQube   │  │ PostgreSQL   │      │
│  │              │  │              │  │              │      │
│  │ localhost:   │  │ localhost:   │  │ (internal)   │      │
│  │   8080       │  │   9000       │  │              │      │
│  │              │  │              │  │              │      │
│  │ admin/       │  │ admin/       │  │              │      │
│  │ admin123     │  │ admin        │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │             │
│         └──────────────────┴──────────────────┘             │
│                            │                                │
│                    Docker Network                          │
└──────────────────────────────────────────────────────────────┘
```

## File Structure

```
project/
├── docker-compose.yml          (defines services)
├── setup.sh                    (start script - MAIN FILE)
├── docker-install.sh           (install Docker)
├── Jenkinsfile                 (pipeline definition)
├── VIVA_PRACTICE_GUIDE.txt     (viva prep)
└── PROJECT_FLOW.md             (this file)
```

## How to Start

```bash
# Just run this:
./setup.sh

# Everything starts:
# ✅ Jenkins (http://localhost:8080)
# ✅ SonarQube (http://localhost:9000)
# ✅ PostgreSQL (auto-starts)
```

## How to Stop

```bash
docker compose down
```

## First Time Setup (Manual, 5-10 min)

1. Run `./setup.sh`
2. Open http://localhost:8080
3. Unlock Jenkins (check docker logs)
4. Create admin user: admin / admin123
5. Install plugins: Git, Pipeline, SonarQube
6. Create Pipeline job
7. Configure SonarQube token

## Daily Usage (After First Setup)

```bash
./setup.sh  # That's it!
```

=====================================================
