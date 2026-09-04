# AstroCollector Backend Agent Guide
This file provides guidance to agents when working with code in this repository.

## Project overview

AstroCollector is a web application for astronomers who need photometric measurements from multiple sky-survey archives. The backend searches supported catalogs, resolves object names to coordinates, retrieves measurements, converts catalog-specific data to one format, preserves original data, and exposes results for plotting and export.
The application fetches photometric data from various sources called photometric star surveys (referred to as catalogs). Photometry is a technique that measures the brightness of a star in an image. We are interested in those parts of the measurements: time stamp, magnitude, magnitude error, and the photometric filter used, which can be then exported or are shown on a plot at frontend.

Time stamp is usually expressed in Julian Date. That is the number of days elapsed since noon on January 1, 4713 BC. However, the time stamp is defined unequivocally by its time standard and reference frame. We try to produce the time stamps in the BJD_TDB format to be able to work with data from multiple sources.

The unified photometric format contains:

- timestamp in BJD_TDB
- magnitude
- magnitude error
- photometric filter

## Use cases

- Search for stellar objects by name through SIMBAD or VSX, or by coordinates and radius.
- Search supported catalogs for nearby object identifiers.
- Fetch and process selected objects' photometric data asynchronously.
- Poll task status and retrieve completed search or data results.
- Export unified or original data as CSV files in ZIP archives.
- Let super admins create, update, and remove catalog plugins and resources at runtime.
- Periodically remove expired task data, raw files, and export archives.

## Architecture

The project uses a client-server architecture. This module owns the REST API and application logic.

- **Presentation layer:** FastAPI routers expose endpoints and validate requests.
- **Service layer:** feature-specific business logic.
- **Repository layer:** SQLAlchemy-based database access, including a shared generic repository.
- **Task layer:** Celery workers perform catalog searches, data retrieval, conversion, and other long-running work outside the HTTP request-response cycle. Redis is the broker; clients poll task status.
- **Persistence:** PostgreSQL stores metadata, tasks, identifiers, processed photometry, users, and export records. The filesystem stores plugin scripts/resources, original CSV data, and generated exports.
- **Scheduling:** Celery Beat schedules database and filesystem cleanup.

This is an open-layered, vertical-slice architecture: a layer may call lower layers directly when that avoids unnecessary boilerplate, while feature code remains grouped by capability. For example, the tasks related code (all layers) is located in `src/tasks`.
## Tech stack

- Python 3.13 and `uv` package manager
- FastAPI
- Pydantic (DTO validation) and pydantic-settings
- Celery as the distributed task queue for async tasks outside of the HTTP request-response cycle () and Celery Beat
- Redis for the task broker and separately for session storage
- PostgreSQL, SQLAlchemy, and Alembic
- Astropy, Astroquery, and PyVO for astronomy-specific work (and other packages, which are included in plugin implementations)
- Podman/Compose for deployment

## Directory structure

```text
ac-backend/
├── alembic/                 # Database migrations
├── logs/                    # FastAPI and Celery logs
├── plugins/                 # Runtime-installed catalog modules
├── resources/               # Per-plugin resources to support offline star surveys
├── temp/                    # Expiring raw CSV and export files
├── tests/                   # Contains backend tests
|   └── services/            # .env, running script for the tests
├── .env                     # Expiring raw CSV and export files
├── pyproject.toml           # Contains project dependencies
├── README.md                # Instructions on running the project in DEV mode
└── src/
    ├── core/
    │   ├── celery/          # Celery setup and configuration
    │   ├── config/          # Application settings
    │   ├── database/        # Database connection setup
    │   ├── exception/       # Shared application exceptions
    │   ├── repository/      # Generic repository infrastructure
    │   ├── security/        # Authentication and authorization
    │   └── service/         # Shared service DTOs
    ├── data_retrieval/      # Task-result retrieval
    ├── export/              # Raw and processed data exports
    ├── phase_curve/         # VSX epoch and period lookup
    ├── plugin/
    │   ├── default_plugins/ # Built-in catalogs
    │   └── interface/       # Plugin contracts and DTOs
    ├── so_name_resolving/   # Object-name resolution
    ├── tasks/               # Celery tasks, enqueueing, and status
    └── main.py              # FastAPI setup and startup initialization
```

## Backend invariants

- Keep HTTP handlers thin; long-running catalog access or processing belongs in Celery tasks.
- A catalog plugin subclasses `CatalogPlugin` and uses a catalog-specific `StellarObjectIdentificatorDto` subtype.
- `list_objects(...)` and `get_photometric_data(...)` are generators so results can be persisted in chunks.
- `get_photometric_data(...)` must return unified `PhotometricDataDto` values and write the original catalog response to the supplied CSV path.
- `list_objects` and `get_photometric_data` is run asynchronously, outside the FastAPI application
- Preserve runtime plugin loading and per-plugin resource isolation.
- Database schema changes require Alembic migrations.
- Export reuse is keyed by the requested task set and export option; exports and source CSV files are temporary.
- Public endpoints remain public unless requirements change. Plugin management requires the `super_admin` role.
- Preserve session-cookie protections, CSRF-token validation, and role checks on protected endpoints.
- Read configuration through the settings object and `.env`; never hardcode secrets or environment-specific paths.
- Inspect current source and project configuration before changing behavior; they take precedence if this description is outdated.

## Plugin system
This subsection describes the details of the core part of the system — the catalog plugins. Every plugin consists of three parts: a plugin script, a correspoding plugin database entity to store metadata, and a resources directory. The database keeps track of the registered plugins. Every plugin must implement a class that extends the `CatalogPlugin` abstract class defined in the `src.plugin.interface` package.

### `CatalogPlugin`
The subclasses must implement these two methods:

- `list_objects` must return stellar objects that were found in the radius around the given coordinates. The stellar objects are identified by the StellarObjectIdentificatorDto subclass
- `get_photometric_data` is responsible for fetching photometric data for a given stellar object. The fetched data must be converted into the unified format as PhotometricDataDto objects before being returned. The original data fetched from the catalog must be written to the CSV file specified by the csv_path parameter. Both methods include the resources_dir parameter, which provides the access to the plugin’s corresponding resources directory.
- Each catalog has its own way of identifying stellar objects. To make the system flexible and allow every catalog to manage the identification independently, the plugin class is parametrized by a subclass of `StellarObjectIdentificatorDto`

## General behavioral guidelines

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:

```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```
Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.
