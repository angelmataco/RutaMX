"""Evita que las pruebas gasten tokens de una IA real: la estimación de
casetas por IA se apaga y se usa siempre el promedio por km."""

import pytest

from app.services import llm_provider


@pytest.fixture(autouse=True)
def sin_ia_para_casetas(monkeypatch):
    monkeypatch.setattr(llm_provider, "estimar_casetas", lambda *args, **kwargs: None)
