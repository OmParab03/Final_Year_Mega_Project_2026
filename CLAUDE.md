# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

**Toxi-Scan** ("AI-Based Personalized Skincare Analyzer") is a final-year B.Tech project. It's a monorepo with two independent apps and no shared code or package manager workspace:

- `Backend/` — Flask REST API (Python)
- `Frontend/` — Angular 21 SPA (TypeScript, SSR-capable)

Full product/domain context (problem statement, functional requirements, planned AI pipeline, database ER design) lives in [README.md](README.md) — read it for the "why" behind features, but see **README vs. actual implementation** below before trusting its architecture claims.

## Commands

### Backend (from `Backend/`)
```bash
pip install -r requirements.txt
cp .env.example .env              # fill in MONGODB_URI (Atlas connection string) at minimum
python app.py                     # runs on http://127.0.0.1:5000
```
No test suite, linter, or formatter is currently configured for the backend. `Backend/.env` is required (gitignored) — see `.env.example` for the full variable list (Mongo URI/DB name, JWT secret, Hugging Face Space ids).

### Frontend (from `Frontend/`)
```bash
npm install
ng serve                          # dev server on http://localhost:4200
ng build                          # production build to dist/
ng test                           # unit tests via Vitest
```
Run a single test file with `ng test` filtering, e.g. `ng test --include='**/home.spec.ts'`.

### Whole project
`setup.sh` / `setup.bat` install both sides (and force a clean `node_modules` reinstall for the frontend). `run.sh` boots backend + frontend together. Both require `Backend/.env` with a working `MONGODB_URI` first (see below) — there is no local-DB fallback wired up.

## Architecture

### Backend — Flask app-factory + blueprints, MongoDB (pymongo, no ODM)
- `app.py` — `create_app()` factory: initializes extensions (`init_mongo(app)` connects and creates indexes), registers all blueprints under `/api`.
- `extensions.py` — the single place `db` (a pymongo `Database`, set by `init_mongo()`), `jwt` (Flask-JWT-Extended), and `cors` are instantiated, imported everywhere else to avoid circular imports. There's no ORM/ODM — `db.<collection>.find_one(...)` etc. directly.
- `config.py` — all config in one `Config` class, values sourced from `Backend/.env` via `python-dotenv` (see `.env.example` for the required keys: `MONGODB_URI`, `MONGODB_DB_NAME`, `JWT_SECRET_KEY`, `HF_SKIN_CLASSIFIER_SPACE`, `HF_SKIN_CONDITION_SPACE`). `.env` is gitignored — never commit real credentials.
- `models/` — one module per collection (`user.py`, `user_settings.py`, `skin_analysis.py`), each exporting plain functions that operate on dicts (`create_user`, `find_by_id`, `to_dict`, ...) rather than ORM classes. Mongo `_id`/`user_id` fields are `bson.ObjectId`; every `to_dict()` stringifies them for the API response.
- `routes/` — one Flask Blueprint per resource (`auth_routes`, `profile_routes`, `settings_routes`, `analysis_routes`), each mounted at its own `/api/...` prefix in `app.py`.
- Auth: JWT identity is the user's Mongo `_id` as a string — `create_access_token(identity=str(user['_id']))` on login, and `get_jwt_identity()` passed straight into model functions (which do the `ObjectId(...)` conversion internally) on every protected route. Follow this convention exactly.
- CORS is locked to a single origin, `http://localhost:4200`; update it in `app.py` if the frontend origin changes.
- Uploaded profile photos go to `UPLOAD_FOLDER` (served at `/uploads/profiles/<filename>`); uploaded skin-scan photos go to `SKIN_SCAN_FOLDER` (served at `/uploads/skin_scans/<filename>`) — both routes live in `app.py`. `profile_routes.py` also supports storing a photo as a raw base64 string directly on `photo_url` instead of a file.
- **Skin analysis** (`routes/analysis_routes.py` `POST /api/analysis/scan` + `services/hf_analysis.py`): saves the uploaded photo, calls two Hugging Face Gradio Spaces via `gradio_client` (a skin-type classifier and a YOLO-based condition detector — space ids in config), normalizes their output into `{skin_type, conditions, severity, score}`, stores both the normalized result and the raw API responses in a `skin_analyses` doc, and returns it. The condition Space's exact output schema was confirmed once via `Client(space).view_api()` (metadata only, no inference call) rather than by burning real inference requests — if its output format ever changes, re-run `view_api()` before touching `_parse_conditions()` in `hf_analysis.py` rather than guessing.

### README vs. actual implementation
The README's MongoDB design is now real for the implemented slice: `users`, `user_settings`, and `skin_analyses` collections exist and are driven by MongoDB Atlas. The README's `products` / `ingredients` / `scan_history` collections (Phase 2 — OCR + ingredient-risk pipeline) are still aspirational; only the Phase 1 skin-analysis flow is implemented. Check the actual `Backend/` code before assuming a README-described component exists.

### Frontend — Angular 21, standalone components, no NgModules
- Routing is centralized in `src/app/app.routes.ts`: a top-level `''` auth/landing route plus a `dashboard` route with child routes for each dashboard page (`home`, `history`, `skin-analysis`, `profile`, `settings`) rendered inside `dashboard/dashboard-layout/`.
- Feature folders live under `src/app/dashboard/pages/<feature>/`, each with paired `.ts` / `.html` / `.css` files and a standalone `@Component`. There's no consistent `*Component` naming suffix — follow whatever the existing sibling files in that folder already use rather than assuming a convention.
- `src/app/auth/auth.service.ts` is the single HTTP client for the whole app — every backend call (signin/signup, profile, settings, analysis scan/save/history) goes through it. The API base URL (`apiUrl`) and origin (`apiOrigin`, for building absolute `/uploads/...` URLs) are hardcoded there, not in environment files.
- Auth state is plain `localStorage` (`token`, `user` JSON), guarded with `isPlatformBrowser()` checks since the app is SSR-capable (`main.server.ts`, `app.config.server.ts`, `server.ts` — Express-based Angular SSR). Don't touch `localStorage`/`window` outside those guards or SSR rendering will break.
- Tests use Vitest (not Karma/Jasmine), configured via Angular CLI's newer builder — `*.spec.ts` files sit next to their component.
- `ng build` (production config) currently fails on pre-existing Google Fonts CSS budget errors in `angular.json` (unrelated to app code — `ng build --configuration=development` compiles clean). Not caused by the Mongo/HF migration; worth fixing separately if a real production build is needed.
