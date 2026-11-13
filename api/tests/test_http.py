"""Testa a função HTTP de ponta a ponta (CORS, JSON) com requisições Flask reais."""

import flask
import pytest

import main
from memoria import RepositorioMemoria

app = flask.Flask(__name__)


@pytest.fixture(autouse=True)
def ambiente(monkeypatch):
    monkeypatch.setattr(main, "_repo", RepositorioMemoria())
    monkeypatch.setenv("ALLOWED_ORIGIN", "https://exemplo.com")


def chamar(metodo, caminho, **kwargs):
    with app.test_request_context(caminho, method=metodo, **kwargs):
        return app.make_response(main.api(flask.request))


def test_preflight_cors():
    r = chamar("OPTIONS", "/produtos")
    assert r.status_code == 204
    assert r.headers["Access-Control-Allow-Origin"] == "https://exemplo.com"


def test_post_e_get_json():
    r = chamar("POST", "/produtos", json={"nome": "Caneta", "quantidade": 1, "minimo": 0, "preco": 1})
    assert r.status_code == 201
    assert r.headers["Access-Control-Allow-Origin"] == "https://exemplo.com"
    r = chamar("GET", "/produtos?busca=can")
    assert r.status_code == 200
    assert r.get_json()[0]["nome"] == "Caneta"


def test_json_invalido():
    r = chamar("POST", "/produtos", data="{xx", content_type="application/json")
    assert r.status_code == 400
    assert "JSON" in r.get_json()["erro"]


def test_delete_sem_corpo():
    criado = chamar("POST", "/produtos", json={"nome": "X"}).get_json()
    r = chamar("DELETE", f"/produtos/{criado['id']}")
    assert r.status_code == 204
