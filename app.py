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

    # Conversão de data
    df["Horário do pedido"] = pd.to_datetime(df["Horário do pedido"], dayfirst=True)

    # Conversão da comissão
    coluna_comissao = "Comissão líquida do afiliado(R$)"
    df[coluna_comissao] = df[coluna_comissao].astype(str).str.replace("R$", "", regex=False).str.replace(",", ".").astype(float)

    # Opções para os filtros
    opcoes_status = df["Status do Pedido"].dropna().unique()
    opcoes_canais = df["Canal"].dropna().unique()
    opcoes_categorias = df["Categoria Global L2"].dropna().unique()

    # Filtros lado a lado
    col1, col2, col3 = st.columns(3)

    with col1:
        status_selecionado = st.multiselect("Status do Pedido", opcoes_status)

    with col2:
        canais_selecionados = st.multiselect("Canal", opcoes_canais)

    with col3:
        categorias_selecionadas = st.multiselect("Categoria Global L2", opcoes_categorias)

    # Filtros de data
    col4, col5 = st.columns(2)
    with col4:
        data_inicio = st.date_input("Data inicial", df["Horário do pedido"].min().date())
    with col5:
        data_fim = st.date_input("Data final", df["Horário do pedido"].max().date())

    # Se nenhum filtro for selecionado, usar todos os valores
    if not status_selecionado:
        status_selecionado = opcoes_status
    if not canais_selecionados:
        canais_selecionados = opcoes_canais
    if not categorias_selecionadas:
        categorias_selecionadas = opcoes_categorias

    # Aplicar filtros
    df_filtrado = df[
        (df["Status do Pedido"].isin(status_selecionado)) &
        (df["Canal"].isin(canais_selecionados)) &
        (df["Categoria Global L2"].isin(categorias_selecionadas)) &
        (df["Horário do pedido"].dt.date >= data_inicio) &
        (df["Horário do pedido"].dt.date <= data_fim)
    ]

    if df_filtrado.empty:
        st.warning("Nenhum dado encontrado com os filtros aplicados.")
    else:
        # Métricas
        total_pedidos = len(df_filtrado)
        total_comissao = df_filtrado[coluna_comissao].sum()

        st.metric("🧾 Total de Pedidos", total_pedidos)
        st.metric("💰 Comissão Total (R$)", f"{total_comissao:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        # Gráfico por Status
        st.subheader("📈 Pedidos por Status")
        grafico_status = df_filtrado["Status do Pedido"].value_counts()
        fig1, ax1 = plt.subplots(figsize=(10, 4))
        grafico_status.plot(kind="bar", ax=ax1, color="#6C5DD3")
        st.pyplot(fig1)

        # Gráfico por Canal
        st.subheader("📊 Pedidos por Canal")
        grafico_canal = df_filtrado["Canal"].value_counts()
        fig2, ax2 = plt.subplots(figsize=(10, 4))
        grafico_canal.plot(kind="bar", ax=ax2, color="#00C49F")
        st.pyplot(fig2)

        # Top categorias por comissão
        st.subheader("🏆 Top 5 Categorias por Comissão")
        top_categorias = df_filtrado.groupby("Categoria Global L2")[coluna_comissao].sum().sort_values(ascending=False).head(5)
        fig3, ax3 = plt.subplots(figsize=(10, 4))
        top_categorias.plot(kind="bar", ax=ax3, color="#FF8850")
        st.pyplot(fig3)

    # Comparação entre períodos
    st.subheader("📅 Comparação entre dois períodos")

    colA, colB = st.columns(2)
    with colA:
        data_inicio_A = st.date_input("Início Período A", df["Horário do pedido"].min().date(), key="A1")
        data_fim_A = st.date_input("Fim Período A", df["Horário do pedido"].max().date(), key="A2")
    with colB:
        data_inicio_B = st.date_input("Início Período B", df["Horário do pedido"].min().date(), key="B1")
        data_fim_B = st.date_input("Fim Período B", df["Horário do pedido"].max().date(), key="B2")

    periodo_A = df[
        (df["Horário do pedido"].dt.date >= data_inicio_A) &
        (df["Horário do pedido"].dt.date <= data_fim_A)
    ]
    periodo_B = df[
        (df["Horário do pedido"].dt.date >= data_inicio_B) &
        (df["Horário do pedido"].dt.date <= data_fim_B)
    ]

    def resumo_periodo(df_periodo):
        return {
            "Pedidos": len(df_periodo),
            "Comissão (R$)": df_periodo[coluna_comissao].sum()
        }

    resumo_A = resumo_periodo(periodo_A)
    resumo_B = resumo_periodo(periodo_B)

    comparacao = pd.DataFrame({
        "Período A": resumo_A,
        "Período B": resumo_B
    })

    st.dataframe(comparacao)

else:
    st.info("Por favor, envie um arquivo CSV para começar.")
