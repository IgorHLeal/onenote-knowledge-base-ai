import json
import os
import re
import time

import msal
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# CONFIGURAÇÕES
# ============================================================

CLIENT_ID = os.getenv("ONENOTE_CLIENT_ID", "").strip()
TENANT_ID = os.getenv("ONENOTE_TENANT_ID", "").strip()

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"

SCOPES = [
    "Notes.Read.All"
]

GRAPH_URL = "https://graph.microsoft.com/v1.0"


# ============================================================
# DIRETÓRIOS E ARQUIVOS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

CACHE_FILE = os.path.join(
    BASE_DIR,
    ".token_cache.json"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "output"
)

PAGINAS_DIR = os.path.join(
    OUTPUT_DIR,
    "paginas"
)

INVENTARIO_FILE = os.path.join(
    OUTPUT_DIR,
    "inventario.json"
)

CHECKPOINT_FILE = os.path.join(
    OUTPUT_DIR,
    "checkpoint.json"
)

BASE_BRUTA_FILE = os.path.join(
    OUTPUT_DIR,
    "base_bruta.json"
)

ERROS_FILE = os.path.join(
    OUTPUT_DIR,
    "erros_extracao.json"
)


# ============================================================
# FONTES ONENOTE
# ============================================================

CONFIG_DIR = os.path.join(BASE_DIR, "config")
FONTES_CONFIG_FILE = os.path.join(CONFIG_DIR, "fontes.json")


def carregar_fontes_config():
    if not os.path.exists(FONTES_CONFIG_FILE):
        raise FileNotFoundError(
            "Arquivo config/fontes.json não encontrado. "
            "Copie config/fontes.example.json para config/fontes.json "
            "e informe as contas que possuem os notebooks do OneNote."
        )

    with open(FONTES_CONFIG_FILE, "r", encoding="utf-8-sig") as arquivo:
        dados = json.load(arquivo)

    fontes = dados.get("fontes", dados) if isinstance(dados, dict) else dados

    if not isinstance(fontes, list) or not fontes:
        raise ValueError("config/fontes.json deve conter uma lista não vazia de fontes.")

    for fonte in fontes:
        if not isinstance(fonte, dict) or not fonte.get("nome") or not fonte.get("usuario"):
            raise ValueError("Cada fonte deve possuir os campos 'nome' e 'usuario'.")

    return fontes


FONTES_ONENOTE = carregar_fontes_config()


NOTEBOOKS_EXCLUIDOS = {
    "OTIMIZA - GESTÃO DE EQUIPE"
}


# ============================================================
# CACHE DE AUTENTICAÇÃO
# ============================================================

def carregar_cache_token():

    cache = msal.SerializableTokenCache()

    if not os.path.exists(CACHE_FILE):
        return cache

    try:

        with open(
            CACHE_FILE,
            "r",
            encoding="utf-8"
        ) as arquivo:

            conteudo = arquivo.read()

        if conteudo:
            cache.deserialize(conteudo)

    except Exception as erro:

        print(
            "Aviso: não foi possível carregar "
            "o cache de autenticação."
        )

        print(
            f"Detalhes: {erro}"
        )

    return cache


def salvar_cache_token(cache):

    try:

        with open(
            CACHE_FILE,
            "w",
            encoding="utf-8"
        ) as arquivo:

            arquivo.write(
                cache.serialize()
            )

    except Exception as erro:

        print(
            "Não foi possível salvar "
            "o cache de autenticação."
        )

        print(
            f"Detalhes: {erro}"
        )


# ============================================================
# AUTENTICAÇÃO
# ============================================================

