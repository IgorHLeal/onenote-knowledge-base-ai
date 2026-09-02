import argparse
import json
import os
import re
import time
import traceback
import unicodedata
import urllib.request
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

BASE_ECV_MG_FILE = os.path.join(
    PROCESSAMENTO_DIR,
    "base_normalizada_ecv_mg.json"
)

OLLAMA_DIR = os.path.join(
    PROCESSAMENTO_DIR,
    "ollama"
)

RESPOSTAS_DIR = os.path.join(
    OLLAMA_DIR,
    "respostas"
)

RELATORIOS_DIR = os.path.join(
    OLLAMA_DIR,
    "relatorios"
)

RELATORIO_LOTE_FILE = os.path.join(
    RELATORIOS_DIR,
    "relatorio_processamento_ecv_mg.json"
)


# ============================================================
# OLLAMA
# ============================================================

OLLAMA_URL = (
    "http://localhost:11434/api/generate"
)

MODELO = (
    "qwen2.5:1.5b-instruct-q5_0"
)

TIMEOUT_OLLAMA = 900

MAX_TENTATIVAS_CONEXAO = 2

PAUSA_RETENTATIVA = 5


# ============================================================
# SEÇÕES DE ORIGEM
# ============================================================

SECAO_ERROS = (
    "ERROS - SISTEMA"
)

SECAO_PROCEDIMENTOS = (
    "PROCEDIMENTOS OPERACIONAIS"
)


# ============================================================
# RÓTULOS PRINCIPAIS
# ============================================================

ROTULOS_OBJETIVO = {
    "objetivo",
}

ROTULOS_DESCRICAO = {
    "descricao",
    "descricao do problema",
    "problema",
    "como o cliente relata",
    "como o cliente normalmente relata",
}

ROTULOS_CAUSA = {
    "causa",
    "causa provavel",
}

ROTULOS_SOLUCAO = {
    "como resolver",
    "passo a passo",
    "passo a passo de solucao",
    "procedimento",
    "solucao",
}

ROTULOS_QUANDO_UTILIZAR = {
    "quando utilizar",
    "quando usar",
}

ROTULOS_EVIDENCIAS = {
    "evidencias",
    "evidencias obrigatorias",
    "evidencias e validacao",
    "anexar ao chamado",
    "anexe ao chamado",
}

ROTULOS_OBSERVACOES = {
    "observacoes",
    "observacao",
    "observacoes importantes",
    "atencao",
}

ROTULOS_QUANDO_ESCALAR = {
    "quando escalar",
    "quando escalonar",
    "escalonamento",
}

ROTULOS_FUNDAMENTACAO = {
    "fundamentacao legal",
    "fundamentacao legal (mg)",
    "base legal",
    "legislacao",
}

ROTULOS_REFERENCIA = {
    "referencia normativa",
    "referencias normativas",
    "documento de referencia",
}

ROTULOS_ENCERRAMENTO = {
    "encerramento",
}

ROTULOS_CANAIS = {
    "canais de atendimento",
}

ROTULOS_METADATA = {
    "codigo interno",
    "titulo do artigo",
    "categoria principal",
    "subcategoria",
    "palavras-chave",
    "palavras chave",
}


# ============================================================
# REFERÊNCIAS DE TICKET
# ============================================================

ROTULOS_TICKET = {
    "ticket referencia",
    "ticket de referencia",
    "tickets referencia",
    "tickets de referencia",
    "ticket relacionado",
    "tickets relacionados",
    "ticket exemplo",
    "tickets exemplo",
    "protocolo referencia",
    "protocolo de referencia",
}


# ============================================================
# ETAPAS PRINCIPAIS CONHECIDAS
#
# Uma linha desta lista pode iniciar uma ETAPA.
#
# Não coloque aqui comandos ou campos.
# ============================================================

SUBTITULOS_PRINCIPAIS = {
    "validacoes iniciais",
    "validacao inicial",
    "verificacoes iniciais",
    "verificacao inicial",

    "validacao dos videos",
    "validacao de videos",
    "validacao de ambiente",
    "validacao de evidencias",
    "validacao de evidencias (fotos)",
    "validacao apos a correcao",

    "ajuste em banco de dados",
    "ajuste no banco de dados",
    "correcao em multiplos videos",
    "apos a correcao",

    "consulta do veiculo",
    "consulta da distribuicao",
    "conexao ao wi-fi da ecv",
    "envio do processo fotografico",

    "conceito",
    "diretrizes gerais",
    "regras importantes",
    "orientacoes para agendamento",
    "requisitos para realizacao",
    "como funciona o processo",

    "informacoes necessarias",
    "encaminhamento",
    "envio da solicitacao",
    "possibilidade de isencao",
    "procedimento para solicitacao",

    "retificacao com alteracao de fotos",
    "retificacao sem alteracao de fotos",
    "laudo pendente de pericia",
    "vistoria de baixa",

    "utilizacao de servidor temporario",
    "retorno do servidor principal",
    "restricao de operacao",
    "servidor de backup",

    "cobranca de nova vistoria",
    "regra geral",
    "solicitacao de isencao de laudo",

    "vistoria com processo fotografico concluido",
    "expiracao das imagens",
    "prazo",

    "laudo emitido como aprovado com apontamento",
    "orientacao ao cidadao",
    "regularizacao da restricao",
    "consulta de restricoes",
    "retificacao do laudo",

    "possiveis causas",
    "acionamento da cet",

    "validacao dos boxes no portal transito mg",
    "conferencia das informacoes",

    "modelo de solicitacao para o fale conosco",
    "principais requisitos do curso de formacao",

    "diretorio do banco de dados sql server",
    "arquivos obrigatorios no backup",

    "configuracao de resolucao",
}


# ============================================================
# SUBGRUPOS FORTES
#
# Diferentemente da versão anterior, NÃO usamos mais
# Title Case genérico.
#
# Só linhas que atendam a critérios fortes viram subgrupo.
# ============================================================

SUBGRUPOS_EXATOS = {
    "organizacoes que nao devem ser utilizadas",
    "excecoes",

    "situacoes permitidas",

    "caso exista foto",
    "se existir foto",
    "se nao existir foto",

    "caso exista mais de um video com erro",

    "especificacao para vistoria de baixa",
    "atencao ao preenchimento",
    "agendamento incorreto",
    "finalizacao do processo",
}


PREFIXOS_SUBGRUPO_FORTES = (
    "especificacao para ",
    "atencao ao ",
    "agendamento incorreto",
    "finalizacao do ",
    "organizacoes que ",
)


# ============================================================
# JSON
# ============================================================

def carregar_json(
    caminho,
    padrao=None
):

    if not os.path.exists(
        caminho
    ):

        if padrao is not None:

            return padrao

        raise FileNotFoundError(
            f"Arquivo não encontrado: {caminho}"
        )

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
# TEXTO
# ============================================================

def texto_valido(
    valor
):

    if valor is None:

        return None

    if isinstance(
        valor,
        str
    ):

        valor = valor.strip()

        return valor or None

    valor = str(
        valor
    ).strip()

    return valor or None


