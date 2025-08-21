import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.io as pio

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

# --- Criar um placeholder para o contêiner de upload ---
upload_container = st.sidebar.empty()
arquivo = None

# --- Conteúdo da barra lateral inicial (dentro do placeholder) ---
with upload_container:
    st.header("📁 Upload de Arquivo")
    st.markdown(
        """
        <p style="font-size:14px; margin-top: -10px; margin-bottom: 10px;">
        Faça upload do arquivo CSV exportado da Shopee.
        </p>
        """,
        unsafe_allow_html=True
    )
    arquivo = st.file_uploader(" ", type=["csv"], label_visibility="collapsed")

# --- Processamento do CSV (só continua se o arquivo for upado) ---
if arquivo is not None:
    # Se o arquivo foi upado, esvazia o contêiner de upload e exibe a mensagem de sucesso na barra lateral
    upload_container.empty()
    st.sidebar.success(f"✅ Arquivo carregado: **{arquivo.name}**")
    
    try:
        df = pd.read_csv(arquivo)
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
    min_date_concluido = df["Tempo de Conclusão"].min() if pd.notna(df["Tempo de Conclusão"].min()) else pd.Timestamp.now()
    max_date_concluido = df["Tempo de Conclusão"].max() if pd.notna(df["Tempo de Conclusão"].max()) else pd.Timestamp.now()
    
    data_inicio_concluido = st.sidebar.date_input(
        "Data de início (Concluído)", 
        min_date_concluido.date(),
        key="inicio_concluido"
    )
    data_fim_concluido = st.sidebar.date_input(
        "Data de fim (Concluído)", 
        max_date_concluido.date(),
        key="fim_concluido"
    )
    
    st.sidebar.markdown("### 📅 Filtro para Outros Status")
    min_date_outros = df["Horário do pedido"].min() if pd.notna(df["Horário do pedido"].min()) else pd.Timestamp.now()
    max_date_outros = df["Horário do pedido"].max() if pd.notna(df["Horário do pedido"].max()) else pd.Timestamp.now()

    data_inicio_outros = st.sidebar.date_input(
        "Data de início (Pendente, Não Pago, Cancelado)", 
        min_date_outros.date(),
        key="inicio_outros"
    )
    data_fim_outros = st.sidebar.date_input(
        "Data de fim (Pendente, Não Pago, Cancelado)", 
        max_date_outros.date(),
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
        
        if canal:
            df_filtrado = df_filtrado[df_filtrado["Canal"].isin(canal)]
        
        if categoria:
            df_filtrado = df_filtrado[df_filtrado["Categoria Global L2"].isin(categoria)]

        if not df_filtrado[coluna_data].empty and pd.notna(df_filtrado[coluna_data].iloc[0]):
            df_filtrado = df_filtrado[
                (df_filtrado[coluna_data].dt.date >= inicio) &
                (df_filtrado[coluna_data].dt.date <= fim)
            ]
        return df_filtrado

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

    # Mapeamento e filtragem dos DataFrames por status
    status_resumo = {
        "Pendente": df_periodo[df_periodo["Status do Pedido"].str.contains("endente", case=False, na=False)],
        "Concluído": df_periodo[df_periodo["Status do Pedido"].str.contains("conclu", case=False, na=False)],
        "Não Pago": df_periodo[df_periodo["Status do Pedido"].str.contains("não pago|nao pago", case=False, na=False)],
        "Cancelado": df_periodo[df_periodo["Status do Pedido"].str.contains("cancel", case=False, na=False)],
    }
    
    # Calcular os totais
    total_pendente = status_resumo["Pendente"][coluna_comissao].sum()
    total_concluido = status_resumo["Concluído"][coluna_comissao].sum()
    total_estimado = total_pendente + total_concluido
    total_estimado_liquido = total_estimado * 0.89  # Subtrai 11%

    # Formatar os valores
    valor_concluido_formatado = f"R$ {total_concluido:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    valor_pendente_formatado = f"R$ {total_pendente:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    valor_estimado_formatado = f"R$ {total_estimado:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    valor_estimado_liquido_formatado = f"R$ {total_estimado_liquido:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    # Formatar as datas para o rótulo
    data_concluido_str = f"({data_inicio_concluido.strftime('%d/%m/%Y')} a {data_fim_concluido.strftime('%d/%m/%Y')})"
    data_outros_str = f"({data_inicio_outros.strftime('%d/%m/%Y')} a {data_fim_outros.strftime('%d/%m/%Y')})"
    
    # Exibir a primeira linha de cartões (principais)
    col1, col2, col3 = st.columns(3)
    col1.metric(f"📌 Concluído {data_concluido_str}", valor_concluido_formatado, f"Pedidos: {len(status_resumo['Concluído'])}")
    col2.metric("📌 Total Estimado", valor_estimado_formatado, help="Soma dos valores Pendentes e Concluídos.")
    col3.metric("📌 Não Pago", f"{len(status_resumo['Não Pago'])} pedidos")

    # Exibir a segunda linha de cartões (secundários)
    col4, col5, col6 = st.columns([1, 1, 1])
    col4.metric(f"📌 Pendente {data_outros_str}", valor_pendente_formatado, f"Pedidos: {len(status_resumo['Pendente'])}")
    col5.metric("📌 Total Estimado Líquido", valor_estimado_liquido_formatado, help="Soma dos valores Pendentes e Concluídos com 11% subtraído.")
    col6.metric("📌 Cancelado", f"{len(status_resumo['Cancelado'])} pedidos")

    st.divider()

    # Gráficos principais
    st.subheader("📈 Visualização de Dados")

    tipo_grafico = st.radio("Escolha o tipo de gráfico", ["Barras", "Pizza"], horizontal=True)
    agrupamento = st.radio("Agrupar por", ["Status do Pedido", "Canal", "Categoria Global L2"], horizontal=True)

    df_agrupado = df_periodo.groupby(agrupamento)[coluna_comissao].sum().reset_index()

    # --- Estilização dos Gráficos ---
    if tipo_grafico == "Barras":
        fig = px.bar(
            df_agrupado, 
            x=agrupamento, 
            y=coluna_comissao, 
            title=f"Comissão Total por {agrupamento}",
            labels={agrupamento: agrupamento, coluna_comissao: "Comissão Total (R$)"},
            color=agrupamento,
            color_discrete_sequence=px.colors.qualitative.Plotly,
            hover_data={coluna_comissao: ":.2f"}
        )
        fig.update_layout(
            height=500,
            yaxis_title="Comissão Total (R$)",
            yaxis_tickprefix="R$ ",
            yaxis_tickformat=",.0f"
        )
        fig.update_traces(texttemplate='R$%{y:,.2f}', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
    
    else: # Gráfico de Pizza
        fig = px.pie(
            df_agrupado, 
            names=agrupamento, 
            values=coluna_comissao, 
            title=f"Distribuição de Comissão por {agrupamento}",
            color_discrete_sequence=px.colors.qualitative.Plotly
        )
        fig.update_traces(
            textposition="inside", 
            textinfo="percent+label", 
            hovertemplate="<b>%{label}</b><br>Comissão: R$ %{value:,.2f}<br>Porcentagem: %{percent}<extra></extra>"
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

    # ============================================
    # 🛍️ SEÇÃO: Top 10 Itens Mais Comprados (em um pop-up)
    # ============================================
    st.divider()
    
    # Verifica se o DataFrame e as colunas necessárias existem
    colunas_necessarias = ["ID do item", "Nome do Item", "Qtd"]
    if df_periodo.empty or not all(coluna in df_periodo.columns for coluna in colunas_necessarias):
        st.warning("Dados de produtos não disponíveis ou colunas 'ID do item', 'Nome do Item' e/ou 'Qtd' não encontradas no arquivo.")
    else:
        # Agrupa os dados por ID e Nome do Item e soma a quantidade
        top_itens = df_periodo.groupby(["ID do item", "Nome do Item"])["Qtd"].sum().nlargest(10).reset_index()
    
        if not top_itens.empty:
            # Renomeia as colunas para melhor visualização na tabela
            tabela_para_exibir = top_itens.rename(columns={"Nome do Item": "Produto", "Qtd": "Quantidade Vendida"})
            
            # Cria o botão que abre o pop-up
            with st.popover("Clique para ver o Top 10 Produtos"):
                st.subheader("🛍️ Top 10 Produtos Mais Comprados")
                # Exibe a tabela dentro do pop-up
                st.table(tabela_para_exibir)
        else:
            st.info("Nenhum item encontrado com os filtros selecionados.")
else:
    # Mensagem de instrução quando nenhum arquivo é upado
    st.info("⬆️ **Por favor, faça o upload de um arquivo CSV da Shopee na barra lateral para começar a análise.**")
