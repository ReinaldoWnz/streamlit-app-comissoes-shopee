import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Análise de Comissões", layout="wide")

st.title("📊 Análise de Comissões de Afiliado")

# Upload do arquivo CSV
arquivo = st.file_uploader("Selecione o arquivo CSV", type="csv")

if arquivo is not None:
    df = pd.read_csv(arquivo, sep=",", encoding="utf-8")

    # Converter coluna de data
    df.columns = df.columns.str.strip() # <<< essa linha evita erro com nomes de colunas
    
    # Adicione esta linha para ver todos os nomes das colunas 
    df["Horário do pedido"] = pd.to_datetime(df["Horário do pedido"], dayfirst=True)

    # Filtros
    status = st.multiselect("Status do Pedido", options=df["Status do Pedido"].unique(), default=df["Status do Pedido"].unique())
    canal = st.multiselect("Canal", options=df["Canal"].unique(), default=df["Canal"].unique())
    categoria = st.multiselect("Categoria", options=df["Categoria Global L2"].unique(), default=df["Categoria Global L2"].unique())
    data_inicio = st.date_input("Data inicial", df["Horário do pedido"].min().date())
    data_fim = st.date_input("Data final", df["Horário do pedido"].max().date())

    # Aplicar filtros
    df_filtrado = df[
        (df["Status do Pedido"].isin(status)) &
        (df["Canal"].isin(canal)) &
        (df["Categoria Global L2"].isin(categoria)) &
        (df["Horário do pedido"].dt.date >= data_inicio) & \
        (df["Horário do pedido"].dt.date <= data_fim)
    ]

    # Métricas
    total_pedidos = len(df_filtrado)
    total_comissao = df_filtrado["Comissão líquida do afiliado(R$)"].astype(str).str.replace("R$", "", regex=False).str.replace(",", ".").astype(float).sum()
    
    st.metric("🧾 Total de Pedidos", total_pedidos)
    st.metric("💰 Comissão Total (R$)", f"{total_comissao:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    # Gráfico por status
    st.subheader("📈 Pedidos por Status")
    grafico_status = df_filtrado["Status do Pedido"].value_counts()
    fig1, ax1 = plt.subplots()
    grafico_status.plot(kind="bar", ax=ax1, color="#6C5DD3")
    st.pyplot(fig1)

    # Gráfico por canal
    st.subheader("📊 Pedidos por Canal")
    grafico_canal = df_filtrado["Canal"].value_counts()
    fig2, ax2 = plt.subplots()
    grafico_canal.plot(kind="bar", ax=ax2, color="#00C49F")
    st.pyplot(fig2)

else:
    st.info("Por favor, envie um arquivo CSV para começar.")
