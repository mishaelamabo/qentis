# Qentis: Universal Blockchain-Powered Authenticity Verification Platform

> SEN3244 Software Architecture | Spring 2026 | ICT University Cameroon

Qentis is a microservices-based web platform that enables verified organisations
to register items for authentication and allows anyone to verify those items
instantly using multiple verification methods. Every record is stored permanently
as a SHA-256 hash on the Ethereum blockchain which provide tamper-proof, immutable, and
independently verifiable without relying on any central authority.

---

## Team

| Name | Registration | Role |
|---|---|---|
| Mbetga Yomba Daniel Leo | ICTU20233822 | Scrum Master + Team Member |
| Neba Mishael Amabo | ICTU20241112 | Team Member |

---

## The Problem Qentis Solves

Fake diplomas, counterfeit medicines, fraudulent land titles, and counterfeit
banknotes cause direct harm in Cameroon and across Africa. Existing verification
systems are slow, manual, centralised, and vulnerable to corruption. Qentis
provides a single blockchain-powered platform that makes verification instant,
tamper-proof, and accessible to anyone with a smartphone.

---

## Authentication Categories

| Category | QR Code | Serial No. | Digital Signature | OCR Photo | Watermark |
|---|---|---|---|---|---|
| Academic Certificates | ✅ | ✅ | ✅ | ❌ | ✅ |
| Pharmaceutical Products | ✅ | ✅ | ❌ | ❌ | ❌ |
| Official Documents | ✅ | ✅ | ✅ | ❌ | ✅ |
| Currency / Banknotes | ✅ | ✅ | ❌ | ✅ | ✅ |

---

## Architecture

**Primary style:** Microservices Architecture
**Supporting patterns:** Event-Driven, API Gateway, Layered Architecture

| Service | Responsibility | Port |
|---|---|---|
| User and Auth | Registration, login, JWT, RBAC | 8001 |
| Institution Management | Issuer onboarding, admin approval | 8002 |
| Item Registration | Category forms, hash generation | 8003 |
| Blockchain Service | Ethereum smart contracts, web3.py | 8004 |
| Authentication Output | QR codes, serial numbers, signatures, watermarks | 8005 |
| Verification Service | All 5 verification methods, fraud detection | 8006 |
| Admin and Analytics | Platform management, fraud alerts, analytics | 8007 |

---

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | HTML / CSS / JavaScript |
| Backend | Python / Django (one project per service) |
| Database | PostgreSQL |
| Caching | Redis |
| Blockchain | Ethereum / Ganache + Web3.py |
| Smart Contracts | Solidity |
| Containerisation | Docker |
| Local Dev | Docker Compose |
| Orchestration | Kubernetes (k3s) |
| CI/CD | Jenkins + GitHub |
| Monitoring | Prometheus + Grafana |
| IaC | Ansible |
| Reverse Proxy | Nginx |
| API Docs | Swagger (drf-yasg) |
| OCR | OpenCV + Pytesseract |
| Watermark | LSB Steganography via Pillow |
| Crypto / Signing | Python cryptography library |

---

## Running Locally

### Prerequisites
- Docker Desktop installed and running
- Git

### Clone the repository
```bash
git clone https://github.com/DanielLeo09/qentis.git
cd qentis/backend
git checkout backend
```

### Start all services
```bash
docker-compose up
```

This starts all 7 services, PostgreSQL, Redis, and Ganache automatically.

### Apply migrations (first run only)
```bash
docker-compose run --rm user-auth python manage.py migrate
docker-compose run --rm institution python manage.py migrate
docker-compose run --rm item-registration python manage.py migrate
docker-compose run --rm blockchain python manage.py migrate
docker-compose run --rm auth-output python manage.py migrate
docker-compose run --rm verification python manage.py migrate
docker-compose run --rm admin-analytics python manage.py migrate
```

### Service URLs
| Service | URL |
|---|---|
| User and Auth | http://localhost:8001 |
| Institution | http://localhost:8002 |
| Item Registration | http://localhost:8003 |
| Blockchain | http://localhost:8004 |
| Auth Output | http://localhost:8005 |
| Verification | http://localhost:8006 |
| Admin and Analytics | http://localhost:8007 |

---

## Running Tests

### Unit tests per service
```bash
docker-compose run --rm blockchain python manage.py test blockchain_app
docker-compose run --rm auth-output python manage.py test output_app
docker-compose run --rm admin-analytics python manage.py test admin_app
```

### Coverage report per service
```bash
docker-compose run --rm blockchain coverage run --rcfile=.coveragerc manage.py test blockchain_app
docker-compose run --rm blockchain coverage report --rcfile=.coveragerc

docker-compose run --rm auth-output coverage run --rcfile=.coveragerc manage.py test output_app
docker-compose run --rm auth-output coverage report --rcfile=.coveragerc

docker-compose run --rm admin-analytics coverage run --rcfile=.coveragerc manage.py test admin_app
docker-compose run --rm admin-analytics coverage report --rcfile=.coveragerc
```

### Integration tests
```bash
# All services must be running first
docker-compose up

# In a separate terminal
python tests/test_integration.py
```

### Test results summary
| Service | Tests | Coverage |
|---|---|---|
| Blockchain Service | 19 passing | 82% |
| Auth Output Service | 25 passing | 91% |
| Admin and Analytics | 17 passing | 99% |

---

## API Documentation

All services expose interactive Swagger documentation at `/api/docs/`.

| Service | Swagger URL |
|---|---|
| User and Auth | http://localhost:8001/api/docs/ |
| Institution | http://localhost:8002/api/docs/ |
| Item Registration | http://localhost:8003/api/docs/ |
| Blockchain | http://localhost:8004/api/docs/ |
| Auth Output | http://localhost:8005/api/docs/ |
| Verification | http://localhost:8006/api/docs/ |
| Admin and Analytics | http://localhost:8007/api/docs/ |

---

## Repository Structure
frontened/
|
backend/
├── services/
│   ├── user-auth/          ← User & Auth Service (Daniel)
│   ├── institution/        ← Institution Management (Mishael)
│   ├── item-registration/  ← Item Registration (Mishael)
│   ├── blockchain/         ← Blockchain Service (Daniel)
│   ├── auth-output/        ← Auth Output Service (Daniel)
│   ├── verification/       ← Verification Service (Mishael)
│   └── admin-analytics/    ← Admin & Analytics (Daniel)
├── infrastructure/
│   ├── kubernetes/         ← K8s manifests
│   ├── ansible/            ← Ansible playbooks
│   └── nginx/              ← Nginx configuration
├── monitoring/             ← Prometheus + Grafana configs
├── jenkins/                ← Jenkinsfile
├── tests/
│   └── test_integration.py ← Integration tests
├── docs/
│   ├── PROGRESS.md         ← Development log
│   └── REPORT_NOTES.md     ← Report reference notes
└── docker-compose.yml      ← Local development orchestration

---

## Git Branching

| Branch | Purpose |
|---|---|
| `main` | Stable, reviewed code only |
| `backend` | All backend services |
| `frontend` | Frontend HTML/CSS/JS |

---

## Contribution Guidelines

1. Pull latest changes before starting work: `git pull origin backend`
2. Create or work on your assigned branch
3. Write tests for every new endpoint
4. Maintain minimum 80% coverage
5. Open a Pull Request for review before merging
6. Update `docs/PROGRESS.md` when a service is complete

---

*Qentis © 2026 · ICT University Cameroon · SEN3244 Software Architecture*# test auto deploy
