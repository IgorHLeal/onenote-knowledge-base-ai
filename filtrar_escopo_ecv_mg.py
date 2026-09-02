import json
import os
import shutil
import unicodedata
from datetime import datetime


# ============================================================
# DIRETÓRIOS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

PROCESSAMENTO_DIR = os.path.join(
    BASE_DIR,
    "output",
    "processamento"
)

BASE_NORMALIZADA_FILE = os.path.join(
    PROCESSAMENTO_DIR,
    "base_normalizada.json"
)

BASE_COMPLETA_FILE = os.path.join(
    PROCESSAMENTO_DIR,
    "base_normalizada_completa.json"
)

BASE_ECV_MG_FILE = os.path.join(
    PROCESSAMENTO_DIR,
    "base_normalizada_ecv_mg.json"
)

RELATORIO_FILE = os.path.join(
    PROCESSAMENTO_DIR,
    "relatorio_filtro_ecv_mg.json"
)


# ============================================================
# ESCOPO DA BASE ECV MG
# ============================================================

NOTEBOOK_ALVO = "ECV MG"


# ============================================================
# IMPORTANTE
# ============================================================
#
# O Microsoft Graph continua retornando nomes antigos para
# duas seções do notebook ECV MG.
#
# Correspondência confirmada:
#
# Graph:
#   ERROS
#
# OneNote atual:
#   ERROS - SISTEMA
#
#
# Graph:
#   MENSAGENS PADRÃO
#
# OneNote atual:
#   PROCEDIMENTOS OPERACIONAIS
#
#
# Portanto, o filtro deve considerar os nomes retornados
# pelo Graph, mas a base filtrada deverá utilizar os nomes
# lógicos/atuais.
# ============================================================

SECOES_ALVO = {
    "ERROS",
    "MENSAGENS PADRAO"
}


MAPA_NOMES_SECOES = {

    "ERROS":
        "ERROS - SISTEMA",

    "MENSAGENS PADRAO":
        "PROCEDIMENTOS OPERACIONAIS"
}


# ============================================================
# NORMALIZAÇÃO
# ============================================================

def normalizar_texto(texto):

    if not isinstance(
        texto,
        str
    ):
        return ""

    texto = texto.strip().upper()

    texto = unicodedata.normalize(
        "NFD",
        texto
    )

    texto = "".join(
        caractere
        for caractere in texto
        if unicodedata.category(
            caractere
        ) != "Mn"
    )

    return texto


# ============================================================
# JSON
# ============================================================

def carregar_json(caminho):

    with open(
        caminho,
        "r",
        encoding="utf-8-sig"
    ) as arquivo:

        return json.load(
            arquivo
        )


