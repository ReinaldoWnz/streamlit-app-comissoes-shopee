import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Análise de Comissões", layout="wide")

st.title("📊 Análise de Comissões de Afiliado")

# Upload do arquivo CSV
arquivo = st.file_uploader("Selecione o arquivo CSV", type="csv")

if arquivo is not None:
    df = pd.read_csv(arquivo, sep=",", encoding="utf-8")
    df.columns = df.columns.str.strip()

    # Conversão da data
    try:
        df["Horário do pedido"] = pd.to_datetime(df["Horário do pedido"], dayfirst=True)
    except Exception as e:
        st.error("Erro ao converter a coluna 'Horário do pedido' para data.")
        st.stop()

    # Conversão da comissão
    try:
        df["Comissão líquida do afiliado(R$)"] = (
            df["Comissão líquida do afiliado(R$)"]
            .astype(str)
            .str.replace("R$", "", regex=False)
            .str.replace(",", ".")
            .astype(float)
        )
    except Exception as e:
        st.error("Erro ao converter a coluna 'Comissão líquida do afiliado(R$)' para número.")
        st.stop()

    # Filtros interativos
    status = st.multiselect("Status do Pedido", options=df["Status do Pedido"].dropna().unique(), default=df["Status do Pedido"].dropna().unique())
    canal = st.multiselect("Canal", options=df["Canal"].dropna().unique(), default=df["Canal"].dropna().unique())
    categoria = st.multiselect("Categoria", options=df["Categoria Global L2"].dropna().unique(), default=df["Categoria Global L2"].dropna().unique())
    data_inicio = st.date_input("Data inicial", df["Horário do pedido"].min().date())
    data_fim = st.date_input("Data final", df["Horário do pedido"].max().date())

    # Aplicar filtros
    df_filtrado = df[
        (df["Status do Pedido"].isin(status)) &
        (df["Canal"].isin(canal)) &
        (df["Categoria Global L2"].isin(categoria)) &
        (df["Horário do pedido"].dt.date >= data_inicio) &
        (df["Horário do pedido"].dt.date <= data_fim)
    ]

    # Métricas principais
    total_pedidos = len(df_filtrado)
    total_comissao = df_filtrado["Comissão líquida do afiliado(R$)"].sum()

    col1, col2 = st.columns(2)
    col1.metric("🧾 Total de Pedidos", total_pedidos)
    col2.metric("💰 Comissão Total (R$)", f"{total_comissao:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    # Top categorias
    st.subheader("🏆 Top 5 Categorias com Mais Comissão")
    top_categorias = (
        df_filtrado.groupby("Categoria Global L2")["Comissão líquida do afiliado(R$)"].sum()
        .sort_values(ascending=False).head(5)
    )
    st.bar_chart(top_categorias)

    # Estatísticas
    st.subheader("📐 Estatísticas da Comissão Líquida")
    media = df_filtrado["Comissão líquida do afiliado(R$)"].mean()
    minimo = df_filtrado["Comissão líquida do afiliado(R$)"].min()
    maximo = df_filtrado["Comissão líquida do afiliado(R$)"].max()
    st.markdown(f"- Média: R${media:.2f}\n- Mínima: R${minimo:.2f}\n- Máxima: R${maximo:.2f}")

    # Gráfico por Status
    st.subheader("📈 Pedidos por Status")
    grafico_status = df_filtrado["Status do Pedido"].value_counts()
    fig1, ax1 = plt.subplots()
    grafico_status.plot(kind="bar", ax=ax1, color="#6C5DD3")
    st.pyplot(fig1)

    # Gráfico por Canal
    st.subheader("📊 Pedidos por Canal")
    grafico_canal = df_filtrado["Canal"].value_counts()
    fig2, ax2 = plt.subplots()
    grafico_canal.plot(kind="bar", ax=ax2, color="#00C49F")
    st.pyplot(fig2)

    # Gráfico de comissão por canal
    st.subheader("💸 Comissão Total por Canal")
    canal_group = df_filtrado.groupby("Canal")["Comissão líquida do afiliado(R$)"].sum().sort_values(ascending=False)
    fig3, ax3 = plt.subplots()
    canal_group.plot(kind="barh", ax=ax3, color="#FF6A55")
    plt.xlabel("Comissão R$")
    plt.tight_layout()
    st.pyplot(fig3)

else:
    st.info("Por favor, envie um arquivo CSV para começar.")
