import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.user import User, FinancialRecord, StudyActivity

print("DB URL:", settings.DATABASE_URL)

db = SessionLocal()
u = db.query(User).filter(User.email == "ramprasad16007@gmail.com").first()
if u:
    fin   = db.query(FinancialRecord).filter(FinancialRecord.user_id == u.id).count()
    study = db.query(StudyActivity).filter(StudyActivity.user_id == u.id).count()
    print(f"User found: id={u.id}  financial={fin}  study={study}")
else:
    print("User NOT found in this database")

total = db.query(User).count()
print(f"Total users in DB: {total}")
db.close()
