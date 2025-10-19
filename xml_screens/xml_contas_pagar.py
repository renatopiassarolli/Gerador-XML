# xml_screens/xml_contas_pagar.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton,
    QMessageBox, QDialog, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QFileDialog, QApplication
)
from PyQt5.QtCore import Qt, QRegExp
from PyQt5.QtGui import QRegExpValidator
from utils.xml_utils import gerar_xml_pretty
from utils.db_utils import salvar_xml, listar_xmls, listar_agentes
import xml.etree.ElementTree as ET
import re
from datetime import datetime


class TelaContasPagar(QWidget):
    """Tela para geração e consulta de XMLs de Contas a Pagar vinculados a um Agente"""

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        layout = QVBoxLayout()

        if getattr(self.parent, "conn", None):
            agentes = listar_agentes(self.parent.conn)
            for agente in agentes:
                self.combo_agente.addItem(f"{agente['nome']} ({agente['tipo_pessoa']})", agente["id"])

        # Campos principais
        self.agente_id = None  # Armazena o ID do agente selecionado
        self.agente_nome = QLineEdit()
        self.agente_nome.setReadOnly(True)
        self.agente_cnpj = QLineEdit()
        self.agente_cnpj.setReadOnly(True)
        self.agente_email = QLineEdit()
        self.agente_email.setReadOnly(True)

        self.btn_selecionar_agente = QPushButton("Selecionar Agente")
        self.btn_selecionar_agente.clicked.connect(self.selecionar_agente)

        self.descricao = QLineEdit()
        self.valor = QLineEdit()
        valor_regex = QRegExp(r"^\d{1,9}([.,]\d{0,2})?$")
        self.valor.setValidator(QRegExpValidator(valor_regex))

        self.data_emissao = QLineEdit()
        self.data_emissao.setInputMask("00/00/0000;_")

        self.data_vencimento = QLineEdit()
        self.data_vencimento.setInputMask("00/00/0000;_")

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
        layout.addWidget(QLabel("Agente Vinculado:"))
        layout.addWidget(self.btn_selecionar_agente)
        layout.addWidget(QLabel("Nome:"))
        layout.addWidget(self.agente_nome)
        layout.addWidget(QLabel("CNPJ/CPF:"))
        layout.addWidget(self.agente_cnpj)
        layout.addWidget(QLabel("Email:"))
        layout.addWidget(self.agente_email)

        layout.addWidget(QLabel("Descrição da Conta:"))
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
    def selecionar_agente(self):
        """Abre lista de agentes cadastrados para vincular à conta"""
        if not getattr(self.parent, "conn", None):
            QMessageBox.warning(self, "Erro", "Conecte-se ao Oracle primeiro!")
            return

        try:
            agentes = listar_xmls(self.parent.conn, "XML_AGENTES")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao consultar agentes:\n{e}")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Selecionar Agente")
        layout = QVBoxLayout()

        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["ID", "Nome", "Tipo"])
        table.setRowCount(len(agentes))
        table.setColumnWidth(0, 80)
        table.setColumnWidth(1, 250)
        table.setColumnWidth(2, 150)

        for i, (id_val, xml_val) in enumerate(agentes):
            xml_texto = xml_val if xml_val is not None else ""
            try:
                root = ET.fromstring(xml_texto)
                nome = root.findtext("Nome", "")
                tipo = root.findtext("TipoPessoa", "")
            except ET.ParseError:
                nome = "[XML inválido]"
                tipo = "N/A"

            table.setItem(i, 0, QTableWidgetItem(str(id_val)))
            table.setItem(i, 1, QTableWidgetItem(nome))
            table.setItem(i, 2, QTableWidgetItem(tipo))

        def on_select():
            row = table.currentRow()
            if row < 0:
                QMessageBox.warning(dialog, "Atenção", "Selecione um agente da lista.")
                return
            id_val = int(table.item(row, 0).text())
            xml_texto = agentes[row][1]
            self.preencher_dados_agente(id_val, xml_texto)
            dialog.accept()

        btn_selecionar = QPushButton("Selecionar")
        btn_cancelar = QPushButton("Cancelar")
        btn_selecionar.clicked.connect(on_select)
        btn_cancelar.clicked.connect(dialog.reject)

        botoes = QHBoxLayout()
        botoes.addWidget(btn_selecionar)
        botoes.addWidget(btn_cancelar)

        layout.addWidget(table)
        layout.addLayout(botoes)
        dialog.setLayout(layout)
        dialog.resize(600, 400)
        dialog.exec_()

    # ---------------------------------------------------------------------
    def preencher_dados_agente(self, id_val, xml_texto):
        """Preenche campos com base no XML do agente selecionado"""
        try:
            root = ET.fromstring(xml_texto)
            self.agente_id = id_val
            self.agente_nome.setText(root.findtext("Nome", ""))
            self.agente_cnpj.setText(root.findtext("CNPJ", root.findtext("CPF", "")))
            self.agente_email.setText(root.findtext("Email", ""))
        except ET.ParseError:
            QMessageBox.critical(self, "Erro", "Falha ao ler XML do agente selecionado.")

    # ---------------------------------------------------------------------
    def validar_campos(self):
        """Valida campos obrigatórios"""
        if not self.agente_id:
            return "Selecione um agente antes de continuar."

        if not self.descricao.text().strip():
            return "O campo Descrição é obrigatório."

        if not self.valor.text().strip():
            return "O campo Valor é obrigatório."

        try:
            valor = float(self.valor.text().replace(",", "."))
            if valor <= 0:
                return "O valor deve ser maior que zero."
        except ValueError:
            return "O campo Valor deve conter apenas números."

        for campo, nome in [(self.data_emissao, "Data de Emissão"), (self.data_vencimento, "Data de Vencimento")]:
            data_txt = campo.text().strip()
            if not data_txt or "_" in data_txt:
                return f"{nome} é obrigatória e deve estar completa (dd/mm/aaaa)."
            try:
                datetime.strptime(data_txt, "%d/%m/%Y")
            except ValueError:
                return f"{nome} está em formato inválido. Use dd/mm/aaaa."

        return None

    # ---------------------------------------------------------------------
    def gerar_xml(self):
        """Gera XML de Conta a Pagar vinculado ao agente"""
        erro = self.validar_campos()
        if erro:
            QMessageBox.warning(self, "Erro de validação", erro)
            return

        dados = {
            "AgenteID": str(self.agente_id),
            "AgenteNome": self.agente_nome.text().strip(),
            "CNPJ_CPF": self.agente_cnpj.text().strip(),
            "EmailAgente": self.agente_email.text().strip(),
            "Descricao": self.descricao.text().strip(),
            "Valor": self.valor.text().strip().replace(",", "."),
            "DataEmissao": self.data_emissao.text().strip(),
            "DataVencimento": self.data_vencimento.text().strip(),
        }

        xml_pretty = gerar_xml_pretty("ContaPagar", dados)
        self.xml_preview.setPlainText(xml_pretty)
        QMessageBox.information(self, "Sucesso", "XML gerado com sucesso!")

    # ---------------------------------------------------------------------
    def salvar_xml(self):
        """Salva XML no Oracle"""
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
        """Consulta XMLs de Contas a Pagar"""
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
        """Exibe XML completo com opção de copiar/salvar"""
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
        