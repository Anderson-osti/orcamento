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


# --- TELAS ---
def tela_login():
    st.title("🔐 Login")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if autenticar(usuario, senha):
            st.session_state.usuario = usuario
            st.success(f"Bem-vindo, {usuario}! ✅")
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos. ❌")


def tela_cadastro():
    st.title("📝 Novo Orçamento")

    nome = st.text_input("Nome do Cliente", value=st.session_state.get("nome", ""))
    endereco = st.text_input("Endereço", value=st.session_state.get("endereco", ""))
    cidade = st.text_input("Cidade", value=st.session_state.get("cidade", ""))
    cnpj = st.text_input("CNPJ", value=st.session_state.get("cnpj", ""))
    validade_dias = st.number_input("Validade do orçamento (dias)", min_value=1,
                                    value=st.session_state.get("validade_dias", 10))

    st.subheader("Itens do Orçamento")

    modelo = st.selectbox("Modelo do Extintor", [
        "Extintor PQSP (Novo)",
        "Extintor PQSP (Carga)",
        "Extintor CO2 (Novo)",
        "Extintor CO2 (Carga)",
        "Extintor Água Pressurizada (Novo)",
        "Extintor Água Pressurizada (Carga)"
    ])
    capacidade = st.selectbox("Capacidade", [
        "4 Kg", "6 Kg", "8 Kg", "10 Kg", "12 Kg",
        "10 L", "20 L", "75 L"
    ])
    preco_unitario = st.number_input("Preço Unitário", min_value=0.0, step=0.01, format="%.2f")
    quantidade = st.number_input("Quantidade", min_value=1, step=1)

    if st.button("➕ Adicionar Extintor"):
        total = preco_unitario * quantidade
        st.session_state.itens.append({
            "modelo": modelo,
            "capacidade": capacidade,
            "preco_unitario": preco_unitario,
            "quantidade": quantidade,
            "total": total
        })

    st.subheader("Adicionar Produto Personalizado")
    produto_manual = st.text_input("Descrição do Produto")
    qtd_manual = st.number_input("Quantidade do Produto", min_value=1, step=1, key="qtd_manual")
    preco_manual = st.number_input("Valor Unitário", min_value=0.0, step=0.01, key="preco_manual")

    if st.button("➕ Adicionar Produto Manual"):
        total_manual = qtd_manual * preco_manual
        st.session_state.itens.append({
            "modelo": produto_manual,
            "capacidade": "-",
            "preco_unitario": preco_manual,
            "quantidade": qtd_manual,
            "total": total_manual
        })

    st.markdown("---")
    st.subheader("🛒 Itens Adicionados")
    if len(st.session_state.itens) == 0:
        st.info("Nenhum item adicionado ainda.")
    else:
        for i, item in enumerate(st.session_state.itens):
            col1, col2 = st.columns([8, 2])
            with col1:
                st.markdown(f"**{item['modelo']} ({item['capacidade']})** - {item['quantidade']} un - R$"
                            f"{item['preco_unitario']:.2f} un - Total: R$ {item['total']:.2f}")
            with col2:
                if st.button("❌", key=f"del_{i}"):
                    st.session_state.itens.pop(i)
                    st.rerun()

    st.markdown("---")
    if st.button("💾 Salvar Orçamento"):
        if not nome or not endereco or not cidade or not cnpj:
            st.error("Por favor, preencha todos os dados do cliente.")
            return
        if len(st.session_state.itens) == 0:
            st.error("Adicione ao menos um item ao orçamento.")
            return

        orcamento = {
            "cliente": {"nome": nome, "endereco": endereco, "cidade": cidade, "cnpj": cnpj},
            "itens": st.session_state.itens,
            "validade_dias": validade_dias,
            "data": datetime.now()
        }

        if "orcamento_em_edicao" in st.session_state:
            colecao.update_one(
                {"_id": ObjectId(st.session_state.orcamento_em_edicao)},
                {"$set": orcamento}
            )
            st.success("Orçamento atualizado com sucesso! 📝")
            del st.session_state.orcamento_em_edicao
        else:
            colecao.insert_one(orcamento)
            st.success("Orçamento salvo com sucesso! 🎉")

        # Limpar sessão
        st.session_state.itens = []
        st.session_state.nome = ""
        st.session_state.endereco = ""
        st.session_state.cidade = ""
        st.session_state.cnpj = ""
        st.session_state.validade_dias = 10
        st.rerun()


def tela_listagem():
    st.title("📋 Orçamentos Salvos")
    orcamentos = list(colecao.find().sort("data", -1))

    if len(orcamentos) == 0:
        st.info("Nenhum orçamento salvo.")
        return

    for orc in orcamentos:
        cliente_nome = orc['cliente']['nome']
        data_emissao = orc['data'].strftime('%d/%m/%Y %H:%M')
        validade = orc.get("validade_dias", 10)
        with st.expander(f"👤 {cliente_nome} - 🗓️ {data_emissao} - Validade: {validade} dias"):
            st.markdown(gerar_link_pdf(orc), unsafe_allow_html=True)
            if st.button("✏️ Editar", key=f"editar_{orc['_id']}"):
                st.session_state.itens = orc['itens']
                st.session_state["nome"] = orc['cliente']['nome']
                st.session_state["endereco"] = orc['cliente']['endereco']
                st.session_state["cidade"] = orc['cliente']['cidade']
                st.session_state["cnpj"] = orc['cliente']['cnpj']
                st.session_state["validade_dias"] = orc['validade_dias']
                st.session_state.orcamento_em_edicao = str(orc['_id'])
                st.session_state.pagina = "Novo Orçamento"
                st.rerun()
            if st.button("🗑️ Excluir", key=f"excluir_{orc['_id']}"):
                colecao.delete_one({"_id": ObjectId(orc['_id'])})
                st.success("Orçamento excluído com sucesso! 🗑️")
                st.rerun()


# --- CONTROLE DE PÁGINAS ---
if "usuario" not in st.session_state:
    st.session_state.itens = []
    tela_login()
else:
    if "pagina" not in st.session_state:
        st.session_state.pagina = "Novo Orçamento"
    pagina = st.sidebar.selectbox("Navegação", ["Novo Orçamento", "Orçamentos Salvos"],
                                  index=["Novo Orçamento", "Orçamentos Salvos"].index(st.session_state.pagina))
    if pagina == "Novo Orçamento":
        if "itens" not in st.session_state:
            st.session_state.itens = []
        tela_cadastro()
    else:
        tela_listagem()
