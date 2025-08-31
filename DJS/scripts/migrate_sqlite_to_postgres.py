import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models.models import (
    Base,
    Company,
    University,
    Professor,
    News,
    Round,
    Relation,
    RelationHistory,
    ScheduledJob,
    SystemConfig,
    RelationType,
    User,
)

SQLITE_URL = os.getenv("SQLITE_URL", "sqlite:///./data/djs.db")
POSTGRES_URL = os.getenv(
    "POSTGRES_URL", "postgresql+psycopg2://djs:djs_pw@localhost:5432/djs"
)

src_engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
dst_engine = create_engine(POSTGRES_URL)

SrcSession = sessionmaker(bind=src_engine)
DstSession = sessionmaker(bind=dst_engine)

# Ensure destination tables
Base.metadata.create_all(bind=dst_engine)


def copy_table(model):
    src = SrcSession()
    dst = DstSession()
    try:
        for row in src.query(model).all():
            data = {c.name: getattr(row, c.name) for c in model.__table__.columns}
            obj = model(**data)
            dst.add(obj)
        dst.commit()
        print(f"Copied {model.__tablename__}")
    finally:
        src.close()
        dst.close()


if __name__ == "__main__":
    for m in [
        User,
        Company,
        University,
        Professor,
        News,
        Round,
        Relation,
        RelationHistory,
        ScheduledJob,
        SystemConfig,
        RelationType,
    ]:
        copy_table(m)
    print("Migration completed")
