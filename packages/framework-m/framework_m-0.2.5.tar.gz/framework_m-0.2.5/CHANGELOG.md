# Changelog

## framework-m v0.2.5

### Bug Fixes

- add pypi and pipeline badges to readme (62590fc)


## framework-m v0.2.4

### Bug Fixes

- robust package detection and safe MR title truncation (36385b6)
- improve changelog extraction for GitLab release pages (bb636b0)


## framework-m v0.2.3

### Bug Fixes

- use show-ref for robust tag check and clear local ghost tags (79563c5)


## framework-m v0.2.2

### Bug Fixes

- finalize air-tight release automation with GitLab releases, professional logging, and zero-spam logic (0dc7b19)
- simplify release rules and regex to stop recursive loops (790b318)
- fix auto-tagging trigger and regex for merge commits (5e69fb9)


## framework-m v0.2.1

### Bug Fixes

- improve commit filtering and fix linting (6e4082d)
- prevent duplicate changelog entries by ensuring tags are fetched and handled correctly (a498f85)
- make release tag parsing more robust for large monorepos (8e1b5d8)
- update project URLs to GitLab and refactor versioning source of truth (84e0bd3)
- prevent recursive release loops and cleanup dead code (6ff3776)


## framework-m 0.2.0

### Features

- add unique constraint support and refine docs (5f9af98)
- add PyPI publishing for framework-m-studio and update docs (d6ed80a)
- comprehensive documentation covering fundamentals, migration guides, i18n, multi-tenancy usage, and API references (6a2c1df)
- implement Frontend Build & Serving (9f9aa79)
- implement desk ui (13ebcc8)
- implement workflows and advanced features (22a7745)
- implement system doctypes and features (05e7f3d)
- implement built-in doctypes and system adapters (23195d1)
- cli tools implementation (18a1d83)
- implement events, webhooks, monitoring and websockets (9381d3f)
- phase-03 complete (00123da)
- prepare for package split after completion (e8abae2)
- permission system implemented (632afb7)
- litestar application setup and authentication middleware (7854664)
- Complete DocType Engine & Database Layer (523f211)
- refactor phase-01 and implemented doctype-engine with CRUD, migrations and cli (3c36234)
- complete Phase 01 - Core Kernel & Interfaces (1dcbfab)
- automated pipeline for gitlab registry (c1a9e2b)

### Bug Fixes

- remove create-studio-release-mr and detached HEAD (d814206)
- lint issues (0c1dc94)
- studio issues and ci pipeline (e17e9c2)
- ruff issue (24fb2ef)
- ruff issue (2b3dfb0)
- mypy issues (23c539b)
- Fix ruff linting errors (ad8997c)
- lint format (8fc33e8)
- format with ruff (c9d5f39)
- mypy issues (5ab1715)
- format all files with ruff (90e3808)
- remove skip ci from release commit message (2db2b6f)
- correct directory navigation in release-package job (5b67a98)
- lint error in base_doctype (47e8c37)
- lint error in test_base_doctype (354f66f)
- use twine for GitLab registry publishing (6472dc7)
- specify dist path for uv publish (86df5c7)
- exclude cache directories from source (695d2fb)
- lint errors in tests (8b4120d)
- rename workspace to avoid package name conflict (20e46bb)


## framework-m 0.1.0

### Features

- Initial release of Framework M
