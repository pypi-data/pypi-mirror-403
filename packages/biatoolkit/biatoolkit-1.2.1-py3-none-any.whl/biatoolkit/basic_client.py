"""
biatoolkit.basic_client

Este módulo contém o BiaClient, um cliente HTTP assíncrono para comunicação
com servidores MCP (Model Context Protocol).

Responsabilidades:
- Abrir e gerenciar conexões HTTP streamable com servidores MCP.
- Inicializar sessões MCP.
- Encapsular chamadas comuns (listar tools, executar tool).

O objetivo é esconder os detalhes de sessão, streams e inicialização,
expondo uma API simples para quem consome a biblioteca.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Optional, Dict

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from .settings import BiaToolkitSettings


class BiaClient:
    """
    Cliente básico para interação com servidores MCP.

    Esta classe encapsula toda a complexidade envolvida em:
    - Abrir conexões HTTP streamable
    - Criar e inicializar ClientSession
    - Executar chamadas MCP

    Exemplos de uso:
        client = BiaClient("http://localhost:8000")
        tools = await client.list_tools()
        result = await client.call_tool("minha_tool", {"x": 1})
    """

    def __init__(
        self,
        url: str = "http://0.0.0.0:8000/mcp",
        headers: Optional[Dict[str, str]] = None,
        settings: Optional[BiaToolkitSettings] = None,
    ):
        """
        Inicializa o cliente MCP.

        Args:
            url:
                URL base do servidor MCP.
                - Se não terminar com '/mcp', o sufixo será adicionado automaticamente.
            headers:
                Headers HTTP opcionais enviados em todas as requisições.
                Normalmente usados para enviar contexto (runtime, autenticação, etc.).
            settings:
                Configurações opcionais da biblioteca (timeout, etc.).
                Se None, carrega defaults e overrides via variáveis de ambiente.
        """
        # Carrega configurações globais (timeout, etc.)
        self.settings = settings or BiaToolkitSettings.from_env()

        # Garante que a URL termine com '/mcp'
        suffix = "/mcp"
        self.url = url if url.endswith(suffix) else f"{url}{suffix}"

        # Headers HTTP que serão enviados para o servidor MCP
        self.headers = headers

    async def _with_session(self, fn: Callable[[ClientSession], Awaitable[Any]]) -> Any:
        """
        Executa uma função dentro de uma sessão MCP já inicializada.

        Este método centraliza todo o boilerplate necessário para:
        - Abrir a conexão HTTP streamable
        - Criar a ClientSession
        - Chamar session.initialize()
        - Garantir fechamento correto dos recursos

        Ele recebe uma função (callback) que recebe a ClientSession e
        executa a lógica específica (listar tools, chamar tool, etc.).

        Args:
            fn: Função assíncrona que recebe uma ClientSession.

        Returns:
            O valor retornado pela função fn.
        """
        async with streamablehttp_client(
            self.url,
            self.headers,
            # Timeout configurável via settings
            timeout=self.settings.client_timeout_seconds,
            # Mantém o servidor ativo mesmo após fechar streams
            terminate_on_close=False,
        ) as (read_stream, write_stream, _):

            # Cria a sessão MCP usando os streams
            async with ClientSession(read_stream, write_stream) as session:
                # Inicialização obrigatória do protocolo MCP
                await session.initialize()

                # Executa a lógica específica passada pelo caller
                return await fn(session)

    async def list_tools(self) -> dict:
        """
        Lista todas as ferramentas (tools) disponíveis no servidor MCP.

        Returns:
            dict: Estrutura contendo as tools expostas pelo servidor.
        """

        async def _call(session: ClientSession) -> Any:
            return await session.list_tools()

        return await self._with_session(_call)

    async def call_tool(self, tool_name: str, params: dict = None) -> dict:
        """
        Executa uma ferramenta específica disponível no servidor MCP.

        Args:
            tool_name:
                Nome da tool a ser executada (exatamente como exposta pelo servidor).
            params:
                Parâmetros da tool, enviados como dicionário.
                Pode ser None se a tool não exigir parâmetros.

        Returns:
            dict: Resultado da execução da tool.
        """

        async def _call(session: ClientSession) -> Any:
            return await session.call_tool(tool_name, params)

        return await self._with_session(_call)


__all__ = ["BiaClient"]
