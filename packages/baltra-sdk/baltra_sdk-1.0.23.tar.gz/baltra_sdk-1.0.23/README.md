# Baltra SDK - Centralized and Decoupled Architecture

Internal SDK package for sharing Baltra domain models, infrastructure adapters, and common utilities across microservices.

## Changelog

### Version 1.0.8 (Current)

#### Database Models
- **HiringObjectives**: Added `role_id` foreign key field referencing `roles.role_id` with CASCADE delete
- **HiringObjectives**: Added `objective_amount` integer field (required, non-nullable)

These changes enable hiring objectives to be linked to specific roles and track target hiring amounts per role.

### Version 1.0.7
- Initial stable release of the SDK

### Version 1.0.6
- Foundation models and database adapters

### Version 1.0.5
- Core screening models and utilities

### Version 1.0.4
- Initial database models migration

### Version 1.0.3
- Basic SDK structure and packaging

### Version 1.0.2
- Initial repository setup

### Version 1.0.1
- Project initialization

---

## Overview

This SDK consolidates business logic, domain contracts, and common integrations (databases, Meta, Step Functions, external providers) into a single reusable package, avoiding duplication across microservices and reducing maintenance time when models or schemas change.

## Scope

- Python library (`baltra-sdk`) distributed via private PyPI or Git repository
- Exports services, models, repositories, and external clients used by Baltra microservices
- Includes shared utilities (logging, configuration, validations, unit of work)
- Defines explicit contracts between domain and infrastructure layers to preserve backward compatibility

## Design Principles

- **Domain independent of infrastructure**: services consume ports (interfaces) without knowing concrete implementations
- **No side effects on import**: initializations (sessions, clients) execute under factories or context managers
- **Idempotency and backward compatibility**: schema changes must be exposed without breaking existing versions
- **Semantic versioning**: any breaking change must increment the major version and trigger coordinated migrations
- **Built-in observability**: SDK exposes hooks for metrics, logging, and tracing without coupling to a particular provider

## Current Architecture

```
baltra_sdk/
├── backend/
│   └── db/
│       ├── models.py              # Legacy database models
│       └── screening_models.py    # Screening domain models (26 models)
├── lambdas/
│   ├── db/
│   │   └── sql_utils.py          # SQL utilities for Lambda functions
│   ├── services/
│   │   ├── openai_utils.py       # OpenAI integration utilities
│   │   ├── whatsapp_messages.py  # WhatsApp message handling
│   │   └── whatsapp_utils.py     # WhatsApp utilities
│   └── utils/
│       └── candidate_data_fetcher.py  # Candidate data fetching logic
├── shared/
│   ├── elevenlabs/
│   │   └── elevenlabs_prompt.py  # ElevenLabs integration
│   ├── email_templates/
│   │   └── email_templates.py    # Email template utilities
│   ├── funnel_states/
│   │   └── funnel_states.py      # Funnel state definitions
└── __init__.py                    # Public entry points
```

## Database Models

The SDK provides SQLAlchemy models for the screening domain through `baltra_sdk.backend.db.screening_models`. The main models include:

### Core Models
- **Users**: User authentication and profile data
- **CompanyGroups**: Company group configurations
- **BusinessUnits**: Business unit definitions
- **Roles**: Role definitions with eligibility criteria
- **Locations**: Location data for jobs and interviews

### Hiring Models
- **HiringObjectives**: Hiring goals with role association and target amounts
- **Candidates**: Candidate profiles and tracking
- **CandidateFunnelLog**: Funnel state transitions
- **CandidateReferences**: Candidate reference tracking
- **ReferenceMessages**: Reference message logs

### Screening Models
- **QuestionSets**: Question set definitions
- **ScreeningQuestions**: Individual screening questions
- **ScreeningAnswers**: Candidate answers to screening questions
- **PhoneInterviews**: Phone interview records
- **PhoneInterviewQuestions**: Phone interview question sets

### Communication Models
- **MessageTemplates**: WhatsApp message templates
- **ScreeningMessages**: Screening conversation messages
- **WhatsappStatusUpdates**: WhatsApp message status tracking
- **EmailLogs**: Email communication logs
- **OnboardingResponses**: Onboarding form responses

### Additional Models
- **ProductUsage**: Product usage tracking
- **DashboardConfigurations**: Dashboard configuration settings
- **CandidateMedia**: Candidate media files
- **ResponseTiming**: Response time analytics
- **EligibilityEvaluationLog**: Eligibility evaluation tracking
- **AdTemplate**: Advertisement template definitions