def autenticar():

    if not CLIENT_ID or not TENANT_ID:
        raise RuntimeError(
            "Defina ONENOTE_CLIENT_ID e ONENOTE_TENANT_ID no arquivo .env "
            "antes de executar o extrator."
        )

    print()
    print("=" * 60)
    print("AUTENTICAÇÃO MICROSOFT")
    print("=" * 60)
    print()

    cache = carregar_cache_token()

    app = msal.PublicClientApplication(
        client_id=CLIENT_ID,
        authority=AUTHORITY,
        token_cache=cache
    )

    accounts = app.get_accounts()

    # --------------------------------------------------------
    # TENTA AUTENTICAÇÃO SILENCIOSA
    # --------------------------------------------------------

    if accounts:

        print(
            "Sessão Microsoft encontrada."
        )

        print(
            "Tentando autenticação silenciosa..."
        )

        result = app.acquire_token_silent(
            SCOPES,
            account=accounts[0]
        )

        salvar_cache_token(cache)

        if (
            result
            and "access_token" in result
        ):

            print(
                "Autenticação realizada "
                "silenciosamente."
            )

            return result["access_token"]

        print(
            "A sessão armazenada não pôde "
            "ser reutilizada."
        )

    # --------------------------------------------------------
    # LOGIN INTERATIVO
    # --------------------------------------------------------

    print(
        "Será necessário realizar o login."
    )

    print()

    flow = app.initiate_device_flow(
        scopes=SCOPES
    )

    if "user_code" not in flow:

        raise RuntimeError(
            "Não foi possível iniciar "
            "o fluxo de autenticação."
        )

    print(
        flow["message"]
    )

    print()

    result = app.acquire_token_by_device_flow(
        flow
    )

    if "access_token" not in result:

        print(
            "Erro na autenticação:"
        )

        print(result)

        raise RuntimeError(
            "Não foi possível obter "
            "o token de acesso."
        )

    salvar_cache_token(
        cache
    )

    print(
        "Autenticação realizada com sucesso!"
    )

    return result["access_token"]


# ============================================================
# MICROSOFT GRAPH - JSON
# ============================================================

def graph_get(
    token,
    url,
    tentativas=5
):

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    for tentativa in range(
        1,
        tentativas + 1
    ):

        try:

            response = requests.get(
                url,
                headers=headers,
                timeout=60
            )

        except requests.RequestException as erro:

            if tentativa == tentativas:
                raise

            espera = min(
                2 ** tentativa,
                30
            )

            print(
                f"Erro de conexão: {erro}"
            )

            print(
                f"Nova tentativa em {espera}s..."
            )

            time.sleep(
                espera
            )

            continue

        if response.ok:

            return response.json()

        if response.status_code in {
            429,
            500,
            502,
            503,
            504
        }:

            espera = obter_tempo_retry(
                response,
                tentativa
            )

            print(
                f"Erro temporário "
                f"{response.status_code}. "
                f"Nova tentativa em {espera}s..."
            )

            time.sleep(
                espera
            )

            continue

        print()
        print("=" * 60)
        print("ERRO MICROSOFT GRAPH")
        print("=" * 60)

        print(
            "URL:",
            url
        )

        print(
            "Status:",
            response.status_code
        )

        print(
            response.text
        )

        response.raise_for_status()

    raise RuntimeError(
        f"Falha após {tentativas} tentativas: {url}"
    )


# ============================================================
# RETRY
# ============================================================

def obter_tempo_retry(
    response,
    tentativa
):

    retry_after = response.headers.get(
        "Retry-After"
    )

    if retry_after:

        try:

            return int(
                retry_after
            )

        except ValueError:
            pass

    return min(
        2 ** tentativa,
        30
    )


# ============================================================
# MICROSOFT GRAPH - HTML DA PÁGINA
# ============================================================

