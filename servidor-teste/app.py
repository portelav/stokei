"""Servidor Flask mínimo, só para testar se a configuração do Google Cloud funciona.

Não faz parte do Stokei. Serve apenas para confirmar que o deploy, a URL
pública e os logs estão funcionando antes de publicar a API de verdade.
"""

import logging
import os
import socket
from datetime import datetime, timezone

from flask import Flask, jsonify

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)


def informacoes():
    return {
        "status": "ok",
        "mensagem": "Servidor do Stokei funcionando",
        "horario_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "maquina": socket.gethostname(),
        # O Cloud Run preenche estas variáveis; localmente ficam vazias.
        "servico": os.environ.get("K_SERVICE", "local"),
        "revisao": os.environ.get("K_REVISION", "local"),
        "projeto": os.environ.get("GOOGLE_CLOUD_PROJECT", ""),
    }


@app.get("/")
def inicio():
    info = informacoes()
    logging.info("Acesso à página inicial (serviço %s)", info["servico"])
    linhas = "".join(f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in info.items())
    return (
        "<!doctype html><html lang='pt-BR'><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<title>Stokei: servidor de teste</title>"
        "<body style='font-family:system-ui;max-width:640px;margin:40px auto;padding:0 16px'>"
        "<h1>Servidor funcionando</h1>"
        f"<table style='border-collapse:collapse'>{linhas}</table>"
        "<p>JSON em <a href='/saude'>/saude</a></p></body></html>"
    )


@app.get("/saude")
def saude():
    return jsonify(informacoes())


if __name__ == "__main__":
    # Local: python app.py  ->  http://localhost:8080
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
