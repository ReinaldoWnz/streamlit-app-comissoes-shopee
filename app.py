import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Análise de Comissões - Shopee", layout="wide")

st.title("💰 Análise de Comissões - Shopee Afiliados")

uploaded_file = st.file_uploader("📁 Faça upload do arquivo CSV exportado da Shopee", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Conversões
    df["Horário do pedido"] = pd.to_datetime(df["Horário do pedido"], format="%d/%m/%Y %H:%M")
    df["Data do pedido"] = df["Horário do pedido"].dt.date
    coluna_comissao = "Comissão líquida do afiliado (R$)"

    # Filtros (lado a lado)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        canais = st.multiselect("Canal", options=sorted(df["Canal"].unique()), default=[])
    with col2:
        status = st.multiselect("Status do Pedido", options=sorted(df["Status do Pedido"].unique()), default=[])
    with col3:
        categorias = st.multiselect("Categoria Global L2", options=sorted(df["Categoria Global L2"].unique()), default=[])
    with col4:
        datas = st.date_input("Período", [])

    # Aplicação dos filtros
    df_filtrado = df.copy()
    if canais:
        df_filtrado = df_filtrado[df_filtrado["Canal"].isin(canais)]
    if status:
        df_filtrado = df_filtrado[df_filtrado["Status do Pedido"].isin(status)]
    if categorias:
        df_filtrado = df_filtrado[df_filtrado["Categoria Global L2"].isin(categorias)]
    if len(datas) == 2:
        df_filtrado = df_filtrado[(df_filtrado["Data do pedido"] >= datas[0]) & (df_filtrado["Data do pedido"] <= datas[1])]

    st.markdown("---")
    st.subheader("📊 Gráficos interativos")

    col_tipo, col_agrupamento = st.columns(2)
    with col_tipo:
        tipo_grafico = st.radio("Tipo de gráfico", ["Barras", "Pizza"], horizontal=True)
    with col_agrupamento:
        opcao_agrupamento = st.radio(
            "Agrupar por",
            ["Status do Pedido", "Canal", "Categoria Global L2"],
            horizontal=True
        )

    if not df_filtrado.empty:
        df_agrupado = df_filtrado.groupby(opcao_agrupamento)[coluna_comissao].sum().reset_index()

        if tipo_grafico == "Barras":
            fig = px.bar(
                df_agrupado,
                x=opcao_agrupamento,
                y=coluna_comissao,
                color=opcao_agrupamento,
                text_auto=".2s",
                title=f"Comissões por {opcao_agrupamento}"
            )
        else:
            fig = px.pie(
                df_agrupado,
                names=opcao_agrupamento,
                values=coluna_comissao,
                hole=0.4,
                title=f"Comissões por {opcao_agrupamento}"
            )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados.")

    st.markdown("---")
    st.subheader("📅 Comparação entre dois períodos")

    col_a, col_b = st.columns(2)
    with col_a:
        periodo_1 = st.date_input("Período 1", key="p1", value=[])
    with col_b:
        periodo_2 = st.date_input("Período 2", key="p2", value=[])

    if len(periodo_1) == 2 and len(periodo_2) == 2:
        df_p1 = df[(df["Data do pedido"] >= periodo_1[0]) & (df["Data do pedido"] <= periodo_1[1])]
        df_p2 = df[(df["Data do pedido"] >= periodo_2[0]) & (df["Data do pedido"] <= periodo_2[1])]

        total_1 = df_p1[coluna_comissao].sum()
        total_2 = df_p2[coluna_comissao].sum()

        col1, col2 = st.columns(2)
        col1.metric("Total comissão período 1", f"R${total_1:,.2f}")
        col2.metric("Total comissão período 2", f"R${total_2:,.2f}", delta=f"R${(total_2 - total_1):,.2f}")
