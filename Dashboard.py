import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

# --------------------
#       configurações da página
# --------------------
#
st.set_page_config(layout= "wide")

# --------------------
#       Dados
# --------------------
dados = pd.read_csv('A2_data.csv')

# --------------------
#       Ajustes de dados
# --------------------


# Converte a coluna de timestamp para datetime (ajuste o nome da coluna se necessário)
dados['timestamp'] = pd.to_datetime(dados['timestamp'])

# Cria uma coluna de semana
dados['semana'] = dados['timestamp'].dt.isocalendar().week

#contando quantas máquinas precisaram de manutenção
quantidade_manutenção = (dados['maintenance_required'] == 'yes').sum()
# Contando quantas máquinas tiveram anomalias
quantidade_anomalias = (dados['anomaly_flag'] == 'yes').sum()

# --------------------
#       Sidebar
# --------------------
st.sidebar.title('Filtros')
# Filtro de máquinas e semanas
maquinas = sorted(dados['machine'].unique())
# Adiciona opção "Selecionar todas"
maquinas_opcoes = ['Selecionar todas'] + list(maquinas)
maquinas_selecionadas = st.sidebar.multiselect('Selecione a(s) máquina(s):', maquinas_opcoes, default=['Selecionar todas'])

# Se "Selecionar todas" estiver selecionado, seleciona todas as máquinas
if 'Selecionar todas' in maquinas_selecionadas or not maquinas_selecionadas:
    maquinas_filtrar = maquinas
else:
    maquinas_filtrar = maquinas_selecionadas

semanas = sorted(dados['semana'].unique())
# Adiciona opção "Selecionar todas"
semanas_opcoes = ['Selecionar todas'] + semanas
semanas_selecionadas = st.sidebar.multiselect('Selecione a(s) semana(s):', semanas_opcoes, default=['Selecionar todas'])

# Se "Selecionar todas" estiver selecionado, seleciona todas as semanas
if 'Selecionar todas' in semanas_selecionadas or not semanas_selecionadas:
    semanas_filtrar = semanas
else:
    semanas_filtrar = semanas_selecionadas

# Filtra os dados pelas máquinas e semanas selecionadas
dados_filtrados = dados[
    (dados['machine'].isin(maquinas_filtrar)) &
    (dados['semana'].isin(semanas_filtrar))
]
st.session_state['dados_filtrados'] = dados_filtrados
# --------------------
#       Dashboard
# --------------------


# cria as abas da aplicação
tab_manutencao, tab_disponibilidade, tab_tabelas = st.tabs(['manutenção', 'disponibilidade', 'tabelas'])

# Seção de Manutenção   
with tab_manutencao:
    # --------------------
    #       Gráfico de barras: máquinas por quantidade de manutenção
    # --------------------

    st.subheader('Quantidade de manutenções por máquina (aplicando filtros)')

    # Conta quantos "yes" em maintenance_required por máquina nos dados filtrados
    manutencoes_por_maquina = (
        dados_filtrados[dados_filtrados['maintenance_required'].str.lower() == 'yes']
        .groupby('machine')
        .size()
        .reset_index(name='Quantidade de Manutenção')
    )

    fig = px.bar(
        manutencoes_por_maquina,
        x='machine',
        y='Quantidade de Manutenção',
        labels={'machine': 'Máquina', 'Quantidade de Manutenção': 'Qtd. Manutenção'},
        title='Quantidade de manutenções por máquina (filtrado)'
    )
    st.plotly_chart(fig, use_container_width=True)

    # --------------------
    #       Gráfico de barras: máquinas com anomalias
    # --------------------

    st.subheader('Quantidade de máquinas com anomalias (aplicando filtros)')

    # Conta quantos "yes" em anomaly_flag por máquina nos dados filtrados
    anomalias_por_maquina = (
        dados_filtrados[dados_filtrados['anomaly_flag'].str.lower() == 'yes']
        .groupby('machine')
        .size()
        .reset_index(name='Quantidade de Anomalias')
    )

    fig_anomalias = px.bar(
        anomalias_por_maquina,
        x='machine',
        y='Quantidade de Anomalias',
        labels={'machine': 'Máquina', 'Quantidade de Anomalias': 'Qtd. Anomalias'},
        title='Quantidade de máquinas com anomalias (filtrado)'
    )
    st.plotly_chart(fig_anomalias, use_container_width=True)