def salvar_json(
    dados,
    caminho
):

    os.makedirs(
        os.path.dirname(
            caminho
        ),
        exist_ok=True
    )

    temporario = (
        caminho
        + ".tmp"
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
# CÓPIA SEGURA DE REGISTRO
# ============================================================

def copiar_registro(
    registro
):

    return json.loads(
        json.dumps(
            registro,
            ensure_ascii=False
        )
    )


# ============================================================
# FILTRO DE ESCOPO
# ============================================================

def registro_esta_no_escopo(
    registro
):

    origem = registro.get(
        "origem",
        {}
    )

    notebook = normalizar_texto(
        origem.get(
            "notebook"
        )
    )

    secao = normalizar_texto(
        origem.get(
            "secao"
        )
    )

    notebook_alvo = (
        normalizar_texto(
            NOTEBOOK_ALVO
        )
    )

    secoes_normalizadas = {
        normalizar_texto(
            item
        )
        for item in SECOES_ALVO
    }

    if notebook != notebook_alvo:

        return False

    if secao not in secoes_normalizadas:

        return False

    return True


# ============================================================
# AJUSTAR NOME LÓGICO DA SEÇÃO
# ============================================================

def ajustar_nome_secao(
    registro
):

    registro_filtrado = (
        copiar_registro(
            registro
        )
    )

    origem = (
        registro_filtrado
        .setdefault(
            "origem",
            {}
        )
    )

    secao_graph = (
        origem.get(
            "secao",
            ""
        )
        or ""
    )

    secao_normalizada = (
        normalizar_texto(
            secao_graph
        )
    )

    # --------------------------------------------------------
    # Preserva o nome originalmente retornado pelo Graph
    # --------------------------------------------------------

    origem[
        "secao_graph"
    ] = secao_graph

    # --------------------------------------------------------
    # Substitui o campo "secao" pelo nome atual/lógico
    # utilizado no OneNote.
    # --------------------------------------------------------

    origem[
        "secao"
    ] = (
        MAPA_NOMES_SECOES.get(
            secao_normalizada,
            secao_graph
        )
    )

    return registro_filtrado


# ============================================================
# ESTATÍSTICAS DAS SEÇÕES
# ============================================================

def contar_secoes(
    base
):

    contagem = {}

    notebook_alvo = (
        normalizar_texto(
            NOTEBOOK_ALVO
        )
    )

    for registro in base:

        origem = registro.get(
            "origem",
            {}
        )

        notebook = normalizar_texto(
            origem.get(
                "notebook"
            )
        )

        if notebook != notebook_alvo:

            continue

        secao = (
            origem.get(
                "secao"
            )
            or "[SEM SEÇÃO]"
        )

        contagem[
            secao
        ] = (
            contagem.get(
                secao,
                0
            )
            + 1
        )

    return contagem


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print(
        "FILTRO DE ESCOPO - BASE ECV MG"
    )
    print("=" * 70)

    # --------------------------------------------------------
    # VALIDAR BASE
    # --------------------------------------------------------

    if not os.path.exists(
        BASE_NORMALIZADA_FILE
    ):

        raise FileNotFoundError(
            "Arquivo base_normalizada.json "
            "não encontrado em:\n"
            f"{BASE_NORMALIZADA_FILE}"
        )

    print()
    print(
        "Carregando base_normalizada.json..."
    )

    base = carregar_json(
        BASE_NORMALIZADA_FILE
    )

    if not isinstance(
        base,
        list
    ):

        raise ValueError(
            "base_normalizada.json "
            "deve conter uma lista de registros."
        )

    print(
        f"{len(base)} registro(s) "
        "encontrado(s)."
    )

    # --------------------------------------------------------
    # MOSTRAR SEÇÕES EXISTENTES
    # --------------------------------------------------------

    contagem_secoes = (
        contar_secoes(
            base
        )
    )

    print()
    print("=" * 70)
    print(
        "SEÇÕES ENCONTRADAS EM ECV MG"
    )
    print("=" * 70)

    for secao, quantidade in sorted(
        contagem_secoes.items()
    ):

        print(
            f"{secao}: {quantidade}"
        )

    # --------------------------------------------------------
    # FILTRAR
    # --------------------------------------------------------

    filtrados = []

    ignorados = []

    for registro in base:

        if registro_esta_no_escopo(
            registro
        ):

            registro_filtrado = (
                ajustar_nome_secao(
                    registro
                )
            )

            filtrados.append(
                registro_filtrado
            )

        else:

            ignorados.append(
                registro
            )

    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print(
        "RESULTADO DO FILTRO"
    )
    print("=" * 70)

    print(
        f"Registros incluídos: "
        f"{len(filtrados)}"
    )

    print(
        f"Registros ignorados: "
        f"{len(ignorados)}"
    )

    # --------------------------------------------------------
    # SEGURANÇA
    # --------------------------------------------------------

    if len(
        filtrados
    ) == 0:

        print()
        print(
            "ERRO: nenhum registro foi "
            "encontrado para as seções-alvo."
        )

        print()
        print(
            "Nenhum arquivo será substituído."
        )

        return

    # --------------------------------------------------------
    # PRESERVAR BASE COMPLETA
    # --------------------------------------------------------

    if not os.path.exists(
        BASE_COMPLETA_FILE
    ):

        shutil.copy2(
            BASE_NORMALIZADA_FILE,
            BASE_COMPLETA_FILE
        )

        print()
        print(
            "Backup da base completa criado em:"
        )

        print(
            BASE_COMPLETA_FILE
        )

    else:

        print()
        print(
            "Backup da base completa já existe:"
        )

        print(
            BASE_COMPLETA_FILE
        )

    # --------------------------------------------------------
    # SALVAR BASE FILTRADA
    # --------------------------------------------------------

    salvar_json(
        filtrados,
        BASE_ECV_MG_FILE
    )

    # --------------------------------------------------------
    # CONTAGEM FINAL POR SEÇÃO
    # --------------------------------------------------------

    contagem_final = {}

    for registro in filtrados:

        origem = registro.get(
            "origem",
            {}
        )

        secao = (
            origem.get(
                "secao"
            )
            or "[SEM SEÇÃO]"
        )

        contagem_final[
            secao
        ] = (
            contagem_final.get(
                secao,
                0
            )
            + 1
        )

    print()
    print("=" * 70)
    print(
        "BASE ECV MG FILTRADA"
    )
    print("=" * 70)

    for secao, quantidade in sorted(
        contagem_final.items()
    ):

        print(
            f"{secao}: {quantidade}"
        )

    # --------------------------------------------------------
    # IDS INCLUÍDOS
    # --------------------------------------------------------

    ids_incluidos = []

    for registro in filtrados:

        ids_incluidos.append(
            registro.get(
                "id_interno"
            )
        )

    # --------------------------------------------------------
    # RELATÓRIO
    # --------------------------------------------------------

    relatorio = {

        "executado_em":
            datetime.now().isoformat(),

        "notebook":
            NOTEBOOK_ALVO,

        "regra_mapeamento": {

            "ERROS":
                "ERROS - SISTEMA",

            "MENSAGENS PADRÃO":
                "PROCEDIMENTOS OPERACIONAIS"
        },

        "secoes_graph_incluidas": [
            "ERROS",
            "MENSAGENS PADRÃO"
        ],

        "secoes_logicas_resultantes": [
            "ERROS - SISTEMA",
            "PROCEDIMENTOS OPERACIONAIS"
        ],

        "registros_base_completa":
            len(base),

        "registros_incluidos":
            len(filtrados),

        "registros_ignorados":
            len(ignorados),

        "contagem_secoes_originais":
            contagem_secoes,

        "contagem_secoes_filtradas":
            contagem_final,

        "ids_incluidos":
            ids_incluidos
    }

    salvar_json(
        relatorio,
        RELATORIO_FILE
    )

    # --------------------------------------------------------
    # FINAL
    # --------------------------------------------------------

    print()
    print(
        "Base filtrada salva em:"
    )

    print(
        BASE_ECV_MG_FILE
    )

    print()
    print(
        "Relatório salvo em:"
    )

    print(
        RELATORIO_FILE
    )

    print()
    print("=" * 70)
    print(
        "FILTRO CONCLUÃDO COM SUCESSO"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
