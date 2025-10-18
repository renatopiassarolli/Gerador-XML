import sys
import os
import json
import keyring
import oracledb
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox, QTextEdit, QDialog, QFormLayout,
    QStatusBar, QGridLayout, QTabWidget
)
from xml.etree.ElementTree import Element, tostring, SubElement
from xml.dom.minidom import parseString
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QPushButton, QDialog, QTextEdit

CONFIG_FILE = "config.json"

# --------------------------------------------------------
# Diálogo de Conexão com o Banco Oracle
# --------------------------------------------------------
class ConexaoDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Conexão com Banco Oracle")
        self.conn = None

        layout = QFormLayout()

        self.dsn_input = QLineEdit("localhost:1521/XEPDB1")
        self.user_input = QLineEdit()
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.Password)

        layout.addRow("TNS / DSN:", self.dsn_input)
        layout.addRow("Usuário (Owner):", self.user_input)
        layout.addRow("Senha:", self.pass_input)

        btn_testar = QPushButton("Testar Conexão")
        btn_conectar = QPushButton("Conectar")

        btn_testar.clicked.connect(self.testar_conexao)
        btn_conectar.clicked.connect(self.conectar)

        hbox = QHBoxLayout()
        hbox.addWidget(btn_testar)
        hbox.addWidget(btn_conectar)

        layout.addRow(hbox)
        self.setLayout(layout)

    def testar_conexao(self):
        try:
            conn = oracledb.connect(
                user=self.user_input.text(),
                password=self.pass_input.text(),
                dsn=self.dsn_input.text()
            )
            conn.close()
            QMessageBox.information(self, "Sucesso", "Conexão estabelecida com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro de conexão", str(e))

    def conectar(self):
        try:
            self.conn = oracledb.connect(
                user=self.user_input.text(),
                password=self.pass_input.text(),
                dsn=self.dsn_input.text()
            )
            self.salvar_config()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível conectar: {e}")

    def salvar_config(self):
        dados = {
            "dsn": self.dsn_input.text(),
            "user": self.user_input.text()
        }
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(dados, f, indent=4)
            keyring.set_password("app_xml_oracle", dados["user"], self.pass_input.text())
        except Exception as e:
            print("Falha ao salvar config:", e)