def obter_html_pagina(
    token,
    page_id,
    fonte_usuario,
    tentativas=5
):

    # IMPORTANTE:
    # usamos /users/{usuario} porque parte dos notebooks
    # pertence a outros usuários da organização.

    url = (
        f"{GRAPH_URL}"
        f"/users/{fonte_usuario}"
        f"/onenote/pages/{page_id}/content"
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "text/html"
    }

    for tentativa in range(
        1,
        tentativas + 1
    ):

        try:

            response = requests.get(
                url,
                headers=headers,
                timeout=60
            )

        except requests.RequestException as erro:

            if tentativa == tentativas:
                raise

            espera = min(
                2 ** tentativa,
                30
            )

            print(
                f"   Erro de conexão: {erro}"
            )

            print(
                f"   Nova tentativa em {espera}s..."
            )

            time.sleep(
                espera
            )

            continue

        if response.ok:

            return response.text

        # ----------------------------------------------------
        # ERROS TEMPORÁRIOS
        # ----------------------------------------------------

        if response.status_code in {
            429,
            500,
            502,
            503,
            504
        }:

            espera = obter_tempo_retry(
                response,
                tentativa
            )

            print(
                f"   Erro temporário "
                f"{response.status_code}. "
                f"Nova tentativa em {espera}s..."
            )

            time.sleep(
                espera
            )

            continue

        # ----------------------------------------------------
        # ERRO DEFINITIVO
        # ----------------------------------------------------

        response.raise_for_status()

    raise RuntimeError(
        f"Falha após {tentativas} tentativas "
        f"para a página {page_id}."
    )


# ============================================================
# HTML → TEXTO
# ============================================================

def html_para_texto(html):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    # Remove elementos sem valor para a base textual.

    for elemento in soup(
        [
            "script",
            "style"
        ]
    ):

        elemento.decompose()

    texto = soup.get_text(
        separator="\n"
    )

    linhas = [
        linha.strip()
        for linha in texto.splitlines()
        if linha.strip()
    ]

    return "\n".join(
        linhas
    )


# ============================================================
# NOME SEGURO PARA ARQUIVO WINDOWS
# ============================================================

def nome_arquivo_seguro(
    page_id
):

    nome = re.sub(
        r'[<>:"/\\|?*]',
        "_",
        page_id
    )

    return nome


# ============================================================
# JSON
# ============================================================

def carregar_json_seguro(
    caminho,
    valor_padrao
):

    if not os.path.exists(
        caminho
    ):

        return valor_padrao

    try:

        with open(
            caminho,
            "r",
            encoding="utf-8"
        ) as arquivo:

            return json.load(
                arquivo
            )

    except Exception as erro:

        print(
            f"Aviso: não foi possível carregar "
            f"{caminho}."
        )

        print(
            f"Detalhes: {erro}"
        )

        return valor_padrao


def salvar_json_atomico(
    dados,
    caminho
):

    os.makedirs(
        os.path.dirname(caminho),
        exist_ok=True
    )

    temporario = (
        caminho + ".tmp"
    )

    with open(
        temporario,
        "w",
        encoding="utf-8"
    ) as arquivo:

        json.dump(
            dados,
            arquivo,
            ensure_ascii=False,
            indent=2
        )

    os.replace(
        temporario,
        caminho
    )


# ============================================================
# CHECKPOINT
# ============================================================

def carregar_checkpoint():

    dados = carregar_json_seguro(
        CHECKPOINT_FILE,
        {
            "paginas_concluidas": []
        }
    )

    return set(
        dados.get(
            "paginas_concluidas",
            []
        )
    )


def salvar_checkpoint(
    paginas_concluidas
):

    salvar_json_atomico(
        {
            "paginas_concluidas":
                sorted(
                    paginas_concluidas
                )
        },
        CHECKPOINT_FILE
    )


# ============================================================
# PAGINAÇÃO
# ============================================================

def obter_todos(
    token,
    url
):

    resultados = []

    while url:

        dados = graph_get(
            token,
            url
        )

        resultados.extend(
            dados.get(
                "value",
                []
            )
        )

        url = dados.get(
            "@odata.nextLink"
        )

    return resultados


# ============================================================
# NOTEBOOKS DE UM USUÁRIO
# ============================================================

def listar_notebooks_usuario(
    token,
    usuario
):

    url = (
        f"{GRAPH_URL}"
        f"/users/{usuario}"
        f"/onenote/notebooks"
    )

    return obter_todos(
        token,
        url
    )


# ============================================================
# CARREGAR FONTES
# ============================================================

