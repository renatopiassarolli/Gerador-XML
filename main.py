import sys
import json
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QStackedWidget, QLineEdit, QLabel, QMessageBox
)
from xml_screens.xml_agente import TelaAgente
from xml_screens.xml_contas_pagar import TelaContasPagar
from utils.db_utils import conectar_oracle, desconectar_oracle, testar_conexao


class MainWindow(QMainWindow):
    """Janela principal do sistema"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gerador de XMLs com Oracle")
        self.resize(900, 750)

        self.conn = None
        self.config_path = "config.json"

        # ==========================
        # Topo - Área de conexão
        # ==========================
        self.tns_input = QLineEdit()
        self.user_input = QLineEdit()
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.Password)

        self.btn_conectar = QPushButton("Conectar")
        self.btn_desconectar = QPushButton("Desconectar")

        self.btn_conectar.clicked.connect(self.conectar)
        self.btn_desconectar.clicked.connect(self.desconectar)

        top_conn_layout = QHBoxLayout()
        top_conn_layout.addWidget(QLabel("TNS:"))
        top_conn_layout.addWidget(self.tns_input)
        top_conn_layout.addWidget(QLabel("Usuário:"))
        top_conn_layout.addWidget(self.user_input)
        top_conn_layout.addWidget(QLabel("Senha:"))
        top_conn_layout.addWidget(self.pass_input)
        top_conn_layout.addWidget(self.btn_conectar)
        top_conn_layout.addWidget(self.btn_desconectar)

        # ==========================
        # Menu superior de telas
        # ==========================
        self.btn_agente = QPushButton("Cadastro de Agente")
        self.btn_contas = QPushButton("Contas a Pagar")

        top_menu_layout = QHBoxLayout()
        top_menu_layout.addWidget(self.btn_agente)
        top_menu_layout.addWidget(self.btn_contas)
        top_menu_layout.addStretch()

        # ==========================
        # Stack de telas
        # ==========================
        self.stack = QStackedWidget()
        self.tela_agente = TelaAgente(self)
        self.tela_contas = TelaContasPagar(self)
        self.stack.addWidget(self.tela_agente)
        self.stack.addWidget(self.tela_contas)

        # ==========================
        # Layout principal
        # ==========================
        main_layout = QVBoxLayout()
        main_layout.addLayout(top_conn_layout)
        main_layout.addLayout(top_menu_layout)
        main_layout.addWidget(self.stack)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Liga botões às telas
        self.btn_agente.clicked.connect(lambda: self.stack.setCurrentWidget(self.tela_agente))
        self.btn_contas.clicked.connect(lambda: self.stack.setCurrentWidget(self.tela_contas))

        # Tenta carregar última conexão
        self.carregar_config()

    # ======================================================
    # Conexão Oracle
    # ======================================================
    def conectar(self):
        tns = self.tns_input.text().strip()
        usuario = self.user_input.text().strip()
        senha = self.pass_input.text().strip()

        if not all([tns, usuario, senha]):
            QMessageBox.warning(self, "Erro", "Preencha todos os campos de conexão!")
            return

        try:
            self.conn = conectar_oracle(usuario, senha, tns)
            if self.conn:
                QMessageBox.information(self, "Conectado", "Conexão com Oracle estabelecida!")
                self.salvar_config(tns, usuario)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao conectar:\n{e}")

    def desconectar(self):
        if self.conn:
            desconectar_oracle(self.conn)
            self.conn = None
            QMessageBox.information(self, "Desconectado", "Conexão encerrada.")
        else:
            QMessageBox.warning(self, "Aviso", "Nenhuma conexão ativa.")

    def carregar_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                cfg = json.load(f)
                self.tns_input.setText(cfg.get("tns", ""))
                self.user_input.setText(cfg.get("usuario", ""))

    def salvar_config(self, tns, usuario):
        with open(self.config_path, "w") as f:
            json.dump({"tns": tns, "usuario": usuario}, f, indent=4)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
