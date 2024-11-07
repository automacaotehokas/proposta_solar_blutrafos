import streamlit as st
import requests
from datetime import datetime

st.set_page_config(layout="wide")

def carregar_cidades():
    if 'cidades' not in st.session_state:
        url = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                st.session_state['cidades'] = sorted(
                    [f"{cidade['nome']}/{cidade['microrregiao']['mesorregiao']['UF']['sigla']}" for cidade in response.json()]
                )
            else:
                st.error("Erro ao buscar as cidades. Por favor, tente novamente mais tarde.")
                st.session_state['cidades'] = []
        except Exception as e:
            st.error(f"Erro ao conectar com a API: {e}")
            st.session_state['cidades'] = []


if 'local_frete' not in st.session_state:
    st.session_state['local_frete'] = "None"
    
carregar_cidades()
# Adicionar a opção "None" à lista de cidades
cidades_com_none = [""] + st.session_state['cidades']

# Funções para carregar e salvar os valores do estado temporário
def store_value(key):
    st.session_state[key] = st.session_state[f"_{key}"]

def load_value(key):
    if key in st.session_state:
        st.session_state[f"_{key}"] = st.session_state[key]

def aplicar_mascara_telefone():
    telefone = ''.join(filter(str.isdigit, st.session_state['fone_raw']))  # Remove todos os caracteres que não são dígitos
    if len(telefone) == 11:
        telefone_formatado = f"({telefone[:2]}) 9 {telefone[2:7]}-{telefone[7:]}"
    elif len(telefone) == 10:
        telefone_formatado = f"({telefone[:2]}) {telefone[2:6]}-{telefone[6:]}"
    else:
        telefone_formatado = telefone
    st.session_state['dados_iniciais']['fone'] = telefone_formatado

# Inicializa o session_state se ele ainda não existe
if 'dados_iniciais' not in st.session_state:
    st.session_state['dados_iniciais'] = {
        'dia': '',
        'mes': '',
        'ano': '',
        'bt': '',
        'rev': '',
        'cliente': '',
        'obra': ' ',
        'nomeCliente': '',
        'email': '',
        'local': '',
        'fone': '',
        'tipofrete': 'CIF',
        'local_frete': '',
    }

def configurar_informacoes():
    st.title('Dados Iniciais')
    st.markdown("---")
    
    # Campo para a data da proposta
    data_hoje = datetime.today()
    data_selecionada = st.date_input('Data da Proposta:', value=data_hoje)

    # Mapeando o número do mês para o nome em português
    meses_pt = [
        "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", 
        "Junho", "Julho", "Agosto", "Setembro", "Outubro", 
        "Novembro", "Dezembro"
    ]
    
    # Atualiza as informações de data no session_state
    st.session_state['dados_iniciais'].update({
        'dia': data_selecionada.strftime('%d'),
        'mes': meses_pt[data_selecionada.month],
        'ano': data_selecionada.strftime('%Y'),
    })

    # Criação de duas colunas, cada uma ocupando 50% do espaço
    col1, col2 = st.columns(2)

    with col1:
        st.session_state['dados_iniciais'].update({
            'bt': st.text_input('Nº OR:', st.session_state['dados_iniciais'].get('bt', ''), autocomplete='off'),
            'rev': st.text_input('Rev:', st.session_state['dados_iniciais'].get('rev', ''), autocomplete='off'),
            'cliente': st.text_input('Cliente:', st.session_state['dados_iniciais'].get('cliente', ''), autocomplete='off', placeholder='Digite o nome da empresa'),
            'obra': st.text_input('Obra:', st.session_state['dados_iniciais'].get('obra', ''), autocomplete='off'),
        })

        with col2:
            st.session_state['dados_iniciais'].update({
                'diasvalidade': st.text_input('Validade da Proposta (Dias):', st.session_state['dados_iniciais'].get('diasvalidade', ''), autocomplete='off'),
                'mesesgarantia': st.text_input('Meses de Garantia:', st.session_state['dados_iniciais'].get('mesesgarantia', ''), autocomplete='off'),
                
                # Tipo de Frete adicionado aqui dentro, como solicitado
                'tipofrete': st.selectbox(
                    'Tipo de Frete:',
                    ['CIF', 'FOB'],
                    index=['CIF', 'FOB'].index(st.session_state['dados_iniciais'].get('tipofrete', 'CIF'))
                ),
                                # Tipo de Frete adicionado aqui dentro, como solicitado
                'localentrega': st.selectbox(
                    'Local de Entrega:',
                    cidades_com_none,
                    index=cidades_com_none.index(st.session_state['dados_iniciais'].get('localentrega', ''))
                ),


            })
    

# Chamada para configurar as informações na interface
configurar_informacoes()