def carregar_fontes(
    token
):

    todos_notebooks = []

    notebooks_processados = set()

    for fonte in FONTES_ONENOTE:

        print()
        print("=" * 60)
        print(
            f"FONTE: {fonte['nome']}"
        )
        print("=" * 60)

        try:

            notebooks = listar_notebooks_usuario(
                token,
                fonte["usuario"]
            )

        except requests.HTTPError as erro:

            print(
                f"Não foi possível consultar "
                f"{fonte['nome']}."
            )

            print(
                erro
            )

            continue

        print(
            f"{len(notebooks)} "
            "notebook(s) encontrado(s)."
        )

        for notebook in notebooks:

            notebook_id = notebook.get(
                "id"
            )

            notebook_nome = notebook.get(
                "displayName"
            )

            print(
                f" - {notebook_nome}"
            )

            # ------------------------------------------------
            # EXCLUSÕES
            # ------------------------------------------------

            if (
                notebook_nome
                in NOTEBOOKS_EXCLUIDOS
            ):

                print(
                    "   [ignorado - fora do escopo]"
                )

                continue

            # ------------------------------------------------
            # DUPLICIDADE
            # ------------------------------------------------

            if (
                notebook_id
                in notebooks_processados
            ):

                print(
                    "   [duplicado - já processado]"
                )

                continue

            notebooks_processados.add(
                notebook_id
            )

            todos_notebooks.append(
                {
                    "fonte_nome":
                        fonte["nome"],

                    "fonte_usuario":
                        fonte["usuario"],

                    "notebook_id":
                        notebook_id,

                    "notebook_nome":
                        notebook_nome,

                    "notebook":
                        notebook
                }
            )

    return todos_notebooks


# ============================================================
# INVENTÁRIO - PÁGINAS DA SEÇÃO
# ============================================================

def listar_paginas_secao(
    token,
    secao
):

    pages_url = secao.get(
        "pagesUrl"
    )

    if not pages_url:
        return []

    return obter_todos(
        token,
        pages_url
    )


# ============================================================
# INVENTÁRIO - SEÇÃO
# ============================================================

def processar_secao(
    token,
    secao,
    caminho
):

    nome_secao = secao.get(
        "displayName",
        "Sem nome"
    )

    paginas = listar_paginas_secao(
        token,
        secao
    )

    print(
        f"{caminho} > {nome_secao}: "
        f"{len(paginas)} página(s)"
    )

    return {

        "nome":
            nome_secao,

        "id":
            secao.get("id"),

        "caminho":
            caminho,

        "total_paginas":
            len(paginas),

        "paginas": [

            {
                "id":
                    pagina.get("id"),

                "titulo":
                    pagina.get("title"),

                "criada_em":
                    pagina.get(
                        "createdDateTime"
                    ),

                "alterada_em":
                    pagina.get(
                        "lastModifiedDateTime"
                    )
            }

            for pagina in paginas
        ]
    }


# ============================================================
# INVENTÁRIO - GRUPOS DE SEÇÕES
# ============================================================

def processar_grupo_secao(
    token,
    grupo,
    caminho=""
):

    nome_grupo = grupo.get(
        "displayName",
        "Grupo sem nome"
    )

    caminho_atual = (
        f"{caminho} > {nome_grupo}"
        if caminho
        else nome_grupo
    )

    print()
    print(
        f"[Grupo] {caminho_atual}"
    )

    # --------------------------------------------------------
    # SEÇÕES DO GRUPO
    # --------------------------------------------------------

    sections_url = grupo.get(
        "sectionsUrl"
    )

    secoes = []

    if sections_url:

        secoes = obter_todos(
            token,
            sections_url
        )

    secoes_processadas = []

    for secao in secoes:

        resultado = processar_secao(
            token,
            secao,
            caminho_atual
        )

        secoes_processadas.append(
            resultado
        )

    # --------------------------------------------------------
    # SUBGRUPOS
    # --------------------------------------------------------

    section_groups_url = grupo.get(
        "sectionGroupsUrl"
    )

    subgrupos = []

    if section_groups_url:

        subgrupos = obter_todos(
            token,
            section_groups_url
        )

    subgrupos_processados = []

    for subgrupo in subgrupos:

        resultado = processar_grupo_secao(
            token,
            subgrupo,
            caminho_atual
        )

        subgrupos_processados.append(
            resultado
        )

    # --------------------------------------------------------
    # TOTAL
    # --------------------------------------------------------

    total_paginas = sum(
        secao["total_paginas"]
        for secao in secoes_processadas
    )

    total_paginas += sum(
        grupo_item["total_paginas"]
        for grupo_item
        in subgrupos_processados
    )

    return {

        "nome":
            nome_grupo,

        "id":
            grupo.get("id"),

        "caminho":
            caminho_atual,

        "secoes":
            secoes_processadas,

        "subgrupos":
            subgrupos_processados,

        "total_paginas":
            total_paginas
    }


