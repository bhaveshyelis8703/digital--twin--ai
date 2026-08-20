"""
Run once to create the Milestone 3 simulation_results table in the
existing database without running Alembic.

Usage:  python create_m3_tables.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

# Import ALL models so metadata is complete
import app.models.user  # noqa: F401

from app.core.database import Base, engine

# create_all is safe to run multiple times — skips tables that already exist
Base.metadata.create_all(bind=engine)
print("simulation_results table created (or already existed).")
print("Milestone 3 database setup complete.")
