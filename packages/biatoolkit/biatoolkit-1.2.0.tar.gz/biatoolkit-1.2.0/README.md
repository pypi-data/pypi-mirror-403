# Bia Toolkit

Biblioteca Python para facilitar o desenvolvimento de servidores MCP integrados ao Bia Agent Builder.

## **Execução Local**

1. Instale o [Python 3.10](https://www.python.org/downloads/).
2. (Opcional) Crie e ative um ambiente virtual:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

ou instale as dependências diretamente no Python do sistema operacional:

```bash
pip install -r requirements.txt
```

## **Execução do código localmente**

Como este projeto é uma **biblioteca de código**, não existe nenhum método ou arquivo principal. Você pode instanciar objetos e chamar diretamente os métodos que precisa executar, respeitando a assinatura e o comportamento de cada componente. Uma sugestão é criar um arquivo chamado **app.py** na raiz do projeto (que já está no .gitignore) e incluir as classes que deseja executar.

## **Fluxo de desenvolvimento no GitLab**

Para incluir ou alterar classes/métodos na biblioteca do **Bia Toolkit**, siga o fluxo abaixo no GitLab:

1. Crie uma nova branch a partir da branch **develop**.
2. Realize a inclusão ou alteração de classes/métodos localmente, executando o projeto na sua máquina utilizando o VSCode ou outra IDE de sua preferência.
3. Faça o commit/push do seu código para a sua branch recém-criada.
4. Ao finalizar o desenvolvimento e testar o código, crie um **Merge Request (MR)** da sua branch para a branch **develop** e solicite a revisão de um colega.
5. O revisor irá analisar o MR e, se estiver tudo certo, aprovará e fará o merge do seu código na branch **develop**.
6. Depois que o código for aprovado na branch **develop**, o revisor deverá fazer um merge request da branch **develop** para a branch **master**. Isso fará com que a esteira de deploy seja executada e, caso não ocorra nenhum erro, a nova versão da biblioteca **Bia Toolkit** será publicada no Pypi.

## **Principais classes da biblioteca**

Nesta seção você encontrará uma breve descrição de cada classe da biblioteca **Bia Toolkit**.

### **BiaClient**

A classe `BiaClient` tem o objetivo de criar um cliente HTTP para comunicação com servidores MCP (Model Context Protocol).

**Principais métodos**:

- **list_tools**: Lista todas as ferramentas disponíveis no servidor MCP.
- **call_tool**: Executa uma ferramenta específica no servidor MCP.

### **BiaUtil**

A classe `BiaUtil` fornece métodos auxiliares para gerenciar headers de requisições e parâmetros de configuração em servidores MCP.

#### Principais métodos

- **construtor**
  - Recebe uma instância de `FastMCP` para acessar o contexto da requisição atual.
  - Permite (opcionalmente) receber configurações via `BiaToolkitSettings`.

- **get_header()**
  - Extrai e retorna os headers customizados enviados pelo runtime do Bia Agent Builder.
  - Retorna um objeto `Header` tipado com os campos:
    - current_host
    - user_email
    - jwt_token
    - jsessionid
    - organization_id
    - codparc
    - iam_user_id
    - gateway_token

- **get_parameter(parameter_name: str)**
  - Recupera parâmetros sensíveis seguindo a seguinte ordem:
    1. Variáveis de ambiente do sistema
    2. AWS SSM Parameter Store (fallback)

  **Observações importantes:**
  - O SSM só é consultado se o parâmetro **não existir** nas variáveis de ambiente.
  - A consulta ao SSM depende do header  
    `X-Amzn-Bedrock-AgentCore-Runtime-Custom-prefix`.
  - Caso esse header não esteja presente, o método retorna `None`.

## Configuração da biblioteca (BiaToolkitSettings)

A biblioteca utiliza a classe `BiaToolkitSettings` para centralizar configurações
e permitir ajustes sem alteração de código.

Essas configurações podem ser sobrescritas via variáveis de ambiente.

### Parâmetros disponíveis

- **BIATOOLKIT_HEADER_PREFIX**
  - Prefixo dos headers enviados pelo runtime
  - Padrão: `x-amzn-bedrock-agentcore-runtime-custom`

- **BIATOOLKIT_AWS_REGION**
  - Região AWS utilizada para acesso ao SSM
  - Padrão: `sa-east-1`

- **BIATOOLKIT_CLIENT_TIMEOUT_SECONDS**
  - Timeout (em segundos) para chamadas HTTP do `BiaClient`
  - Padrão: `120`

### Exemplo

```bash
export BIATOOLKIT_AWS_REGION=us-east-1
export BIATOOLKIT_CLIENT_TIMEOUT_SECONDS=60
export BIATOOLKIT_HEADER_PREFIX=x-amzn-bedrock-agentcore-runtime-custom

## **Como utilizar**

Nesta seção você encontrará uma breve descrição de como utilizar os principais recursos da biblioteca **Bia Toolkit**.

### **Criando um MCP Server**

Primeiro, instale os pacotes **MCP** e **Bia Toolkit**.

```bash
pip install mcp biatoolkit
```

Crie um novo arquivo chamado `meu_mcp_server.py` com o seguinte conteúdo:

```python
from mcp.server.fastmcp import FastMCP
import json

mcp = FastMCP(host="0.0.0.0", stateless_http=True)

@mcp.tool()
def listar() -> str:
    """Retorna uma lista de exemplo"""
    exemplo = {
        "itens": [
            {"id": 1, "nome": "Item 1"},
            {"id": 2, "nome": "Item 2"},
            {"id": 3, "nome": "Item 3"},
        ]
    }
    return json.dumps(exemplo, indent=4, sort_keys=True)

@mcp.tool()
def adicionar(id: int, nome: str) -> str:
    """Adiciona um item à lista de exemplo"""
    novo_item = {"id": id, "nome": nome}
    return json.dumps(novo_item, indent=4, sort_keys=True)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
```

#### **Entendendo o código**

- **FastMCP**: Cria um servidor MCP que pode hospedar suas ferramentas.
- **@mcp.tool()**: Decorador que transforma suas funções Python em ferramentas MCP.
- **Tool**: Duas ferramentas simples que demonstram diferentes tipos de operação.

⚠️ **IMPORTANTE**: Para fazer o deploy no ambiente do Bia Agent Builder, o nome do arquivo, que neste exemplo é `meu_mcp_server.py`, será utilizado para gerar um `pacote Python`. Este pacote deverá ser `único` no Bia Agent Builder. Portanto, no deploy, caso este pacote `já exista` no Bia Agent Builder, você precisará renomear o seu arquivo.

#### **Iniciando o servidor localmente**

Para executar o seu servidor localmente:

```bash
python meu_mcp_server.py
```

Você deverá receber uma mensagem no console semelhante à imagem a seguir:

![Figura 01 - Servidor MCP executando localmente](img/img01.png)

#### **Como testar o servidor local**

Crie um novo arquivo chamado `local.py` com o seguinte conteúdo:

```python
import asyncio
from biatoolkit.basic_client import BiaClient

MCP_SERVER_URL = "http://0.0.0.0:8000/mcp"
client = BiaClient(MCP_SERVER_URL)

async def list_tools() -> None:
    tools = await client.list_tools()
    for tool in tools.tools:
        print(f"Tool: {tool.name}, Description: {tool.description}")


async def call_tool(tool_name: str, params: dict = None) -> None:
    result = await client.call_tool(tool_name, params)
    print(result.content[0].text)


async def main():
    await list_tools()
    

asyncio.run(main())
```

#### **Entendendo o código**

- **BiaClient**: É uma classe da biblioteca **Bia Toolkit** que encapsula um cliente HTTP para comunicação com servidores MCP.
- **list_tools**: Executa a instrução `client.list_tools()` para recuperar todas as ferramentas disponíveis no servidor MCP.
- **call_tool**: Executa a instrução `client.call_tool(tool_name, params)` para executar uma ferramenta específica do servidor MCP.

#### **Executando o código**

⚠️ Certifique-se de que o servidor MCP `meu_mcp_server.py` ainda esteja em execução.

Execute o arquivo `local.py` em outro terminal:

```bash
python local.py
```

Você deverá ver a saída no console semelhante a:

![Figura 02 - Cliente MCP listando tools do servidor](img/img02.png)

Caso deseje testar a execução de uma **tool**, basta alterar o método `main` conforme a seguir:

```python
async def main():
    await call_tool("adicionar", {"id": 4, "nome": "Novo item"})
```

Veja que o método `call_tool` possui dois parâmetros:

- O primeiro é o nome da tool que queremos executar.
- O segundo é um `dicionário` com os parâmetros da tool, sendo o segundo __(opcional)__ caso exista.

Ao executar o arquivo `local.py`, você deverá ver a saída no console semelhante a: 

![Figura 03 - Cliente MCP executando uma tool do servidor](img/img03.png)

### **Enviando parâmetros via header**

Se seu servidor MCP estiver sendo executado **localmente**, você conseguirá informar qualquer parâmetro no `header` da requisição. Entretanto, quando o seu servidor MCP estiver hospedado no ambiente de produção do **Bia Agent Builder** (AWS Bedrock AgentCore), apenas os parâmetros abaixo podem ser utilizados.

⚠️ QUALQUER OUTRO PARÂMETRO SERÁ IGNORADO PELO SERVIDOR. ⚠️

- **X-Amzn-Bedrock-AgentCore-Runtime-Custom-current-host**: Host do ERP no qual o copilot está em execução.
- **X-Amzn-Bedrock-AgentCore-Runtime-Custom-user-email**: Email do usuário autenticado.
- **X-Amzn-Bedrock-AgentCore-Runtime-Custom-jwt-token**: JWT token do usuário -> SankhyaID, SankhyaPass ou Token interno Bia.
- **X-Amzn-Bedrock-AgentCore-Runtime-Custom-jsessionid**: ID de autenticação do ERP.
- **X-Amzn-Bedrock-AgentCore-Runtime-Custom-organization-id**: ID da organização da Bia.
- **X-Amzn-Bedrock-AgentCore-Runtime-Custom-codparc**: Código do parceiro (parceiro Sankhya).
- **X-Amzn-Bedrock-AgentCore-Runtime-Custom-iam-user-id**: ID do usuário do BIA IAM.
- **X-Amzn-Bedrock-AgentCore-Runtime-Custom-gateway-token**: Token primário do Sankhya API Gateway.

```python
import asyncio
from biatoolkit.basic_client import BiaClient

MCP_SERVER_URL = "http://0.0.0.0:8000/mcp"

# Se seu servidor MCP estiver sendo executado **localmente**, você conseguirá informar qualquer parâmetro
# no `header` da requisição. Entretanto, quando o seu servidor MCP estiver hospedado no ambiente de produção
# do Bia Agent Builder (AWS Bedrock AgentCore), apenas os parâmetros abaixo podem ser utilizados.

# Ao utilizar os serviços de interação com a Bia (/agent/stream, /agent/message ou /agent/invoke), 
# os parâmetros abaixo já são automaticamente preenchidos e enviados pelos serviços.
headers = {
    "X-Amzn-Bedrock-AgentCore-Runtime-Custom-current-host": "current-host-123456", # Host do ERP no qual o copilot está em execução.
    "X-Amzn-Bedrock-AgentCore-Runtime-Custom-user-email": "user-email-123456", # Email do usuário autenticado.
    "X-Amzn-Bedrock-AgentCore-Runtime-Custom-jwt-token": "jwt-token-123456", # JWT token do usuário -> SankhyaID, SankhyaPass ou Token interno Bia.
    "X-Amzn-Bedrock-AgentCore-Runtime-Custom-jsessionid": "jsessionid-123456", # ID de autenticação do ERP.
    "X-Amzn-Bedrock-AgentCore-Runtime-Custom-organization-id": "123", # ID da organização da Bia.
    "X-Amzn-Bedrock-AgentCore-Runtime-Custom-codparc": "456", # Código do parceiro (parceiro Sankhya).
    "X-Amzn-Bedrock-AgentCore-Runtime-Custom-iam-user-id": "789", # ID do usuário do BIA IAM.
    "X-Amzn-Bedrock-AgentCore-Runtime-Custom-gateway-token": "gateway-token-123456", # Token primário do Sankhya API Gateway.
    "Content-Type": "application/json"
}

client = BiaClient(MCP_SERVER_URL, headers=headers)

async def list_tools() -> None:
    tools = await client.list_tools()
    for tool in tools.tools:
        print(f"Tool: {tool.name}, Description: {tool.description}")


async def call_tool(tool_name: str, params: dict = None) -> None:
    result = await client.call_tool(tool_name, params)
    print(result.content[0].text)


async def main():
    await call_tool("listar")
    
    
asyncio.run(main())
```

#### **Entendendo o código**

- **headers**: Veja que a variável `headers` é definida com a lista de parâmetros válidos e depois utilizada em `client = BiaClient(MCP_SERVER_URL, headers=headers)`.

⚠️ IMPORTANTE: Ao utilizar os serviços de interação com a Bia (**/agent/stream**, **/agent/message** ou **/agent/invoke**),  os parâmetros já são automaticamente preenchidos e enviados pelos serviços.

### **Recuperando os parâmetros no MCP Server enviados via header**

Para recuperar os parâmetros no MCP Server que foram enviados por meio do `header` da requisição, basta utilizar a classe `BiaUtil` conforme a seguir:

```python
from mcp.server.fastmcp import FastMCP
from biatoolkit.util import BiaUtil

mcp = FastMCP(host="0.0.0.0", stateless_http=True)

@mcp.tool()
def processar() -> str:
    """Executa o processamento de algo"""
    
    util = BiaUtil(mcp)
    header = util.get_header()

    # Exemplo de uso dos parâmetros do header. Utilize conforme a necessidade 
    # do seu processamento, como autenticação de endpoints, identificação, etc.
    
    print("Valor do parâmetro current_host:", header.current_host)
    print("Valor do parâmetro user_email:", header.user_email)
    print("Valor do parâmetro jwt_token:", header.jwt_token)
    print("Valor do parâmetro jsessionid:", header.jsessionid)
    print("Valor do parâmetro organization_id:", header.organization_id)
    print("Valor do parâmetro codparc:", header.codparc)
    print("Valor do parâmetro iam_user_id:", header.iam_user_id)
    print("Valor do parâmetro gateway_token:", header.gateway_token)
    
    return f"Processamento executado"

    
if __name__ == "__main__":
    mcp.run(transport="streamable-http")
```

### **Recuperando parâmetros do cofre de segredos**

Você pode utilizar parâmetros sensíveis de duas formas:

- Usando arquivos `.env` para execução local.
- Usando o cofre de segredos do Bia Agent Builder para execução em ambiente produtivo.
  - Você pode adicionar parâmetros sensíveis no cofre de segredos do Bia Agent Builder. Para adicionar, alterar e excluir os parâmetros do cofre, utilize as funcionalidades da Plataforma Bia Agent Builder UI.

Para recuperar um valor sensível no seu MCP Server, utilize o método `get_parameter(parameter_name: str)` da classe `BiaUtil`.

```python
from mcp.server.fastmcp import FastMCP
from biatoolkit.util import BiaUtil

mcp = FastMCP(host="0.0.0.0", stateless_http=True)

@mcp.tool()
def processar() -> str:
    """Executa o processamento de algo"""
    
    util = BiaUtil(mcp)
    valor = util.get_parameter("meu_parametro")

    # Exemplo de uso do parâmetro recuperado. Utilize conforme a necessidade 
    # do seu processamento, como autenticação de endpoints, identificação, etc.

    print("Valor do parâmetro:", valor)
    return f"Processamento executado"

    
if __name__ == "__main__":
    mcp.run(transport="streamable-http")
```

O método `get_parameter(parameter_name: str)` busca o parâmetro informado em duas fontes distintas. Primeiro, o método tenta buscar o parâmetro consultando as **variáveis de ambiente** do sistema. Caso não exista, o método tenta buscar o parâmetro na AWS SSM Parameter Store.
Essa busca depende da presença do header
`X-Amzn-Bedrock-AgentCore-Runtime-Custom-prefix`, que é automaticamente
fornecido em ambiente produtivo pelo Bia Agent Builder.

✅ Isso é vantajoso pois você pode armazenar o parâmetro em:

- Um arquivo `.env` para testes locais.
- No cofre de segredos do Bia Agent Builder para usar em ambiente produtivo. 


## **Validação e Coerção de Dados**

O Bia Toolkit oferece funções utilitárias para normalização, sanitização e coerção de dados, facilitando o consumo seguro de entradas vindas de APIs, headers, payloads e integrações legadas.


### **Validação de Dados** (`biatoolkit.validation.validation`)

Utilize a classe **BiaValidation** para acessar as funções de validação de forma padronizada:

- **BiaValidation.parse_int_list(value, dedupe=True, keep_order=True)**
  - Normaliza um valor arbitrário em uma lista de inteiros.
  - Suporta: None, int, str (extrai números), list/tuple (recursivo).
  - Ignora valores inválidos.
  - Deduplica e mantém ordem por padrão.
  - Exemplo:
    ```python
    from biatoolkit.validation.validation import BiaValidation
    BiaValidation.parse_int_list("SKU=300231 x2")  # [300231, 2]
    BiaValidation.parse_int_list([1, 2, 1, 3], dedupe=False)  # [1, 2, 1, 3]
    ```

- **BiaValidation.sanitize_like(value, max_len=80, upper=True)**
  - Sanitiza texto para uso seguro em filtros LIKE/search SQL.
  - Remove caracteres fora da allowlist, limita tamanho, escapa aspas simples, %, _ e normaliza espaços.
  - Converte para maiúsculas por padrão.
  - Exemplo:
    ```python
    from biatoolkit.validation.validation import BiaValidation
    BiaValidation.sanitize_like("O'Reilly")  # "O''REILLY"
    BiaValidation.sanitize_like("100%_OK")   # "100\\%\\_OK"
    ```

### **Coerção de Dados** (`biatoolkit.validation.coercion`)

Utilize a classe **BiaCoercion** para acessar as funções de coerção de forma padronizada:

- **BiaCoercion.ensure_list(value)**
  - Garante que o valor seja retornado como lista.
  - None → [], list → list, tuple/set → list, dict → [dict], outro → [valor].
  - Exemplo:
    ```python
    from biatoolkit.validation.coercion import BiaCoercion
    BiaCoercion.ensure_list(None)  # []
    BiaCoercion.ensure_list({"a": 1})  # [{"a": 1}]
    BiaCoercion.ensure_list(5)  # [5]
    ```

- **BiaCoercion.unwrap_dollar_value(value)**
  - Desembrulha valores no formato {"$": ...} (comum em integrações legadas).
  - Exemplo:
    ```python
    from biatoolkit.validation.coercion import BiaCoercion
    BiaCoercion.unwrap_dollar_value({"$": 123})  # 123
    BiaCoercion.unwrap_dollar_value("abc")  # "abc"
    ```

- **BiaCoercion.to_int(value, default=0)**
  - Converte valor para int de forma segura.
  - None, "", bool, NaN/inf → default.
  - Aceita strings numéricas, floats (trunca), etc.
  - Exemplo:
    ```python
    from biatoolkit.validation.coercion import BiaCoercion
    BiaCoercion.to_int(" 42 ")  # 42
    BiaCoercion.to_int(None, default=-1)  # -1
    ```

- **BiaCoercion.to_float(value, default=0.0)**
  - Converte valor para float de forma segura.
  - None, "", bool, NaN/inf → default.
  - Aceita strings com vírgula decimal.
  - Exemplo:
    ```python
    to_float("12,34")  # 12.34
    to_float("abc", default=-1.0)  # -1.0
    ```

Essas funções são úteis para garantir robustez e previsibilidade ao tratar dados vindos de múltiplas fontes, reduzindo erros e if/else espalhados pelo código.