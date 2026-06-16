import os
import requests
from datetime import datetime
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import logging
from sentinela.db import AlertaINMET, SessionLocal, Base, engine
from sentinela.utils import setup_logging

load_dotenv()
setup_logging()

# Configurações
API_KEY = os.getenv('WEATHER_API_KEY')
# Exemplo: região Yanomami (RR)
REGIONS = [
    {"name": "Yanomami", "lat": -0.5, "lon": -64.5},
    # Adicione outras regiões se necessário
]

# Exemplo de endpoint WeatherAPI para alertas climáticos
BASE_URL = "http://api.weatherapi.com/v1/alerts.json"

def fetch_weather_alerts(region):
    if not API_KEY:
        logging.warning("WEATHER_API_KEY não configurada; ingestão climática ignorada.")
        return None

    params = {
        "key": API_KEY,
        "q": f"{region['lat']},{region['lon']}"
    }
    try:
        response = requests.get(BASE_URL, params=params, timeout=20)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        logging.error(f"Erro ao buscar alertas para {region['name']}: {exc}")
        return None

def save_alerts_to_db(alerts, region_name, db: Session):
    logging.info(f'Processando alertas para região: {region_name}')
    alert_list = []
    if 'alerts' in alerts and 'alert' in alerts['alerts']:
        alert_list = alerts['alerts']['alert']
    if not alert_list:
        logging.info(f"Nenhum alerta encontrado para {region_name}.")
        return
    for alert in alert_list:
        data_emissao_str = alert.get('effective') or alert.get('expires') or alert.get('date')
        if data_emissao_str:
            try:
                data_emissao = datetime.strptime(data_emissao_str[:16], '%Y-%m-%dT%H:%M')
            except Exception:
                data_emissao = datetime.now()
        else:
            data_emissao = datetime.now()
        # Controle de duplicidade: verifica se já existe alerta igual
        exists = db.query(AlertaINMET).filter_by(
            regiao=region_name,
            data_emissao=data_emissao,
            tipo=alert.get('event', 'N/A')
        ).first()
        if exists:
            logging.info(f'Alerta duplicado ignorado: {region_name} - {data_emissao}')
            continue
        db_alert = AlertaINMET(
            regiao=region_name,
            data_emissao=data_emissao,
            tipo=alert.get('event', 'N/A'),
            descricao=alert.get('headline', '') + "\n" + alert.get('desc', ''),
            fonte=alert.get('source', 'WeatherAPI')
        )
        db.add(db_alert)
        logging.info(f'Alerta salvo: {region_name} - {data_emissao}')
    db.commit()


def ingest_weather_alerts():
    db = SessionLocal()
    try:
        for region in REGIONS:
            alerts = fetch_weather_alerts(region)
            if alerts:
                save_alerts_to_db(alerts, region['name'], db)
    finally:
        db.close()

if __name__ == "__main__":
    setup_logging()
    Base.metadata.create_all(bind=engine)
    try:
        ingest_weather_alerts()
        logging.info("Ingestão de alertas climáticos concluída.")
    except Exception as e:
        logging.error(f"Erro na ingestão de alertas climáticos: {e}")
