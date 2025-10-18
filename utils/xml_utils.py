from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString


def gerar_xml_pretty(root_tag, dados_dict):
    """Gera XML formatado com indentação bonita"""
    root = Element(root_tag)
    for chave, valor in dados_dict.items():
        SubElement(root, chave).text = valor or ""
    xml_bytes = tostring(root, 'utf-8')
    xml_pretty = parseString(xml_bytes).toprettyxml(indent="  ")
    return xml_pretty
