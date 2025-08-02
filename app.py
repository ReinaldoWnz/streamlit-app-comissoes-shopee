import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Análise de Comissões", layout="wide")
st.title("📊 Painel de Análise de Comissões - Shopee Afiliados")

# Upload do CSV
arquivo = st.file_uploader("Faça upload do relatório CSV da Shopee", type=["csv"])

if arquivo is not None:
    try:
        df = pd.read_csv(arquivo)
    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}")
        st.stop()

    try:
        df["Horário do pedido"] = pd.to_datetime(df["Horário do pedido"], errors="coerce")
    except:
        st.error("Erro ao converter a coluna 'Horário do pedido'. Verifique o formato.")
        st.stop()

    datas_invalidas = df["Horário do pedido"].isna().sum()
    if datas_invalidas > 0:
        st.warning(f"{datas_invalidas} registros têm datas inválidas e foram ignorados.")
    
    # Conversão da comissão
    coluna_comissao = "Comissão líquida do afiliado(R$)"
    df[coluna_comissao] = df[coluna_comissao].astype(str).str.replace("R$", "", regex=False).str.replace(",", ".").astype(float)

    # Filtros principais
    st.sidebar.markdown("### 🔍 Filtros")

    status = st.sidebar.multiselect("Status do Pedido", df["Status do Pedido"].dropna().unique())
    canal = st.sidebar.multiselect("Canal", df["Canal"].dropna().unique())
    categoria = st.sidebar.multiselect("Categoria Global L2", df["Categoria Global L2"].dropna().unique())

    st.sidebar.markdown("### 📅 Período Principal")
    data_inicio = st.sidebar.date_input("Data de início", df["Horário do pedido"].min().date(), key="inicio")
    data_fim = st.sidebar.date_input("Data de fim", df["Horário do pedido"].max().date(), key="fim")

    st.sidebar.markdown("### 📅 Período de Comparação")
    comparar = st.sidebar.checkbox("Ativar comparação com outro período")
    if comparar:
        data_inicio_comp = st.sidebar.date_input("Início (comparação)", df["Horário do pedido"].min().date(), key="inicio_comp")
        data_fim_comp = st.sidebar.date_input("Fim (comparação)", df["Horário do pedido"].max().date(), key="fim_comp")

    # Aplicar filtros principais
    def filtrar(df, inicio, fim):
        df_filtrado = df.copy()
        if status:
            df_filtrado = df_filtrado[df_filtrado["Status do Pedido"].isin(status)]
        if canal:
            df_filtrado = df_filtrado[df_filtrado["Canal"].isin(canal)]
        if categoria:
            df_filtrado = df_filtrado[df_filtrado["Categoria Global L2"].isin(categoria)]
        return df_filtrado[
            (df_filtrado["Horário do pedido"].dt.date >= inicio) &
            (df_filtrado["Horário do pedido"].dt.date <= fim)
        ]

    df_periodo = filtrar(df, data_inicio, data_fim)

    if df_periodo.empty:
        st.warning("Nenhum dado encontrado no período principal com os filtros selecionados.")
        st.stop()

    total_pedidos = len(df_periodo)
    total_comissao = df_periodo[coluna_comissao].sum()

    coL2, col2 = st.columns(2)
    coL2.metric("🧾 Total de Pedidos", total_pedidos)
    col2.metric("💰 Comissão Total (R$)", f"{total_comissao:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    st.divider()

    # Gráficos principais
    st.subheader("📈 Visualização de Dados")

    tipo_grafico = st.radio("Escolha o tipo de gráfico", ["Barras", "Pizza"], horizontal=True)
    agrupamento = st.radio("Agrupar por", ["Status do Pedido", "Canal", "Categoria Global L2"], horizontal=True)

    df_agrupado = df_periodo.groupby(agrupamento)[coluna_comissao].sum().reset_index()

    if tipo_grafico == "Barras":
        fig = px.bar(df_agrupado, x=agrupamento, y=coluna_comissao, title=f"Comissão por {agrupamento}", text_auto=".2s")
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    else:
        fig = px.pie(df_agrupado, names=agrupamento, values=coluna_comissao, title=f"Comissão por {agrupamento}")
        fig.update_traces(textinfo="percent+label")
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

    # Gráfico de comparação
    if comparar:
        st.divider()
        st.subheader("📊 Comparação Entre Períodos")

        df_comparado = filtrar(df, data_inicio_comp, data_fim_comp)
        if df_comparado.empty:
            st.warning("Nenhum dado encontrado no período de comparação.")
        else:
            df1 = df_periodo.groupby(agrupamento)[coluna_comissao].sum().reset_index()
            df1["Período"] = "Atual"
            df2 = df_comparado.groupby(agrupamento)[coluna_comissao].sum().reset_index()
            df2["Período"] = "Comparação"
            df_comp = pd.concat([df1, df2])

            fig_comp = px.bar(
                df_comp,
                x=agrupamento,
                y=coluna_comissao,
                color="Período",
                barmode="group",
                title=f"Comparação de Comissão por {agrupamento}"
            )
            fig_comp.update_layout(height=500)
            st.plotly_chart(fig_comp, use_container_width=True)
