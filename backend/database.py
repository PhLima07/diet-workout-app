import os
import socket
from urllib.parse import urlparse, unquote
from sqlalchemy import create_engine
from sqlalchemy.engine import URL as SAURL
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import NullPool

# Vercel Lambda não suporta IPv6 outbound — força IPv4
_orig_getaddrinfo = socket.getaddrinfo
def _ipv4_only(host, port, family=0, *args, **kwargs):
    return _orig_getaddrinfo(host, port, socket.AF_INET, *args, **kwargs)
socket.getaddrinfo = _ipv4_only

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    _p = urlparse(DATABASE_URL)
    engine = create_engine(
        SAURL.create(
            drivername="postgresql+psycopg2",
            username=unquote(_p.username or ""),
            password=unquote(_p.password or ""),
            host=_p.hostname,
            port=_p.port,
            database=(_p.path or "/postgres").lstrip("/"),
            query={"sslmode": "require"},
        ),
        poolclass=NullPool,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
