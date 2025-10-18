import oracledb

def get_connection():
    try:
        conn = oracledb.connect(
            user="xdb",
            password="1234",
            dsn="localhost:1521/XEPDB1"  # ajuste conforme seu ambiente
        )
        return conn
    except oracledb.DatabaseError as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None

