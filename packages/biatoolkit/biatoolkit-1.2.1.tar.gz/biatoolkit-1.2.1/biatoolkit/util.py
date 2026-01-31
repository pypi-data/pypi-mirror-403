"""
biatoolkit.util

Este módulo contém a classe BiaUtil, uma "fachada" (facade) com utilidades comuns
para MCP Servers no ecossistema Bia Agent Builder.

Responsabilidades principais:
- Ler e interpretar headers padronizados enviados no runtime (AWS Bedrock AgentCore).
- Buscar parâmetros de configuração/segredos primeiro no ambiente (.env/variáveis),
  e como fallback no AWS SSM Parameter Store (cofre de segredos no ambiente produtivo).
"""

from typing import Optional
import os

import boto3
from mcp.server.fastmcp import FastMCP

from .settings import BiaToolkitSettings
from .schema.header import Header


class BiaUtil:
    """
    Classe utilitária para uso dentro de um MCP Server.

    Exemplos de uso:
        util = BiaUtil(mcp)
        header = util.get_header()
        token = util.get_parameter("MEU_TOKEN")

    Observações:
    - Esta classe depende do contexto de requisição do FastMCP (mcp.get_context()).
    - Em produção (AgentCore), apenas alguns headers são repassados pelo runtime.
    """

    # Prefixo base dos headers customizados aceitos no runtime do AgentCore.
    # Exemplo de header final: "x-amzn-bedrock-agentcore-runtime-custom-user-email"
    HEADER_PREFIX = "x-amzn-bedrock-agentcore-runtime-custom"

    def __init__(self, mcp: FastMCP, settings: Optional[BiaToolkitSettings] = None):
        """
        Inicializa o utilitário.

        Args:
            mcp: Instância do FastMCP, usada para acessar o contexto da requisição.
            settings: Configurações opcionais (region, timeout, header_prefix).
                      Se None, carrega defaults e overrides via variáveis de ambiente.
        """
        self.mcp = mcp

        # Settings podem vir explicitamente (testes/uso avançado) ou via environment.
        self.settings = settings or BiaToolkitSettings.from_env()

        # Permite sobrescrever o prefixo dos headers via settings.
        # Mantém compatibilidade: self.HEADER_PREFIX é usado na composição das chaves.
        self.HEADER_PREFIX = self.settings.header_prefix

    def _headers(self) -> dict:
        """
        Obtém o dicionário de headers da requisição atual via contexto do MCP.

        Returns:
            dict: Headers presentes na requisição (ou {} se ausentes).
        """
        ctx = self.mcp.get_context()
        # Estrutura esperada no FastMCP: ctx.request_context.request.headers
        return ctx.request_context.request.headers or {}

    def _h(self, suffix: str):
        """
        Lê um header customizado do runtime, dado o sufixo.

        Exemplo:
            suffix="user-email" -> lê "x-amzn-bedrock-agentcore-runtime-custom-user-email"

        Args:
            suffix: Parte final do nome do header.

        Returns:
            O valor do header (str) ou None.
        """
        return self._headers().get(f"{self.HEADER_PREFIX}-{suffix}", None)

    def _to_int(self, value, default: int = 0) -> int:
        """
        Converte um valor para int de forma segura.

        Por quê:
        - Headers podem vir como None, string vazia ou valores inválidos ("abc").
        - Este método evita exceptions e padroniza o fallback para 'default'.

        Args:
            value: valor a converter.
            default: valor retornado caso não seja possível converter.

        Returns:
            int: valor convertido ou default.
        """
        try:
            if value is None:
                return default
            if isinstance(value, str) and value.strip() == "":
                return default
            return int(value)
        except (TypeError, ValueError):
            return default

    def __get_from_ssm(self, parameter_name: str) -> str:
        """
        Busca o valor de um parâmetro no AWS SSM Parameter Store.

        Como funciona:
        - O runtime envia um header "...-prefix" que define a "pasta" (path) base dos segredos.
        - O nome final do parâmetro no SSM fica: "{prefix}/{parameter_name}"
        - WithDecryption=True permite ler SecureString.

        Importante:
        - Se não houver prefix no header, retorna None (não tenta chamar AWS).
          Isso evita chamadas inválidas como "None/MEU_PARAM".

        Args:
            parameter_name: Nome do parâmetro a ser buscado.

        Returns:
            str | None: Valor do parâmetro, ou None se não encontrado/sem prefix.
        """
        # Obtém headers do contexto do MCP
        headers = self._headers()

        # Prefixo customizado do header que aponta para a "pasta" de segredos
        prefix = headers.get(f"{self.HEADER_PREFIX}-prefix", None)

        # Sem prefix não é possível montar o path no SSM; evita chamadas inválidas.
        if not prefix:
            return None

        # Cria cliente SSM na região configurada (default: sa-east-1)
        client = boto3.client("ssm", region_name=self.settings.aws_region)

        try:
            response = client.get_parameter(
                Name=f"{prefix}/{parameter_name}",
                WithDecryption=True,
            )
        except client.exceptions.ParameterNotFound:
            # Retorna None se o parâmetro não existir no SSM
            return None

        # Estrutura da resposta: {"Parameter": {"Value": "..."}}
        return response.get("Parameter", {}).get("Value")

    def get_header(self) -> Header:
        """
        Extrai e retorna um objeto Header com os principais campos do runtime.

        Returns:
            Header: dataclass/objeto com os campos interpretados do header.
        """
        return Header(
            # Strings (podem ser None)
            current_host=self._h("current-host"),
            user_email=self._h("user-email"),
            jwt_token=self._h("jwt-token"),
            jsessionid=self._h("jsessionid"),

            # Inteiros (com fallback seguro para 0)
            organization_id=self._to_int(self._h("organization-id"), 0),
            codparc=self._to_int(self._h("codparc"), 0),
            iam_user_id=self._to_int(self._h("iam-user-id"), 0),

            # String (pode ser None)
            gateway_token=self._h("gateway-token"),
        )

    def get_parameter(self, parameter_name: str) -> str:
        """
        Recupera um parâmetro sensível/configurável.

        Ordem de resolução:
        1) Variáveis de ambiente (ideal para execução local / CI)
        2) AWS SSM Parameter Store (ideal para produção via cofre)

        Observação:
        - Implementação evita avaliar SSM antecipadamente.
          (Não usamos mais os.getenv(name, default_func()) porque chamaria AWS sempre.)

        Args:
            parameter_name: Nome do parâmetro.

        Returns:
            str | None: valor encontrado ou None.
        """
        value = self._get_from_env(parameter_name)
        if value is not None:
            return value
        return self._get_from_stores(parameter_name)

    def _get_from_env(self, parameter_name: str):
        """
        Provider interno: busca em variáveis de ambiente do sistema.

        Args:
            parameter_name: Nome do parâmetro.

        Returns:
            str | None
        """
        return os.getenv(parameter_name)

    def _get_from_stores(self, parameter_name: str):
        """
        Provider interno: busca em fontes externas (hoje apenas SSM).

        Este método existe para facilitar manutenção e evolução:
        amanhã pode incluir outros provedores (Secrets Manager, Vault, etc.)
        sem mudar a API pública de get_parameter().

        Args:
            parameter_name: Nome do parâmetro.

        Returns:
            str | None
        """
        return self.__get_from_ssm(parameter_name)


__all__ = ["BiaUtil"]
