import pandas as pd
from sentinela.db import Base, engine, SessionLocal, MalariaCaso, PredicaoRisco
from sentinela.ingest_malaria import ingest_malaria_cases
from sentinela.ingest_predicoes import ingest_predicoes
import pytest


@pytest.fixture()
def clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    try:
        yield
    finally:
        Base.metadata.drop_all(bind=engine)


def test_ingest_malaria_cases(clean_db, tmp_path):
    csv_path = tmp_path / "malaria.csv"
    pd.DataFrame(
        [
            {"municipio": "A", "data": "2025-01-01", "casos": 10},
            {"municipio": "A", "data": "2025-01-01", "casos": 10},
            {"municipio": "B", "data": "2025-01-02", "casos": 5},
        ]
    ).to_csv(csv_path, index=False)

    ingest_malaria_cases(csv_path)

    with SessionLocal() as db:
        casos = db.query(MalariaCaso).all()

    assert len(casos) == 2


def test_ingest_predicoes(clean_db, tmp_path):
    csv_path = tmp_path / "predicoes.csv"
    pd.DataFrame(
        [
            {"municipio": "A", "data": "2025-01-01", "risco": "alto", "score": 0.9},
            {"municipio": "A", "data": "2025-01-01", "risco": "alto", "score": 0.9},
            {"municipio": "B", "data": "2025-01-02", "risco": "medio", "score": 0.5},
        ]
    ).to_csv(csv_path, index=False)

    ingest_predicoes(csv_path)

    with SessionLocal() as db:
        preds = db.query(PredicaoRisco).all()

    assert len(preds) == 2
