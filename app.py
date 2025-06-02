import streamlit as st
from pymongo import MongoClient
from datetime import datetime, timedelta
from fpdf import FPDF
import base64
import urllib.parse
from bson.objectid import ObjectId

# --- CONEXÃO COM MONGODB USANDO st.secrets ---
client = MongoClient(st.secrets["database"]["url"])
db = client["decio_orcamentos"]
colecao = db["orcamentos"]


# --- FUNÇÕES DE AUTENTICAÇÃO ---
def autenticar(usuario, senha):
    usuarios = st.secrets["usuarios"]
    return usuarios.get(usuario) == senha


# --- FUNÇÕES PARA GERAR PDF ---
def gerar_pdf(orc):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # LOGO - coloque o arquivo Logotipo.jpg na mesma pasta do app
    try:
        pdf.image("Logotipo.jpg", x=80, y=10, w=50)
        pdf.ln(35)
    except Exception:
        pdf.ln(45)  # caso não encontre o logo, só avança a linha

    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="ORÇAMENTO - DÉCIO EXTINTORES", ln=True, align='C')
    pdf.ln(10)

    pdf.set_font("Arial", '', 12)
    cliente = orc['cliente']
    produto = orc['produto']
    validade = orc.get("validade_dias", 10)
    pdf.cell(200, 10, txt=f"Cliente: {cliente['nome']}", ln=True)
    pdf.cell(200, 10, txt=f"Endereço: {cliente['endereco']} - {cliente['cidade']}", ln=True)
    pdf.cell(200, 10, txt=f"CNPJ: {cliente['cnpj']}", ln=True)
    pdf.ln(5)

    pdf.cell(200, 10, txt=f"Produto: {produto['modelo']} - {produto['capacidade']}", ln=True)
    pdf.cell(200, 10, txt=f"Mangueira: {'Sim' if produto['com_mangueira'] else 'Não'}", ln=True)
    pdf.cell(200, 10, txt=f"Preço unitário: R$ {produto['preco_unitario']:.2f}", ln=True)
    pdf.cell(200, 10, txt=f"Quantidade: {produto['quantidade']}", ln=True)
    pdf.cell(200, 10, txt=f"Total: R$ {produto['total']:.2f}", ln=True)
    pdf.ln(10)

    data = orc['data'].strftime('%d/%m/%Y %H:%M')
    pdf.cell(200, 10, txt=f"Data de emissão: {data}", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", 'I', 11)
    pdf.multi_cell(0, 10, txt=f"Este orçamento tem validade de {validade} dias a partir da data de emissão.")

    return pdf.output(dest='S').encode('latin1')


def gerar_link_pdf(orcamento):
    pdf_bytes = gerar_pdf(orcamento)
    b64 = base64.b64encode(pdf_bytes).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="orcamento.pdf">📄 Baixar PDF</a>'
    return href


# --- TELA DE LOGIN ---
def tela_login():
    st.title("🔒 Login - Décio Extintores")
    with st.form("login_form"):
        usuario_input = st.text_input("Usuário")
        senha_input = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar")

    if submit:
        if autenticar(usuario_input, senha_input):
            st.session_state["usuario"] = usuario_input
            st.success(f"Bem-vindo(a), {usuario_input}!")
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")


# --- TELA DE CADASTRO DE ORÇAMENTO ---
def tela_cadastro():
    st.title("📋 Gerador de Orçamentos - Décio Extintores")

    # Identificação do Cliente
    st.header("🧾 Identificação do Cliente")
    nome_cliente = st.text_input("Nome completo")
    endereco = st.text_input("Endereço (com número)")
    cidade = st.text_input("Cidade")
    cnpj = st.text_input("CNPJ (formato: 00.000.000/0000-00)")

    # Itens do Orçamento
    st.header("🧯 Itens do Orçamento")

    modelo = st.selectbox("Modelo do extintor", ["Água", "Pó químico", "CO₂"])
    capacidade = st.selectbox("Capacidade", ["4kg", "6kg", "10kg"])
    com_mangueira = st.checkbox("Incluir mangueira?")

    preco_unitario = st.number_input(f"Preço unitário para {modelo} (R$)", min_value=0.0, step=0.01, format="%.2f")
    quantidade = st.number_input("Quantidade", min_value=1, step=1)

    validade_dias = st.number_input("Validade do orçamento (dias)", min_value=1, max_value=365, value=10, step=1)

    total = preco_unitario * quantidade
    st.markdown(f"**Total:** R$ {total:,.2f}")

    data_atual = datetime.now()

    if st.button("💾 Salvar Orçamento"):
        if not all([nome_cliente, endereco, cidade, cnpj]):
            st.warning("Por favor, preencha todos os dados do cliente.")
        else:
            orcamento = {
                "usuario": st.session_state["usuario"],
                "cliente": {
                    "nome": nome_cliente,
                    "endereco": endereco,
                    "cidade": cidade,
                    "cnpj": cnpj,
                },
                "produto": {
                    "modelo": modelo,
                    "capacidade": capacidade,
                    "com_mangueira": com_mangueira,
                    "preco_unitario": preco_unitario,
                    "quantidade": quantidade,
                    "total": total,
                },
                "validade_dias": validade_dias,
                "data": data_atual
            }
            colecao.insert_one(orcamento)
            st.success("Orçamento salvo com sucesso!")


# --- TELA DE LISTAGEM DE ORÇAMENTOS ---
def tela_listagem():
    st.title("📚 Orçamentos Salvos - Décio Extintores")
    usuario = st.session_state["usuario"]

    filtro_cliente = st.text_input("Filtrar por nome do cliente")

    query = {"usuario": usuario}
    if filtro_cliente.strip():
        query["cliente.nome"] = {"$regex": filtro_cliente, "$options": "i"}

    orcamentos = list(colecao.find(query).sort("data", -1))

    if not orcamentos:
        st.info("Nenhum orçamento encontrado.")
        return

    for o in orcamentos:
        with st.expander(f"{o['cliente']['nome']} - {o['data'].strftime('%d/%m/%Y %H:%M')}"):
            st.write(f"**Endereço:** {o['cliente']['endereco']}, {o['cliente']['cidade']}")
            st.write(f"**CNPJ:** {o['cliente']['cnpj']}")
            st.write(f"**Produto:** {o['produto']['modelo']} - {o['produto']['capacidade']}")
            st.write(f"**Mangueira:** {'Sim' if o['produto']['com_mangueira'] else 'Não'}")
            st.write(f"**Preço unitário:** R$ {o['produto']['preco_unitario']:.2f}")
            st.write(f"**Quantidade:** {o['produto']['quantidade']}")
            st.write(f"**Total:** R$ {o['produto']['total']:.2f}")
            st.write(f"**Data:** {o['data'].strftime('%d/%m/%Y %H:%M')}")
            st.write(f"**Validade:** {o.get('validade_dias',10)} dias")

            st.markdown(gerar_link_pdf(o), unsafe_allow_html=True)

            texto = f"""Orçamento Décio Extintores:
Cliente: {o['cliente']['nome']}
Endereço: {o['cliente']['endereco']} - {o['cliente']['cidade']}
CNPJ: {o['cliente']['cnpj']}
Produto: {o['produto']['modelo']} - {o['produto']['capacidade']}
Mangueira: {"Sim" if o['produto']['com_mangueira'] else "Não"}
Preço unitário: R$ {o['produto']['preco_unitario']:.2f}
Quantidade: {o['produto']['quantidade']}
Total: R$ {o['produto']['total']:.2f}
Data: {o['data'].strftime('%d/%m/%Y %H:%M')}
Validade: {o.get('validade_dias',10)} dias
"""

            mailto = f"mailto:?subject=Orçamento%20Décio%20Extintores&body={urllib.parse.quote(texto)}"
            st.markdown(f"[📧 Enviar por Email]({mailto})", unsafe_allow_html=True)

            whatsapp_link = f"https://wa.me/?text={urllib.parse.quote(texto)}"
            st.markdown(f"[📱 Enviar pelo WhatsApp]({whatsapp_link})", unsafe_allow_html=True)

            if st.button("🗑️ Excluir", key=str(o["_id"])):
                colecao.delete_one({"_id": ObjectId(o["_id"])})
                st.success("Orçamento excluído.")
                st.rerun()


# --- CONTROLE DE PÁGINAS ---
if "usuario" not in st.session_state:
    tela_login()
else:
    pagina = st.sidebar.selectbox("Navegação", ["Novo Orçamento", "Orçamentos Salvos"])
    if pagina == "Novo Orçamento":
        tela_cadastro()
    else:
        tela_listagem()
