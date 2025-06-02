import streamlit as st
from pymongo import MongoClient
from datetime import datetime
from fpdf import FPDF
import base64
from bson.objectid import ObjectId

# --- CONEXÃO COM MONGODB USANDO st.secrets ---
def conectar_mongodb():
    try:
        db_url = st.secrets["database"]["url"]
        client = MongoClient(db_url)
        db = client["decio_orcamentos"]
        return db["orcamentos"]
    except KeyError as e:
        st.error(f"Erro de configuração: {e}. Verifique se você configurou corretamente os segredos.")
        st.stop()

colecao = conectar_mongodb()

# --- FUNÇÕES DE AUTENTICAÇÃO ---
def autenticar(usuario, senha):
    usuarios = st.secrets["usuarios"]
    return usuarios.get(usuario) == senha

# --- FUNÇÃO PARA GERAR PDF ---
def gerar_pdf(orc):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    try:
        pdf.image("Logotipo.jpg", x=10, y=10, w=40)
    except Exception:
        pass

    pdf.set_xy(60, 10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(150, 8, txt="DÉCIO EXTINTORES LTDA.", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(150, 8, txt="Email: mbextintores19@gmail.com", ln=True)
    pdf.cell(150, 8, txt="Endereço: Uberlândia, 290 - Indaial/SC", ln=True)
    pdf.cell(150, 8, txt="CNPJ: 33.462.690/0001-50", ln=True)
    pdf.cell(150, 8, txt="Tel: (47) 99938-5952", ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="ORÇAMENTO - DÉCIO EXTINTORES", ln=True, align='C')
    pdf.ln(10)

    cliente = orc['cliente']
    validade = orc.get("validade_dias", 10)
    pdf.set_font("Arial", '', 12)
    pdf.cell(200, 10, txt=f"Cliente: {cliente['nome']}", ln=True)
    pdf.cell(200, 10, txt=f"Endereço: {cliente['endereco']} - {cliente['cidade']}", ln=True)
    pdf.cell(200, 10, txt=f"CNPJ: {cliente['cnpj']}", ln=True)
    pdf.ln(5)

    for idx, produto in enumerate(orc.get('produtos', [])):
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt=f"Item {idx+1}", ln=True)
        pdf.set_font("Arial", '', 12)
        pdf.cell(200, 10, txt=f"Produto: {produto['modelo']} - {produto['capacidade']}", ln=True)
        pdf.cell(200, 10, txt=f"Preço unitário: R$ {produto['preco_unitario']:.2f}", ln=True)
        pdf.cell(200, 10, txt=f"Quantidade: {produto['quantidade']}", ln=True)
        pdf.cell(200, 10, txt=f"Total: R$ {produto['total']:.2f}", ln=True)
        pdf.ln(5)

    if 'acessorios' in orc:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Acessórios", ln=True)
        pdf.set_font("Arial", '', 12)
        for acc in orc['acessorios']:
            pdf.cell(200, 10, txt=f"Descrição: {acc['descricao']} | Qtd: {acc['quantidade']} | Valor: R$ {acc['valor']:.2f}", ln=True)
        pdf.ln(5)

    pdf.cell(200, 10, txt=f"Data de emissão: {orc['data'].strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", 'I', 11)
    pdf.multi_cell(0, 10, txt=f"Este orçamento tem validade de {validade} dias a partir da data de emissão.")
    pdf.ln(2)
    pdf.multi_cell(0, 10, txt="Os extintores quando novos não é cobrado placas e instalação.")
    pdf.multi_cell(0, 10, txt="Opção de pagamento: Dinheiro, Débito, Boleto para 28 dias.")

    pdf.ln(15)
    pdf.set_text_color(255, 0, 0)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt="Att.: Décio Extintores", ln=True, align='C')
    pdf.set_text_color(0, 0, 0)

    return pdf.output(dest='S').encode('latin1')
