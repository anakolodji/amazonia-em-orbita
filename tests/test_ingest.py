import os
import tempfile
import pandas as pd
from datetime import datetime
from sentinela.db import Base, engine, SessionLocal, MalariaCaso, PredicaoRisco
from sentinela.ingest_malaria import ingest_malaria_cases
from sentinela.ingest_predicoes import ingest_predicoes
import pytest

def setup_test_db():
    # Cria as tabelas no banco de teste
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def teardown_test_db():
    # Remove todos os dados após o teste
    Base.metadata.drop_all(bind=engine)

def test_ingest_malaria_cases():
    setup_test_db()
    db = SessionLocal()
    # Cria CSV temporário
    tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
    df = pd.DataFrame([
        {'municipio': 'A', 'data': '2025-01-01', 'casos': 10},
        {'municipio': 'A', 'data': '2025-01-01', 'casos': 10},  # duplicado
        {'municipio': 'B', 'data': '2025-01-02', 'casos': 5}
    ])
    df.to_csv(tmpfile.name, index=False)
    ingest_malaria_cases(tmpfile.name)
    casos = db.query(MalariaCaso).all()
    assert len(casos) == 2  # Duplicado não inserido
    os.unlink(tmpfile.name)
    teardown_test_db()

def test_ingest_predicoes():
    setup_test_db()
    db = SessionLocal()
    tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
    df = pd.DataFrame([
        {'municipio': 'A', 'data': '2025-01-01', 'risco': 'alto', 'score': 0.9},
        {'municipio': 'A', 'data': '2025-01-01', 'risco': 'alto', 'score': 0.9},  # duplicado
        {'municipio': 'B', 'data': '2025-01-02', 'risco': 'medio', 'score': 0.5}
    ])
    df.to_csv(tmpfile.name, index=False)
    ingest_predicoes(tmpfile.name)
    preds = db.query(PredicaoRisco).all()
    assert len(preds) == 2  # Duplicado não inserido
    os.unlink(tmpfile.name)
    teardown_test_db()

if __name__ == "__main__":
    test_ingest_malaria_cases()
    test_ingest_predicoes()
    print("Testes de ingestão executados com sucesso.")
