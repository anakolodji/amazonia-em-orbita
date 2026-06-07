import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()

Base = declarative_base()

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), '../../sentinela_data.db')
DB_PATH = os.getenv('SENTINELA_DB_PATH', DEFAULT_DB_PATH)
DB_URL = f'sqlite:///{DB_PATH}'
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class MalariaCaso(Base):
    __tablename__ = 'malaria_casos'
    id = Column(Integer, primary_key=True, index=True)
    municipio = Column(String, index=True)
    data = Column(DateTime)
    casos = Column(Integer)

class EnchenteDetectada(Base):
    __tablename__ = 'enchentes_detectadas'
    id = Column(Integer, primary_key=True, index=True)
    municipio = Column(String, index=True)
    data = Column(DateTime)
    area_alagada_km2 = Column(Float)
    imagem_path = Column(String)

class AlertaINMET(Base):
    __tablename__ = 'alertas_inmet'
    id = Column(Integer, primary_key=True, index=True)
    regiao = Column(String, index=True)
    data_emissao = Column(DateTime)
    tipo = Column(String)
    descricao = Column(Text)
    fonte = Column(String)

class PredicaoRisco(Base):
    __tablename__ = 'predicoes_risco'
    id = Column(Integer, primary_key=True, index=True)
    municipio = Column(String, index=True)
    data = Column(DateTime)
    risco = Column(String)  # baixo, medio, alto
    score = Column(Float)

class VulnerabilidadeInundacao(Base):
    __tablename__ = 'vulnerabilidade_inundacoes'
    id = Column(Integer, primary_key=True, index=True)
    municipio = Column(String, index=True)
    ano = Column(Integer, index=True)
    indice_vulnerabilidade = Column(Float)
    area_indigena = Column(Float)
    area_urbana = Column(Float)
    area_rural = Column(Float)
    area_garimpo = Column(Float)
    area_assentamento = Column(Float)
    total_geral = Column(Float)

# Inicializar banco
if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