# ============================================================
# INVENTÁRIO - NOTEBOOK
# ============================================================

def inventariar_notebook(
    token,
    item
):

    notebook = item[
        "notebook"
    ]

    nome_notebook = item[
        "notebook_nome"
    ]

    print()
    print("=" * 60)
    print(
        f"NOTEBOOK: {nome_notebook}"
    )
    print(
        f"FONTE: {item['fonte_nome']}"
    )
    print("=" * 60)

    # --------------------------------------------------------
    # SEÇÕES DIRETAS
    # --------------------------------------------------------

    sections_url = notebook.get(
        "sectionsUrl"
    )

    secoes = []

    if sections_url:

        secoes = obter_todos(
            token,
            sections_url
        )

    secoes_processadas = []

    for secao in secoes:

        resultado = processar_secao(
            token,
            secao,
            nome_notebook
        )

        secoes_processadas.append(
            resultado
        )

    # --------------------------------------------------------
    # GRUPOS
    # --------------------------------------------------------

    groups_url = notebook.get(
        "sectionGroupsUrl"
    )

    grupos = []

    if groups_url:

        grupos = obter_todos(
            token,
            groups_url
        )

    grupos_processados = []

    for grupo in grupos:

        resultado = processar_grupo_secao(
            token,
            grupo,
            nome_notebook
        )

        grupos_processados.append(
            resultado
        )

    # --------------------------------------------------------
    # TOTAL
    # --------------------------------------------------------

    total_paginas = sum(
        secao["total_paginas"]
        for secao
        in secoes_processadas
    )

    total_paginas += sum(
        grupo["total_paginas"]
        for grupo
        in grupos_processados
    )

    print()
    print(
        f"Total de páginas: "
        f"{total_paginas}"
    )

    return {

        "fonte_nome":
            item["fonte_nome"],

        "fonte_usuario":
            item["fonte_usuario"],

        "notebook_nome":
            nome_notebook,

        "notebook_id":
            item["notebook_id"],

        "secoes":
            secoes_processadas,

        "grupos":
            grupos_processados,

        "total_paginas":
            total_paginas
    }


# ============================================================
# SALVAR INVENTÁRIO
# ============================================================

def salvar_inventario(
    inventario
):

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    salvar_json_atomico(
        inventario,
        INVENTARIO_FILE
    )

    print()
    print(
        "Inventário salvo em:"
    )

    print(
        INVENTARIO_FILE
    )


# ============================================================
# CARREGAR INVENTÁRIO
# ============================================================

def carregar_inventario():

    if not os.path.exists(
        INVENTARIO_FILE
    ):

        raise FileNotFoundError(
            "O arquivo inventario.json "
            "não foi encontrado."
        )

    with open(
        INVENTARIO_FILE,
        "r",
        encoding="utf-8"
    ) as arquivo:

        return json.load(
            arquivo
        )


# ============================================================
# COLETAR SEÇÕES DOS GRUPOS
# ============================================================

