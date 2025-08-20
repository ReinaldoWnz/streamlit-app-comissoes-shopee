import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Análise de Comissões", layout="wide")
st.title("📊 Painel de Análise de Comissões - Shopee Afiliados")

# --- CSS para esconder o texto "Drag and drop file here" ---
st.markdown(
    """
    <style>
    .st-emotion-cache-1c7y2o4 {
        visibility: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Barra Lateral ---
st.sidebar.header("📁 Upload de Arquivo")
st.sidebar.markdown(
    """
    <p style="font-size:14px; margin-top: -10px; margin-bottom: 10px;">
    Faça upload do arquivo CSV exportado da Shopee.
    </p>
    """,
    unsafe_allow_html=True
)

# Upload do arquivo na barra lateral
arquivo = st.sidebar.file_uploader(" ", type=["csv"], label_visibility="collapsed")

# --- Processamento do CSV (só continua se o arquivo for upado) ---
if arquivo is not None:
    try:
        df = pd.read_csv(arquivo)
        st.success(f"✅ Arquivo carregado: **{arquivo.name}**")
    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}")
        st.stop()

    # --- Conteúdo da Barra Lateral (Filtros) ---
    st.sidebar.markdown("---")
    st.sidebar.header("🔍 Filtros de Análise")

    # Conversão das duas colunas para datetime
    try:
        if "Horário do pedido" in df.columns:
            df["Horário do pedido"] = pd.to_datetime(df["Horário do pedido"], errors="coerce")
        if "Tempo de Conclusão" in df.columns:
            df["Tempo de Conclusão"] = pd.to_datetime(df["Tempo de Conclusão"], errors="coerce")
    except:
        st.error("Erro ao converter as colunas de data. Verifique o formato.")
        st.stop()

    # Conversão da comissão
    coluna_comissao = "Comissão líquida do afiliado(R$)"
    if coluna_comissao in df.columns:
        df[coluna_comissao] = (
            df[coluna_comissao]
            .astype(str)
            .str.replace("R$", "", regex=False)
            .str.replace(",", ".")
            .astype(float)
        )
    else:
        st.error(f"Coluna '{coluna_comissao}' não encontrada no CSV.")
        st.stop()
    
    # --- Filtros de data separados na barra lateral ---
    st.sidebar.markdown("### 📅 Filtro para Status 'Concluído'")
    data_inicio_concluido = st.sidebar.date_input(
        "Data de início (Concluído)", 
        df["Tempo de Conclusão"].min().date() if pd.notna(df["Tempo de Conclusão"].min()) else pd.Timestamp.now().date(),
        key="inicio_concluido"
    )
    data_fim_concluido = st.sidebar.date_input(
        "Data de fim (Concluído)", 
        df["Tempo de Conclusão"].max().date() if pd.notna(df["Tempo de Conclusão"].max()) else pd.Timestamp.now().date(),
        key="fim_concluido"
    )
    
    st.sidebar.markdown("### 📅 Filtro para Outros Status")
    data_inicio_outros = st.sidebar.date_input(
        "Data de início (Pendente, Não Pago, Cancelado)", 
        df["Horário do pedido"].min().date() if pd.notna(df["Horário do pedido"].min()) else pd.Timestamp.now().date(),
        key="inicio_outros"
    )
    data_fim_outros = st.sidebar.date_input(
        "Data de fim (Pendente, Não Pago, Cancelado)", 
        df["Horário do pedido"].max().date() if pd.notna(df["Horário do pedido"].max()) else pd.Timestamp.now().date(),
        key="fim_outros"
    )
    
    # --- Filtros de canal e categoria aplicados a todos os dados ---
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔍 Outros Filtros")
    canal = st.sidebar.multiselect("Canal", df["Canal"].dropna().unique())
    categoria = st.sidebar.multiselect("Categoria Global L2", df["Categoria Global L2"].dropna().unique())


    # --- Função para filtrar dados ---
    def filtrar_df(df_base, inicio, fim, coluna_data, canal, categoria):
        df_filtrado = df_base.copy()
        
        # Filtro de Canal
        if canal:
            df_filtrado = df_filtrado[df_filtrado["Canal"].isin(canal)]
        
        # Filtro de Categoria
        if categoria:
            df_filtrado = df_filtrado[df_filtrado["Categoria Global L2"].isin(categoria)]

        # Filtro de Data
        return df_filtrado[
            (df_filtrado[coluna_data].dt.date >= inicio) &
            (df_filtrado[coluna_data].dt.date <= fim)
        ]

    # Dividir o DataFrame por status
    df_concluido_base = df[df["Status do Pedido"].str.contains("conclu", case=False, na=False)]
    df_outros_base = df[~df["Status do Pedido"].str.contains("conclu", case=False, na=False)]

    # Aplicar os filtros de data específicos a cada sub-DataFrame
    df_concluido_filtrado = filtrar_df(df_concluido_base, data_inicio_concluido, data_fim_concluido, "Tempo de Conclusão", canal, categoria)
    df_outros_filtrado = filtrar_df(df_outros_base, data_inicio_outros, data_fim_outros, "Horário do pedido", canal, categoria)

    # Combinar os DataFrames filtrados
    df_periodo = pd.concat([df_concluido_filtrado, df_outros_filtrado])
    
    if df_periodo.empty:
        st.warning("Nenhum dado encontrado com os filtros selecionados.")
        st.stop()

    # ======================
    # 🔹 SEÇÃO: Resumo por Status
    # ======================
    st.subheader("📌 Resumo por Status")

    status_resumo = {
        "Pendente": df_periodo[df_periodo["Status do Pedido"].str.contains("endente", case=False, na=False)],
        "Concluído": df_periodo[df_periodo["Status do Pedido"].str.contains("conclu", case=False, na=False)],
        "Não Pago": df_periodo[df_periodo["Status do Pedido"].str.contains("não pago|nao pago", case=False, na=False)],
        "Cancelado": df_periodo[df_periodo["Status do Pedido"].str.contains("cancel", case=False, na=False)],
    }

    col1, col2, col3, col4 = st.columns(4)
    for i, (nome, df_status) in enumerate(status_resumo.items()):
        qtd = len(df_status)
        total = df_status[coluna_comissao].sum()
        valor_formatado = f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        quantidade_formatada = f"Pedidos: {qtd}"
        
        if i == 0:
            col1.metric(f"📌 {nome}", valor_formatado, quantidade_formatada)
        elif i == 1:
            col2.metric(f"📌 {nome}", valor_formatado, quantidade_formatada)
        elif i == 2:
            col3.metric(f"📌 {nome}", quantidade_formatada_diff)
        else:
            col4.metric(f"📌 {nome}", quantidade_formatada_diff)

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

else:
    # Mensagem de instrução quando nenhum arquivo é upado
    st.info("⬆️ **Por favor, faça o upload de um arquivo CSV da Shopee na barra lateral para começar a análise.**")
