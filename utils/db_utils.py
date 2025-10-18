"""
utils/db_utils.py
Implementação usando python-oracledb (import as oracledb).
Fornece: conectar_oracle, desconectar_oracle, testar_conexao,
         salvar_xml, listar_xmls.
"""

import oracledb
from contextlib import contextmanager

# ---------- CONFIGURAÇÃO OPCIONAL DO INSTANT CLIENT (thick mode) ----------
# Se precisar usar o Instant Client (modo thick), descomente e ajuste o caminho:
# oracledb.init_oracle_client(lib_dir=r"C:\oracle\instantclient_19_11")

# ---------- FUNÇÕES ----------
def conectar_oracle(usuario: str, senha: str, tns: str):
    """
    Abre e retorna uma conexão oracledb.Connection.
    tns pode ser:
      - "host:port/service_name"  (ex: "localhost:1521/XEPDB1")
      - um alias TNS (se Instant Client e tnsnames.ora estiverem configurados)
    """
    # Em modo thin (padrão) basta passar dsn = tns
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


def salvar_xml(conn, tabela: str, xml_conteudo: str):
    """
    Insere um XML na tabela informada.
    Atenção: tabela deve ter coluna XML_CONTEUDO do tipo XMLTYPE ou CLOB conforme o DB.
    Usamos bind para evitar SQL injection.
    """
    sql = f"INSERT INTO {tabela} (ID, XML_CONTEUDO) VALUES (SEQ_{tabela}.NEXTVAL, XMLType(:xml))"
    # Observação: se sua sequência tiver outro nome, ajuste.
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
            # oracledb já devolve string ou LOB; se for LOB, chamar read()
            if hasattr(xml_val, "read"):
                xml_text = xml_val.read()
            else:
                xml_text = str(xml_val) if xml_val is not None else ""
            rows.append((id_val, xml_text))
        return rows
    finally:
        cur.close()
