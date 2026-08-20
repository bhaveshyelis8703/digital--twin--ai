# Bugs and Fixes

- Fixed import path issues by exposing the FastAPI app through the backend entrypoint.
- Fixed SQLAlchemy relationship mapping by adding explicit foreign keys to user-owned tables.
- Fixed analytics logging middleware so unauthenticated requests do not fail the app.
- Replaced passlib-based hashing with bcrypt-compatible hashing for reliable registration on the installed environment.