def normalizar(
    texto
):

    texto = (
        texto_valido(
            texto
        )
        or ""
    )

    texto = unicodedata.normalize(
        "NFD",
        texto
    )

    texto = "".join(
        caractere
        for caractere in texto
        if unicodedata.category(
            caractere
        )
        != "Mn"
    )

    texto = (
        texto
        .lower()
        .strip()
        .replace(
            "–",
            "-"
        )
        .replace(
            "—",
            "-"
        )
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    return texto


def limpar_linha(
    texto
):

    texto = (
        texto_valido(
            texto
        )
        or ""
    )

    texto = (
        texto
        .replace(
            "\u00a0",
            " "
        )
        .replace(
            "\ufffc",
            ""
        )
        .replace(
            "￼",
            ""
        )
        .replace(
            "\t",
            " "
        )
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    texto = texto.strip()

    texto = re.sub(
        r"^[•]\s*",
        "",
        texto
    )

    texto = texto.strip()

    if texto in {
        "⚠",
        "⚠️",
    }:

        return ""

    return texto


def limpar_lista(
    itens
):

    if not isinstance(
        itens,
        list
    ):

        return []

    resultado = []

    for item in itens:

        item = limpar_linha(
            item
        )

        if not item:

            continue

        if item not in resultado:

            resultado.append(
                item
            )

    return resultado


def juntar_texto(
    itens
):

    itens = limpar_lista(
        itens
    )

    if not itens:

        return None

    texto = " ".join(
        itens
    )

    texto = re.sub(
        r"\s+([,.;:])",
        r"\1",
        texto
    )

    return texto.strip()


# ============================================================
# REGISTRO
# ============================================================

def localizar_registro(
    base,
    id_interno
):

    alvo = str(
        id_interno
    )

    for registro in base:

        if str(
            registro.get(
                "id_interno"
            )
        ) == alvo:

            return registro

    return None


def obter_tipo_artigo(
    registro
):

    secao = (
        registro
        .get(
            "origem",
            {}
        )
        .get(
            "secao",
            ""
        )
        or ""
    ).strip().upper()

    if secao == SECAO_ERROS:

        return "ERRO"

    if secao == SECAO_PROCEDIMENTOS:

        return "PROCEDIMENTO"

    raise ValueError(
        f"Seção fora do escopo: {secao}"
    )


def registro_esta_no_escopo(
    registro
):

    try:

        obter_tipo_artigo(
            registro
        )

        return True

    except ValueError:

        return False


def obter_titulo(
    registro
):

    conteudo = registro.get(
        "conteudo",
        {}
    )

    origem = registro.get(
        "origem",
        {}
    )

    return (
        texto_valido(
            conteudo.get(
                "titulo_normalizado"
            )
        )
        or
        texto_valido(
            origem.get(
                "titulo_original"
            )
        )
        or
        (
            f"Artigo "
            f"{registro.get('id_interno')}"
        )
    )


def obter_texto(
    registro
):

    return (
        registro
        .get(
            "conteudo",
            {}
        )
        .get(
            "texto",
            ""
        )
        or ""
    ).strip()


# ============================================================
# RÓTULOS
# ============================================================

def obter_rotulo(
    linha
):

    linha = limpar_linha(
        linha
    )

    if ":" not in linha:

        return (
            None,
            None
        )

    esquerda, direita = linha.split(
        ":",
        1
    )

    return (
        normalizar(
            esquerda
        ),
        direita.strip()
    )


def corresponde_rotulo(
    linha,
    conjunto
):

    linha = limpar_linha(
        linha
    )

    chave, valor = obter_rotulo(
        linha
    )

    if chave in conjunto:

        return (
            True,
            valor
        )

    normalizado = normalizar(
        linha.rstrip(
            ":"
        )
    )

    if normalizado in conjunto:

        return (
            True,
            None
        )

    return (
        False,
        None
    )


# ============================================================
# TICKETS
# ============================================================

def eh_rotulo_ticket(
    linha
):

    encontrou, _ = corresponde_rotulo(
        linha,
        ROTULOS_TICKET
    )

    return encontrou


def parece_numero_ticket(
    linha
):

    linha = limpar_linha(
        linha
    )

    if not linha:

        return False

    linha = linha.strip(
        " ,;"
    )

    return bool(
        re.fullmatch(
            (
                r"\d{4,12}"
                r"(?:\s*[,;/]\s*\d{4,12})*"
            ),
            linha
        )
    )


def extrair_numeros_ticket(
    linha
):

    return re.findall(
        r"\b\d{4,12}\b",
        limpar_linha(
            linha
        )
    )


# ============================================================
# REFERÊNCIA EMBUTIDA
# ============================================================

def remover_referencia_ticket_embutida(
    linha
):

    linha = limpar_linha(
        linha
    )

    if not linha:

        return (
            "",
            []
        )

    padrao = re.compile(
        (
            r"(?i)"
            r"\b"
            r"(?:ticket(?:s)?|protocolo)"
            r"\s+"
            r"(?:de\s+)?"
            r"refer[eê]ncia"
            r"\s*:\s*"
            r"(?P<numeros>"
            r"\d{4,12}"
            r"(?:\s*[,;/]\s*\d{4,12})*"
            r")"
            r"\s*"
            r"[,;:\-–—]?"
            r"\s*"
        )
    )

    tickets = []

    while True:

        match = padrao.search(
            linha
        )

        if not match:

            break

        tickets.extend(
            re.findall(
                r"\b\d{4,12}\b",
                match.group(
                    "numeros"
                )
            )
        )

        linha = (
            linha[
                :match.start()
            ]
            +
            linha[
                match.end():
            ]
        ).strip()

    linha = re.sub(
        r"^[,;:\-–—]\s*",
        "",
        linha
    )

    linha = re.sub(
        r"\s{2,}",
        " ",
        linha
    )

    return (
        linha.strip(),
        tickets
    )


# ============================================================
# AVISOS
# ============================================================

def remover_icone_aviso(
    linha
):

    linha = limpar_linha(
        linha
    )

    linha = re.sub(
        r"^[⚠️\s]+",
        "",
        linha
    )

    return linha.strip()


# ============================================================
# SEÇÕES ESPECIAIS
# ============================================================

def classificar_secao_especial(
    linha
):

    linha = remover_icone_aviso(
        linha
    )

    grupos = [
        (
            "OBJETIVO",
            ROTULOS_OBJETIVO
        ),
        (
            "DESCRICAO",
            ROTULOS_DESCRICAO
        ),
        (
            "CAUSA",
            ROTULOS_CAUSA
        ),
        (
            "QUANDO_UTILIZAR",
            ROTULOS_QUANDO_UTILIZAR
        ),
        (
            "EVIDENCIAS",
            ROTULOS_EVIDENCIAS
        ),
        (
            "OBSERVACOES",
            ROTULOS_OBSERVACOES
        ),
        (
            "QUANDO_ESCALAR",
            ROTULOS_QUANDO_ESCALAR
        ),
        (
            "FUNDAMENTACAO",
            ROTULOS_FUNDAMENTACAO
        ),
        (
            "REFERENCIA",
            ROTULOS_REFERENCIA
        ),
        (
            "ENCERRAMENTO",
            ROTULOS_ENCERRAMENTO
        ),
        (
            "CANAIS",
            ROTULOS_CANAIS
        ),
    ]

    for estado, conjunto in grupos:

        encontrou, valor = corresponde_rotulo(
            linha,
            conjunto
        )

        if encontrou:

            return (
                estado,
                valor
            )

    return (
        None,
        None
    )


# ============================================================
# NUMERAÇÃO DE TÍTULO
# ============================================================

def possui_numeracao_titulo(
    linha
):

    return bool(
        re.match(
            r"^\d+\s*[\.\-\)]\s*\S+",
            limpar_linha(
                linha
            )
        )
    )


def remover_numeracao_titulo(
    linha
):

    linha = limpar_linha(
        linha
    )

    linha = re.sub(
        r"^\d+\s*[\.\-\)]\s*",
        "",
        linha
    )

    return linha.strip()


# ============================================================
# ETAPA PRINCIPAL
# ============================================================

def eh_subtitulo_principal_conhecido(
    linha
):

    valor = normalizar(
        remover_numeracao_titulo(
            linha.rstrip(
                ":"
            )
        )
    )

    for conhecido in (
        SUBTITULOS_PRINCIPAIS
    ):

        conhecido_norm = normalizar(
            conhecido
        )

        if valor == conhecido_norm:

            return True

        if valor.startswith(
            conhecido_norm
            + " ("
        ):

            return True

    return False


def eh_subtitulo_principal(
    linha
):

    linha = limpar_linha(
        linha
    )

    if not linha:

        return False

    especial, _ = (
        classificar_secao_especial(
            linha
        )
    )

    if especial:

        return False

    if eh_rotulo_ticket(
        linha
    ):

        return False

    if parece_numero_ticket(
        linha
    ):

        return False

    # Cabeçalhos numerados são evidência forte.
    if possui_numeracao_titulo(
        linha
    ):

        return True

    if eh_subtitulo_principal_conhecido(
        linha
    ):

        return True

    return False


def titulo_subtitulo_principal(
    linha
):

    return remover_numeracao_titulo(
        limpar_linha(
            linha
        ).rstrip(
            ":"
        )
    )


# ============================================================
# PROTEÇÕES DE SUBGRUPO
# ============================================================

def parece_macro(
    linha
):

    linha = limpar_linha(
        linha
    )

    return linha.startswith(
        "/"
    )


def parece_status(
    linha
):

    linha = limpar_linha(
        linha
    ).rstrip(
        ".;"
    )

    if not linha:

        return False

    conhecidos = {
        "ONLINE",
        "ONLINE NO VOIP",
        "ONLINE NO ZENDESK",
        "ABERTO",
        "PENDENTE",
        "PENDENTE DEV",
        "PENDENTE EXTERNO",
        "PENDENTE FORNECEDOR",
    }

    if linha.upper() in conhecidos:

        return True

    return False


def parece_valor_de_campo(
    linha
):

    valor = normalizar(
        linha.rstrip(
            ".;"
        )
    )

    campos_conhecidos = {
        "servico atendido",
        "assunto",
        "data limite de retorno",
        "grupo otimiza",
        "otimiza solucoes",
        "otimiza sistemas ltda",
        "otimiza solucoes em ti",
    }

    return valor in campos_conhecidos


def parece_item_lista_simples(
    linha
):

    valor = normalizar(
        linha
    )

    exemplos = (
        "alteracao de dados",
        "baixa de impedimento",
        "segunda via de crv",
        "baixa de veiculo",
        "transferencia de propriedade",
        "documento oficial com foto",
        "documento do veiculo",
    )

    if valor.rstrip(
        ".;"
    ) in exemplos:

        return True

    return False


def parece_comando_operacional(
    linha
):

    valor = normalizar(
        linha
    )

    verbos = (
        "acessar ",
        "acesse ",
        "abrir ",
        "clicar ",
        "clique ",
        "selecionar ",
        "selecione ",
        "verificar ",
        "verifique ",
        "validar ",
        "valide ",
        "informar ",
        "informe ",
        "orientar ",
        "confirmar ",
        "confirme ",
        "solicitar ",
        "realizar ",
        "execute ",
        "executar ",
        "pressionar ",
        "inserir ",
        "ajustar ",
        "encaminhar ",
        "garantir ",
        "conferir ",
        "comparecer ",
        "efetuar ",
        "anexar ",
        "preencher ",
        "mantenha ",
        "manter ",
        "desligue ",
        "desligar ",
        "conecte-se ",
        "conectar ",
        "desconecte-se ",
        "desconectar ",
        "capture ",
        "capturar ",
        "ative ",
        "ativar ",
        "instalar ",
        "retornar ",
        "aguardar ",
        "utilizar ",
        "tire ",
    )

    return valor.startswith(
        verbos
    )


# ============================================================
# SUBGRUPOS CONSERVADORES
# ============================================================

def eh_subgrupo_nivel(
    linha
):

    return bool(
        re.match(
            r"^nivel\s+\d+\s*-\s*.+",
            normalizar(
                linha
            )
        )
    )


def eh_subgrupo_opcao(
    linha
):

    return bool(
        re.fullmatch(
            r"opcao\s+\d+",
            normalizar(
                linha.rstrip(
                    ":"
                )
            )
        )
    )


def eh_subgrupo_exato(
    linha
):

    valor = normalizar(
        linha.rstrip(
            ":"
        )
    )

    return valor in {
        normalizar(
            item
        )
        for item in SUBGRUPOS_EXATOS
    }


def eh_subgrupo_prefixo_forte(
    linha
):

    valor = normalizar(
        linha.rstrip(
            ":"
        )
    )

    return valor.startswith(
        tuple(
            normalizar(
                item
            )
            for item in PREFIXOS_SUBGRUPO_FORTES
        )
    )


def eh_subgrupo(
    linha
):

    linha = limpar_linha(
        linha
    )

    if not linha:

        return False

    # --------------------------------------------------------
    # PRIMEIRO: exclusões.
    # --------------------------------------------------------

    if eh_subtitulo_principal(
        linha
    ):

        return False

    especial, _ = (
        classificar_secao_especial(
            linha
        )
    )

    if especial:

        return False

    if eh_rotulo_ticket(
        linha
    ):

        return False

    if parece_numero_ticket(
        linha
    ):

        return False

    if parece_macro(
        linha
    ):

        return False

    if parece_status(
        linha
    ):

        return False

    if parece_valor_de_campo(
        linha
    ):

        return False

    if parece_item_lista_simples(
        linha
    ):

        return False

    if parece_comando_operacional(
        linha
    ):

        return False

    # --------------------------------------------------------
    # SOMENTE regras positivas fortes.
    # --------------------------------------------------------

    if eh_subgrupo_nivel(
        linha
    ):

        return True

    if eh_subgrupo_opcao(
        linha
    ):

        return True

    if eh_subgrupo_exato(
        linha
    ):

        return True

    if eh_subgrupo_prefixo_forte(
        linha
    ):

        return True

    return False


# ============================================================
# FRASES FRAGMENTADAS
# ============================================================

def linha_anterior_exige_complemento(
    linha
):

    valor = normalizar(
        linha
    )

    if not valor:

        return False

    frases_incompletas = {
        "apos",
        "mantenha os",
        "mantenha as",
        "nao utilize",
        "permanecer",
        "o ticket retornara automaticamente para o status",
        "caso o lider nao consiga prosseguir com a tratativa em ate",
    }

    if valor in frases_incompletas:

        return True

    conectores = (
        " de",
        " da",
        " do",
        " das",
        " dos",
        " em",
        " no",
        " na",
        " nos",
        " nas",
        " para",
        " com",
        " por",
        " pelo",
        " pela",
        " ao",
        " a",
        " o",
        " as",
        " os",
        " um",
        " uma",
        " ate",
    )

    if valor.endswith(
        conectores
    ):

        return True

    return False


def deve_juntar_fragmento(
    anterior,
    atual
):

    anterior = limpar_linha(
        anterior
    )

    atual = limpar_linha(
        atual
    )

    if not anterior or not atual:

        return False

    if eh_subtitulo_principal(
        atual
    ):

        return False

    if eh_subgrupo(
        atual
    ):

        return False

    especial, _ = (
        classificar_secao_especial(
            atual
        )
    )

    if especial:

        return False

    if eh_rotulo_ticket(
        atual
    ):

        return False

    if parece_numero_ticket(
        atual
    ):

        return False

    if atual.startswith(
        (
            ",",
            ".",
            ";",
        )
    ):

        return True

    if atual.startswith(
        "("
    ):

        return True

    if atual[:1].islower():

        return True

    if linha_anterior_exige_complemento(
        anterior
    ):

        return True

    if anterior.endswith(
        (
            ",",
            "→",
            "->",
            "(",
            "/",
        )
    ):

        return True

    return False


def reconstruir_linhas(
    linhas
):

    resultado = []

    for linha in linhas:

        linha = limpar_linha(
            linha
        )

        if not linha:

            continue

        if (
            resultado
            and
            deve_juntar_fragmento(
                resultado[-1],
                linha
            )
        ):

            anterior = resultado[
                -1
            ]

            if linha.startswith(
                (
                    ",",
                    ".",
                    ";",
                    ":",
                )
            ):

                novo = (
                    anterior.rstrip()
                    + linha
                )

            else:

                novo = (
                    anterior.rstrip()
                    + " "
                    + linha
                )

            novo = re.sub(
                r"\s+([,.;:])",
                r"\1",
                novo
            )

            resultado[
                -1
            ] = novo.strip()

        else:

            resultado.append(
                linha
            )

    return resultado


def reconstruir_linhas_completo(
    linhas
):

    atual = limpar_lista(
        linhas
    )

    assinatura_anterior = None

    for _ in range(
        5
    ):

        atual = reconstruir_linhas(
            atual
        )

        assinatura = tuple(
            atual
        )

        if assinatura == assinatura_anterior:

            break

        assinatura_anterior = assinatura

    return atual


# ============================================================
# ESTRUTURA BASE
# ============================================================

def novo_resultado_segmentacao():

    return {
        "objetivo":
            [],

        "descricao":
            [],

        "causa":
            [],

        "quando_utilizar":
            [],

        "blocos_procedimento":
            [],

        "evidencias":
            [],

        "observacoes":
            [],

        "quando_escalar":
            [],

        "fundamentacao_legal":
            [],

        "referencia_normativa":
            [],

        "encerramento":
            [],

        "canais_atendimento":
            [],

        "outros":
            [],

        "tickets_referencia":
            [],
    }


def adicionar_em_estado(
    resultado,
    estado,
    linha
):

    mapa = {
        "OBJETIVO":
            "objetivo",

        "DESCRICAO":
            "descricao",

        "CAUSA":
            "causa",

        "QUANDO_UTILIZAR":
            "quando_utilizar",

        "EVIDENCIAS":
            "evidencias",

        "OBSERVACOES":
            "observacoes",

        "QUANDO_ESCALAR":
            "quando_escalar",

        "FUNDAMENTACAO":
            "fundamentacao_legal",

        "REFERENCIA":
            "referencia_normativa",

        "ENCERRAMENTO":
            "encerramento",

        "CANAIS":
            "canais_atendimento",
    }

    campo = mapa.get(
        estado
    )

    if campo:

        resultado[
            campo
        ].append(
            linha
        )


# ============================================================
# ESTRUTURAR UMA ETAPA
# ============================================================

def estruturar_bloco(
    bloco
):

    titulo = (
        texto_valido(
            bloco.get(
                "titulo"
            )
        )
        or
        "Procedimento"
    )

    linhas = reconstruir_linhas_completo(
        bloco.get(
            "linhas",
            []
        )
    )

    itens_principais = []

    subgrupos = []

    subgrupo_atual = None

    for linha in linhas:

        # ----------------------------------------------------
        # Só uma regra forte pode abrir subgrupo.
        # ----------------------------------------------------

        if eh_subgrupo(
            linha
        ):

            subgrupo_atual = {
                "titulo":
                    limpar_linha(
                        linha
                    ).rstrip(
                        ":"
                    ),

                "itens":
                    []
            }

            subgrupos.append(
                subgrupo_atual
            )

            continue

        # ----------------------------------------------------
        # Se já existe subgrupo, o restante pertence a ele
        # até outro subgrupo.
        # ----------------------------------------------------

        if subgrupo_atual is not None:

            subgrupo_atual[
                "itens"
            ].append(
                linha
            )

        else:

            itens_principais.append(
                linha
            )

    # ========================================================
    # LIMPEZA DOS SUBGRUPOS
    # ========================================================

    subgrupos_limpos = []

    for subgrupo in subgrupos:

        itens = reconstruir_linhas_completo(
            subgrupo.get(
                "itens",
                []
            )
        )

        if not itens:

            continue

        subgrupos_limpos.append(
            {
                "titulo":
                    subgrupo[
                        "titulo"
                    ],

                "itens":
                    itens
            }
        )

    return {
        "titulo":
            titulo,

        "linhas":
            reconstruir_linhas_completo(
                itens_principais
            ),

        "subgrupos":
            subgrupos_limpos
    }


# ============================================================
# PRÉ-SEGMENTAÇÃO
# ============================================================

def pre_segmentar_fonte(
    registro
):

    titulo = obter_titulo(
        registro
    )

    tipo = obter_tipo_artigo(
        registro
    )

    linhas = [
        limpar_linha(
            linha
        )
        for linha
        in obter_texto(
            registro
        ).splitlines()
    ]

    linhas = [
        linha
        for linha in linhas
        if linha
    ]

    linhas = [
        linha
        for linha in linhas
        if normalizar(
            linha
        )
        != normalizar(
            titulo
        )
    ]

    resultado = (
        novo_resultado_segmentacao()
    )

    estado = None

    bloco_atual = None

    ignorando_tickets = False

    for linha_original in linhas:

        linha = linha_original

        # ====================================================
        # REFERÊNCIA EMBUTIDA
        # ====================================================

        (
            linha,
            tickets_embutidos
        ) = remover_referencia_ticket_embutida(
            linha
        )

        if tickets_embutidos:

            resultado[
                "tickets_referencia"
            ].extend(
                tickets_embutidos
            )

        if not linha:

            continue

        # ====================================================
        # TICKET EM BLOCO
        # ====================================================

        if eh_rotulo_ticket(
            linha
        ):

            ignorando_tickets = True

            resultado[
                "tickets_referencia"
            ].extend(
                extrair_numeros_ticket(
                    linha
                )
            )

            continue

        if ignorando_tickets:

            if parece_numero_ticket(
                linha
            ):

                resultado[
                    "tickets_referencia"
                ].extend(
                    extrair_numeros_ticket(
                        linha
                    )
                )

                continue

            ignorando_tickets = False

        if parece_numero_ticket(
            linha
        ):

            resultado[
                "tickets_referencia"
            ].extend(
                extrair_numeros_ticket(
                    linha
                )
            )

            continue

        # ====================================================
        # METADADOS
        # ====================================================

        chave, _ = obter_rotulo(
            linha
        )

        linha_norm = normalizar(
            linha.rstrip(
                ":"
            )
        )

        if (
            chave in ROTULOS_METADATA
            or
            linha_norm
            in ROTULOS_METADATA
        ):

            continue

        # ====================================================
        # COMO RESOLVER / PROCEDIMENTO
        # ====================================================

        (
            encontrou_solucao,
            valor_solucao
        ) = corresponde_rotulo(
            linha,
            ROTULOS_SOLUCAO
        )

        if encontrou_solucao:

            estado = "PROCEDIMENTO"

            bloco_atual = None

            if valor_solucao:

                bloco_atual = {
                    "titulo":
                        "Procedimento",

                    "linhas": [
                        valor_solucao
                    ]
                }

                resultado[
                    "blocos_procedimento"
                ].append(
                    bloco_atual
                )

            continue

        # ====================================================
        # SEÇÕES ESPECIAIS
        # ====================================================

        (
            novo_estado,
            valor
        ) = classificar_secao_especial(
            linha
        )

        if novo_estado:

            estado = novo_estado

            bloco_atual = None

            if valor:

                adicionar_em_estado(
                    resultado,
                    estado,
                    valor
                )

            continue

        # ====================================================
        # ETAPA PRINCIPAL
        # ====================================================

        if eh_subtitulo_principal(
            linha
        ):

            estado = "PROCEDIMENTO"

            bloco_atual = {
                "titulo":
                    titulo_subtitulo_principal(
                        linha
                    ),

                "linhas":
                    []
            }

            resultado[
                "blocos_procedimento"
            ].append(
                bloco_atual
            )

            continue

        # ====================================================
        # CONTEÚDO
        # ====================================================

        if estado == "PROCEDIMENTO":

            if bloco_atual is None:

                bloco_atual = {
                    "titulo":
                        "Procedimento",

                    "linhas":
                        []
                }

                resultado[
                    "blocos_procedimento"
                ].append(
                    bloco_atual
                )

            bloco_atual[
                "linhas"
            ].append(
                linha
            )

            continue

        if estado:

            adicionar_em_estado(
                resultado,
                estado,
                linha
            )

            continue

        resultado[
            "outros"
        ].append(
            linha
        )

    # ========================================================
    # FALLBACK PARA PROCEDIMENTOS CURTOS
    # ========================================================

    if (
        tipo == "PROCEDIMENTO"
        and
        not resultado[
            "blocos_procedimento"
        ]
    ):

        candidatos = (
            reconstruir_linhas_completo(
                resultado[
                    "outros"
                ]
            )
        )

        if candidatos:

            resultado[
                "blocos_procedimento"
            ] = [
                {
                    "titulo":
                        "Procedimento",

                    "linhas":
                        candidatos
                }
            ]

            resultado[
                "outros"
            ] = []

    # ========================================================
    # CAMPOS DE TEXTO
    # ========================================================

    resultado[
        "objetivo"
    ] = juntar_texto(
        resultado[
            "objetivo"
        ]
    )

    resultado[
        "quando_utilizar"
    ] = juntar_texto(
        resultado[
            "quando_utilizar"
        ]
    )

    campos_lista = (
        "descricao",
        "causa",
        "evidencias",
        "observacoes",
        "quando_escalar",
        "fundamentacao_legal",
        "referencia_normativa",
        "encerramento",
        "canais_atendimento",
        "outros",
    )

    for campo in campos_lista:

        resultado[
            campo
        ] = reconstruir_linhas_completo(
            resultado[
                campo
            ]
        )

    # ========================================================
    # ESTRUTURA ETAPAS
    # ========================================================

    blocos_estruturados = []

    for bloco in resultado[
        "blocos_procedimento"
    ]:

        estruturado = estruturar_bloco(
            bloco
        )

        if (
            estruturado[
                "linhas"
            ]
            or
            estruturado[
                "subgrupos"
            ]
        ):

            blocos_estruturados.append(
                estruturado
            )

    resultado[
        "blocos_procedimento"
    ] = blocos_estruturados

    resultado[
        "tickets_referencia"
    ] = limpar_lista(
        resultado[
            "tickets_referencia"
        ]
    )

    return resultado


# ============================================================
# CAMPOS PROTEGIDOS
# ============================================================

def montar_campos_protegidos(
    registro,
    segmentos
):

    tipo = obter_tipo_artigo(
        registro
    )

    protegidos = {
        "objetivo":
            segmentos.get(
                "objetivo"
            ),

        "quando_utilizar":
            segmentos.get(
                "quando_utilizar"
            ),

        "evidencias_obrigatorias":
            segmentos.get(
                "evidencias",
                []
            ),

        "observacoes":
            segmentos.get(
                "observacoes",
                []
            ),

        "quando_escalar":
            segmentos.get(
                "quando_escalar",
                []
            ),

        "fundamentacao_legal":
            segmentos.get(
                "fundamentacao_legal",
                []
            ),

        "referencia_normativa":
            segmentos.get(
                "referencia_normativa",
                []
            ),

        "encerramento":
            segmentos.get(
                "encerramento",
                []
            ),

        "canais_atendimento":
            segmentos.get(
                "canais_atendimento",
                []
            ),
    }

    if tipo == "ERRO":

        protegidos[
            "como_cliente_relata"
        ] = segmentos.get(
            "descricao",
            []
        )

        protegidos[
            "causa_provavel"
        ] = segmentos.get(
            "causa",
            []
        )

    return protegidos


# ============================================================
# PROMPT
# ============================================================

def montar_prompt(
    registro,
    segmentos
):

    tipo = obter_tipo_artigo(
        registro
    )

    titulo = obter_titulo(
        registro
    )

    blocos = segmentos.get(
        "blocos_procedimento",
        []
    )

    if tipo == "ERRO":

        formato = """
{
  "produto": [],
  "mensagens_erro": [],
  "como_resolver": [
    {
      "etapa": "",
      "itens": [],
      "subgrupos": [
        {
          "titulo": "",
          "itens": []
        }
      ]
    }
  ]
}
"""

    else:

        formato = """
{
  "produto": [],
  "procedimento": [
    {
      "etapa": "",
      "itens": [],
      "subgrupos": [
        {
          "titulo": "",
          "itens": []
        }
      ]
    }
  ]
}
"""

    return f"""
Você é um curador técnico de base de conhecimento.

O Python já definiu a estrutura do artigo.

Você NÃO deve reorganizar essa estrutura.

TIPO:
{tipo}

TÍTULO:
{titulo}

ESTRUTURA DEFINIDA PELO PYTHON:
{json.dumps(
    blocos,
    ensure_ascii=False,
    indent=2
)}

REGRAS:

1. Preserve exatamente todas as etapas.
2. Preserve exatamente o título de cada etapa.
3. Preserve exatamente os subgrupos.
4. Preserve exatamente o título de cada subgrupo.
5. Não transforme itens em subgrupos.
6. Não transforme subgrupos em itens.
7. Não crie etapas.
8. Não remova etapas.
9. Não crie subgrupos.
10. Não remova subgrupos.
11. Não mova conteúdo.
12. Não invente conteúdo.
13. Reconstrua somente frases claramente quebradas.
14. Preserve nomes de sistemas.
15. Preserve macros iniciadas por /.
16. Preserve nomes de campos.
17. Preserve comandos técnicos.
18. Preserve opções.
19. Não inclua tickets ou protocolos.
20. Não inclua observações.
21. Não inclua fundamentação legal.
22. Retorne somente JSON válido.
23. Não use Markdown.

FORMATO:
{formato}
""".strip()


# ============================================================
# OLLAMA
# ============================================================

def consultar_ollama(
    prompt
):

    payload = {
        "model":
            MODELO,

        "prompt":
            prompt,

        "stream":
            False,

        "format":
            "json",

        "options": {
            "temperature":
                0.1
        }
    }

    dados = json.dumps(
        payload,
        ensure_ascii=False
    ).encode(
        "utf-8"
    )

    ultimo_erro = None

    for tentativa in range(
        1,
        MAX_TENTATIVAS_CONEXAO + 1
    ):

        try:

            requisicao = urllib.request.Request(
                OLLAMA_URL,
                data=dados,
                headers={
                    "Content-Type":
                        "application/json"
                },
                method="POST"
            )

            with urllib.request.urlopen(
                requisicao,
                timeout=TIMEOUT_OLLAMA
            ) as resposta:

                corpo = (
                    resposta
                    .read()
                    .decode(
                        "utf-8"
                    )
                )

            retorno = json.loads(
                corpo
            )

            resposta_texto = (
                retorno.get(
                    "response",
                    ""
                )
                or ""
            ).strip()

            if not resposta_texto:

                raise ValueError(
                    "Resposta vazia do Ollama."
                )

            return (
                json.loads(
                    resposta_texto
                ),
                retorno
            )

        except Exception as erro:

            ultimo_erro = erro

            if (
                tentativa
                <
                MAX_TENTATIVAS_CONEXAO
            ):

                print(
                    "    Falha de comunicação com o Ollama."
                )

                print(
                    (
                        "    Nova tentativa em "
                        f"{PAUSA_RETENTATIVA}s..."
                    )
                )

                time.sleep(
                    PAUSA_RETENTATIVA
                )

    raise ultimo_erro


# ============================================================
# PRODUTOS
# ============================================================

def sanear_produtos(
    registro
):

    fonte = normalizar(
        (
            obter_titulo(
                registro
            )
            + " "
            + obter_texto(
                registro
            )
        )
    )

    conhecidos = {
        "MPI": (
            "mpi",
        ),

        "VistoSoft App": (
            "vistosoft app",
            "vistosoftapp",
        ),

        "VistoSoft": (
            "vistosoft",
            "visto soft",
        ),

        "IP Utility": (
            "ip utility",
        ),

        "SCE": (
            "sce",
        ),

        "SSC": (
            "ssc",
        ),

        "SDVV": (
            "sdvv",
        ),

        "Zendesk": (
            "zendesk",
        ),
    }

    resultado = []

    for nome, termos in conhecidos.items():

        if any(
            termo in fonte
            for termo in termos
        ):

            if (
                nome == "VistoSoft"
                and
                "VistoSoft App"
                in resultado
            ):

                continue

            resultado.append(
                nome
            )

    return resultado


# ============================================================
# RESPOSTA DO OLLAMA
# ============================================================

def localizar_etapa_ollama(
    resposta_etapas,
    titulo
):

    if not isinstance(
        resposta_etapas,
        list
    ):

        return None

    alvo = normalizar(
        titulo
    )

    for etapa in resposta_etapas:

        if not isinstance(
            etapa,
            dict
        ):

            continue

        if normalizar(
            etapa.get(
                "etapa",
                ""
            )
        ) == alvo:

            return etapa

    return None


def localizar_subgrupo_ollama(
    etapa_ollama,
    titulo
):

    if not isinstance(
        etapa_ollama,
        dict
    ):

        return None

    subgrupos = etapa_ollama.get(
        "subgrupos",
        []
    )

    if not isinstance(
        subgrupos,
        list
    ):

        return None

    alvo = normalizar(
        titulo
    )

    for subgrupo in subgrupos:

        if not isinstance(
            subgrupo,
            dict
        ):

            continue

        if normalizar(
            subgrupo.get(
                "titulo",
                ""
            )
        ) == alvo:

            return subgrupo

    return None


# ============================================================
# SANEAR ETAPAS
#
# A fonte Python é a autoridade estrutural.
# ============================================================

def sanear_etapas(
    resposta_etapas,
    blocos_fonte
):

    resultado = []

    for bloco in blocos_fonte:

        titulo = (
            texto_valido(
                bloco.get(
                    "titulo"
                )
            )
            or
            "Procedimento"
        )

        fonte_itens = reconstruir_linhas_completo(
            bloco.get(
                "linhas",
                []
            )
        )

        etapa_ollama = localizar_etapa_ollama(
            resposta_etapas,
            titulo
        )

        # ====================================================
        # ITENS PRINCIPAIS
        #
        # REGRA IMPORTANTE:
        #
        # Se a fonte não possui itens principais,
        # o Ollama NÃO pode criar itens.
        #
        # Isso elimina a duplicação observada no ID 107.
        # ====================================================

        if fonte_itens:

            itens_ollama = []

            if isinstance(
                etapa_ollama,
                dict
            ):

                itens_ollama = (
                    etapa_ollama.get(
                        "itens",
                        []
                    )
                )

            if (
                isinstance(
                    itens_ollama,
                    list
                )
                and
                itens_ollama
            ):

                itens = reconstruir_linhas_completo(
                    itens_ollama
                )

            else:

                itens = fonte_itens

        else:

            itens = []

        # ====================================================
        # SUBGRUPOS
        # ====================================================

        subgrupos_resultado = []

        for subgrupo_fonte in bloco.get(
            "subgrupos",
            []
        ):

            titulo_subgrupo = (
                subgrupo_fonte.get(
                    "titulo"
                )
            )

            fonte_subitens = (
                reconstruir_linhas_completo(
                    subgrupo_fonte.get(
                        "itens",
                        []
                    )
                )
            )

            subgrupo_ollama = localizar_subgrupo_ollama(
                etapa_ollama,
                titulo_subgrupo
            )

            itens_ollama = []

            if isinstance(
                subgrupo_ollama,
                dict
            ):

                itens_ollama = (
                    subgrupo_ollama.get(
                        "itens",
                        []
                    )
                )

            if (
                isinstance(
                    itens_ollama,
                    list
                )
                and
                itens_ollama
            ):

                subitens = (
                    reconstruir_linhas_completo(
                        itens_ollama
                    )
                )

            else:

                subitens = fonte_subitens

            if subitens:

                subgrupos_resultado.append(
                    {
                        "titulo":
                            titulo_subgrupo,

                        "itens":
                            subitens
                    }
                )

        resultado.append(
            {
                "etapa":
                    titulo,

                "itens":
                    itens,

                "subgrupos":
                    subgrupos_resultado
            }
        )

    return resultado


# ============================================================
# MENSAGENS DE ERRO
# ============================================================

def parece_estrutura_serializada(
    valor
):

    if not isinstance(
        valor,
        str
    ):

        return True

    texto = valor.strip()

    if not texto:

        return False

    if texto.startswith(
        (
            "{",
            "[",
        )
    ):

        return True

    marcadores = (
        "'titulo':",
        '"titulo":',
        "'subgrupos':",
        '"subgrupos":',
        "'itens':",
        '"itens":',
        "'etapa':",
        '"etapa":',
        "'como_resolver':",
        '"como_resolver":',
        "'procedimento':",
        '"procedimento":',
    )

    texto_lower = texto.lower()

    return any(
        marcador.lower()
        in texto_lower
        for marcador
        in marcadores
    )


def parece_descricao_generica_erro(
    valor
):

    texto = normalizar(
        valor
    )

    prefixos_genericos = (
        "erro exibido na etapa",
        "erro apresentado na etapa",
        "mensagem exibida na etapa",
        "mensagem apresentada na etapa",
        "erro ao tentar",
        "erro ao abrir",
        "cliente relata",
        "o cliente relata",
    )

    return texto.startswith(
        prefixos_genericos
    )


def sanear_mensagens_erro(
    mensagens,
    registro
):

    if not isinstance(
        mensagens,
        list
    ):

        return []

    fonte = obter_texto(
        registro
    )

    fonte_normalizada = normalizar(
        fonte
    )

    resultado = []

    for mensagem in mensagens:

        # Nunca converter dict/list para string.
        if not isinstance(
            mensagem,
            str
        ):

            continue

        mensagem = limpar_linha(
            mensagem
        )

        if not mensagem:

            continue

        if parece_estrutura_serializada(
            mensagem
        ):

            continue

        if parece_descricao_generica_erro(
            mensagem
        ):

            continue

        # Mensagens muito longas normalmente são resumo,
        # estrutura serializada ou conteúdo inventado.
        if len(
            mensagem
        ) > 500:

            continue

        # O Ollama não pode criar uma mensagem que não exista
        # no conteúdo original da página.
        if normalizar(
            mensagem
        ) not in fonte_normalizada:

            continue

        if mensagem not in resultado:

            resultado.append(
                mensagem
            )

    return resultado


# ============================================================
# RESULTADO FINAL
# ============================================================

def montar_resultado_final(
    registro,
    segmentos,
    protegidos,
    resposta_ollama
):

    tipo = obter_tipo_artigo(
        registro
    )

    blocos = segmentos.get(
        "blocos_procedimento",
        []
    )

    resultado = {
        "tipo_artigo":
            tipo,

        "titulo":
            obter_titulo(
                registro
            ),

        "produto":
            sanear_produtos(
                registro
            ),

        "objetivo":
            protegidos.get(
                "objetivo"
            ),

        "quando_utilizar":
            protegidos.get(
                "quando_utilizar"
            ),

        "quando_escalar":
            protegidos.get(
                "quando_escalar",
                []
            ),

        "evidencias_obrigatorias":
            protegidos.get(
                "evidencias_obrigatorias",
                []
            ),

        "observacoes":
            protegidos.get(
                "observacoes",
                []
            ),

        "fundamentacao_legal":
            protegidos.get(
                "fundamentacao_legal",
                []
            ),

        "referencia_normativa":
            protegidos.get(
                "referencia_normativa",
                []
            ),

        "canais_atendimento":
            protegidos.get(
                "canais_atendimento",
                []
            ),

        "encerramento":
            protegidos.get(
                "encerramento",
                []
            ),
    }

    if tipo == "ERRO":

        resultado[
            "como_cliente_relata"
        ] = protegidos.get(
            "como_cliente_relata",
            []
        )

        resultado[
            "causa_provavel"
        ] = protegidos.get(
            "causa_provavel",
            []
        )

        resultado[
            "mensagens_erro"
        ] = sanear_mensagens_erro(
            resposta_ollama.get(
                "mensagens_erro",
                []
            ),
            registro
        )

        resultado[
            "como_resolver"
        ] = sanear_etapas(
            resposta_ollama.get(
                "como_resolver",
                []
            ),
            blocos
        )

    else:

        resultado[
            "procedimento"
        ] = sanear_etapas(
            resposta_ollama.get(
                "procedimento",
                []
            ),
            blocos
        )

    return resultado


# ============================================================
# VALIDAÇÃO
# ============================================================

def validar_resultado(
    registro,
    segmentos,
    resultado
):

    problemas = []

    tipo = obter_tipo_artigo(
        registro
    )

    if tipo == "ERRO":

        etapas = resultado.get(
            "como_resolver",
            []
        )

    else:

        etapas = resultado.get(
            "procedimento",
            []
        )

    blocos_fonte = segmentos.get(
        "blocos_procedimento",
        []
    )

    if tipo == "ERRO":

        for mensagem in resultado.get(
            "mensagens_erro",
            []
        ):

            if parece_estrutura_serializada(
                mensagem
            ):

                problemas.append(
                    "Estrutura serializada encontrada em mensagens_erro."
                )

    if (
        tipo == "PROCEDIMENTO"
        and
        not etapas
    ):

        problemas.append(
            "Procedimento sem etapas."
        )

    if len(
        etapas
    ) != len(
        blocos_fonte
    ):

        problemas.append(
            (
                "Quantidade de etapas diferente "
                "da fonte. "
                f"Fonte={len(blocos_fonte)} "
                f"Resultado={len(etapas)}"
            )
        )

        return problemas

    # ========================================================
    # VERIFICA ETAPA POR ETAPA
    # ========================================================

    for (
        etapa_resultado,
        bloco_fonte
    ) in zip(
        etapas,
        blocos_fonte
    ):

        titulo_resultado = normalizar(
            etapa_resultado.get(
                "etapa",
                ""
            )
        )

        titulo_fonte = normalizar(
            bloco_fonte.get(
                "titulo",
                ""
            )
        )

        if titulo_resultado != titulo_fonte:

            problemas.append(
                (
                    "Título de etapa diferente: "
                    f"{etapa_resultado.get('etapa')}"
                )
            )

        # ====================================================
        # SUBGRUPOS
        # ====================================================

        subgrupos_resultado = (
            etapa_resultado.get(
                "subgrupos",
                []
            )
        )

        subgrupos_fonte = (
            bloco_fonte.get(
                "subgrupos",
                []
            )
        )

        if len(
            subgrupos_resultado
        ) != len(
            subgrupos_fonte
        ):

            problemas.append(
                (
                    "Quantidade de subgrupos diferente "
                    f"na etapa '{bloco_fonte.get('titulo')}'. "
                    f"Fonte={len(subgrupos_fonte)} "
                    f"Resultado={len(subgrupos_resultado)}"
                )
            )

        # ====================================================
        # PROTEÇÃO CONTRA DUPLICAÇÃO
        # ====================================================

        itens_norm = {
            normalizar(
                item
            )
            for item in etapa_resultado.get(
                "itens",
                []
            )
        }

        for subgrupo in subgrupos_resultado:

            titulo_subgrupo = normalizar(
                subgrupo.get(
                    "titulo",
                    ""
                )
            )

            if (
                titulo_subgrupo
                and
                titulo_subgrupo
                in itens_norm
            ):

                problemas.append(
                    (
                        "Título de subgrupo também "
                        "presente como item da etapa: "
                        f"{subgrupo.get('titulo')}"
                    )
                )

    return problemas


# ============================================================
# CAMINHO DA RESPOSTA
# ============================================================

def caminho_resposta(
    id_interno
):

    return os.path.join(
        RESPOSTAS_DIR,
        (
            f"artigo_"
            f"{int(id_interno):03d}"
            f".json"
        )
    )


# ============================================================
# PROCESSAMENTO
# ============================================================

def processar_registro(
    registro,
    mostrar_detalhes=False
):

    inicio = time.time()

    segmentos = pre_segmentar_fonte(
        registro
    )

    protegidos = montar_campos_protegidos(
        registro,
        segmentos
    )

    if mostrar_detalhes:

        print()
        print(
            "Blocos operacionais detectados:"
        )

        print(
            json.dumps(
                segmentos.get(
                    "blocos_procedimento",
                    []
                ),
                ensure_ascii=False,
                indent=2
            )
        )

        print()
        print(
            "Tickets de referência ignorados:"
        )

        print(
            json.dumps(
                segmentos.get(
                    "tickets_referencia",
                    []
                ),
                ensure_ascii=False,
                indent=2
            )
        )

        print()
        print(
            "Seções especiais:"
        )

        print(
            json.dumps(
                {
                    "objetivo":
                        segmentos.get(
                            "objetivo"
                        ),

                    "quando_utilizar":
                        segmentos.get(
                            "quando_utilizar"
                        ),

                    "quando_escalar":
                        segmentos.get(
                            "quando_escalar"
                        ),

                    "evidencias":
                        segmentos.get(
                            "evidencias"
                        ),

                    "observacoes":
                        segmentos.get(
                            "observacoes"
                        ),

                    "fundamentacao_legal":
                        segmentos.get(
                            "fundamentacao_legal"
                        ),

                    "referencia_normativa":
                        segmentos.get(
                            "referencia_normativa"
                        ),

                    "encerramento":
                        segmentos.get(
                            "encerramento"
                        ),
                },
                ensure_ascii=False,
                indent=2
            )
        )

    print(
        "    Tentativa 1/1..."
    )

    (
        resposta_ollama,
        metricas
    ) = consultar_ollama(
        montar_prompt(
            registro,
            segmentos
        )
    )

    resultado_final = (
        montar_resultado_final(
            registro,
            segmentos,
            protegidos,
            resposta_ollama
        )
    )

    problemas = validar_resultado(
        registro,
        segmentos,
        resultado_final
    )

    aprovado = not problemas

    pacote = {
        "id_interno":
            registro.get(
                "id_interno"
            ),

        "processado_em":
            datetime.now().isoformat(),

        "modelo":
            MODELO,

        "tipo_artigo":
            obter_tipo_artigo(
                registro
            ),

        "titulo_original":
            obter_titulo(
                registro
            ),

        "status":
            (
                "APROVADO"
                if aprovado
                else
                "REVISAR"
            ),

        "duracao_segundos":
            round(
                time.time()
                - inicio,
                2
            ),

        "pre_segmentacao_python":
            segmentos,

        "campos_protegidos":
            protegidos,

        "resposta_bruta_ollama":
            resposta_ollama,

        "resposta_final":
            resultado_final,

        "problemas_validacao":
            problemas,

        "metricas_ollama":
            metricas,
    }

    salvar_json(
        pacote,
        caminho_resposta(
            registro.get(
                "id_interno"
            )
        )
    )

    return pacote


# ============================================================
# JÁ APROVADO
# ============================================================

def artigo_ja_aprovado(
    id_interno
):

    caminho = caminho_resposta(
        id_interno
    )

    if not os.path.exists(
        caminho
    ):

        return False

    try:

        pacote = carregar_json(
            caminho
        )

        return (
            pacote.get(
                "status"
            )
            ==
            "APROVADO"
        )

    except Exception:

        return False


# ============================================================
# PROCESSAR UM
# ============================================================

def processar_um(
    id_interno
):

    base = carregar_json(
        BASE_ECV_MG_FILE
    )

    registro = localizar_registro(
        base,
        id_interno
    )

    if registro is None:

        raise ValueError(
            f"ID {id_interno} não encontrado."
        )

    print()
    print("=" * 70)
    print(
        "PROCESSAMENTO ESTRUTURAL PYTHON + OLLAMA"
    )
    print("=" * 70)

    print(
        f"ID: {id_interno}"
    )

    print(
        f"Tipo: "
        f"{obter_tipo_artigo(registro)}"
    )

    print(
        f"Título: "
        f"{obter_titulo(registro)}"
    )

    pacote = processar_registro(
        registro,
        mostrar_detalhes=True
    )

    print()
    print("=" * 70)

    print(
        f"STATUS: "
        f"{pacote['status']}"
    )

    print("=" * 70)
    print()

    print(
        json.dumps(
            pacote[
                "resposta_final"
            ],
            ensure_ascii=False,
            indent=2
        )
    )

    if pacote[
        "problemas_validacao"
    ]:

        print()
        print(
            "Problemas de validação:"
        )

        for problema in pacote[
            "problemas_validacao"
        ]:

            print(
                f" - {problema}"
            )


# ============================================================
# PROCESSAMENTO EM LOTE
# ============================================================

def processar_todos(
    reprocessar=False,
    limite=None
):

    base = carregar_json(
        BASE_ECV_MG_FILE
    )

    registros = [
        registro
        for registro in base
        if registro_esta_no_escopo(
            registro
        )
    ]

    registros.sort(
        key=lambda registro:
        int(
            registro.get(
                "id_interno",
                0
            )
        )
    )

    if limite:

        registros = registros[
            :limite
        ]

    total = len(
        registros
    )

    aprovados = []

    revisar = []

    erros = []

    pulados = []

    inicio = time.time()

    print()
    print("=" * 70)
    print(
        "PROCESSAMENTO EM LOTE"
    )
    print("=" * 70)

    for indice, registro in enumerate(
        registros,
        start=1
    ):

        id_interno = registro.get(
            "id_interno"
        )

        print()
        print(
            f"[{indice}/{total}] "
            f"ID {id_interno}"
        )

        print(
            obter_titulo(
                registro
            )
        )

        if (
            not reprocessar
            and
            artigo_ja_aprovado(
                id_interno
            )
        ):

            print(
                "    JÁ APROVADO - pulando."
            )

            pulados.append(
                id_interno
            )

            aprovados.append(
                id_interno
            )

            continue

        try:

            pacote = processar_registro(
                registro
            )

            if (
                pacote.get(
                    "status"
                )
                ==
                "APROVADO"
            ):

                aprovados.append(
                    id_interno
                )

                print(
                    "    APROVADO"
                )

            else:

                revisar.append(
                    id_interno
                )

                print(
                    "    REVISAR"
                )

        except KeyboardInterrupt:

            print()
            print(
                "Processamento interrompido."
            )

            break

        except Exception as erro:

            print(
                f"    ERRO: {erro}"
            )

            erros.append(
                {
                    "id_interno":
                        id_interno,

                    "titulo":
                        obter_titulo(
                            registro
                        ),

                    "erro":
                        str(
                            erro
                        ),

                    "traceback":
                        traceback.format_exc()
                }
            )

    duracao = (
        time.time()
        - inicio
    )

    relatorio = {
        "executado_em":
            datetime.now().isoformat(),

        "total":
            total,

        "aprovados":
            len(
                set(
                    aprovados
                )
            ),

        "revisar":
            len(
                set(
                    revisar
                )
            ),

        "erros":
            len(
                erros
            ),

        "pulados":
            len(
                pulados
            ),

        "ids_aprovados":
            list(
                dict.fromkeys(
                    aprovados
                )
            ),

        "ids_revisar":
            list(
                dict.fromkeys(
                    revisar
                )
            ),

        "ids_erro":
            [
                item[
                    "id_interno"
                ]
                for item
                in erros
            ],

        "detalhes_erros":
            erros,

        "duracao_minutos":
            round(
                duracao
                / 60,
                2
            ),
    }

    salvar_json(
        relatorio,
        RELATORIO_LOTE_FILE
    )

    print()
    print("=" * 70)
    print(
        "RESULTADO"
    )
    print("=" * 70)

    print(
        f"Aprovados: "
        f"{relatorio['aprovados']}"
    )

    print(
        f"Revisar: "
        f"{relatorio['revisar']}"
    )

    print(
        f"Erros: "
        f"{relatorio['erros']}"
    )

    print(
        f"Pulados: "
        f"{relatorio['pulados']}"
    )

    print(
        f"Tempo: "
        f"{relatorio['duracao_minutos']} min"
    )

    if revisar:

        print()
        print(
            (
                "IDs REVISAR: "
                + ", ".join(
                    str(
                        item
                    )
                    for item
                    in revisar
                )
            )
        )

    if erros:

        print()
        print(
            (
                "IDs ERRO: "
                + ", ".join(
                    str(
                        item[
                            "id_interno"
                        ]
                    )
                    for item
                    in erros
                )
            )
        )


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "id_interno",
        nargs="?"
    )

    parser.add_argument(
        "--todos-ecv",
        action="store_true"
    )

    parser.add_argument(
        "--reprocessar",
        action="store_true"
    )

    parser.add_argument(
        "--limite",
        type=int,
        default=None
    )

    args = parser.parse_args()

    if args.todos_ecv:

        processar_todos(
            reprocessar=args.reprocessar,
            limite=args.limite
        )

        return

    if args.id_interno:

        processar_um(
            args.id_interno
        )

        return

    parser.print_help()


if __name__ == "__main__":
    main()