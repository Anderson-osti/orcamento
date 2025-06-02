import streamlit as st
from pymongo import MongoClient
from datetime import datetime
from fpdf import FPDF
import base64
from bson.objectid import ObjectId

# --- CONEXÃO COM MONGODB USANDO st.secrets ---
client = MongoClient(st.secrets["database"]["url"])
db = client["decio_orcamentos"]
colecao = db["orcamentos"]

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
        pdf.image("Logotipo.jpg", x=80, y=10, w=50)
        pdf.ln(35)
    except Exception:
        pdf.ln(45)

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

    for idx, produto in enumerate(orc['produtos']):
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt=f"Item {idx+1}", ln=True)
        pdf.set_font("Arial", '', 12)
        pdf.cell(200, 10, txt=f"Produto: {produto['modelo']} - {produto['capacidade']}", ln=True)
        pdf.cell(200, 10, txt=f"Preço unitário: R$ {produto['preco_unitario']:.2f}", ln=True)
        pdf.cell(200, 10, txt=f"Quantidade: {produto['quantidade']}", ln=True)
        pdf.cell(200, 10, txt=f"Total: R$ {produto['total']:.2f}", ln=True)
        pdf.ln(5)

    if 'acessorio' in orc:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Acessórios", ln=True)
        pdf.set_font("Arial", '', 12)
        pdf.cell(200, 10, txt=f"Descrição: {orc['acessorio']['descricao']}", ln=True)
        pdf.cell(200, 10, txt=f"Quantidade: {orc['acessorio']['quantidade']}", ln=True)
        pdf.cell(200, 10, txt=f"Valor: R$ {orc['acessorio']['valor']:.2f}", ln=True)
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

    st.header("🧾 Identificação do Cliente")
    nome_cliente = st.text_input("Nome completo")
    endereco = st.text_input("Endereço (com número)")
    cidade = st.text_input("Cidade")
    cnpj = st.text_input("CNPJ (formato: 00.000.000/0000-00)")

    st.header("🧯 Itens do Orçamento")
    produtos = []
    with st.form("form_produto"):
        modelo = st.selectbox("Modelo do extintor", [
            "Extintor PQSP (Novo)",
            "Extintor PQSP (Carga)",
            "Extintor CO₂ (Novo)",
            "Extintor CO₂ (Carga)",
            "Extintor Água Pressurizada",
            "Extintor Classe D"
        ])
        capacidade = st.selectbox("Capacidade", ["2kg", "4kg", "6kg", "8kg", "10kg", "12kg", "20kg", "25kg", "50kg", "5L", "10L", "12L", "20L"])
        preco_unitario = st.number_input("Preço unitário (R$)", min_value=0.0, step=0.01, format="%.2f")
        quantidade = st.number_input("Quantidade", min_value=1, step=1)
        add = st.form_submit_button("Adicionar Item")

        if add:
            total = preco_unitario * quantidade
            if "produtos_temp" not in st.session_state:
                st.session_state["produtos_temp"] = []
            st.session_state["produtos_temp"].append({
                "modelo": modelo,
                "capacidade": capacidade,
                "preco_unitario": preco_unitario,
                "quantidade": quantidade,
                "total": total
            })

    if "produtos_temp" in st.session_state:
        st.subheader("Itens adicionados")
        for i, p in enumerate(st.session_state["produtos_temp"]):
            st.markdown(f"**{i+1}. {p['modelo']} - {p['capacidade']} | Qtd: {p['quantidade']} | Total: R$ {p['total']:.2f}**")

    st.header("📦 Acessórios (opcional)")
    descricao_acessorio = st.text_input("Descrição do acessório")
    quantidade_acessorio = st.number_input("Quantidade do acessório", min_value=0, step=1)
    valor_acessorio = st.number_input("Valor total do acessório (R$)", min_value=0.0, step=0.01, format="%.2f")

    validade_dias = st.number_input("Validade do orçamento (dias)", min_value=1, max_value=365, value=10, step=1)

    if st.button("💾 Salvar Orçamento"):
        if not all([nome_cliente, endereco, cidade, cnpj]):
            st.warning("Por favor, preencha todos os dados do cliente.")
        elif "produtos_temp" not in st.session_state or not st.session_state["produtos_temp"]:
            st.warning("Adicione pelo menos um item ao orçamento.")
        else:
            orcamento = {
                "usuario": st.session_state["usuario"],
                "cliente": {
                    "nome": nome_cliente,
                    "endereco": endereco,
                    "cidade": cidade,
                    "cnpj": cnpj,
                },
                "produtos": st.session_state["produtos_temp"],
                "validade_dias": validade_dias,
                "data": datetime.now()
            }

            if descricao_acessorio:
                orcamento["acessorio"] = {
                    "descricao": descricao_acessorio,
                    "quantidade": quantidade_acessorio,
                    "valor": valor_acessorio
                }

            colecao.insert_one(orcamento)
            st.success("Orçamento salvo com sucesso!")
            st.markdown(gerar_link_pdf(orcamento), unsafe_allow_html=True)
            del st.session_state["produtos_temp"]


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
