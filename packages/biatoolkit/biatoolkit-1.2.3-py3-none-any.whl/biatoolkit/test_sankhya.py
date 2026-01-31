import sys
import os
#sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))
from biatoolkit.sankhya_call import Sankhya, SankhyaHTTPError
import json


# Opcional: não depende mais disso, mas pode deixar.
os.environ.setdefault("SANKHYA_SERVICE_PATH", "/mge/service.sbr")

# ⚠️ COLE AQUI seu JSESSIONID em UMA LINHA (sem ENTER no meio)
REAL = "qwd6yyqtbw4xMURqiaxQIJx6NLE447ZvwReMA5TP.sankhya-w-78598f67f-n7mc"

if not REAL:
    raise SystemExit("Token JSESSIONID não fornecido.")

# Base URL do ambiente correto (o novo)
BASE_URL = "https://ecossistema2.sankhyacloud.com.br"

sk = Sankhya()

try:
    out = sk.load_view(
        "BIA_VW_MB_RULES",
        "1=1",
        fields="*",
        jsessionid=REAL,
        base_url=BASE_URL
    )
    print("OK! Resposta (top-level keys):", list(out.keys()))
    print(out)
    if isinstance(out, dict):
        print(json.dumps(out, indent=2, ensure_ascii=False))

except SankhyaHTTPError as e:
    print("HTTP ERROR:", e.status_code)
    print("BODY (primeiros 500 chars):")
    print((e.response_text or "")[:500])