# Seção de Disponibilidade
with tab_disponibilidade:

    # --------------------
    #       Cálculo de disponibilidade das máquinas
    # --------------------

    st.subheader('Disponibilidade das máquinas (aplicando filtros)')

    # Ordena por máquina e timestamp para garantir sequência correta
    dados_filtrados = dados_filtrados.sort_values(['machine', 'timestamp'])

    # Calcula o tempo entre registros consecutivos para cada máquina
    dados_filtrados['tempo_intervalo'] = dados_filtrados.groupby('machine')['timestamp'].diff().dt.total_seconds().fillna(0)

    # Considera apenas intervalos positivos (ignora o primeiro registro de cada máquina)
    dados_filtrados['tempo_intervalo'] = dados_filtrados['tempo_intervalo'].apply(lambda x: x if x > 0 else 0)

    # Tempo total disponível por máquina (soma dos intervalos)
    tempo_total = dados_filtrados.groupby('machine')['tempo_intervalo'].sum().reset_index(name='Tempo Total (s)')

    # Tempo disponível (status diferente de 'Failure')
    tempo_disponivel = dados_filtrados[dados_filtrados['machine_status'].str.lower() != 'failure'].groupby('machine')['tempo_intervalo'].sum().reset_index(name='Tempo Disponível (s)')

    # Junta os dois DataFrames
    disponibilidade = pd.merge(tempo_total, tempo_disponivel, on='machine', how='left').fillna(0)

    # Calcula a disponibilidade percentual
    disponibilidade['Disponibilidade (%)'] = (disponibilidade['Tempo Disponível (s)'] / disponibilidade['Tempo Total (s)']) * 100

    # Função para converter segundos em dias, horas, minutos e segundos
    def formatar_tempo(segundos):
        dias = int(segundos // 86400)
        horas = int((segundos % 86400) // 3600)
        minutos = int((segundos % 3600) // 60)
        seg = int(segundos % 60)
        return f"{dias}d {horas}h {minutos}m {seg}s"

    # Aplica a função para as colunas de tempo
    disponibilidade['Tempo Total Formatado'] = disponibilidade['Tempo Total (s)'].apply(formatar_tempo)
    disponibilidade['Tempo Disponível Formatado'] = disponibilidade['Tempo Disponível (s)'].apply(formatar_tempo)

    # Gráfico de barras de disponibilidade
    fig_disp = px.bar(
        disponibilidade,
        x='machine',
        y='Disponibilidade (%)',
        labels={'machine': 'Máquina', 'Disponibilidade (%)': 'Disponibilidade (%)'},
        title='Disponibilidade (%) por máquina (filtrado)'
    )
    st.plotly_chart(fig_disp, use_container_width=True)

    # --------------------
    #       Gráfico de linha: Disponibilidade por semana para cada máquina filtrada
    # --------------------

    st.subheader('Disponibilidade (%) por semana para cada máquina (apenas filtro de máquina)')

    # Calcula a disponibilidade por semana apenas para as máquinas filtradas (todas as semanas)
    dados_maquinas = dados[dados['machine'].isin(maquinas_filtrar)].copy()
    dados_maquinas = dados_maquinas.sort_values(['machine', 'timestamp'])

    # Calcula o tempo entre registros consecutivos para cada máquina
    dados_maquinas['tempo_intervalo'] = dados_maquinas.groupby('machine')['timestamp'].diff().dt.total_seconds().fillna(0)
    dados_maquinas['tempo_intervalo'] = dados_maquinas['tempo_intervalo'].apply(lambda x: x if x > 0 else 0)

    # Agrupa por máquina e semana
    tempo_total_semana = dados_maquinas.groupby(['machine', 'semana'])['tempo_intervalo'].sum().reset_index(name='Tempo Total (s)')
    tempo_disp_semana = dados_maquinas[dados_maquinas['machine_status'].str.lower() != 'failure'].groupby(['machine', 'semana'])['tempo_intervalo'].sum().reset_index(name='Tempo Disponível (s)')

    # Junta os dois DataFrames
    disp_semana = pd.merge(tempo_total_semana, tempo_disp_semana, on=['machine', 'semana'], how='left').fillna(0)
    disp_semana['Disponibilidade (%)'] = (disp_semana['Tempo Disponível (s)'] / disp_semana['Tempo Total (s)']) * 100

    # Gráfico de linha de disponibilidade por semana (apenas filtro de máquina)
    fig_linha_disp = px.line(
        disp_semana,
        x='semana',
        y='Disponibilidade (%)',
        color='machine',
        markers=True,
        labels={'semana': 'Semana', 'Disponibilidade (%)': 'Disponibilidade (%)', 'machine': 'Máquina'},
        title='Disponibilidade (%) por semana para cada máquina'
    )
    st.plotly_chart(fig_linha_disp, use_container_width=True)

    # --------------------
    #       Gráfico de linha: Indisponibilidade por semana para cada máquina filtrada
    # --------------------

    st.subheader('Indisponibilidade (%) por semana para cada máquina (apenas filtro de máquina)')

    # Indisponibilidade é 100 - disponibilidade
    disp_semana['Indisponibilidade (%)'] = 100 - disp_semana['Disponibilidade (%)']

    fig_linha_indisp = px.line(
        disp_semana,
        x='semana',
        y='Indisponibilidade (%)',
        color='machine',
        markers=True,
        labels={'semana': 'Semana', 'Indisponibilidade (%)': 'Indisponibilidade (%)', 'machine': 'Máquina'},
        title='Indisponibilidade (%) por semana para cada máquina'
    )
    st.plotly_chart(fig_linha_indisp, use_container_width=True)

    # --------------------
    #       Gráfico de mapa de árvore: Disponibilidade por máquina (com valores no gráfico)
    # --------------------

    st.subheader('Mapa de Árvore: Disponibilidade (%) por máquina (com valores)')

    fig_treemap_disp = px.treemap(
        disponibilidade,
        path=['machine'],
        values='Disponibilidade (%)',
        color='Disponibilidade (%)',
        color_continuous_scale='Greens',
        title='Mapa de Árvore: Disponibilidade (%) por máquina',
        custom_data=['Disponibilidade (%)']
    )

    fig_treemap_disp.update_traces(
        texttemplate='<b>%{label}</b><br>%{customdata[0]:.2f}%',
        textinfo='label+value'
    )

    st.plotly_chart(fig_treemap_disp, use_container_width=True)

    # --------------------
    #       Gráfico de mapa de árvore: Indisponibilidade por máquina (com valores no gráfico)
    # --------------------

    st.subheader('Mapa de Árvore: Indisponibilidade (%) por máquina (com valores)')

    # Garante que a coluna exista
    disponibilidade['Indisponibilidade (%)'] = 100 - disponibilidade['Disponibilidade (%)']

    fig_treemap_indisp = px.treemap(
        disponibilidade,
        path=['machine'],
        values='Indisponibilidade (%)',
        color='Indisponibilidade (%)',
        color_continuous_scale='Reds',
        title='Mapa de Árvore: Indisponibilidade (%) por máquina',
        custom_data=['Indisponibilidade (%)']
    )

    fig_treemap_indisp.update_traces(
        texttemplate='<b>%{label}</b><br>%{customdata[0]:.2f}%',
        textinfo='label+value'
    )

    st.plotly_chart(fig_treemap_indisp, use_container_width=True)

    # --------------------
    #       Gráfico de mapa de árvore: Vida útil restante prevista por máquina (com valores no gráfico)
    # --------------------

    st.subheader('Mapa de Árvore: Vida útil restante prevista')

    # Calcula a média da vida útil prevista por máquina nos dados filtrados
    vida_util_media = dados_filtrados.groupby('machine')['predicted_remaining_life'].mean().reset_index()

    fig_treemap_life = px.treemap(
        vida_util_media,
        path=['machine'],
        values='predicted_remaining_life',
        color='predicted_remaining_life',
        color_continuous_scale='Blues',
        title='Mapa de Árvore: Vida útil restante prevista (média) por máquina',
        custom_data=['predicted_remaining_life']
    )

    fig_treemap_life.update_traces(
        texttemplate='<b>%{label}</b><br>%{customdata[0]:.2f}',
        textinfo='label+value'
    )

    st.plotly_chart(fig_treemap_life, use_container_width=True)

# Seção de tabelas
with tab_tabelas:
  
    # --------------------
    #       Tabelas
    # --------------------

    st.subheader('Média dos itens para as semanas e máquinas filtradas')
    media_semanas_filtradas = (
        dados_filtrados
        .mean(numeric_only=True)
        .to_frame(name='Média')
        .reset_index()
        .rename(columns={'index': 'Item'})
    )
    st.dataframe(media_semanas_filtradas)

    # Exibe a tabela de disponibilidade com tempos formatados
    st.subheader('Tabela de Disponibilidade')
    st.dataframe(disponibilidade[['machine', 'Tempo Total Formatado', 'Tempo Disponível Formatado', 'Disponibilidade (%)']])
