import pandas as pd
from datetime import datetime
from sentinela.db import PredicaoRisco, SessionLocal, Base, engine
import logging
from sentinela.utils import setup_logging

def ingest_predicoes(csv_path):
    setup_logging()
    df = pd.read_csv(csv_path)
    db = SessionLocal()
    inseridos = 0
    ignorados = 0
    vistos_no_arquivo = set()
    for _, row in df.iterrows():
        municipio = row['municipio']
        data = datetime.strptime(row['data'], '%Y-%m-%d')
        risco = row['risco']
        score = float(row['score'])
        chave = (municipio, data, risco)
        if chave in vistos_no_arquivo:
            logging.info(f'Predição duplicada ignorada no arquivo: {municipio} - {data.date()} - {risco}')
            ignorados += 1
            continue
        exists = db.query(PredicaoRisco).filter_by(municipio=municipio, data=data, risco=risco).first()
        if exists:
            logging.info(f'Predição duplicada ignorada: {municipio} - {data.date()} - {risco}')
            ignorados += 1
            continue
        pred = PredicaoRisco(
            municipio=municipio,
            data=data,
            risco=risco,
            score=score
        )
        db.add(pred)
        vistos_no_arquivo.add(chave)
        inseridos += 1
    db.commit()
    db.close()
    logging.info(f'Predições inseridas: {inseridos}, duplicadas ignoradas: {ignorados}')

if __name__ == "__main__":
    setup_logging()
    Base.metadata.create_all(bind=engine)
    # Exemplo de uso: ingest_predicoes('predicoes.csv')
