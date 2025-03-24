import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2
import json

# Configurar conexão com o PostgreSQL
def conectar_bd():
    return psycopg2.connect(
        dbname="streamlitdb_2geg",
        user="root",
        password="wEBCpL7N6tRjYsVZaTH9haSxM3EZ0SFH",
        host="dpg-cvgakv2qgecs739d2o2g-a.oregon-postgres.render.com",
        port="5432"
    )

st.set_page_config(page_title="Gerenciador de Gráficos by (Ezequiel Barazetti)", layout="wide")
st.title("📊 Gerenciador de Gráficos Salvos  by (Ezequiel Barazetti)")

# Carregar gráficos salvos no banco de dados
def carregar_graficos():
    try:
        conn = conectar_bd()
        cur = conn.cursor()
        cur.execute("SELECT id, nome FROM graficos ORDER BY data_criacao DESC")
        graficos = cur.fetchall()
        cur.close()
        conn.close()
        return graficos
    except Exception as e:
        st.error(f"Erro ao carregar gráficos: {e}")
        return []

# Listar gráficos salvos
graficos_disponiveis = carregar_graficos()
graficos_nomes = {str(g[0]): g[1] for g in graficos_disponiveis}

grafico_escolhido = st.selectbox(
    "Selecione um gráfico salvo:", 
    options=graficos_nomes.keys(), 
    format_func=lambda x: graficos_nomes[x]
)

# Espaço reservado para o gráfico
grafico_container = st.empty()

if grafico_escolhido:
    try:
        conn = conectar_bd()
        cur = conn.cursor()
        cur.execute("SELECT eixo_x, eixo_y, filtros, tipo_grafico, path FROM graficos WHERE id = %s", (grafico_escolhido,))
        resultado = cur.fetchone()
        cur.close()
        conn.close()

        if resultado:
            eixo_x, eixo_y, filtros_json,  tipo_grafico, path = resultado

            # Garantir que os filtros sejam um dicionário válido
            try:
                filtros_aplicados = json.loads(filtros_json) if isinstance(filtros_json, str) else filtros_json
            except (json.JSONDecodeError, TypeError):
                filtros_aplicados = {}

            st.success("Gráfico carregado com sucesso!")

            # Carregar o dataset
            uploaded_file = path
            df = pd.read_csv(uploaded_file)

            # Criar filtros interativos
            colunas_filtraveis = list(filtros_aplicados.keys())
            filtros_selecionados = {}

            if colunas_filtraveis:
                st.subheader("📌 Filtros disponíveis")

                for coluna in colunas_filtraveis:
                    valores_unicos = df[coluna].dropna().unique().tolist()

                    # Criar multiselect para cada coluna sem recarregar a página
                    filtros_selecionados[coluna] = st.multiselect(
                        f"Escolha os valores para {coluna}:",
                        options=valores_unicos
                    )

                # Opção para selecionar o tipo do gráfico
                tipo_grafico = st.selectbox("Escolha o tipo de gráfico:", ["Barras", "Linhas", "Dispersão", "Pizza"], index=["Barras", "Linhas", "Dispersão", "Pizza"].index(tipo_grafico))

                # Filtrar os dados
                df_filtrado = df.copy()
                for coluna, valores in filtros_selecionados.items():
                    if valores:
                        df_filtrado = df_filtrado[df_filtrado[coluna].isin(valores)]

                # Atualizar apenas o gráfico dentro do container
                with grafico_container:
                    if tipo_grafico == "Barras":
                        fig = px.bar(df_filtrado, x=eixo_x, y=eixo_y, text_auto=True)
                    elif tipo_grafico == "Linhas":
                        fig = px.line(df_filtrado, x=eixo_x, y=eixo_y, markers=True)
                    elif tipo_grafico == "Dispersão":
                        fig = px.scatter(df_filtrado, x=eixo_x, y=eixo_y, color=eixo_x)
                    elif tipo_grafico == "Pizza":
                        fig = px.pie(df_filtrado, names=eixo_x, values=eixo_y)

                    st.plotly_chart(fig, use_container_width=True)

            else:
                st.info("Nenhum filtro salvo para este gráfico.")
    
    except Exception as e:
        st.error(f"Erro ao carregar gráfico: {e}")
else:
    st.info("Nenhum gráfico salvo disponível.")
