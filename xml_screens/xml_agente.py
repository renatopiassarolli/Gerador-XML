# xml_screens/xml_agente.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton,
    QComboBox, QMessageBox, QTableWidget, QTableWidgetItem, QHBoxLayout,
    QDialog, QApplication, QFileDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtCore import QRegExp
from utils.xml_utils import gerar_xml_pretty
from utils.db_utils import salvar_xml, listar_xmls
import re


class TelaAgente(QWidget):
    """Tela de geração e consulta de XMLs de Agente"""
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        layout = QVBoxLayout()

        # Campo para escolher PF ou PJ
        self.tipo_pessoa = QComboBox()
        self.tipo_pessoa.addItems(["Pessoa Física", "Pessoa Jurídica"])
        self.tipo_pessoa.currentIndexChanged.connect(self.alternar_tipo_pessoa)

        # Campos de identificação
        self.nome = QLineEdit()
        self.cpf = QLineEdit()
        self.cnpj = QLineEdit()
        self.tipo = QComboBox()
        self.tipo.addItems(["Cliente", "Fornecedor"])

        # Aplicar máscaras
        self.cpf.setInputMask("000.000.000-00;_")
        self.cnpj.setInputMask("00.000.000/0000-00;_")

        # Campos de contato
        self.endereco = QLineEdit()
        self.telefone = QLineEdit()
        self.telefone.setInputMask("(00) 00000-0000;_")
        self.email = QLineEdit()

        # Validador de e-mail
        email_regex = QRegExp(r"^[\w\.-]+@[\w\.-]+\.\w+$")
        self.email.setValidator(QRegExpValidator(email_regex))

        # Botões principais
        self.btn_gerar = QPushButton("Gerar XML")
        self.btn_salvar = QPushButton("Salvar XML no Oracle")
        self.btn_consultar = QPushButton("Consultar XMLs Gravados")

        self.btn_gerar.clicked.connect(self.gerar_xml)
        self.btn_salvar.clicked.connect(self.salvar_xml)
        self.btn_consultar.clicked.connect(self.consultar_xmls)

        # Campo de visualização do XML
        self.xml_preview = QTextEdit()
        self.xml_preview.setReadOnly(True)

        # Montagem do layout
        layout.addWidget(QLabel("Tipo de Pessoa:"))
        layout.addWidget(self.tipo_pessoa)

        layout.addWidget(QLabel("Nome:"))
        layout.addWidget(self.nome)

        self.label_cpf = QLabel("CPF:")
        layout.addWidget(self.label_cpf)
        layout.addWidget(self.cpf)

        self.label_cnpj = QLabel("CNPJ:")
        layout.addWidget(self.label_cnpj)
        layout.addWidget(self.cnpj)

        layout.addWidget(QLabel("Tipo de Agente:"))
        layout.addWidget(self.tipo)

        layout.addWidget(QLabel("Endereço:"))
        layout.addWidget(self.endereco)

        layout.addWidget(QLabel("Telefone:"))
        layout.addWidget(self.telefone)

        layout.addWidget(QLabel("Email:"))
        layout.addWidget(self.email)

        # Linha de botões
        botoes_row = QHBoxLayout()
        botoes_row.addWidget(self.btn_gerar)
        botoes_row.addWidget(self.btn_salvar)
        botoes_row.addWidget(self.btn_consultar)
        botoes_row.addStretch()
        layout.addLayout(botoes_row)

        layout.addWidget(QLabel("XML Gerado:"))
        layout.addWidget(self.xml_preview)

        self.setLayout(layout)

        # Inicializar visibilidade dos campos
        self.alternar_tipo_pessoa()

    # ---------------------------------------------------------------------

    def alternar_tipo_pessoa(self):
        """Alterna entre exibir CPF ou CNPJ conforme o tipo de pessoa"""
        tipo = self.tipo_pessoa.currentText()
        if tipo == "Pessoa Física":
            self.cpf.show()
            self.label_cpf.show()
            self.cnpj.hide()
            self.label_cnpj.hide()
        else:
            self.cnpj.show()
            self.label_cnpj.show()
            self.cpf.hide()
            self.label_cpf.hide()

    # ---------------------------------------------------------------------

    def validar_campos(self):
        """Valida todos os campos antes de gerar/salvar XML"""
        tipo = self.tipo_pessoa.currentText()

        if not self.nome.text().strip():
            return "O campo Nome é obrigatório."

        if tipo == "Pessoa Física":
            cpf = self.cpf.text().strip().replace(".", "").replace("-", "")
            if len(cpf) != 11:
                return "CPF inválido ou incompleto."
        else:
            cnpj = self.cnpj.text().strip().replace(".", "").replace("/", "").replace("-", "")
            if len(cnpj) != 14:
                return "CNPJ inválido ou incompleto."

        if not self.telefone.text().strip().replace("(", "").replace(")", "").replace("-", "").replace(" ", ""):
            return "Telefone é obrigatório."

        if not self.email.text().strip():
            return "E-mail é obrigatório."

        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", self.email.text().strip()):
            return "E-mail inválido."

        return None  # Nenhum erro

    # ---------------------------------------------------------------------

    def gerar_xml(self):
        """Gera o XML do agente validando os dados"""
        erro = self.validar_campos()
        if erro:
            QMessageBox.warning(self, "Erro de validação", erro)
            return

        tipo_pessoa = self.tipo_pessoa.currentText()
        dados = {
            "Nome": self.nome.text().strip(),
            "TipoPessoa": tipo_pessoa,
            "TipoAgente": self.tipo.currentText(),
            "Endereco": self.endereco.text().strip(),
            "Telefone": self.telefone.text().strip(),
            "Email": self.email.text().strip(),
        }

        if tipo_pessoa == "Pessoa Física":
            dados["CPF"] = self.cpf.text().strip()
        else:
            dados["CNPJ"] = self.cnpj.text().strip()

        xml_pretty = gerar_xml_pretty("Agente", dados)
        self.xml_preview.setPlainText(xml_pretty)
        QMessageBox.information(self, "Sucesso", "XML gerado com sucesso!")

    # ---------------------------------------------------------------------

    def salvar_xml(self):
        """Salva o XML no banco Oracle"""
        if not getattr(self.parent, "conn", None):
            QMessageBox.warning(self, "Erro", "Conecte-se ao Oracle primeiro!")
            return

        xml_conteudo = self.xml_preview.toPlainText().strip()
        if not xml_conteudo:
            QMessageBox.warning(self, "Erro", "Nenhum XML gerado para salvar.")
            return

        try:
            salvar_xml(self.parent.conn, "XML_AGENTES", xml_conteudo)
            QMessageBox.information(self, "Sucesso", "XML salvo no banco com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar XML:\n{e}")

    # ---------------------------------------------------------------------

    def consultar_xmls(self):
        """Lista os XMLs gravados no Oracle"""
        if not getattr(self.parent, "conn", None):
            QMessageBox.warning(self, "Erro", "Conecte-se ao Oracle primeiro!")
            return

        try:
            rows = listar_xmls(self.parent.conn, "XML_AGENTES")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao consultar XMLs:\n{e}")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("XMLs de Agentes Gravados")
        layout = QVBoxLayout()

        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["ID", "Preview", "Ações"])
        table.setRowCount(len(rows))
        table.setColumnWidth(0, 80)
        table.setColumnWidth(1, 300)
        table.setColumnWidth(2, 150)

        for i, (id_val, xml_val) in enumerate(rows):
            xml_texto = xml_val if xml_val is not None else ""
            item_id = QTableWidgetItem(str(id_val))
            item_id.setFlags(item_id.flags() ^ Qt.ItemIsEditable)
            table.setItem(i, 0, item_id)

            preview_text = (xml_texto[:150] + "...") if len(xml_texto) > 150 else xml_texto
            item_preview = QTableWidgetItem(preview_text)
            item_preview.setFlags(item_preview.flags() ^ Qt.ItemIsEditable)
            table.setItem(i, 1, item_preview)

            btn = QPushButton("Ver XML")
            btn.clicked.connect(lambda _, x=xml_texto, idv=id_val: self.ver_xml(idv, x))
            table.setCellWidget(i, 2, btn)

        layout.addWidget(table)
        dialog.setLayout(layout)
        dialog.resize(800, 500)
        dialog.exec_()

    # ---------------------------------------------------------------------

    def ver_xml(self, id_val, xml_texto):
        """Abre janela com o XML completo + botões de copiar/salvar"""
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Visualizar XML - ID {id_val}")
        layout = QVBoxLayout()

        txt = QTextEdit()
        txt.setPlainText(xml_texto)
        txt.setReadOnly(True)
        layout.addWidget(txt)

        botoes = QHBoxLayout()
        btn_copiar = QPushButton("Copiar XML")
        btn_salvar_arquivo = QPushButton("Salvar como .xml")
        btn_fechar = QPushButton("Fechar")

        def copiar():
            app = QApplication.instance()
            if app:
                app.clipboard().setText(xml_texto)
                QMessageBox.information(dlg, "Copiado", "XML copiado para a área de transferência!")
            else:
                QMessageBox.warning(dlg, "Erro", "Não foi possível acessar a área de transferência.")

        def salvar_arquivo():
            fname, _ = QFileDialog.getSaveFileName(dlg, "Salvar XML", f"agente_{id_val}.xml", "Arquivos XML (*.xml)")
            if fname:
                try:
                    with open(fname, "w", encoding="utf-8") as f:
                        f.write(xml_texto)
                    QMessageBox.information(dlg, "Salvo", f"Arquivo salvo em:\n{fname}")
                except Exception as e:
                    QMessageBox.critical(dlg, "Erro", f"Falha ao salvar arquivo:\n{e}")

        btn_copiar.clicked.connect(copiar)
        btn_salvar_arquivo.clicked.connect(salvar_arquivo)
        btn_fechar.clicked.connect(dlg.close)

        botoes.addWidget(btn_copiar)
        botoes.addWidget(btn_salvar_arquivo)
        botoes.addStretch()
        botoes.addWidget(btn_fechar)

        layout.addLayout(botoes)
        dlg.setLayout(layout)
        dlg.resize(700, 550)
        dlg.exec_()
        