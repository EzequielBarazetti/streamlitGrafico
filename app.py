import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2
import json
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Gerador de Gráficos Dinâmico by (Ezequiel Barazetti)", layout="wide")

# Configurar conexão com o PostgreSQL
def conectar_bd():
    return psycopg2.connect(
        dbname="streamlitdb_2geg",
        user="root",
        password="wEBCpL7N6tRjYsVZaTH9haSxM3EZ0SFH",
        host="dpg-cvgakv2qgecs739d2o2g-a.oregon-postgres.render.com",
        port="5432"
    )

st.title("📊 Gerador de Gráficos Dinâmico")

# Função para carregar gráficos salvos
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

# Carregar gráficos salvos no banco
graficos_salvos = carregar_graficos()

# Opções de edição e criação de gráficos
opcao = st.selectbox("Escolha uma opção:", ["Criar novo gráfico", "Editar gráfico existente"])

# Se o usuário escolher "Criar novo gráfico"
if opcao == "Criar novo gráfico":
    # Carregar o arquivo CSV (mesmo processo anterior)
    uploaded_file = st.file_uploader("Carregue um arquivo CSV", type=["csv"])

    if uploaded_file:
        # Carregar o dataset
        df = pd.read_csv(uploaded_file)

        # Mostrar uma prévia dos dados
        st.write("Prévia do dataset:")
        st.dataframe(df.head())

        # Seleção dos campos para o gráfico
        colunas = df.columns.tolist()
        x_axis = st.selectbox("Selecione o eixo X", colunas)
        y_axis = st.selectbox("Selecione o eixo Y", colunas)

        # Selecionar o tipo de gráfico
        tipo_grafico = st.selectbox("Escolha o tipo de gráfico:", ["Barras", "Linhas", "Dispersão", "Pizza"])

        # Filtros selecionados
        filtros_selecionados = st.multiselect("Escolha quais colunas deseja usar como filtro:", colunas)
        filtros_aplicados = {}

        st.subheader("Filtros disponíveis:")
        for coluna in filtros_selecionados:
            with st.expander(f"Filtro: {coluna}"):
                valores_unicos = df[coluna].unique()
                novo_valor = st.selectbox(f"Adicionar um valor para {coluna}", valores_unicos, key=f"novo_valor_{coluna}")

                if st.button(f"Adicionar filtro {coluna}", key=f"add_{coluna}"):
                    if coluna not in filtros_aplicados:
                        filtros_aplicados[coluna] = []
                    if novo_valor not in filtros_aplicados[coluna]:
                        filtros_aplicados[coluna].append(novo_valor)
                        st.rerun()

                # Exibir filtros adicionados e permitir remoção
                if coluna in filtros_aplicados:
                    if filtros_aplicados[coluna]:
                        st.write("Valores filtrados:")
                        for val in filtros_aplicados[coluna]:
                            if st.button(f"❌ {val}", key=f"remove_{coluna}_{val}"):
                                filtros_aplicados[coluna].remove(val)
                                st.rerun()

        # Aplicar filtros no dataset
        df_filtrado = df.copy()
        for coluna, valores in filtros_aplicados.items():
            if valores:
                df_filtrado = df_filtrado[df_filtrado[coluna].isin(valores)]

        # Gerar o gráfico de acordo com o tipo escolhido
        if tipo_grafico == "Barras":
            fig = px.bar(df_filtrado, x=x_axis, y=y_axis, text_auto=True)
        elif tipo_grafico == "Linhas":
            fig = px.line(df_filtrado, x=x_axis, y=y_axis, markers=True)
        elif tipo_grafico == "Dispersão":
            fig = px.scatter(df_filtrado, x=x_axis, y=y_axis, color=x_axis)
        elif tipo_grafico == "Pizza":
            fig = px.pie(df_filtrado, names=x_axis, values=y_axis)

        # Exibir o gráfico
        st.plotly_chart(fig, use_container_width=True)

        # Salvar gráfico no banco de dados
        nome_grafico = st.text_input("Nome do gráfico", "")
        if st.button("Salvar Novo Gráfico"):
            if nome_grafico:
                try:
                    conn = conectar_bd()
                    cur = conn.cursor()
                    filtros_json = filtros_aplicados
                    cur.execute(
                        "INSERT INTO graficos (nome, eixo_x, eixo_y, tipo_grafico, filtros, path, data_criacao) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (nome_grafico, x_axis, y_axis, tipo_grafico, filtros_json, uploaded_file, datetime.now())
                    )
                    conn.commit()
                    cur.close()
                    conn.close()
                    st.success("Gráfico salvo com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
            else:
                st.warning("Dê um nome ao gráfico antes de salvar.")

# Se o usuário escolher "Editar gráfico existente"
elif opcao == "Editar gráfico existente":
    if graficos_salvos:
        grafico_selecionado = st.selectbox("Escolha um gráfico salvo:", [g[1] for g in graficos_salvos])

        # Carregar os dados do gráfico selecionado
        if grafico_selecionado:
            try:
                conn = conectar_bd()
                cur = conn.cursor()
                cur.execute("SELECT id, nome, eixo_x, eixo_y, tipo_grafico, filtros, path FROM graficos WHERE nome = %s", (grafico_selecionado,))
                grafico = cur.fetchone()
                cur.close()
                conn.close()

                if grafico:
                    grafico_id, nome, eixo_x, eixo_y, tipo_grafico, filtros_json, path = grafico
                
                    filtros = filtros_json # Aqui está a conversão correta de JSON para dict

                    # Carregar o arquivo CSV (mesmo processo anterior)
                    #uploaded_file = st.file_uploader("Carregue um arquivo CSV", type=["csv"])
                    uploaded_file = path
                    if uploaded_file:
                        df = pd.read_csv(uploaded_file)

                        # Mostrar uma prévia dos dados
                        st.write("Prévia do dataset:")
                        st.dataframe(df.head())

                        # Seleção dos campos para o gráfico
                        colunas = df.columns.tolist()
                        x_axis = st.selectbox("Selecione o eixo X", colunas, index=colunas.index(eixo_x))
                        y_axis = st.selectbox("Selecione o eixo Y", colunas, index=colunas.index(eixo_y))

                        # Selecionar o tipo de gráfico
                        tipo_grafico = st.selectbox("Escolha o tipo de gráfico:", ["Barras", "Linhas", "Dispersão", "Pizza"], index=["Barras", "Linhas", "Dispersão", "Pizza"].index(tipo_grafico))

                        # Filtros selecionados
                        filtros_selecionados = st.multiselect("Escolha quais colunas deseja usar como filtro:", colunas, default=filtros.keys())
                        filtros_aplicados = {}

                        st.subheader("Filtros disponíveis:")
                        for coluna in filtros_selecionados:
                            with st.expander(f"Filtro: {coluna}"):
                                valores_unicos = df[coluna].unique()
                                valores_atualizados = filtros.get(coluna, [])
                                novo_valor = st.selectbox(f"Adicionar um valor para {coluna}", valores_unicos, key=f"novo_valor_{coluna}")

                                if st.button(f"Adicionar filtro {coluna}", key=f"add_{coluna}"):
                                    if novo_valor not in valores_atualizados:
                                        valores_atualizados.append(novo_valor)
                                        st.rerun()

                                # Exibir filtros adicionados e permitir remoção
                                if valores_atualizados:
                                    st.write("Valores filtrados:")
                                    for val in valores_atualizados:
                                        if st.button(f"❌ {val}", key=f"remove_{coluna}_{val}"):
                                            valores_atualizados.remove(val)
                                            st.rerun()

                                filtros_aplicados[coluna] = valores_atualizados

                        # Aplicar filtros no dataset
                        df_filtrado = df.copy()
                        for coluna, valores in filtros_aplicados.items():
                            if valores:
                                df_filtrado = df_filtrado[df_filtrado[coluna].isin(valores)]

                        # Gerar o gráfico de acordo com o tipo escolhido
                        if tipo_grafico == "Barras":
                            fig = px.bar(df_filtrado, x=x_axis, y=y_axis, text_auto=True)
                        elif tipo_grafico == "Linhas":
                            fig = px.line(df_filtrado, x=x_axis, y=y_axis, markers=True)
                        elif tipo_grafico == "Dispersão":
                            fig = px.scatter(df_filtrado, x=x_axis, y=y_axis, color=x_axis)
                        elif tipo_grafico == "Pizza":
                            fig = px.pie(df_filtrado, names=x_axis, values=y_axis)

                        # Exibir o gráfico
                        st.plotly_chart(fig, use_container_width=True)

                        # Botão para salvar o gráfico editado
                        nome_grafico = st.text_input("Nome do gráfico (editar)", value=nome)
                        if st.button("Salvar Gráfico Editado"):
                            if nome_grafico:
                                try:
                                    conn = conectar_bd()
                                    cur = conn.cursor()
                                    cur.execute(
                                        "UPDATE graficos SET nome = %s, eixo_x = %s, eixo_y = %s, tipo_grafico = %s, filtros = %s, data_criacao = %s WHERE id = %s",
                                        (nome_grafico, x_axis, y_axis, tipo_grafico, json.dumps(filtros_aplicados), datetime.now(), grafico_id)
                                    )
                                    conn.commit()
                                    cur.close()
                                    conn.close()
                                    st.success("Gráfico editado e salvo com sucesso!")
                                except Exception as e:
                                    st.error(f"Erro ao salvar: {e}")
                            else:
                                st.warning("Dê um nome ao gráfico antes de salvar.")
                else:
                    st.error("Erro ao carregar os dados do gráfico.")
            except Exception as e:
                st.error(f"Erro ao carregar gráfico: {e}")
    else:
        st.warning("Escolha um gráfico para editar.")