def coletar_secoes_grupo(
    grupo
):

    secoes = list(
        grupo.get(
            "secoes",
            []
        )
    )

    for subgrupo in grupo.get(
        "subgrupos",
        []
    ):

        secoes.extend(
            coletar_secoes_grupo(
                subgrupo
            )
        )

    return secoes


def coletar_todas_secoes(
    notebook
):

    secoes = list(
        notebook.get(
            "secoes",
            []
        )
    )

    for grupo in notebook.get(
        "grupos",
        []
    ):

        secoes.extend(
            coletar_secoes_grupo(
                grupo
            )
        )

    return secoes


# ============================================================
# EXTRAÇÃO DAS PÁGINAS
# ============================================================

def extrair_conteudo_paginas(
    token,
    inventario,
    limite=None
):

    os.makedirs(
        PAGINAS_DIR,
        exist_ok=True
    )

    # --------------------------------------------------------
    # CARREGA ESTADO ANTERIOR
    # --------------------------------------------------------

    base_bruta = carregar_json_seguro(
        BASE_BRUTA_FILE,
        []
    )

    erros = carregar_json_seguro(
        ERROS_FILE,
        []
    )

    paginas_concluidas = (
        carregar_checkpoint()
    )

    # --------------------------------------------------------
    # INDEXA BASE JÁ EXISTENTE
    # --------------------------------------------------------

    indice_base_bruta = {}

    for indice, item in enumerate(
        base_bruta
    ):

        page_id_existente = item.get(
            "page_id"
        )

        if page_id_existente:

            indice_base_bruta[
                page_id_existente
            ] = indice

    ids_base_bruta = set(
        indice_base_bruta.keys()
    )

    # --------------------------------------------------------
    # GARANTE CONSISTÊNCIA ENTRE CHECKPOINT E BASE
    # --------------------------------------------------------

    paginas_concluidas = (
        paginas_concluidas
        & ids_base_bruta
    )

    salvar_checkpoint(
        paginas_concluidas
    )

    # --------------------------------------------------------
    # TOTALIZAÇÃO
    # --------------------------------------------------------

    total_geral = inventario[
        "total_paginas"
    ]

    processadas_nesta_execucao = 0
    visitadas = 0

    print()
    print(
        f"Checkpoint encontrado: "
        f"{len(paginas_concluidas)} "
        "página(s) concluída(s)."
    )

    print()

    # --------------------------------------------------------
    # NOTEBOOKS
    # --------------------------------------------------------

    for notebook in inventario[
        "notebooks"
    ]:

        secoes = coletar_todas_secoes(
            notebook
        )

        # ----------------------------------------------------
        # SEÇÕES
        # ----------------------------------------------------

        for secao in secoes:

            # ------------------------------------------------
            # PÁGINAS
            # ------------------------------------------------

            for pagina in secao[
                "paginas"
            ]:

                visitadas += 1

                page_id = pagina.get(
                    "id"
                )

                titulo = (
                    pagina.get(
                        "titulo"
                    )
                    or "Sem título"
                )

                if not page_id:

                    print()
                    print(
                        f"[{visitadas}/{total_geral}] "
                        f"{titulo}"
                    )

                    print(
                        "   ERRO: página sem ID."
                    )

                    continue

                # --------------------------------------------
                # JÁ PROCESSADA
                # --------------------------------------------

                if (
                    page_id
                    in paginas_concluidas
                ):

                    print(
                        f"[{visitadas}/{total_geral}] "
                        f"{notebook['notebook_nome']} "
                        f"> {secao['nome']} "
                        f"> {titulo}"
                    )

                    print(
                        "   IGNORADA "
                        "(já concluída)"
                    )

                    continue

                # --------------------------------------------
                # LIMITE PARA TESTES
                # --------------------------------------------

                if (
                    limite is not None
                    and
                    processadas_nesta_execucao
                    >= limite
                ):

                    print()
                    print(
                        "Limite desta execução atingido."
                    )

                    return (
                        base_bruta,
                        erros,
                        paginas_concluidas
                    )

                print()
                print(
                    f"[{visitadas}/{total_geral}] "
                    f"{notebook['notebook_nome']} "
                    f"> {secao['nome']} "
                    f"> {titulo}"
                )

                # --------------------------------------------
                # EXTRAÇÃO
                # --------------------------------------------

                try:

                    html = obter_html_pagina(
                        token,
                        page_id,
                        notebook[
                            "fonte_usuario"
                        ]
                    )

                    texto = html_para_texto(
                        html
                    )

                    nome_arquivo = (
                        nome_arquivo_seguro(
                            page_id
                        )
                    )

                    caminho_html = os.path.join(
                        PAGINAS_DIR,
                        f"{nome_arquivo}.html"
                    )

                    # ----------------------------------------
                    # SALVA HTML
                    # ----------------------------------------

                    with open(
                        caminho_html,
                        "w",
                        encoding="utf-8"
                    ) as arquivo:

                        arquivo.write(
                            html
                        )

                    # ----------------------------------------
                    # MONTA REGISTRO
                    # ----------------------------------------

                    registro = {

                        "fonte":
                            notebook[
                                "fonte_nome"
                            ],

                        "fonte_usuario":
                            notebook[
                                "fonte_usuario"
                            ],

                        "notebook":
                            notebook[
                                "notebook_nome"
                            ],

                        "notebook_id":
                            notebook[
                                "notebook_id"
                            ],

                        "caminho":
                            secao[
                                "caminho"
                            ],

                        "secao":
                            secao[
                                "nome"
                            ],

                        "titulo":
                            titulo,

                        "page_id":
                            page_id,

                        "criada_em":
                            pagina.get(
                                "criada_em"
                            ),

                        "alterada_em":
                            pagina.get(
                                "alterada_em"
                            ),

                        "conteudo_texto":
                            texto,

                        "arquivo_html":
                            os.path.relpath(
                                caminho_html,
                                OUTPUT_DIR
                            )
                    }

                    # ----------------------------------------
                    # ADICIONA OU ATUALIZA REGISTRO
                    # ----------------------------------------

                    if (
                        page_id
                        in indice_base_bruta
                    ):

                        indice = (
                            indice_base_bruta[
                                page_id
                            ]
                        )

                        base_bruta[
                            indice
                        ] = registro

                    else:

                        base_bruta.append(
                            registro
                        )

                        indice_base_bruta[
                            page_id
                        ] = (
                            len(base_bruta)
                            - 1
                        )

                    # ----------------------------------------
                    # MARCA COMO CONCLUÍDA
                    # ----------------------------------------

                    paginas_concluidas.add(
                        page_id
                    )

                    # ----------------------------------------
                    # REMOVE ERRO ANTIGO DESSA PÁGINA
                    # ----------------------------------------

                    erros = [
                        item
                        for item in erros
                        if item.get(
                            "page_id"
                        ) != page_id
                    ]

                    # ----------------------------------------
                    # PERSISTÊNCIA IMEDIATA
                    # ----------------------------------------

                    salvar_json_atomico(
                        base_bruta,
                        BASE_BRUTA_FILE
                    )

                    salvar_json_atomico(
                        erros,
                        ERROS_FILE
                    )

                    salvar_checkpoint(
                        paginas_concluidas
                    )

                    print(
                        "   OK"
                    )

                    processadas_nesta_execucao += 1

                # --------------------------------------------
                # ERRO
                # --------------------------------------------

                except Exception as erro:

                    print(
                        f"   ERRO: {erro}"
                    )

                    # Remove erro anterior
                    # da mesma página.

                    erros = [
                        item
                        for item in erros
                        if item.get(
                            "page_id"
                        ) != page_id
                    ]

                    erros.append(
                        {
                            "page_id":
                                page_id,

                            "titulo":
                                titulo,

                            "fonte":
                                notebook[
                                    "fonte_nome"
                                ],

                            "fonte_usuario":
                                notebook[
                                    "fonte_usuario"
                                ],

                            "notebook":
                                notebook[
                                    "notebook_nome"
                                ],

                            "secao":
                                secao[
                                    "nome"
                                ],

                            "erro":
                                str(erro)
                        }
                    )

                    salvar_json_atomico(
                        erros,
                        ERROS_FILE
                    )

                # Pequena pausa entre chamadas.

                time.sleep(
                    0.1
                )

    return (
        base_bruta,
        erros,
        paginas_concluidas
    )


