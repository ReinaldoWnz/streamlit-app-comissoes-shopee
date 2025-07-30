import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Análise de Comissões Shopee", layout="wide")

st.title("📊 Análise de Comissões Shopee")

# Upload do arquivo CSV
arquivo = st.file_uploader("Selecione o arquivo CSV", type="csv")

if arquivo:
    df = pd.read_csv(arquivo)

    # Conversão de datas
    try:
        df["Horário do pedido"] = pd.to_datetime(
        df["Horário do pedido"],
        errors="coerce",  # força erro a virar NaT
        dayfirst=True      # garante que 01/02 seja 1º de fevereiro
        )
    except:
        st.error("Erro ao converter a coluna 'Horário do pedido'. Verifique se o formato está como dia/mês/ano hora:minuto.")
        st.stop()

    df["Comissão líquida do afiliado(R$)"] = df["Comissão líquida do afiliado(R$)"].astype(str).str.replace("R$", "", regex=False).str.replace(",", ".").astype(float)

    # FILTROS
    st.sidebar.header("Filtros")
    status = st.sidebar.multiselect("Status do pedido", df["Status do pedido"].dropna().unique())
    canal = st.sidebar.multiselect("Canal", df["Canal"].dropna().unique())
    categoria = st.sidebar.multiselect("Categoria Global L2", df["Categoria Global L2"].dropna().unique())
    data_inicio = st.sidebar.date_input("Data inicial", value=None)
    data_fim = st.sidebar.date_input("Data final", value=None)

    df_filtrado = df.copy()

    if status:
        df_filtrado = df_filtrado[df_filtrado["Status do pedido"].isin(status)]
    if canal:
        df_filtrado = df_filtrado[df_filtrado["Canal"].isin(canal)]
    if categoria:
        df_filtrado = df_filtrado[df_filtrado["Categoria Global L2"].isin(categoria)]
    if data_inicio:
        df_filtrado = df_filtrado[df_filtrado["Horário do pedido"] >= pd.to_datetime(data_inicio)]
    if data_fim:
        df_filtrado = df_filtrado[df_filtrado["Horário do pedido"] <= pd.to_datetime(data_fim)]

    st.divider()

    # Se não houver dados
    if df_filtrado.empty:
        st.warning("Nenhum dado encontrado com os filtros selecionados.")
        st.stop()
    else:
        st.success(f"{len(df_filtrado)} registros encontrados.")

    # MÉTRICAS RESUMO
    total_pedidos = len(df_filtrado)
    total_comissao = df_filtrado["Comissão líquida do afiliado(R$)"].sum()

    col1, col2 = st.columns(2)
    col1.metric("🧾 Total de Pedidos", total_pedidos)
    col2.metric("💰 Comissão Total (R$)", f"{total_comissao:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    st.divider()

    # CONFIGURAÇÃO DO GRÁFICO
    st.subheader("📈 Visualização de Dados")

    col_tipo, col_agrupamento = st.columns(2)

    tipo_grafico = col_tipo.radio("Tipo de Gráfico", ["Barras", "Pizza"], horizontal=True)
    opcao_agrupamento = col_agrupamento.radio("Agrupar por", ["Status do pedido", "Canal", "Categoria Global L2"], horizontal=True)

    coluna_comissao = "Comissão líquida do afiliado(R$)"

    if opcao_agrupamento not in df_filtrado.columns:
        st.error(f"A coluna '{opcao_agrupamento}' não foi encontrada no arquivo.")
        st.stop()

    df_agrupado = df_filtrado.groupby(opcao_agrupamento)[coluna_comissao].sum().reset_index()
    df_agrupado = df_agrupado.sort_values(by=coluna_comissao, ascending=False)

    if tipo_grafico == "Barras":
        fig = px.bar(
            df_agrupado,
            x=opcao_agrupamento,
            y=coluna_comissao,
            text=coluna_comissao,
            labels={coluna_comissao: "Comissão (R$)"},
            color=opcao_agrupamento
        )
        fig.update_traces(texttemplate="R$ %{text:.2f}", textposition="outside")
        fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
        st.plotly_chart(fig, use_container_width=True)

    elif tipo_grafico == "Pizza":
        fig = px.pie(
            df_agrupado,
            values=coluna_comissao,
            names=opcao_agrupamento,
            hole=0.4
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # COMPARAÇÃO ENTRE PERÍODOS
    st.subheader("📅 Comparação entre dois períodos")

    col_data1, col_data2 = st.columns(2)
    with col_data1:
        inicio1 = st.date_input("Início período 1", key="inicio1")
        fim1 = st.date_input("Fim período 1", key="fim1")
    with col_data2:
        inicio2 = st.date_input("Início período 2", key="inicio2")
        fim2 = st.date_input("Fim período 2", key="fim2")

    if inicio1 and fim1 and inicio2 and fim2:
        periodo1 = df_filtrado[(df_filtrado["Horário do pedido"] >= pd.to_datetime(inicio1)) & (df_filtrado["Horário do pedido"] <= pd.to_datetime(fim1))]
        periodo2 = df_filtrado[(df_filtrado["Horário do pedido"] >= pd.to_datetime(inicio2)) & (df_filtrado["Horário do pedido"] <= pd.to_datetime(fim2))]

        total1 = periodo1[coluna_comissao].sum()
        total2 = periodo2[coluna_comissao].sum()

        col1, col2 = st.columns(2)
        col1.metric("💵 Comissão Período 1", f"R$ {total1:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        col2.metric("💵 Comissão Período 2", f"R$ {total2:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

else:
    st.info("Por favor, envie um arquivo CSV para começar.")
