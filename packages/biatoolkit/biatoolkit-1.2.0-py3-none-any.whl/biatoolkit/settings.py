"""
biatoolkit.settings

Este módulo centraliza todas as configurações globais da Bia Toolkit.

Objetivos:
- Evitar valores hardcoded espalhados pelo código.
- Permitir override simples via variáveis de ambiente.
- Facilitar testes, manutenção e futuras extensões.

Exemplos de override via environment:
    BIATOOLKIT_HEADER_PREFIX=x-amzn-bedrock-agentcore-runtime-custom
    BIATOOLKIT_AWS_REGION=us-east-1
    BIATOOLKIT_CLIENT_TIMEOUT_SECONDS=60
"""

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class BiaToolkitSettings:
    """
    Objeto imutável (frozen) que representa as configurações da biblioteca.

    Por que usar dataclass + frozen?
    - Facilita leitura e manutenção.
    - Garante que as configurações não sejam alteradas em runtime,
      evitando efeitos colaterais difíceis de rastrear.
    """

    # ------------------------------------------------------------------
    # Server / Headers
    # ------------------------------------------------------------------

    # Prefixo base dos headers customizados aceitos pelo runtime do AgentCore.
    # Exemplo final:
    #   x-amzn-bedrock-agentcore-runtime-custom-user-email
    header_prefix: str = "x-amzn-bedrock-agentcore-runtime-custom"

    # ------------------------------------------------------------------
    # AWS
    # ------------------------------------------------------------------

    # Região AWS usada para acessar serviços como SSM Parameter Store.
    # Default alinhado com o ambiente do Bia Agent Builder.
    aws_region: str = "sa-east-1"

    # ------------------------------------------------------------------
    # Client (MCP HTTP Client)
    # ------------------------------------------------------------------

    # Timeout padrão (em segundos) para chamadas HTTP ao servidor MCP.
    # Evita requests presos indefinidamente em ambientes instáveis.
    client_timeout_seconds: int = 120

    # ------------------------------------------------------------------
    # Factory methods
    # ------------------------------------------------------------------

    @staticmethod
    def from_env() -> "BiaToolkitSettings":
        """
        Cria uma instância de BiaToolkitSettings a partir de variáveis de ambiente.

        Comportamento:
        - Cada configuração pode ser sobrescrita individualmente via env.
        - Caso a variável não exista ou seja inválida, usa o valor default.

        Variáveis suportadas:
        - BIATOOLKIT_HEADER_PREFIX
        - BIATOOLKIT_AWS_REGION
        - BIATOOLKIT_CLIENT_TIMEOUT_SECONDS

        Returns:
            BiaToolkitSettings: instância configurada.
        """

        # Header prefix (string simples)
        header_prefix = os.getenv(
            "BIATOOLKIT_HEADER_PREFIX",
            "x-amzn-bedrock-agentcore-runtime-custom",
        )

        # Região AWS
        aws_region = os.getenv(
            "BIATOOLKIT_AWS_REGION",
            "sa-east-1",
        )

        # Timeout do client (conversão segura para int)
        timeout_str = os.getenv(
            "BIATOOLKIT_CLIENT_TIMEOUT_SECONDS",
            "120",
        )
        try:
            timeout = int(timeout_str)
        except ValueError:
            # Se o valor não for um inteiro válido, cai no default
            timeout = 120

        return BiaToolkitSettings(
            header_prefix=header_prefix,
            aws_region=aws_region,
            client_timeout_seconds=timeout,
        )
