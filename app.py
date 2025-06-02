import streamlit as st
from pymongo import MongoClient
from datetime import datetime
from fpdf import FPDF
import base64
from bson.objectid import ObjectId

# --- CONEXÃO COM MONGODB ---
client = MongoClient(st.secrets["mongodb"]["uri"])
db = client[st.secrets["mongodb"]["database"]]
colecao = db[st.secrets["mongodb"]["collection"]]

# --- AUTENTICAÇÃO ---
def autenticar(usuario, senha):
    usuarios = st.secrets["usuarios"]
    return usuarios.get(usuario) == senha

# --- GERAÇÃO DE PDF ---
def gerar_pdf(orc):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

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

    total_geral = 0
    for i, item in enumerate(itens, start=1):
        pdf.cell(200, 10, txt=f"Item {i}: {item['modelo']} - {item['capacidade']}", ln=True)
        pdf.cell(200, 10, txt=f"Mangueira: {item['mangueira']}", ln=True)
        pdf.cell(200, 10, txt=f"Preço unitário: R$ {item['preco_unitario']:.2f}", ln=True)
        pdf.cell(200, 10, txt=f"Quantidade: {item['quantidade']}", ln=True)
        pdf.cell(200, 10, txt=f"Subtotal: R$ {item['total']:.2f}", ln=True)
        pdf.ln(5)
        total_geral += item['total']

    pdf.cell(200, 10, txt=f"Total Geral: R$ {total_geral:.2f}", ln=True)
    pdf.ln(10)

    data = orc['data'].strftime('%d/%m/%Y %H:%M')
    pdf.cell(200, 10, txt=f"Data de emissão: {data}", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", 'I', 11)
    pdf.multi_cell(0, 10, txt=f"Este orçamento tem validade de {validade} dias a partir da data de emissão.")
    pdf.ln(5)
    pdf.multi_cell(0, 10, txt="Os extintores quando novos não é cobrado placas e instalação.")
    pdf.ln(10)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, txt="Opção de pagamento: Dinheiro, Débito, Boleto para 28 dias", ln=True)
    pdf.ln(20)
    pdf.set_text_color(255, 0, 0)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, txt="Att.: Décio Extintores", ln=True, align='C')

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

    if "itens" not in st.session_state:
        st.session_state.itens = []

    with st.form("form_item"):
        modelo = st.selectbox("Modelo do extintor", [
            "Extintor PQSP (Novo)", "Extintor PQSP (Carga)",
            "Extintor CO2 (Novo)", "Extintor CO2 (Carga)",
            "Extintor Água Pressurizada (Novo)", "Extintor Água Pressurizada (Carga)"
        ])
        capacidade = st.selectbox("Capacidade", ["2kg", "4kg", "6kg", "9kg", "10kg", "12kg", "20kg", "25L", "50L"])
        mangueira = st.selectbox("Mangueira de hidrante", ["Nenhuma", "20 metros", "25 metros", "30 metros"])
        preco_unitario = st.number_input("Preço unitário (R$)", min_value=0.0, step=0.01, format="%.2f")
        quantidade = st.number_input("Quantidade", min_value=1, step=1)
        adicionar = st.form_submit_button("Adicionar item")

        if adicionar:
            total = preco_unitario * quantidade
            item = {
                "modelo": modelo,
                "capacidade": capacidade,
                "mangueira": mangueira,
                "preco_unitario": preco_unitario,
                "quantidade": quantidade,
                "total": total
            }
            st.session_state.itens.append(item)
            st.success("Item adicionado.")
            st.rerun()

    if st.session_state.itens:
        st.subheader("Itens adicionados")
        for i, item in enumerate(st.session_state.itens):
            st.write(f"{i+1}. {item['modelo']} - {item['capacidade']}, Mangueira: {item['mangueira']}, Qtde: {item['quantidade']}, Unit: R$ {item['preco_unitario']:.2f}, Total: R$ {item['total']:.2f}")

    validade_dias = st.number_input("Validade do orçamento (dias)", min_value=1, max_value=365, value=10)
    if st.button("💾 Salvar Orçamento"):
        if not all([nome_cliente, endereco, cidade, cnpj]):
            st.warning("Por favor, preencha todos os dados do cliente.")
        elif not st.session_state.itens:
            st.warning("Adicione ao menos um item ao orçamento.")
        else:
            orcamento = {
                "usuario": st.session_state["usuario"],
                "cliente": {
                    "nome": nome_cliente,
                    "endereco": endereco,
                    "cidade": cidade,
                    "cnpj": cnpj,
                },
                "itens": st.session_state.itens,
                "validade_dias": validade_dias,
                "data": datetime.now()
            }
            colecao.insert_one(orcamento)
            st.session_state.itens = []
            st.success("Orçamento salvo com sucesso!")
            st.markdown(gerar_link_pdf(orcamento), unsafe_allow_html=True)

# --- LISTAGEM DE ORÇAMENTOS ---
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
            st.write(f"**Endereço:** {o['cliente']['endereco']} - {o['cliente']['cidade']}")
            st.write(f"**CNPJ:** {o['cliente']['cnpj']}")
            st.write(f"**Validade:** {o.get('validade_dias', 10)} dias")
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