# --------------------------------------------------------
# Janela Principal
# --------------------------------------------------------
class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gerador e Gravador de XML - Oracle")
        self.conn = None
        self.initUI()
        self.carregar_ultima_conexao()

    def initUI(self):
        # -------------------
        # Abas principais
        # -------------------
        self.tabs = QTabWidget()
        self.tab_gerar = QWidget()
        self.tab_consultar = QWidget()

        self.tabs.addTab(self.tab_gerar, "Gerar XML")
        self.tabs.addTab(self.tab_consultar, "Consultar XMLs")

        # ===================
        # Aba 1 — Gerar XML
        # ===================
        from PyQt5.QtGui import QRegularExpressionValidator
        from PyQt5.QtCore import QRegularExpression
        from PyQt5.QtWidgets import QComboBox

        self.nome_input = QLineEdit()
        self.cnpj_input = QLineEdit()
        self.tipo_input = QComboBox()
        self.endereco_input = QLineEdit()
        self.telefone_input = QLineEdit()
        self.email_input = QLineEdit()

        # --- Máscaras e validações ---
        # CNPJ -> 99.999.999/9999-99
        self.cnpj_input.setInputMask("00.000.000/0000-00;_")

        # Telefone -> (99) 99999-9999
        self.telefone_input.setInputMask("(00) 00000-0000;_")

        # Email -> validação com regex simples
        email_regex = QRegularExpression(r"^[\w\.-]+@[\w\.-]+\.\w{2,4}$")
        email_validator = QRegularExpressionValidator(email_regex, self.email_input)
        self.email_input.setValidator(email_validator)

        # Tipo -> Combobox com opções fixas
        self.tipo_input.addItems(["", "Cliente", "Fornecedor"])

        # Layout do formulário
        form_layout = QGridLayout()
        form_layout.addWidget(QLabel("Nome:"), 0, 0)
        form_layout.addWidget(self.nome_input, 0, 1)
        form_layout.addWidget(QLabel("CNPJ:"), 1, 0)
        form_layout.addWidget(self.cnpj_input, 1, 1)
        form_layout.addWidget(QLabel("Tipo:"), 2, 0)
        form_layout.addWidget(self.tipo_input, 2, 1)
        form_layout.addWidget(QLabel("Endereço:"), 3, 0)
        form_layout.addWidget(self.endereco_input, 3, 1)
        form_layout.addWidget(QLabel("Telefone:"), 4, 0)
        form_layout.addWidget(self.telefone_input, 4, 1)
        form_layout.addWidget(QLabel("E-mail:"), 5, 0)
        form_layout.addWidget(self.email_input, 5, 1)

        # Campo de visualização do XML
        self.xml_preview = QTextEdit()
        self.xml_preview.setReadOnly(True)

        # Botões
        self.btn_gerar = QPushButton("Gerar XML")
        self.btn_salvar = QPushButton("Salvar XML no Oracle")

        self.btn_gerar.clicked.connect(self.gerar_xml)
        self.btn_salvar.clicked.connect(self.salvar_xml)

        botoes_xml = QHBoxLayout()
        botoes_xml.addWidget(self.btn_gerar)
        botoes_xml.addWidget(self.btn_salvar)

        layout_gerar = QVBoxLayout()
        layout_gerar.addLayout(form_layout)
        layout_gerar.addWidget(QLabel("Pré-visualização do XML:"))
        layout_gerar.addWidget(self.xml_preview)
        layout_gerar.addLayout(botoes_xml)
        self.tab_gerar.setLayout(layout_gerar)

        # ===================
        # Aba 2 — Consultar XMLs
        # ===================
        self.tabela_xmls = QTableWidget()
        self.tabela_xmls.setColumnCount(2)
        self.tabela_xmls.setHorizontalHeaderLabels(["ID", "Ações"])
        self.tabela_xmls.setColumnWidth(0, 100)
        self.tabela_xmls.setColumnWidth(1, 200)

        self.btn_consultar = QPushButton("Consultar XMLs Gravados")
        self.btn_consultar.clicked.connect(self.consultar_xmls)

        layout_consulta = QVBoxLayout()
        layout_consulta.addWidget(QLabel("Registros encontrados no banco:"))
        layout_consulta.addWidget(self.tabela_xmls)
        layout_consulta.addWidget(self.btn_consultar)
        self.tab_consultar.setLayout(layout_consulta)


        # -------------------
        # Botões de conexão
        # -------------------
        self.btn_conectar = QPushButton("Conectar Banco")
        self.btn_desconectar = QPushButton("Desconectar")
        self.btn_conectar.clicked.connect(self.abrir_conexao)
        self.btn_desconectar.clicked.connect(self.desconectar)

        botoes_conexao = QHBoxLayout()
        botoes_conexao.addWidget(self.btn_conectar)
        botoes_conexao.addWidget(self.btn_desconectar)

        # -------------------
        # Layout principal
        # -------------------
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)
        main_layout.addLayout(botoes_conexao)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Barra de status
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Aplicação iniciada")

    # --------------------------
    # Conexão
    # --------------------------
    def carregar_ultima_conexao(self):
        try:
            if not os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "w") as f:
                    json.dump({}, f)

            with open(CONFIG_FILE, "r") as f:
                dados = json.load(f)

            if dados and "user" in dados and "dsn" in dados:
                senha = keyring.get_password("app_xml_oracle", dados["user"])
                if senha:
                    self.conn = oracledb.connect(
                        user=dados["user"],
                        password=senha,
                        dsn=dados["dsn"]
                    )
                    self.statusbar.showMessage(f"Conectado a {dados['dsn']}")
                else:
                    self.statusbar.showMessage("Senha não encontrada — reconecte.")
            else:
                self.statusbar.showMessage("Nenhuma conexão salva.")
        except Exception as e:
            print("Falha ao carregar conexão:", e)
            self.statusbar.showMessage("Erro ao carregar conexão. Reconecte manualmente.")

    def abrir_conexao(self):
        dialog = ConexaoDialog()
        if dialog.exec_():
            self.conn = dialog.conn
            if self.conn:
                self.statusbar.showMessage("Conexão estabelecida com sucesso.")

    def desconectar(self):
        try:
            if self.conn:
                self.conn.close()
                self.conn = None
                self.statusbar.showMessage("Desconectado do banco Oracle.")
            else:
                self.statusbar.showMessage("Nenhuma conexão ativa.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao desconectar: {e}")

    # --------------------------
    # Gerar XML
    # --------------------------
    def gerar_xml(self):
        """Gera o XML após validar todos os campos"""
        nome = self.nome_input.text().strip()
        cnpj = self.cnpj_input.text().strip()
        tipo = self.tipo_input.currentText().strip()
        endereco = self.endereco_input.text().strip()
        telefone = self.telefone_input.text().strip()
        email = self.email_input.text().strip()

        # ======== Validações ========

        # Nome
        if not nome:
            QMessageBox.warning(self, "Campo obrigatório", "Informe o nome do agente.")
            self.nome_input.setFocus()
            return

        # CNPJ
        cnpj_limpo = "".join([c for c in cnpj if c.isdigit()])
        if len(cnpj_limpo) != 14:
            QMessageBox.warning(self, "CNPJ inválido", "Informe um CNPJ válido (14 dígitos).")
            self.cnpj_input.setFocus()
            return

        # Tipo
        if not tipo:
            QMessageBox.warning(self, "Tipo não selecionado", "Selecione o tipo do agente (Cliente ou Fornecedor).")
            self.tipo_input.setFocus()
            return

        # Endereço
        if not endereco:
            QMessageBox.warning(self, "Campo obrigatório", "Informe o endereço do agente.")
            self.endereco_input.setFocus()
            return

        # Telefone
        telefone_limpo = "".join([c for c in telefone if c.isdigit()])
        if len(telefone_limpo) not in (10, 11):
            QMessageBox.warning(self, "Telefone inválido", "Informe um número de telefone válido com DDD.")
            self.telefone_input.setFocus()
            return

        # Email
        import re
        padrao_email = r'^[\w\.-]+@[\w\.-]+\.\w{2,4}$'
        if not re.match(padrao_email, email):
            QMessageBox.warning(self, "E-mail inválido", "Informe um e-mail válido.")
            self.email_input.setFocus()
            return

        # ======== Geração do XML ========
        from xml.etree.ElementTree import Element, SubElement, tostring
        from xml.dom.minidom import parseString

        root = Element("Agente")
        SubElement(root, "Nome").text = nome
        SubElement(root, "CNPJ").text = cnpj
        SubElement(root, "Tipo").text = tipo
        SubElement(root, "Endereco").text = endereco
        SubElement(root, "Telefone").text = telefone
        SubElement(root, "Email").text = email

        xml_bytes = tostring(root, 'utf-8')
        xml_pretty = parseString(xml_bytes).toprettyxml(indent="  ")

        self.xml_preview.setPlainText(xml_pretty)
        self.statusbar.showMessage("XML gerado com sucesso.")
        QMessageBox.information(self, "Sucesso", "XML gerado com sucesso!")

    # --------------------------
    # Salvar no Oracle
    # --------------------------
    def salvar_xml(self):
        if not self.conn:
            QMessageBox.warning(self, "Aviso", "Conecte-se ao banco antes de salvar.")
            return
        try:
            xml_conteudo = self.xml_preview.toPlainText()
            cur = self.conn.cursor()
            cur.execute("""
                INSERT INTO TABELA_XML (ID, XML_CONTEUDO)
                VALUES (SEQ_TABELA_XML.NEXTVAL, XMLTYPE(:xml_data))
            """, xml_data=xml_conteudo)
            self.conn.commit()
            cur.close()
            QMessageBox.information(self, "Sucesso", "XML salvo com sucesso!")
            self.statusbar.showMessage("XML salvo com sucesso.")
        except Exception as e:
            QMessageBox.critical(self, "Erro ao salvar", str(e))
            self.statusbar.showMessage("Erro ao salvar XML.")

    # --------------------------
    # Consultar XMLs
    # --------------------------
    def consultar_xmls(self):
        """Consulta os XMLs gravados e mostra em grid"""
        if not self.conn:
            QMessageBox.warning(self, "Aviso", "Conecte-se ao banco antes de consultar.")
            return

        try:
            cur = self.conn.cursor()
            cur.execute("""
                SELECT ID, XMLSERIALIZE(CONTENT XML_CONTEUDO AS CLOB)
                FROM TABELA_XML
                ORDER BY ID DESC
            """)
            rows = cur.fetchall()
            cur.close()

            self.tabela_xmls.setRowCount(0)

            if not rows:
                QMessageBox.information(self, "Consulta", "Nenhum XML encontrado.")
                return

            self.tabela_xmls.setRowCount(len(rows))

            for i, (id_val, xml_val) in enumerate(rows):
                # Coluna 1 - ID
                self.tabela_xmls.setItem(i, 0, QTableWidgetItem(str(id_val)))

                # Coluna 2 - Botão de Visualizar
                btn_ver = QPushButton("Visualizar XML")
                btn_ver.clicked.connect(lambda _, xml=xml_val, id=id_val: self.mostrar_xml(id, str(xml.read()) if hasattr(xml, "read") else str(xml)))
                self.tabela_xmls.setCellWidget(i, 1, btn_ver)

            self.statusbar.showMessage(f"{len(rows)} registros carregados.")
        except Exception as e:
            QMessageBox.critical(self, "Erro ao consultar", str(e))
            self.statusbar.showMessage("Erro ao consultar XMLs.")

    def mostrar_xml(self, id_registro, xml_conteudo):
        """Mostra o XML completo em uma janela modal com opção de copiar"""
        # Converte o LOB (caso ainda venha como tal)
        if hasattr(xml_conteudo, "read"):
            xml_texto = xml_conteudo.read()
        else:
            xml_texto = str(xml_conteudo)

        # Cria a janela modal
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Visualização do XML - ID {id_registro}")
        dialog.resize(700, 600)

        layout = QVBoxLayout()

        # Campo de texto somente leitura
        texto = QTextEdit()
        texto.setPlainText(xml_texto)
        texto.setReadOnly(True)
        texto.setStyleSheet(
            "font-family: Consolas, monospace; font-size: 12pt; background-color: #f8f8f8; padding: 6px;"
        )

        # Botões
        btn_copiar = QPushButton("Copiar XML")
        btn_fechar = QPushButton("Fechar")

        # Função para copiar o XML
        def copiar_xml():
            clipboard = QApplication.clipboard()
            clipboard.setText(xml_texto)
            QMessageBox.information(dialog, "Copiado", "XML copiado para a área de transferência!")

        btn_copiar.clicked.connect(copiar_xml)
        btn_fechar.clicked.connect(dialog.close)

        # Layout de botões lado a lado
        botoes_layout = QHBoxLayout()
        botoes_layout.addWidget(btn_copiar)
        botoes_layout.addStretch()
        botoes_layout.addWidget(btn_fechar)

        # Monta a interface
        layout.addWidget(QLabel(f"<b>XML do registro ID {id_registro}:</b>"))
        layout.addWidget(texto)
        layout.addLayout(botoes_layout)

        dialog.setLayout(layout)
        dialog.exec_()


# --------------------------------------------------------
# Execução principal
# --------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = App()
    janela.show()
    sys.exit(app.exec_())