### Database Utilities

The SDK provides `DBShim` for database session management outside Flask contexts:

```python
from baltra_sdk.backend.db.screening_models import DBShim, build_db_url_from_settings
from config.settings import settings

db_shim = DBShim.from_settings(settings)
session = db_shim.session
```

## Dependencies

### Core Dependencies
- SQLAlchemy >=2.0,<3.0
- Flask-SQLAlchemy >=3.0,<4.0
- psycopg2-binary >=2.9,<3.0
- python-dotenv >=0.21,<1.0
- boto3 >=1.26
- requests >=2.28,<3.0
- PyJWT >=2.0,<3.0
- Flask >=2.2,<3.0

### Optional Dependencies

#### Web Extras
```bash
pip install baltra-sdk[web]
```
Includes: Jinja2, gunicorn

#### Auth Extras
```bash
pip install baltra-sdk[auth]
```
Includes: authlib, bcrypt

#### MSSQL Extras
```bash
pip install baltra-sdk[mssql]
```
Includes: pyodbc

#### Scheduler Extras
```bash
pip install baltra-sdk[scheduler]
```
Includes: APScheduler

#### Reporting Extras
```bash
pip install baltra-sdk[reporting]
```
Includes: pandas, numpy, matplotlib, Pillow, playwright

#### AI Extras
```bash
pip install baltra-sdk[ai]
```
Includes: openai, aiohttp

#### All Extras
```bash
pip install baltra-sdk[all]
```
Includes all optional dependencies

## Installation

### Production
```bash
pip install --no-cache-dir --upgrade "baltra-sdk==1.0.8" \
  --extra-index-url "${PIP_EXTRA_INDEX_URL}"
```

### Development (Editable Mode)
```bash
pip install -e ./baltra-sdk
```

### Docker Development
Mount the SDK as a volume for hot-reload in `entrypoint.sh`:

```bash
set -euo pipefail
if [ -d "/sdk" ]; then
  pip install -e /sdk
else
  pip install --no-cache-dir --upgrade "baltra-sdk==${SDK_VERSION:-1.0.*}" \
    --extra-index-url "${PIP_EXTRA_INDEX_URL}"
fi
exec "$@"
```

## Usage Examples

### Database Session Management

```python
from baltra_sdk.backend.db.screening_models import DBShim
from config.settings import settings

db_shim = DBShim.from_settings(settings)
session = db_shim.session

try:
    from baltra_sdk.backend.db.screening_models import Candidates
    candidates = session.query(Candidates).filter_by(business_unit_id=123).all()
finally:
    db_shim.remove_session()
```

### Lambda Function Usage

```python
from baltra_sdk.lambdas.services.whatsapp_messages import process_message
from baltra_sdk.lambdas.utils.candidate_data_fetcher import CandidateDataFetcher

def lambda_handler(event, context):
    fetcher = CandidateDataFetcher()
    candidate_data = fetcher.fetch(phone_number="+1234567890")
    return process_message(event, candidate_data)
```

## Versioning Strategy

- **MAJOR**: Breaking changes in contracts (database models, service interfaces)
- **MINOR**: New features that maintain backward compatibility
- **PATCH**: Bug fixes without API changes

## Release Process

1. Merge to `main` triggers packaging pipeline (`python -m build`)
2. Publication to private PyPI / Git release with changelog
3. Semantic tag (`v1.0.8`) and signed `.whl` artifact
4. Downstream pipelines update images that depend on the SDK

## Migration Notes

When upgrading between versions:

1. Check the changelog for database schema changes
2. Run database migrations if required
3. Update imports if any module paths changed
4. Test integration points before production deployment

### Breaking Changes Policy

- Major version increments indicate breaking changes
- Breaking changes are documented in the changelog
- Migration guides are provided for major version upgrades
- Deprecated features are marked and removed in the next major version

## Quality and Observability

- Unit tests per module (domain isolated with stubs, infra with database fixtures in Docker)
- Contracts validated with type hints and runtime checks
- Integration tests with in-memory SQLite for database operations
- Logging structured through Python's logging module

## Development Guidelines

- Use `DBShim` for database sessions outside Flask contexts
- Do not read environment variables at import time; use cached `get_settings()` functions
- Models use Flask-SQLAlchemy with explicit foreign key relationships
- Repositories should expose idempotent and transactional methods
- Use adapters per service for complex scenarios

## Support

For issues, questions, or contributions, please contact the SDK maintainers or open an issue in the repository.

## License

Proprietary - Baltra Internal Use Only
