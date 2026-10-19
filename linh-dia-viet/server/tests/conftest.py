import os
import re
import tempfile
from pathlib import Path

_tmp = Path(tempfile.mkdtemp(prefix="ld-test-"))
os.environ.update({
    "APP_ENV_FILE": "",
    "ENV": "test",
    "DATABASE_URL": f"sqlite:///{_tmp}/test.db",
    "DATA_DIR": str(_tmp / "data"),
    "DEVICE_BUS": "memory",
    "TTS_PROVIDER": "fake",
    "SCHEDULER_ENABLED": "false",
    "SECRET_KEY": "test-secret",
    "ADMIN_EMAIL": "admin@example.com",
    "ADMIN_PASSWORD": "admin12345",
    "PUBLIC_BASE_URL": "http://testserver",
})

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import db as dbmod  # noqa: E402
from app.db import Base  # noqa: E402
from app.main import app  # noqa: E402
from app.security import hash_password, limiter  # noqa: E402
from app.seed import seed  # noqa: E402
from app.models import Device, Temple, User  # noqa: E402
from app.device_bus import InMemoryDeviceBus, set_bus  # noqa: E402
from app.security import hash_token  # noqa: E402
from sqlalchemy import select  # noqa: E402

P = "/le-chua"


@pytest.fixture
def db():
    Base.metadata.drop_all(dbmod.engine)
    Base.metadata.create_all(dbmod.engine)
    limiter.reset()
    session = dbmod.SessionLocal()
    seed(session)
    # Seed chỉ có 1 thiết bị (đền đầu tiên); test đặt nhiều đền cần thiết bị cho cả 3 đền.
    for i, t in enumerate(session.scalars(select(Temple).where(Temple.device_id.is_(None)).order_by(Temple.id)), 2):
        session.add(Device(id=f"pi-test-0{i}", name=f"Pi test {i}", token_hash=hash_token(f"tok-{i}")))
        session.flush()
        t.device_id = f"pi-test-0{i}"
    session.commit()
    bus = InMemoryDeviceBus()
    set_bus(bus)
    session.bus = bus
    yield session
    session.close()


@pytest.fixture
def client(db):
    with TestClient(app) as c:
        yield c


def csrf_of(client, path=f"{P}/dang-nhap") -> str:
    html = client.get(path).text
    return re.search(r'name="csrf-token" content="([^"]+)"', html).group(1)


def login(client, identifier, password):
    tok = csrf_of(client)
    r = client.post(f"{P}/dang-nhap", data={"identifier": identifier, "password": password, "csrf_token": tok},
                    follow_redirects=False)
    assert r.status_code == 303, r.text
    return csrf_of(client, f"{P}/")


@pytest.fixture
def admin_client(client):
    client.csrf = login(client, "admin@example.com", "admin12345")
    return client


@pytest.fixture
def user(db):
    u = User(name="Nguyễn Văn A", email="a@example.com", password_hash=hash_password("matkhau123"))
    db.add(u)
    db.commit()
    return u


@pytest.fixture
def user_client(client, user):
    client.csrf = login(client, "a@example.com", "matkhau123")
    return client
