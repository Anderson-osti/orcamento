import streamlit as st
from pymongo import MongoClient
from datetime import datetime
from fpdf import FPDF
import base64
from bson.objectid import ObjectId

# --- CONEXÃO COM MONGODB USANDO st.secrets ---
client = MongoClient(st.secrets["mongodb"]["uri"])
db = client[st.secrets["mongodb"]["database"]]
colecao = db[st.secrets["mongodb"]["collection"]]

# --- FUNÇÕES DE AUTENTICAÇÃO ---
def autenticar(usuario, senha):
    usuarios = st.secrets["usuarios"]
    return usuarios.get(usuario) == senha

# --- FUNÇÃO PARA GERAR PDF ---
def gerar_pdf(orc):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # LOGO
    try:
        pdf.image("Logotipo.jpg", x=80, y=10, w=50)
        pdf.ln(35)
    except:
        pdf.ln(45)

    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="ORÇAMENTO - DÉCIO EXTINTORES", ln=True, align='C')
    pdf.ln(10)

    cliente = orc['cliente']
    itens = orc['itens']
    validade = orc.get("validade_dias", 10)

    pdf.set_font("Arial", '', 12)
    pdf.cell(200, 10, txt=f"Cliente: {cliente['nome']}", ln=True)
    pdf.cell(200, 10, txt=f"Endereço: {cliente['endereco']} - {cliente['cidade']}", ln=True)
    pdf.cell(200, 10, txt=f"CNPJ: {cliente['cnpj']}", ln=True)
    pdf.ln(5)

    for i, item in enumerate(itens, 1):
        pdf.cell(200, 10, txt=f"{i}) Modelo: {item['modelo']} - {item['capacidade']}", ln=True)
        pdf.cell(200, 10, txt=f"   Mangueira: {'Sim' if item['com_mangueira'] else 'Não'}", ln=True)
        pdf.cell(200, 10, txt=f"   Preço unitário: R$ {item['preco_unitario']:.2f}", ln=True)
        pdf.cell(200, 10, txt=f"   Quantidade: {item['quantidade']}", ln=True)
        pdf.cell(200, 10, txt=f"   Total: R$ {item['total']:.2f}", ln=True)
        pdf.ln(5)

    pdf.set_font("Arial", '', 12)
    pdf.cell(200, 10, txt=f"Opção de pagamento: {orc.get('forma_pagamento', '')}", ln=True)

    data = orc['data'].strftime('%d/%m/%Y %H:%M')
    pdf.cell(200, 10, txt=f"Data de emissão: {data}", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", 'I', 11)
    pdf.multi_cell(0, 10, txt=f"Este orçamento tem validade de {validade} dias a partir da data de emissão.")
    pdf.ln(5)
    pdf.multi_cell(0, 10, txt="Os extintores quando novos não é cobrado placas e instalação.")
    pdf.ln(10)

    pdf.set_text_color(255, 0, 0)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Att.: Décio Extintores", ln=True, align="C")

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

# --- TELA DE CADASTRO ---
def tela_cadastro():
    st.title("📋 Gerador de Orçamentos - Décio Extintores")
    st.header("🧾 Identificação do Cliente")
    nome_cliente = st.text_input("Nome completo")
    endereco = st.text_input("Endereço (com número)")
    cidade = st.text_input("Cidade")
    cnpj = st.text_input("CNPJ (formato: 00.000.000/0000-00)")

    st.header("🧯 Itens do Orçamento")
    num_itens = st.number_input("Quantidade de tipos de extintor", min_value=1, step=1, value=1)
    itens = []
    for i in range(num_itens):
        st.subheader(f"Item {i+1}")
        modelo = st.selectbox(f"Modelo {i+1}", ["Água", "Pó químico", "CO₂"], key=f"modelo_{i}")
        capacidade = st.selectbox(f"Capacidade {i+1}", ["4kg", "6kg", "10kg"], key=f"capacidade_{i}")
        com_mangueira = st.checkbox("Incluir mangueira?", key=f"mangueira_{i}")
        preco_unitario = st.number_input("Preço unitário (R$)", min_value=0.0, step=0.01, format="%.2f", key=f"preco_{i}")
        quantidade = st.number_input("Quantidade", min_value=1, step=1, key=f"quantidade_{i}")
        total = preco_unitario * quantidade

        itens.append({
            "modelo": modelo,
            "capacidade": capacidade,
            "com_mangueira": com_mangueira,
            "preco_unitario": preco_unitario,
            "quantidade": quantidade,
            "total": total
        })

    validade_dias = st.number_input("Validade do orçamento (dias)", min_value=1, max_value=365, value=10)
    forma_pagamento = st.text_input("Opção de pagamento", value="Dinheiro, Débito, Boleto para 28 dias")
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
                "itens": itens,
                "forma_pagamento": forma_pagamento,
                "validade_dias": validade_dias,
                "data": data_atual
            }
            colecao.insert_one(orcamento)
            st.success("Orçamento salvo com sucesso!")
            st.markdown(gerar_link_pdf(orcamento), unsafe_allow_html=True)

# --- TELA DE LISTAGEM ---
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
            for i, item in enumerate(o['itens'], 1):
                st.write(f"**Item {i}:** {item['modelo']} - {item['capacidade']}")
                st.write(f"Mangueira: {'Sim' if item['com_mangueira'] else 'Não'}")
                st.write(f"Preço unitário: R$ {item['preco_unitario']:.2f}")
                st.write(f"Quantidade: {item['quantidade']}")
                st.write(f"Total: R$ {item['total']:.2f}")
            st.write(f"**Forma de pagamento:** {o.get('forma_pagamento', '')}")
            st.write(f"**Validade:** {o.get('validade_dias',10)} dias")
            st.markdown(gerar_link_pdf(o), unsafe_allow_html=True)
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
