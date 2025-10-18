"""
utils/db_utils.py
Implementação usando python-oracledb (import as oracledb).
Fornece: conectar_oracle, desconectar_oracle, testar_conexao,
         salvar_xml, listar_xmls, listar_agentes.
"""

import oracledb
import xml.etree.ElementTree as ET
from contextlib import contextmanager

# ---------- CONFIGURAÇÃO OPCIONAL DO INSTANT CLIENT (thick mode) ----------
# Se precisar usar o Instant Client (modo thick), descomente e ajuste o caminho:
# oracledb.init_oracle_client(lib_dir=r"C:\oracle\instantclient_19_11")

# ---------- FUNÇÕES DE CONEXÃO ----------
def conectar_oracle(usuario: str, senha: str, tns: str):
    """
    Abre e retorna uma conexão oracledb.Connection.
    tns pode ser:
      - "host:port/service_name"  (ex: "localhost:1521/XEPDB1")
      - um alias TNS (se Instant Client e tnsnames.ora estiverem configurados)
    """
    conn = oracledb.connect(user=usuario, password=senha, dsn=tns)
    return conn


def desconectar_oracle(conn):
    """Fecha a conexão se existir"""
    try:
        if conn:
            conn.close()
    except Exception:
        pass


def testar_conexao(conn):
    """Retorna True se a conexão está válida"""
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM DUAL")
        cur.close()
        return True
    except Exception:
        return False


# ---------- FUNÇÕES DE XML ----------
def salvar_xml(conn, tabela: str, xml_conteudo: str):
    """
    Insere um XML na tabela informada.
    Atenção: tabela deve ter coluna XML_CONTEUDO do tipo XMLTYPE ou CLOB conforme o DB.
    """
    sql = f"""
        INSERT INTO {tabela} (ID, XML_CONTEUDO)
        VALUES (SEQ_{tabela}.NEXTVAL, XMLType(:xml))
    """
    cur = conn.cursor()
    try:
        cur.execute(sql, {"xml": xml_conteudo})
        conn.commit()
    finally:
        cur.close()


def listar_xmls(conn, tabela: str):
    """
    Retorna lista de tuplas (ID, xml_texto).
    Converte LOBs em string usando XMLSERIALIZE para compatibilidade.
    """
    sql = f"""
        SELECT ID,
               XMLSERIALIZE(CONTENT XML_CONTEUDO AS CLOB) AS XML_TEXTO
        FROM {tabela}
        ORDER BY ID DESC
    """
    cur = conn.cursor()
    try:
        cur.execute(sql)
        rows = []
        for r in cur.fetchall():
            id_val = r[0]
            xml_val = r[1]
            if hasattr(xml_val, "read"):
                xml_text = xml_val.read()
            else:
                xml_text = str(xml_val) if xml_val is not None else ""
            rows.append((id_val, xml_text))
        return rows
    finally:
        cur.close()


# ---------- NOVA FUNÇÃO: LISTAR AGENTES ----------
def listar_agentes(conn):
    """
    Retorna lista de agentes cadastrados na tabela XML_AGENTES.
    Faz o parse básico do XML para extrair Nome e TipoPessoa.

    Retorna lista de dicionários:
    [
        {"id": 1, "nome": "Empresa XPTO", "tipo_pessoa": "Pessoa Jurídica", "xml": "<xml...>"},
        {"id": 2, "nome": "João Silva", "tipo_pessoa": "Pessoa Física", "xml": "<xml...>"},
    ]
    """
    agentes = []
    try:
        cur = conn.cursor()
        sql = """
            SELECT ID, XMLSERIALIZE(CONTENT XML_CONTEUDO AS CLOB)
            FROM XML_AGENTES
            ORDER BY ID DESC
        """
        cur.execute(sql)

        for id_val, xml_val in cur.fetchall():
            if hasattr(xml_val, "read"):
                xml_text = xml_val.read()
            else:
                xml_text = str(xml_val) if xml_val is not None else ""

            nome = tipo_pessoa = ""
            try:
                root = ET.fromstring(xml_text)
                nome = root.findtext("Nome", "").strip()
                tipo_pessoa = root.findtext("TipoPessoa", "").strip()
            except Exception:
                nome = "[XML Inválido]"
                tipo_pessoa = "Desconhecido"

            agentes.append({
                "id": id_val,
                "nome": nome or "[Sem Nome]",
                "tipo_pessoa": tipo_pessoa or "N/A",
                "xml": xml_text
            })

        return agentes
    finally:
        cur.close()
