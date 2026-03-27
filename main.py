import streamlit as st
import random
import pandas as pd
import plotly.express as px
import requests

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gerador da Sorte & Análise", layout="wide", page_icon="🎲")

# --- REGRAS DAS LOTERIAS ---
def carregar_regras():
    return {
        "Mega-Sena": {"dezenas": 6, "total": 60, "cor": "#209869", "api_name": "megasena"},
        "Lotofácil": {"dezenas": 15, "total": 25, "cor": "#930089", "api_name": "lotofacil"},
        "Quina": {"dezenas": 5, "total": 80, "cor": "#260085", "api_name": "quina"}
    }

REGRAS = carregar_regras()

# --- FUNÇÕES CORE ---

@st.cache_data(ttl=3600) # Cache de 1 hora para não sobrecarregar a API
def buscar_ultimo_resultado(loteria_api_name):
    """Busca o último resultado de uma loteria específica usando uma API pública."""
    url = f"https://loteriascaixa-api.herokuapp.com/api/{loteria_api_name}/latest"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"Erro ao conectar à API: {e}")
        return None

def gerar_jogos(nome_loteria, quantidade=1):
    """Gera jogos aleatórios sem repetição de números."""
    config = REGRAS[nome_loteria]
    jogos = []
    for _ in range(quantidade):
        palpite = random.sample(range(1, config["total"] + 1), config["dezenas"])
        jogos.append(sorted(palpite))
    return jogos

def verificar_acertos(jogo_gerado, dezenas_sorteadas):
    """Compara um jogo gerado com as dezenas sorteadas."""
    # Converte dezenas da API (strings) para inteiros
    sorteadas_int = [int(d) for d in dezenas_sorteadas]
    # Encontra a interseção entre os dois conjuntos
    acertos = set(jogo_gerado).intersection(set(sorteadas_int))
    return len(acertos), sorted(list(acertos))

# --- INTERFACE STREAMLIT (UI) ---

st.title("🎲 Gerador de Palpites e Analisador de Loterias")
st.markdown("Gere jogos aleatórios e compare-os com o último concurso oficial.")

# --- BARRA LATERAL (SIDEBAR) ---
st.sidebar.header("Configurações do Jogo")
loteria_selecionada = st.sidebar.selectbox("Selecione a Loteria:", list(REGRAS.keys()))
qtd_jogos = st.sidebar.number_input("Quantos jogos gerar?", min_value=1, max_value=50, value=1)
btn_gerar = st.sidebar.button("Gerar Jogos e Analisar")

# --- CONTEÚDO PRINCIPAL ---
if loteria_selecionada:
    config = REGRAS[loteria_selecionada]
    
    # 1. Área de Gerenciamento de Dados (API e Gráfico)
    st.header(f"Análise do Último Concurso: {loteria_selecionada}")
    
    with st.spinner(f"Buscando último resultado da {loteria_selecionada}..."):
        dados_concurso = buscar_ultimo_resultado(config["api_name"])

    if dados_concurso:
        col1, col2, col3 = st.columns([1, 2, 2])
        
        # Coluna 1: Info Básica
    # Coluna 1: Info Básica
        with col1:
            st.metric("Concurso", dados_concurso.get('concurso', 'N/A'))
            st.metric("Data", dados_concurso.get('data', 'N/A'))
            
            # Verificação segura do acumulado
            # Algumas APIs usam 'acumulado', outras 'acumulada' ou 'proximo_estimado'
            foi_acumulado = dados_concurso.get('acumulado') or dados_concurso.get('acumulada')
            
            if foi_acumulado:
                st.warning("💰 ACUMULOU!")
                valor_prox = dados_concurso.get('valorEstimadoProximoConcurso', 0)
                if valor_prox:
                    st.write(f"Estimativa: R$ {valor_prox:,.2f}")
            else:
                st.success("🎉 Teve Ganhador!")

        # Coluna 2: Números Sorteados (UI Estilizada)
        with col2:
            st.subheader("Dezenas Sorteadas")
            dezenas = dados_concurso['dezenas']
            
            # Criar esferas visuais para os números
            html_balls = ""
            for dezena in dezenas:
                html_balls += f"""
                <div style="
                    display: inline-block;
                    width: 40px;
                    height: 40px;
                    background-color: {config['cor']};
                    color: white;
                    border-radius: 50%;
                    text-align: center;
                    line-height: 40px;
                    font-weight: bold;
                    margin: 5px;
                    font-size: 1.2em;
                ">{dezena}</div>
                """
            st.markdown(html_balls, unsafe_allow_html=True)

        # Coluna 3: Gráfico de Distribuição
        with col3:
            st.subheader("Gráfico de Distribuição")
            # Preparar dados para o gráfico (espalhamento dos números no volante)
            df_grafico = pd.DataFrame({
                'Número Sorteado': [int(d) for d in dezenas],
                'Eixo X': [int(d) for d in dezenas],
                'Tamanho': [1]*len(dezenas) # Tamanho uniforme para os pontos
            })
            
            fig = px.scatter(df_grafico, x='Eixo X', y='Número Sorteado', 
                             title=f"Espalhamento das Dezenas (1 to {config['total']})",
                             labels={'Eixo X': 'Número no Volante'},
                             range_x=[0, config['total'] + 1],
                             height=250)
            
            # Customizar o gráfico
            fig.update_traces(marker=dict(size=15, color=config['cor'], line=dict(width=2, color='DarkSlateGrey')))
            fig.update_yaxes(showticklabels=False, showgrid=False, zeroline=False)
            
            st.plotly_chart(fig, use_container_width=True)
            
    else:
        st.error("Não foi possível carregar os dados do último concurso. Tente novamente mais tarde.")

    # 2. Área de Geração de Jogos
    st.divider()
    st.header("Seus Novos Jogos Gerados")

    if btn_gerar:
        jogos_novos = gerar_jogos(loteria_selecionada, qtd_jogos)
        
        for i, jogo in enumerate(jogos_novos):
            with st.expander(f"Jogo #{i+1}: {jogo}", expanded=True):
                if dados_concurso:
                    n_acertos, dezenas_acertadas = verificar_acertos(jogo, dados_concurso['dezenas'])
                    
                    c1, c2 = st.columns(2)
                    c1.metric("Número de Acertos", f"{n_acertos} / {config['dezenas']}")
                    if n_acertos > 0:
                        c2.markdown(f"**Dezenas que você 'acertaria':** {dezenas_acertadas}")
                    else:
                        c2.write("Nenhum número coincidente com o último sorteio.")
                else:
                    st.write(jogo)
    else:
        st.info("Clique em 'Gerar Jogos e Analisar' na barra lateral para ver seus palpites.")