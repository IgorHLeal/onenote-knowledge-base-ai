import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
PROCESSAMENTO_DIR = os.path.join(OUTPUT_DIR, "processamento")
BASE_BRUTA_FILE = os.path.join(OUTPUT_DIR, "base_bruta.json")
BASE_NORMALIZADA_FILE = os.path.join(PROCESSAMENTO_DIR, "base_normalizada.json")
REGISTRO_IDS_FILE = os.path.join(PROCESSAMENTO_DIR, "registro_ids.json")
RELATORIO_FILE = os.path.join(PROCESSAMENTO_DIR, "relatorio_normalizacao.json")


def carregar_json(caminho, padrao=None):
    if not os.path.exists(caminho):
        if padrao is not None:
            return padrao
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
    with open(caminho, "r", encoding="utf-8-sig") as arquivo:
        return json.load(arquivo)


def salvar_json(dados, caminho):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    temporario = caminho + ".tmp"
    with open(temporario, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=2)
    os.replace(temporario, caminho)


def texto(valor):
    return str(valor or "").replace("\u00a0", " ").replace("\ufffc", "").strip()


def carregar_mapa_ids():
    dados = carregar_json(REGISTRO_IDS_FILE, {"page_ids": {}, "proximo_id": 1})
    dados.setdefault("page_ids", {})
    dados.setdefault("proximo_id", 1)
    return dados


def obter_id_estavel(page_id, mapa):
    chave = texto(page_id)
    if not chave:
        novo = int(mapa["proximo_id"])
        mapa["proximo_id"] = novo + 1
        return novo
    if chave in mapa["page_ids"]:
        return int(mapa["page_ids"][chave])
    novo = int(mapa["proximo_id"])
    mapa["page_ids"][chave] = novo
    mapa["proximo_id"] = novo + 1
    return novo


def normalizar_registro(registro, mapa):
    id_interno = obter_id_estavel(registro.get("page_id"), mapa)
    titulo = texto(registro.get("titulo")) or "Sem título"
    conteudo = texto(registro.get("conteudo_texto"))

    return {
        "id_interno": id_interno,
        "origem": {
            "fonte": registro.get("fonte"),
            "fonte_usuario": registro.get("fonte_usuario"),
            "notebook": registro.get("notebook"),
            "notebook_id": registro.get("notebook_id"),
            "caminho": registro.get("caminho"),
            "secao": registro.get("secao"),
            "page_id": registro.get("page_id"),
            "criada_em": registro.get("criada_em"),
            "alterada_em": registro.get("alterada_em"),
            "arquivo_html": registro.get("arquivo_html"),
        },
        "conteudo": {
            "titulo_original": titulo,
            "titulo_normalizado": titulo,
            "texto": conteudo,
        },
        "controle": {
            "normalizado_em": datetime.now().isoformat(),
            "status": "NORMALIZADO",
        },
    }


def main():
    print("=" * 70)
    print("NORMALIZAÇÃO DA BASE BRUTA")
    print("=" * 70)

    base_bruta = carregar_json(BASE_BRUTA_FILE)
    if not isinstance(base_bruta, list):
        raise ValueError("base_bruta.json deve conter uma lista de registros.")

    mapa = carregar_mapa_ids()
    normalizados = []
    vazios = []

    for registro in base_bruta:
        item = normalizar_registro(registro, mapa)
        normalizados.append(item)
        if not item["conteudo"]["texto"]:
            vazios.append(item["id_interno"])

    normalizados.sort(key=lambda item: int(item["id_interno"]))
    salvar_json(normalizados, BASE_NORMALIZADA_FILE)
    salvar_json(mapa, REGISTRO_IDS_FILE)

    relatorio = {
        "executado_em": datetime.now().isoformat(),
        "registros_entrada": len(base_bruta),
        "registros_normalizados": len(normalizados),
        "registros_sem_texto": len(vazios),
        "ids_sem_texto": vazios,
    }
    salvar_json(relatorio, RELATORIO_FILE)

    print(f"Registros de entrada: {len(base_bruta)}")
    print(f"Registros normalizados: {len(normalizados)}")
    print(f"Registros sem texto: {len(vazios)}")
    print(f"Saída: {BASE_NORMALIZADA_FILE}")


if __name__ == "__main__":
    main()
