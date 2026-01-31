"""
biatoolkit.sankhya_call

Classe utilitária para chamadas HTTP a serviços Sankhya (ou gateway),
autenticando via JSESSIONID (cookie), preferencialmente obtido do header
do runtime (AgentCore) via BiaUtil.

Objetivo:
- O dev do MCP Tool não precisa recriar autenticação, headers e session.
- Basta chamar Sankhya(...).call_json(...) ou Sankhya.Call(...) (compat).

Requisitos:
- requests
- urllib3 (vem com requests)
- boto3 (já usado no biatoolkit.util)
- mcp.server.fastmcp.FastMCP (se usar no server; opcional para modo local)

Config via env (todas opcionais):
- SANKHYA_TIMEOUT_CONNECT: default 3.05
- SANKHYA_TIMEOUT_READ: default 12
- SANKHYA_RETRIES_TOTAL: default 3
- SANKHYA_RETRY_BACKOFF: default 0.5
- SANKHYA_VERIFY_SSL: default "1"
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple
import os
import json
import logging

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    # FastMCP só existe no runtime/servidor MCP. Em testes locais, pode faltar.
    from mcp.server.fastmcp import FastMCP
except Exception:  # pragma: no cover
    FastMCP = Any  # type: ignore

from .util import BiaUtil
from .settings import BiaToolkitSettings


logger = logging.getLogger(__name__)




# Caminho fixo do serviço Sankhya
SERVICE_PATH = "/mge/service.sbr"

@dataclass(frozen=True)
class SankhyaSettings:
    """
    Configurações específicas da integração Sankhya (timeouts, retries, SSL).
    Não armazena base_url nem service_path.
    """
    timeout_connect: float
    timeout_read: float
    retries_total: int
    retry_backoff: float
    verify_ssl: bool

    @staticmethod
    def from_env() -> "SankhyaSettings":
        def _f(name: str, default: float) -> float:
            try:
                return float(os.getenv(name, str(default)))
            except Exception:
                return default

        def _i(name: str, default: int) -> int:
            try:
                return int(os.getenv(name, str(default)))
            except Exception:
                return default

        def _b(name: str, default: bool) -> bool:
            raw = os.getenv(name, "1" if default else "0").strip().lower()
            return raw in ("1", "true", "yes", "y", "on")

        return SankhyaSettings(
            timeout_connect=_f("SANKHYA_TIMEOUT_CONNECT", 3.05),
            timeout_read=_f("SANKHYA_TIMEOUT_READ", 12.0),
            retries_total=_i("SANKHYA_RETRIES_TOTAL", 3),
            retry_backoff=_f("SANKHYA_RETRY_BACKOFF", 0.5),
            verify_ssl=_b("SANKHYA_VERIFY_SSL", True),
        )

def build_url(
    *,
    url: Optional[str] = None,
    base_url: Optional[str] = None,
    query: Optional[str] = None,
) -> str:
    """
    Resolve URL final para chamada Sankhya.
    - Se url for completa (http/https), usa como está.
    - Se url for relativo, concatena base_url + url.
    - Se não houver url, monta base_url + SERVICE_PATH.
    - Se não houver base_url, lança erro.
    """
    if url and url.strip():
        u = url.strip()
        if u.startswith("http://") or u.startswith("https://"):
            final = u
        else:
            if not base_url:
                raise ValueError("base_url deve ser informado para url relativo.")
            b = base_url.strip().rstrip("/")
            if not u.startswith("/"):
                u = "/" + u
            final = b + u
    else:
        if not base_url:
            raise ValueError("base_url deve ser informado para montar a URL Sankhya.")
        b = base_url.strip().rstrip("/")
        final = f"{b}{SERVICE_PATH}"
    if query:
        if "?" in final:
            return f"{final}&{query.lstrip('?')}"
        return f"{final}?{query.lstrip('?')}"
    return final



class SankhyaHTTPError(RuntimeError):
    def __init__(self, message: str, status_code: Optional[int] = None, response_text: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text


class Sankhya:
    """
    Classe responsável por integrar e chamar serviços da plataforma Sankhya.

    Uso recomendado (em MCP server):
        sk = Sankhya(mcp)
        out = sk.load_view("BIA_VW_MB_RULES", "CODPROD_A = 123", fields="*")

    Uso compatível com o scaffold (estático):
        out = Sankhya.Call(jsessionID="...", payload={...})
        # ou sem jsessionID se você passar mcp:
        out = Sankhya.Call(jsessionID=None, mcp=mcp, payload={...})
    """

    def __init__(
        self,
        mcp: Optional[FastMCP] = None,
        *,
        toolkit_settings: Optional[BiaToolkitSettings] = None,
        sankhya_settings: Optional[SankhyaSettings] = None,
        default_headers: Optional[Dict[str, str]] = None,
    ):
        """
        Inicializa a instância Sankhya.

        Args:
            mcp: Instância opcional do FastMCP para contexto do runtime.
            toolkit_settings: Configurações globais do toolkit (opcional).
            sankhya_settings: Configurações específicas da integração Sankhya (opcional).
            default_headers: Headers HTTP padrão para todas as requisições (opcional).
        """
        self.mcp = mcp
        self.toolkit_settings = toolkit_settings or BiaToolkitSettings.from_env()
        self.sankhya_settings = sankhya_settings or SankhyaSettings.from_env()
        self.default_headers = default_headers or {}

        # Cria uma sessão HTTP com política de retries configurada
        self._session = self._build_session()

    # -------------------------
    # Sessão HTTP + retries
    # -------------------------
    def _build_session(self) -> requests.Session:
        """
        Cria uma sessão HTTP configurada com política de retries.
        Utiliza as configurações de timeout e retries do Sankhya.
        """
        s = requests.Session()

        # Configura política de retries para falhas temporárias
        retries = Retry(
            total=max(0, int(self.sankhya_settings.retries_total)),
            connect=max(0, int(self.sankhya_settings.retries_total)),
            read=max(0, int(self.sankhya_settings.retries_total)),
            backoff_factor=float(self.sankhya_settings.retry_backoff),
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("POST", "GET"),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retries)
        s.mount("https://", adapter)
        s.mount("http://", adapter)
        return s

    # -------------------------
    # JSESSIONID resolve
    # -------------------------
    def _resolve_jsessionid(self, jsessionid: Optional[str] = None) -> str:
        """
        Resolve o JSESSIONID a ser usado na autenticação.
        Prioriza o valor explícito, depois tenta extrair do header do runtime via BiaUtil.

        Args:
            jsessionid: Token de sessão explícito (opcional).

        Returns:
            str: JSESSIONID válido.

        Raises:
            ValueError: Se não for possível obter o JSESSIONID.
        """
        # 1) parâmetro explícito
        if jsessionid and str(jsessionid).strip():
            return str(jsessionid).strip()

        # 2) header do runtime via BiaUtil (se tiver mcp)
        if self.mcp is not None:
            try:
                util = BiaUtil(self.mcp, self.toolkit_settings)
                h = util.get_header()
                if h and getattr(h, "jsessionid", None):
                    return str(h.jsessionid).strip()
            except Exception as e:
                logger.debug("Falha ao ler jsessionid do header via BiaUtil: %s", e)

        raise ValueError(
            "JSESSIONID ausente. Passe jsessionid explicitamente ou forneça 'mcp' para ler do header."
        )


    # -------------------------
    # Métodos públicos
    # -------------------------
    def call_json(
        self,
        *,
        payload: Optional[Dict[str, Any]] = None,
        jsessionid: Optional[str] = None,
        url: Optional[str] = None,
        base_url: Optional[str] = None,
        query: Optional[str] = None,
        method: str = "POST",
        extra_headers: Optional[Dict[str, str]] = None,
        timeout: Optional[Tuple[float, float]] = None,
        raise_for_http_error: bool = True,
    ) -> Dict[str, Any]:
        """
        Faz uma chamada HTTP ao serviço Sankhya e retorna JSON (ou erro detalhado).

        Args:
            payload: Corpo JSON (para POST). Pode ser None.
            jsessionid: Se None, tenta resolver do header (mcp) automaticamente.
            url: URL completa (se quiser ignorar base_url/service_path).
            base_url: Base URL alternativa (opcional).
            query: Querystring adicional (ex: "serviceName=...&outputType=json")
            method: "POST" ou "GET"
            extra_headers: Headers adicionais.
            timeout: (connect, read) override
            raise_for_http_error: Se True, lança SankhyaHTTPError em status != 200

        Returns:
            dict: Resposta JSON (ou {"raw_text": "..."} se não for JSON)
        """
        # Resolve o token de sessão (JSESSIONID)
        sid = self._resolve_jsessionid(jsessionid)

        # Monta a querystring, sempre incluindo o mgeSession
        query_parts = []
        if query:
            query_parts.append(query.lstrip("?"))
        query_parts.append(f"mgeSession={sid}")
        final_query = "&".join(query_parts)

        # Monta a URL final da requisição
        final_url = build_url(url=url, query=final_query, base_url=base_url)
        print("FINAL URL:", final_url)

        # Monta os headers da requisição
        headers: Dict[str, str] = {
            "Content-Type": "application/json",
            **self.default_headers,
        }
        if extra_headers:
            headers.update(extra_headers)

        # Define o timeout da requisição
        t = timeout or (self.sankhya_settings.timeout_connect, self.sankhya_settings.timeout_read)

        # Realiza a chamada HTTP (GET ou POST)
        if method.upper() == "GET":
            resp = self._session.get(final_url, headers=headers, timeout=t, verify=self.sankhya_settings.verify_ssl)
        else:
            print("\n" + "="*40)
            print("Sankhya POST Request:")
            print(f"URL: {final_url}")
            print(f"Headers: {json.dumps(headers, ensure_ascii=False, indent=2)}")
            print(f"Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
            print(f"Timeout: {t}")
            print(f"Verify SSL: {self.sankhya_settings.verify_ssl}")
            print("="*40 + "\n")
            resp = self._session.post(final_url, headers=headers, json=payload, timeout=t, verify=self.sankhya_settings.verify_ssl)

        # Trata erros HTTP
        if resp.status_code != 200:
            msg = f"Falha HTTP {resp.status_code} ao chamar Sankhya/gateway."
            if raise_for_http_error:
                raise SankhyaHTTPError(msg, status_code=resp.status_code, response_text=resp.text)
            return {"error": True, "status_code": resp.status_code, "message": msg, "response_text": resp.text}

        # Tenta decodificar JSON; se não der, retorna texto puro
        try:
            return resp.json()
        except Exception:
            return {"raw_text": resp.text}

    def load_view(
        self,
        view_name: str,
        where_sql: str,
        *,
        fields: str = "*",
        jsessionid: Optional[str] = None,
        url: Optional[str] = None,
        base_url: Optional[str] = None,
        output_type: str = "json",
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Helper para o CRUDServiceProvider.loadView (mge/service.sbr).
        Monta o payload e a querystring automaticamente para facilitar consultas a views Sankhya.

        Args:
            view_name: Nome da view no Sankhya.
            where_sql: Cláusula WHERE (string).
            fields: Campos a retornar (string).
            jsessionid: Se None, pega do header (mcp).
            url: URL completa opcional (override).
            base_url: Base URL alternativa (opcional).
            output_type: "json" (default).
            extra_headers: Headers adicionais.

        Returns:
            dict: Resposta da consulta à view.
        """
        # Monta a querystring para o serviço
        query = f"serviceName=CRUDServiceProvider.loadView&outputType={output_type}"

        # Monta o corpo do payload conforme esperado pelo serviço
        body = {
            "serviceName": "CRUDServiceProvider.loadView",
            "requestBody": {
                "query": {
                    "viewName": view_name,
                    "where": {"$": where_sql},
                    "fields": {"field": {"$": fields}},
                }
            },
        }
        
        # Se base_url não foi fornecido, tenta obter do util.get_header().current_host
        if not base_url:
            util = BiaUtil(self.mcp)
            header = util.get_header()
            base_url = getattr(header, "current_host", None)

        if not base_url:
            raise ValueError("base_url não definida e não foi possível obter current_host do header.")


        return self.call_json(
            payload=body,
            jsessionid=jsessionid,
            url=url,
            base_url=base_url,
            query=query,
            method="POST",
            extra_headers=extra_headers,
        )

    # -------------------------
    # Compat com scaffold
    # -------------------------
    @staticmethod
    def Call(
        jsessionID: Optional[str] = None,
        *,
        payload: Optional[Dict[str, Any]] = None,
        mcp: Optional[FastMCP] = None,
        url: Optional[str] = None,
        base_url: Optional[str] = None,
        query: Optional[str] = None,
        method: str = "POST",
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Optional[dict]:
        """
        Método estático compatível com o scaffold original.
        Permite chamada rápida ao serviço Sankhya sem instanciar manualmente a classe.

        Exemplos de uso:
            Sankhya.Call(jsessionID="...", payload={...}, query="serviceName=...&outputType=json")
            Sankhya.Call(jsessionID=None, mcp=mcp, payload={...}, query="...")

        Args:
            jsessionID: Token de sessão JSESSIONID (opcional).
            payload: Corpo da requisição (dict).
            mcp: Instância opcional do FastMCP para contexto do runtime.
            url: URL completa (opcional).
            base_url: Base URL alternativa (opcional).
            query: Querystring adicional (opcional).
            method: "POST" ou "GET".
            extra_headers: Headers adicionais.

        Returns:
            dict: Resposta do serviço ou lança erro se HTTP != 200.
        """
        sk = Sankhya(mcp=mcp)
        return sk.call_json(
            payload=payload,
            jsessionid=jsessionID,
            url=url,
            base_url=base_url,
            query=query,
            method=method,
            extra_headers=extra_headers,
        )


__all__ = ["Sankhya", "SankhyaSettings", "SankhyaHTTPError"]