# ============================================================
# GERAR INVENTÁRIO NOVAMENTE
# ============================================================

def gerar_inventario(
    token
):

    print()
    print("=" * 60)
    print(
        "BUSCANDO FONTES DO ONENOTE"
    )
    print("=" * 60)

    notebooks = carregar_fontes(
        token
    )

    if not notebooks:

        raise RuntimeError(
            "Nenhum notebook foi encontrado."
        )

    print()
    print("=" * 60)
    print(
        "INVENTARIANDO BASES"
    )
    print("=" * 60)

    notebooks_inventariados = []

    for item in notebooks:

        resultado = inventariar_notebook(
            token,
            item
        )

        notebooks_inventariados.append(
            resultado
        )

    total_paginas = sum(
        notebook["total_paginas"]
        for notebook
        in notebooks_inventariados
    )

    inventario = {

        "total_notebooks":
            len(
                notebooks_inventariados
            ),

        "total_paginas":
            total_paginas,

        "notebooks":
            notebooks_inventariados
    }

    salvar_inventario(
        inventario
    )

    return inventario


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

def main():

    print()
    print("=" * 60)
    print(
        "ONENOTE KNOWLEDGE BASE EXTRACTOR"
    )
    print("=" * 60)

    # --------------------------------------------------------
    # AUTENTICAÇÃO
    # --------------------------------------------------------

    token = autenticar()

    # --------------------------------------------------------
    # INVENTÁRIO
    # --------------------------------------------------------

    print()
    print(
        "Carregando inventário..."
    )

    try:

        inventario = carregar_inventario()

    except FileNotFoundError:

        print()
        print(
            "Inventário não encontrado."
        )

        print(
            "Gerando inventário..."
        )

        inventario = gerar_inventario(
            token
        )

    print()

    print(
        f"{inventario['total_notebooks']} "
        "notebook(s)."
    )

    print(
        f"{inventario['total_paginas']} "
        "página(s) no inventário."
    )

    # --------------------------------------------------------
    # EXTRAÇÃO
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print(
        "INICIANDO EXTRAÇÃO"
    )
    print("=" * 60)

    (
        base_bruta,
        erros,
        paginas_concluidas
    ) = extrair_conteudo_paginas(
        token,
        inventario,
        limite=None
    )

    # --------------------------------------------------------
    # RESUMO
    # --------------------------------------------------------

    total_previsto = inventario[
        "total_paginas"
    ]

    total_concluido = len(
        paginas_concluidas
    )

    total_base = len(
        base_bruta
    )

    total_erros = len(
        erros
    )

    pendentes = (
        total_previsto
        - total_concluido
    )

    print()
    print("=" * 60)
    print(
        "RESUMO"
    )
    print("=" * 60)

    print(
        f"Páginas previstas: "
        f"{total_previsto}"
    )

    print(
        f"Páginas concluídas: "
        f"{total_concluido}"
    )

    print(
        f"Registros na base bruta: "
        f"{total_base}"
    )

    print(
        f"Erros registrados: "
        f"{total_erros}"
    )

    print(
        f"Páginas pendentes: "
        f"{pendentes}"
    )

    print()

    if (
        total_concluido
        == total_previsto
        and total_erros == 0
    ):

        print("=" * 60)
        print(
            "EXTRAÇÃO COMPLETA COM SUCESSO"
        )
        print("=" * 60)

    else:

        print("=" * 60)
        print(
            "EXTRAÇÃO CONCLUÍDA COM PENDÊNCIAS"
        )
        print("=" * 60)

        print()

        print(
            "Execute o programa novamente "
            "para tentar as páginas pendentes."
        )


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":
    main()
