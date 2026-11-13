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


# --------------------------------------------------------------------------
# Site servido pelo mesmo serviço (STOKEI_WEB)
# --------------------------------------------------------------------------

@pytest.fixture
def site(monkeypatch, tmp_path):
    (tmp_path / "index.html").write_text("<h1>Dashboard</h1>", encoding="utf-8")
    (tmp_path / "style.css").write_text("body{}", encoding="utf-8")
    monkeypatch.setenv("STOKEI_WEB", str(tmp_path))
    return tmp_path


def test_raiz_devolve_index(site):
    r = chamar("GET", "/")
    assert r.status_code == 200
    assert "text/html" in r.headers["Content-Type"]
    r.direct_passthrough = False  # o arquivo vem em streaming; libera a leitura no teste
    assert b"Dashboard" in r.get_data()
    assert r.headers["Cache-Control"] == "no-cache"


def test_arquivo_do_site(site):
    r = chamar("GET", "/style.css")
    assert r.status_code == 200
    assert "text/css" in r.headers["Content-Type"]


def test_rota_da_api_continua_json_com_site(site):
    r = chamar("GET", "/produtos")
    assert r.status_code == 200
    assert r.get_json() == []


def test_arquivo_inexistente_404(site):
    r = chamar("GET", "/nao-existe.html")
    assert r.status_code == 404


def test_nao_sai_da_pasta_do_site(site):
    r = chamar("GET", "/../main.py")
    assert r.status_code == 404


def test_sem_stokei_web_nao_serve_site(monkeypatch):
    monkeypatch.delenv("STOKEI_WEB", raising=False)
    r = chamar("GET", "/index.html")
    assert r.status_code == 404
    assert r.get_json()["erro"] == "Rota não encontrada"
