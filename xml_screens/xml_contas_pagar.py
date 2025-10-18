# xml_screens/xml_contas_pagar.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton,
    QMessageBox, QDialog, QHBoxLayout, QTableWidget, QTableWidgetItem, QFileDialog, QApplication
)
from PyQt5.QtCore import Qt, QRegExp
from PyQt5.QtGui import QRegExpValidator
from utils.xml_utils import gerar_xml_pretty
from utils.db_utils import salvar_xml, listar_xmls
import re
from datetime import datetime


class TelaContasPagar(QWidget):
    """Tela para geração e consulta de XMLs de Contas a Pagar"""

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        layout = QVBoxLayout()

        # Campos principais
        self.fornecedor = QLineEdit()
        self.cnpj_fornecedor = QLineEdit()
        self.cnpj_fornecedor.setInputMask("00.000.000/0000-00;_")

        self.data_emissao = QLineEdit()
        self.data_emissao.setInputMask("00/00/0000;_")

        self.data_vencimento = QLineEdit()
        self.data_vencimento.setInputMask("00/00/0000;_")

        self.valor = QLineEdit()
        valor_regex = QRegExp(r"^\d{1,9}([.,]\d{0,2})?$")
        self.valor.setValidator(QRegExpValidator(valor_regex))

        self.descricao = QLineEdit()
        self.email_fornecedor = QLineEdit()

        email_regex = QRegExp(r"^[\w\.-]+@[\w\.-]+\.\w+$")
        self.email_fornecedor.setValidator(QRegExpValidator(email_regex))

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

        # Layout
        layout.addWidget(QLabel("Fornecedor:"))
        layout.addWidget(self.fornecedor)

        layout.addWidget(QLabel("CNPJ do Fornecedor:"))
        layout.addWidget(self.cnpj_fornecedor)

        layout.addWidget(QLabel("Email do Fornecedor (opcional):"))
        layout.addWidget(self.email_fornecedor)

        layout.addWidget(QLabel("Descrição:"))
        layout.addWidget(self.descricao)

        layout.addWidget(QLabel("Valor (R$):"))
        layout.addWidget(self.valor)

        layout.addWidget(QLabel("Data de Emissão:"))
        layout.addWidget(self.data_emissao)

        layout.addWidget(QLabel("Data de Vencimento:"))
        layout.addWidget(self.data_vencimento)

        botoes_row = QHBoxLayout()
        botoes_row.addWidget(self.btn_gerar)
        botoes_row.addWidget(self.btn_salvar)
        botoes_row.addWidget(self.btn_consultar)
        botoes_row.addStretch()
        layout.addLayout(botoes_row)

        layout.addWidget(QLabel("XML Gerado:"))
        layout.addWidget(self.xml_preview)

        self.setLayout(layout)

    # ---------------------------------------------------------------------

    def validar_campos(self):
        """Valida todos os campos obrigatórios e formatos"""
        if not self.fornecedor.text().strip():
            return "O campo Fornecedor é obrigatório."

        cnpj = self.cnpj_fornecedor.text().strip().replace(".", "").replace("/", "").replace("-", "")
        if len(cnpj) != 14:
            return "CNPJ inválido ou incompleto."

        if not self.valor.text().strip():
            return "O campo Valor é obrigatório."

        # Verifica se o valor é numérico
        valor_txt = self.valor.text().replace(",", ".")
        try:
            valor_float = float(valor_txt)
            if valor_float <= 0:
                return "O valor deve ser maior que zero."
        except ValueError:
            return "O campo Valor deve conter apenas números."

        # Verifica formato das datas
        for campo, nome in [(self.data_emissao, "Data de Emissão"), (self.data_vencimento, "Data de Vencimento")]:
            data_txt = campo.text().strip()
            if not data_txt or "_" in data_txt:
                return f"{nome} é obrigatória e deve estar completa (dd/mm/aaaa)."
            try:
                datetime.strptime(data_txt, "%d/%m/%Y")
            except ValueError:
                return f"{nome} está em formato inválido. Use dd/mm/aaaa."

        # Valida e-mail (se preenchido)
        email = self.email_fornecedor.text().strip()
        if email and not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
            return "E-mail do fornecedor inválido."

        return None  # sem erros

    # ---------------------------------------------------------------------

    def gerar_xml(self):
        """Gera XML validado"""
        erro = self.validar_campos()
        if erro:
            QMessageBox.warning(self, "Erro de validação", erro)
            return

        dados = {
            "Fornecedor": self.fornecedor.text().strip(),
            "CNPJ": self.cnpj_fornecedor.text().strip(),
            "Descricao": self.descricao.text().strip(),
            "Valor": self.valor.text().strip().replace(",", "."),
            "DataEmissao": self.data_emissao.text().strip(),
            "DataVencimento": self.data_vencimento.text().strip(),
        }

        if self.email_fornecedor.text().strip():
            dados["EmailFornecedor"] = self.email_fornecedor.text().strip()

        xml_pretty = gerar_xml_pretty("ContaPagar", dados)
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
            salvar_xml(self.parent.conn, "XML_CONTAS_PAGAR", xml_conteudo)
            QMessageBox.information(self, "Sucesso", "XML salvo no banco com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar XML:\n{e}")

    # ---------------------------------------------------------------------

    def consultar_xmls(self):
        """Consulta XMLs gravados"""
        if not getattr(self.parent, "conn", None):
            QMessageBox.warning(self, "Erro", "Conecte-se ao Oracle primeiro!")
            return

        try:
            rows = listar_xmls(self.parent.conn, "XML_CONTAS_PAGAR")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao consultar XMLs:\n{e}")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("XMLs de Contas a Pagar Gravados")
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
        """Visualiza XML completo com botão de copiar/salvar"""
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

        def salvar_arquivo():
            fname, _ = QFileDialog.getSaveFileName(dlg, "Salvar XML", f"conta_pagar_{id_val}.xml", "Arquivos XML (*.xml)")
            if fname:
                with open(fname, "w", encoding="utf-8") as f:
                    f.write(xml_texto)
                QMessageBox.information(dlg, "Salvo", f"Arquivo salvo em:\n{fname}")

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