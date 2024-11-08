import streamlit as st
import pandas as pd
from config_db import conectar_banco
from dotenv import load_dotenv
from pages.Inicial import carregar_cidades


# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

def ajustar_lista_itens():
    for usina in st.session_state['usinas']:
        while len(usina['itens']) < usina['num_itens']:
            usina['itens'].append({'descricao': '', 'quantidade': 0, 'valor_unitario': 0.0, 'order': 0})
        while len(usina['itens']) > usina['num_itens']:
            usina['itens'].pop()

# Função para buscar dados do banco de dados
@st.cache_data
def buscar_dados_solar():
    conn = conectar_banco()
    query = """
        SELECT produto, potencia, tensao_mt, kva, corrente, preco, cubiculo_mt, qgbt
        FROM custos_solar
        ORDER BY produto, potencia ASC;
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

@st.cache_data
def buscar_dados_media_tensao():
    conn = conectar_banco()
    query = """
        SELECT id, descricao, potencia, classe_tensao, perdas, preco, p_trafo, valor_ip_baixo, valor_ip_alto, p_caixa
        FROM custos_media_tensao
        ORDER BY potencia ASC
    """
    df_media_tensao = pd.read_sql(query, conn)
    conn.close()
    return df_media_tensao

def calcular_preco_total(preco_unit, quantidade):
    return preco_unit * quantidade

def obter_preco_solar(df, produto, potencia, tensao_mt=None, configuracao_mt=None, configuracao_bt=None, corrente=None):
    """
    Filtra o DataFrame para obter o preço do SKID ou QGBT com base nas configurações.
    """
    # Filtra os dados comuns para SKID e QGBT
    filtro = df[
        (df['produto'] == produto) &
        (df['potencia'] == potencia) &
        (df['qgbt'] == configuracao_bt) &
        (df['corrente'] == corrente)
    ]

    # Para o produto SKID, adicionamos o filtro adicional de tensao_mt e cubiculo_mt
    if produto == "SKID" and tensao_mt and configuracao_mt:
        filtro = filtro[
            (filtro['tensao_mt'] == tensao_mt) &
            (filtro['cubiculo_mt'] == configuracao_mt)
        ]

    # Verifica se há algum resultado após o filtro
    if not filtro.empty:
        preco_principal = filtro.iloc[0]['preco']  # Obter o preço da primeira linha do filtro
    else:
        preco_principal = 0  # Caso não encontre, define como 0

    return preco_principal

def generate_item_id(kit_item, usina_index, model_index):
    return f"{kit_item}_{usina_index}_{model_index}"

df_media_tensao = buscar_dados_media_tensao()
df_solar = buscar_dados_solar()

icms_base = 12 / 100
irpj_cssl = 2.28 / 100
tkxadmmkt = 3.7 / 100
mocusfixo = 20 / 100
pisconfins = 9.25 / 100
p_caixa_24 = 30 / 100
p_caixa_36 = 50 / 100
valor_ip_baixo = df_media_tensao['valor_ip_baixo'].iloc[0]
valor_ip_alto = df_media_tensao['valor_ip_alto'].iloc[0]
p_caixa = df_media_tensao['p_caixa'].iloc[0]
percentuais_k = {
    1: 0.0,
    4: 0.0502,
    6: 0.0917,
    13: 0.2317,
    20: 0.3359
}

itens_kit = {
    "Inversor": {
        "Sungrow": {
            "250 HX-20": {
                "valor": 6000,
                "fator_importacao": 1.33
            },
            "333 HX": {
                "valor": 7200,
                "fator_importacao": 1.33
            }
        },
        "Huawei": {
            "SUN2000-12KTL": {
                "valor": 5000,
                "fator_importacao": 1.33
            },
            "SUN2000-20KTL": {
                "valor": 7000,
                "fator_importacao": 1.33
            }
        }
    },
    "Logger": {
        "Sungrow": {
            "1000B": {
                "valor": 500,
                "fator_importacao": 1.58
            },
        },
        "Huawei": {
            "1000B": {
                "valor": 500,
                "fator_importacao": 1.58
            }
        }
    },
    "Cabo": {
        "MT": {
            "25mm 15kV alumínio": {"valor": 23.68},
            "35mm 15kV alumínio": {"valor": 26.1},
            "50mm 15kV alumínio": {"valor": 28.65},
            "70mm 15kV alumínio": {"valor": 33.65},
            "50mm 36kV alumínio": {"valor": 59.06},
            "70mm 36kV alumínio": {"valor": 50.16}
        },
        "BT": {
            "120mm alumínio XLPE": {"valor": 12.77},
            "185mm alumínio XLPE": {"valor": 19.23},
            "240mm alumínio XLPE": {"valor": 25.27}
        },
        "Solar": {
            "4mm 1kV": {"valor": 3.63},
            "6mm 1kV": {"valor": 5.08}
        }
    },
    "Estrutura": {
        "Fixa": {
            "Simples": {"valor": 0.24},
            "Média": {"valor": 0.3},
            "Robusta": {"valor": 0.39}
        },
        "Tracker": {
            "Simples": {"valor": 0.498},
            "Média": {"valor": 0.528},
            "Robusta": {"valor": 0.673}
        }
    },
    "Cabine": {
        "CEMIG 15kV": {
            "1 Medição": {"valor": 145800.00},
            "2 Medição": {"valor": 349488.00},
            "3 Medição": {"valor": 507384.00}
        },
        "EQUATORIAL GO 36kV": {
            "1 Medição": {"valor": 380000},
            "2 Medição": {"valor": 1083341.64},
            "3 Medição": {"valor": 1462849.2}
        },
        "EQUATORIAL PA 36kV": {
            "3 Medição": {"valor": 1162080}
        },
        "NEOENERGIA ELEKTRO 15kV": {           
            "1 Medição": {"valor": 557714.02},
            "3 Medição": {"valor": 661608}
        },
        "ENERGISA MT 36kV": {
            "3 Medição": {"valor": 1026000} 
        },
        "ENERGISA TO 36kV": {
            "3 Medição": {"valor": 1188000}
        },
        "ENERGISA TO 15kV": {
            "3 Medição": {"valor": 658800} 
        }
    },
    "Módulo": {
        "Padrão": {
            "615": {"valor": 0.084},
            "625": {"valor": 0.084},
            "695": {"valor": 0.088},
            "700": {"valor": 0.088},
            "705": {"valor": 0.088}
        }
    }
}

def obter_kva_skid(df_solar, item_selecionado, potencia_escolhida, configuracao_bt_escolhida, corrente_escolhida, tensao_bt_escolhida):
    """
    Obtém o valor do 'kva' da base de dados df_solar de acordo com os campos fornecidos.

    Parâmetros:
    - df_solar: DataFrame contendo os dados.
    - item_selecionado: O produto selecionado.
    - potencia_escolhida: A potência selecionada.
    - configuracao_bt_escolhida: A configuração BT selecionada.
    - corrente_escolhida: A corrente selecionada.
    - tensao_bt_escolhida: A tensão BT selecionada.

    Retorna:
    - O valor do 'kva' se encontrado, caso contrário, None.
    """
    kva_disponiveis = df_solar[
        (df_solar['produto'] == item_selecionado) & 
        (df_solar['potencia'] == potencia_escolhida) & 
        (df_solar['qgbt'] == configuracao_bt_escolhida) &
        (df_solar['tensao_mt'] == tensao_bt_escolhida) & 
        (df_solar['cubiculo_mt'] == configuracao_mt_escolhida)
    ]['kva']

    if not kva_disponiveis.empty:
        return int(kva_disponiveis.iloc[0])  # Converte para int
    else:
        return None

# Funções para carregar e salvar os valores do estado temporário
def store_value(key):
    if "_" + key not in st.session_state:
        st.session_state["_" + key] = st.session_state.get(key, None)
    st.session_state[key] = st.session_state["_" + key]
def load_value(key):
    if key in st.session_state:
        st.session_state["_" + key] = st.session_state[key]

# Função para calcular o preço do SKID ou QGBT com base nos dados do banco
def calcular_preco(df, produto_escolhido, potencia_escolhida, tensao_mt_escolhida, configuracao_mt_escolhida, configuracao_bt_escolhida, corrente_escolhida):
    filtro = df[
        (df['produto'] == produto_escolhido) & 
        (df['potencia'] == potencia_escolhida) & 
        (df['qgbt'] == configuracao_bt_escolhida)
    ]
    if produto_escolhido == "SKID" and tensao_mt_escolhida is not None:
        filtro = filtro[filtro['tensao_mt'] == tensao_mt_escolhida]
        filtro = filtro[filtro['cubiculo_mt'] == configuracao_mt_escolhida]

    filtro = filtro[filtro['corrente'] == corrente_escolhida]

    if not filtro.empty:
        item_selecionado = filtro.iloc[0]
        preco_item = item_selecionado['preco']
        kva = item_selecionado['kva']
    else:
        preco = 0
        kva = 0

    return preco_item, kva

    
def obter_kva_qgbt(df_solar, item_selecionado, potencia_escolhida, configuracao_bt_escolhida):
    """
    Obtém o valor do 'kva' da base de dados df_solar de acordo com os campos fornecidos.

    Parâmetros:
    - df_solar: DataFrame contendo os dados.
    - item_selecionado: O produto selecionado.
    - potencia_escolhida: A potência selecionada.
    - configuracao_bt_escolhida: A configuração BT selecionada.

    Retorna:
    - O valor do 'kva' se encontrado, caso contrário, None.
    """
    kva_disponiveis = df_solar[
        (df_solar['produto'] == item_selecionado) & 
        (df_solar['potencia'] == potencia_escolhida) & 
        (df_solar['qgbt'] == configuracao_bt_escolhida)
    ]['kva'].unique()

    return kva_disponiveis[0] if len(kva_disponiveis) > 0 else None

# Função para formatar a descrição do item (SKID ou QGBT)
def formatar_descricao(item_selecionado, potencia_escolhida, tensao_mt_escolhida, tensao_bt_escolhida, corrente_escolhida, kva):
    descricao = ""
    if item_selecionado == "SKID":
        descricao += f"{item_selecionado} {potencia_escolhida} kVA\n"
        descricao += f"- Skid Estruturado Em Aço para {potencia_escolhida} kVA;\n"
        descricao += f"- Transformador Isolado a Seco {potencia_trafo} kVA {classe_tensao};\n"
        descricao += f"- Perdas = {perdas}; K={fator_k_escolhido}; IP={ip_escolhido};\n"
        descricao += f"- QGBT {tensao_bt_escolhida}V {corrente_escolhida}A {kva}kA"
    else:
        descricao += f"QGBT {tensao_bt_escolhida} V {corrente_escolhida} A  {kva} kA"
    return descricao

# Etapa 1: Configuração dos Percentuais
st.header("Configuração dos Percentuais")

# Função para classificar a proposta como Estação Fotovoltaica ou Subestação Unitária
def classificar_proposta_estacao_subestacao():
    produtos_presentes = set()
    for usina in st.session_state.get('usinas', []):
        for item in usina.get('itens', []):
            produtos_presentes.add(item.get('produto'))

    # Verificar se a proposta possui Inversor, Módulo, Estrutura ou Logger
    if any(produto in produtos_presentes for produto in ["Inversor", "Módulo", "Estrutura", "Logger"]):
        st.session_state['classificacao_estacao_subestacao'] = "Estação Fotovoltaica"
    else:
        st.session_state['classificacao_estacao_subestacao'] = "Subestação Unitária"

def garantir_valores_inicializados():
    if 'lucro' not in st.session_state:
        st.session_state['lucro'] = 5.0
    if 'contribuinte' not in st.session_state:
        st.session_state['contribuinte'] = "Sim"
    if 'icms' not in st.session_state:
        st.session_state['icms'] = 12.0
    if 'frete' not in st.session_state:
        st.session_state['frete'] = 5.0
    if 'comissao' not in st.session_state:
        st.session_state['comissao'] = 5.0
    if 'dolar' not in st.session_state:
        st.session_state['dolar'] = 5.4
    if 'percentuais' not in st.session_state:
        # Calcula o valor inicial de percentuais
        st.session_state['percentuais'] = (
            (st.session_state['lucro'] / 100) +
            (st.session_state['icms'] / 100) +
            (st.session_state['comissao'] / 100) +
            (st.session_state['frete'] / 100) +
            (2.28 / 100) + (3.7 / 100) + (20 / 100) + (9.25 / 100)
        )
    if 'local_frete_itens' not in st.session_state:
        st.session_state['local_frete_itens'] = st.session_state['dados_iniciais'].get('local_frete', '')


# Garantir que os valores dos percentuais estão inicializados
garantir_valores_inicializados()

st.session_state['contribuinte'] = st.radio(
    "O cliente é contribuinte do ICMS?",
    options=["Não", "Sim"],
    index=["Não", "Sim"].index(st.session_state.get('contribuinte', 'Não'))  # Obtém o índice do valor atual, com "Não" como padrão
)

st.session_state['outputcontribuinte'] = "cliente contribuinte do ICMS" if st.session_state['contribuinte'] == "Sim" else "cliente não contribuinte do ICMS"


# Criar os widgets para os percentuais diretamente
st.session_state['lucro'] = st.number_input('Lucro (%):', min_value=0.0, max_value=100.0, step=0.1, value=st.session_state['lucro'])
st.session_state['icms'] = st.number_input('ICMS (%):', min_value=0.0, max_value=100.0, step=0.1, value=st.session_state['icms'])
st.session_state['frete'] = st.number_input('Frete (%):', min_value=0.0, step=0.1, value=st.session_state['frete'])



if 'difal' not in st.session_state:
    st.session_state['difal'] = 0.0
if 'f_pobreza' not in st.session_state:
    st.session_state['f_pobreza'] = 0.0

if 'contribuinte' == "Sim":
    st.session_state['difal'] = 0.0
    st.session_state['f_pobreza'] = 0.0
else:
    st.session_state['difal'] = st.number_input(
        'DIFAL (%):',
        min_value=0.0,
        value=st.session_state['difal'],
        step=0.1
    )
    st.session_state['f_pobreza'] = st.number_input(
        'F. Pobreza (%):',
        min_value=0.0,
        value=st.session_state['f_pobreza'],
        step=0.1
    )

    
st.session_state['comissao'] = st.number_input('Comissão (%):', min_value=0.0, step=0.1, value=st.session_state['comissao'])
st.session_state['dolar'] = st.number_input('Valor do Dólar (R$)', min_value=0.0, step=0.01, value=st.session_state['dolar'])


# Cálculo dos percentuais
percentuais = (
    st.session_state['lucro'] / 100 +
    icms_base +
    st.session_state['comissao'] / 100 +
    st.session_state['frete'] / 100 +
    irpj_cssl + tkxadmmkt + mocusfixo + pisconfins
)
st.session_state['percentuais'] = percentuais

st.header("Configuração das Usinas")


# Inicializar num_usinas no session_state se ainda não estiver presente
if 'num_usinas' not in st.session_state:
    st.session_state['num_usinas'] = 1
if 'usinas' not in st.session_state:
    st.session_state['usinas'] = []

# Controle de número de usinas
num_usinas_input = st.number_input(
    "Quantas usinas terá na proposta?", 
    min_value=1, 
    step=1, 
    value=st.session_state['num_usinas'],  
    key="num_usinas_input"
)

# Atualizar o valor no session_state se o input mudar
if num_usinas_input != st.session_state['num_usinas']:
    st.session_state['num_usinas'] = num_usinas_input

# Ajustar a lista de usinas conforme o número desejado
while len(st.session_state['usinas']) < st.session_state['num_usinas']:
    st.session_state['usinas'].append({'nome': '', 'num_itens': 1, 'itens': []})
while len(st.session_state['usinas']) > st.session_state['num_usinas']:
    st.session_state['usinas'].pop()



# Exibir a configuração das usinas
for i in range(st.session_state['num_usinas']):
    with st.expander(f"Configuração da Usina {i + 1}"):
        # Nome da Usina
        usina_nome = st.text_input(f"Nome da Usina {i + 1}", value=st.session_state['usinas'][i]['nome'], key=f"nome_usina_{i}")
        st.session_state['usinas'][i]['nome'] = usina_nome

        # Número de itens
        num_itens = st.number_input(f"Quantos itens terá a {usina_nome}?", min_value=1, step=1, value=st.session_state['usinas'][i]['num_itens'], key=f"num_itens_{i}")
        st.session_state['usinas'][i]['num_itens'] = num_itens
        
        # Ajustar a lista de itens de cada usina conforme o número desejado
        for usina in st.session_state['usinas']:
            while len(usina['itens']) < usina['num_itens']:
                usina['itens'].append({'descricao': '', 'quantidade': 0, 'valor_unitario': 0.0, 'order': 0})
            while len(usina['itens']) > usina['num_itens']:
                usina['itens'].pop()



        st.write("---")
        for item_idx in range(num_itens):
            # Adicionar estrutura de itens ao session_state se não existir
            while len(st.session_state['usinas'][i]['itens']) <= item_idx:
                st.session_state['usinas'][i]['itens'].append({})

            load_value(f'produto_{i}_{item_idx}')

            item = st.session_state['usinas'][i]['itens'][item_idx]

            # Definir as opções disponíveis para o selectbox e carregar o valor do session_state

            opcoes_produtos = ["Selecione", "SKID", "QGBT", "Transformador Isolado a Seco", "Inversor", "Logger","Módulo","Estrutura","Cabine","Cabo","Outros"]

            # Adicionar o valor inicial para manter a seleção ao mudar de página
            item_selecionado = st.selectbox(
                f"Selecione o tipo de produto para o Item {item_idx + 1} da Usina",
                opcoes_produtos,
                index=opcoes_produtos.index(st.session_state.get(f'produto_{i}_{item_idx}', "Selecione")),
                key=f"_produto_{i}_{item_idx}",
                on_change=store_value,
                args=[f'produto_{i}_{item_idx}']
            )

            # SKID
            if item_selecionado == "SKID":

                # Quantidade
                load_value(f'quantidade_{i}_{item_idx}')
                quantidade = st.number_input(
                    f"Quantidade para o item {item_idx + 1}:",
                    min_value=1,
                    step=1,
                    value=st.session_state.get(f'quantidade_{i}_{item_idx}', 1),
                    key=f"_quantidade_{i}_{item_idx}",
                    on_change=store_value,
                    args=[f'quantidade_{i}_{item_idx}']
                )

                # Potência
                potencias_disponiveis = df_solar[df_solar['produto'] == item_selecionado]['potencia'].unique()
                load_value(f'potencia_{i}_{item_idx}')
                potencia_default = st.session_state.get(f'potencia_{i}_{item_idx}', potencias_disponiveis[0] if potencias_disponiveis.size > 0 else None)

                potencia_escolhida=None
                if potencia_default not in potencias_disponiveis:
                    potencia_default = potencias_disponiveis[0] if potencias_disponiveis.size > 0 else None

                potencia_escolhida = st.selectbox(
                    "Qual a potência do item? (kVA)", 
                    potencias_disponiveis,
                    index=0 if potencia_escolhida is None else list(potencias_disponiveis).index(potencia_default),
                    key=f"_potencia_{i}_{item_idx}",
                    on_change=store_value,
                    args=[f'potencia_{i}_{item_idx}']
                )

                # Definir transformador_auxiliar_potencias e transformador_auxiliar_precos antes de usá-los
                transformador_auxiliar_potencias = ["Nenhum", "5 kVA", "10 kVA", "15 kVA", "20 kVA", "25 kVA", "30 kVA", "40 kVA"]
                transformador_auxiliar_precos = [0, 799, 1290, 1848, 2275, 2720, 3343, 5079]

                # Adicionar o transformador auxiliar ao SKID
                transformador_auxiliar_key = f'transformador_auxiliar_{i}_{item_idx}'
                load_value(transformador_auxiliar_key)

                # Valor padrão do transformador auxiliar
                transformador_auxiliar_default = st.session_state.get(transformador_auxiliar_key, "Nenhum")

                # Verificar se o valor salvo está na lista de opções, caso contrário, definir para "Nenhum"
                if transformador_auxiliar_default not in transformador_auxiliar_potencias:
                    transformador_auxiliar_default = "Nenhum"

                transformador_auxiliar_escolhido = st.selectbox(
                    "Selecione o Transformador Auxiliar (kVA)",
                    transformador_auxiliar_potencias,
                    index=transformador_auxiliar_potencias.index(transformador_auxiliar_default),
                    key=f"_transformador_auxiliar_{i}_{item_idx}",
                    on_change=store_value,
                    args=[transformador_auxiliar_key]
                )

                # Encontrar o preço correspondente ao transformador auxiliar escolhido
                if transformador_auxiliar_escolhido in transformador_auxiliar_potencias:
                    index_auxiliar = transformador_auxiliar_potencias.index(transformador_auxiliar_escolhido)
                    preco_transformador_auxiliar = transformador_auxiliar_precos[index_auxiliar]
                else:
                    index_auxiliar = 0
                    preco_transformador_auxiliar = transformador_auxiliar_precos[index_auxiliar]

                load_value(f'quantidade_transformador_auxiliar_{i}_{item_idx}')
                quantidade_transformador_auxiliar = st.number_input(
                    "Quantidade de Transformadores Auxiliares:",
                    min_value=1,
                    step=1,
                    value=st.session_state.get(f'quantidade_transformador_auxiliar_{i}_{item_idx}', 1),
                    key=f"_quantidade_transformador_auxiliar_{i}_{item_idx}",
                    on_change=store_value,
                    args=[f'quantidade_transformador_auxiliar_{i}_{item_idx}']
                )

                percentuais = st.session_state['percentuais']

                # Tensão MT
                tensoes_mt_disponiveis = df_solar[
                    (df_solar['produto'] == item_selecionado) & 
                    (df_solar['potencia'] == potencia_escolhida)
                ]['tensao_mt'].unique()

                load_value(f'tensao_mt_{i}_{item_idx}')
                tensao_mt_default = st.session_state.get(f'tensao_mt_{i}_{item_idx}', tensoes_mt_disponiveis[0] if tensoes_mt_disponiveis.size > 0 else None)
                
                tensao_mt_escolhida= None
                if tensao_mt_default not in tensoes_mt_disponiveis:
                    tensao_mt_default = tensoes_mt_disponiveis[0] if tensoes_mt_disponiveis.size > 0 else None

                tensao_mt_escolhida = st.selectbox(
                    "Qual é a tensão na média? (kV)", 
                    tensoes_mt_disponiveis,
                    index=0 if tensao_mt_escolhida is None else list(tensoes_mt_disponiveis).index(tensao_mt_default),
                    key=f"_tensao_mt_{i}_{item_idx}",
                    on_change=store_value,
                    args=[f'tensao_mt_{i}_{item_idx}']
                )

                # Configuração MT
                configuracao_mt_disponivel = df_solar[
                    (df_solar['produto'] == item_selecionado) & 
                    (df_solar['potencia'] == potencia_escolhida)
                ]['cubiculo_mt'].unique()

                load_value(f'configuracao_mt_{i}_{item_idx}')
                configuracao_mt_default = st.session_state.get(f'configuracao_mt_{i}_{item_idx}', configuracao_mt_disponivel[0] if configuracao_mt_disponivel.size > 0 else None)

                configuracao_mt_escolhida= None
                if configuracao_mt_default not in configuracao_mt_disponivel:
                    configuracao_mt_default = configuracao_mt_disponivel[0] if configuracao_mt_disponivel.size > 0 else None

                configuracao_mt_escolhida = st.selectbox(
                    "Escolha a configuração MT", 
                    configuracao_mt_disponivel,
                    index=0 if configuracao_mt_escolhida is None else list(configuracao_mt_disponivel).index(configuracao_mt_default),
                    key=f"_configuracao_mt_{i}_{item_idx}",
                    on_change=store_value,
                    args=[f'configuracao_mt_{i}_{item_idx}']
                )

                # Calcular o preço unitário do transformador auxiliar com a fórmula fornecida
                preco_transformador_auxiliar_unitario = preco_transformador_auxiliar / (1 - percentuais)

                if transformador_auxiliar_escolhido == "Nenhum" or None:
                    preco_transformador_auxiliar_total = 0.0
                else:
                    preco_transformador_auxiliar_total = preco_transformador_auxiliar_unitario * quantidade_transformador_auxiliar

                # Tensão BT
                load_value(f'tensao_bt_{i}_{item_idx}')
                tensao_bt_default = st.session_state.get(f'tensao_bt_{i}_{item_idx}', 800)
                tensao_bt_escolhida= 800
                tensao_bt_escolhida = st.selectbox(
                    "Qual a tensão na baixa? (V)", 
                    [800, 600],
                    index=0 if tensao_bt_escolhida is None else ([800, 600].index(tensao_bt_default) if tensao_bt_default in [800, 600] else 0),
                    key=f"_tensao_bt_{i}_{item_idx}",
                    on_change=store_value,
                    args=[f'tensao_bt_{i}_{item_idx}']
                )

                # Configuração BT
                load_value(f'configuracao_bt_{i}_{item_idx}')
                configuracao_bt_default = st.session_state.get(f'configuracao_bt_{i}_{item_idx}', df_solar[
                    (df_solar['produto'] == item_selecionado) & 
                    (df_solar['potencia'] == potencia_escolhida)
                ]['qgbt'].unique()[0] if df_solar[
                    (df_solar['produto'] == item_selecionado) & 
                    (df_solar['potencia'] == potencia_escolhida)
                ]['qgbt'].unique().size > 0 else None)

                configuracao_bt_disponivel = df_solar[
                    (df_solar['produto'] == item_selecionado) & 
                    (df_solar['potencia'] == potencia_escolhida)
                ]['qgbt'].unique()

                configuracao_bt_escolhida= None
                if configuracao_bt_default not in configuracao_bt_disponivel:
                    configuracao_bt_default = configuracao_bt_disponivel[0] if configuracao_bt_disponivel.size > 0 else None

                configuracao_bt_escolhida = st.selectbox(
                    "Escolha a configuração BT", 
                    configuracao_bt_disponivel,
                    index=0 if configuracao_bt_escolhida is None else list(configuracao_bt_disponivel).index(configuracao_bt_default),
                    key=f"_configuracao_bt_{i}_{item_idx}",
                    on_change=store_value,
                    args=[f'configuracao_bt_{i}_{item_idx}']
                )

                correntes_disponiveis = df_solar[
                    (df_solar['produto'] == item_selecionado) & 
                    (df_solar['potencia'] == potencia_escolhida)
                ]['corrente'].unique()

                # Definir o valor da corrente (pode ser o primeiro valor da lista)
                corrente_escolhida = correntes_disponiveis[0] if len(correntes_disponiveis) > 0 else None

                # Configuração de Automação
                automacao_selecionada = st.radio(
                    "Automação", 
                    options=["Não", "Sim"], 
                    key=f"automacao_{i}_{item_idx}"
                )

                st.write(percentuais)
                preco_base2 = obter_preco_solar(
                    df=df_solar, 
                    produto=item_selecionado, 
                    potencia=potencia_escolhida, 
                    tensao_mt=tensao_mt_escolhida, 
                    configuracao_mt=configuracao_mt_escolhida, 
                    configuracao_bt=configuracao_bt_escolhida, 
                    corrente=corrente_escolhida
                ) 
                preco_com_percentuais= preco_base2/(1-percentuais)
                preco_unitario_2 = int((preco_com_percentuais) * (1 - 0.12)) / \
                                (1 - (st.session_state['difal'] / 100) - (st.session_state['f_pobreza'] / 100) - (st.session_state['icms'] / 100) )
               

                # Transformador a Seco P/ SKID
                st.subheader("Configuração do Transformador a Seco")

                fator_k_opcoes = [1, 4, 6, 8, 13]

                # Defina um valor padrão para 'fator_k' para transformador a seco
                fator_k_default = st.session_state['usinas'][i]['itens'][item_idx].get('fator_k', fator_k_opcoes[0])

                # Verificar se fator_k_default está na lista fator_k_opcoes
                if fator_k_default not in fator_k_opcoes:
                    fator_k_default = 1

                # Carregar o valor do Fator K
                load_value(f'fator_k_{i}_{item_idx}')
                fator_k_escolhido = st.selectbox(
                    f"Selecione o Fator K para o item {item_idx + 1}:",
                    fator_k_opcoes,
                    index=fator_k_opcoes.index(fator_k_default),
                    key=f"_fator_k_{i}_{item_idx}",
                    on_change=store_value,
                    args=[f'fator_k_{i}_{item_idx}']
                )

                                # Carregar o valor do IP para transformador a seco
                ip_escolhido= "00"

                # Armazena o Fator K selecionado no session_state com a chave consistente 'fator_k'
                st.session_state['usinas'][i]['itens'][item_idx]['fator_k'] = fator_k_escolhido

                # Carregar o valor da descrição do transformador a seco
                load_value(f'descricao_transformador_{i}_{item_idx}')
                descricao_opcoes = df_media_tensao['descricao'].unique().tolist()
                descricao_escolhida = st.selectbox(
                    f"Selecione a descrição do transformador para o item {item_idx + 1}:",
                    descricao_opcoes,
                    key=f"_descricao_transformador_{i}_{item_idx}",
                    on_change=store_value,
                    args=[f'descricao_transformador_{i}_{item_idx}']
                )



                # Checagem para descrição
                if descricao_escolhida == "":
                    st.warning("Por favor, selecione uma descrição para continuar.")
                    st.session_state['usinas'][i]['itens'][item_idx]['preco_total_trafo'] = 0.0
                    st.session_state['usinas'][i]['itens'][item_idx]['preco_unitario_trafo'] = 0.0
                    continue

                id_item = df_media_tensao[df_media_tensao['descricao'] == descricao_escolhida]['id'].values[0]
                st.session_state['usinas'][i]['itens'][item_idx]['ID'] = id_item
                st.session_state['usinas'][i]['itens'][item_idx]['Descrição'] = descricao_escolhida

                detalhes_item = df_media_tensao[df_media_tensao['descricao'] == descricao_escolhida].iloc[0]
                st.session_state['usinas'][i]['itens'][item_idx]['Potência'] = detalhes_item['potencia']
                st.session_state['usinas'][i]['itens'][item_idx]['Perdas'] = detalhes_item['perdas']
                st.session_state['usinas'][i]['itens'][item_idx]['classe_tensao'] = detalhes_item['classe_tensao']

                valor_ip_baixo = detalhes_item['valor_ip_baixo']
                valor_ip_alto = detalhes_item['valor_ip_alto']
                p_caixa = detalhes_item['p_caixa']
                preco_base = detalhes_item['preco']
                p_trafo = detalhes_item['p_trafo']

                preco_base1 = preco_base / (1 - p_trafo - percentuais)

                opcoes_ip = ['00', '21', '23', '54']
                perdas = st.session_state['usinas'][i]['itens'][item_idx]['Perdas'] = detalhes_item['perdas']
                potencia_trafo = st.session_state['usinas'][i]['itens'][item_idx]['Potência']
                potencia_trafo = str(potencia_trafo).replace('.0', '')

                potencia_equivalente = potencia_trafo

            # Se o Fator K for maior que 5, calcular a potência equivalente
                if fator_k_escolhido > 5:
                    potencia_equivalente = potencia_trafo / (
                        (-0.000000391396 * fator_k_escolhido**6) +
                        (0.000044437349 * fator_k_escolhido**5) -
                        (0.001966117106 * fator_k_escolhido**4) +
                        (0.040938237195 * fator_k_escolhido**3) -
                        (0.345600795014 * fator_k_escolhido**2) -
                        (1.369407483908 * fator_k_escolhido) +
                        101.826204136368
                    ) / 100 * 10000  # Ajuste para multiplicar corretamente
                
                    potencias_disponiveis = sorted(df_media_tensao['potencia'].values)
                    potencia_equivalente = next((p for p in potencias_disponiveis if p >= potencia_equivalente), potencias_disponiveis[-1])

                    st.session_state['usinas'][i]['itens'][item_idx]['Potência Equivalente'] = potencia_equivalente
                    detalhes_item_equivalente = df_media_tensao[df_media_tensao['potencia'] == potencia_equivalente].iloc[0]
                    valor_ip_baixo = detalhes_item_equivalente['valor_ip_baixo']
                    valor_ip_alto = detalhes_item_equivalente['valor_ip_alto']
                    p_caixa = detalhes_item_equivalente['p_caixa']
                else:
                    # Usar os valores da potência original se o fator K for <= 5
                    valor_ip_baixo = detalhes_item['valor_ip_baixo']
                    valor_ip_alto = detalhes_item['valor_ip_alto']
                    p_caixa = detalhes_item['p_caixa']

                # Cálculo do adicional IP baseado no IP escolhido e os valores adequados (potência original ou equivalente)
                if ip_escolhido == '00':
                    adicional_ip = 0.0
                else:
                    adicional_ip = valor_ip_baixo / (1 - percentuais - p_caixa) if int(ip_escolhido) < 54 else valor_ip_alto / (1 - percentuais - p_caixa)

                classe_tensao = detalhes_item['classe_tensao']
                adicional_caixa_classe = 0
                if classe_tensao == "24 kV":
                    adicional_caixa_classe = p_caixa_24 * adicional_ip
                elif classe_tensao == "36 kV":
                    adicional_caixa_classe = p_caixa_36 * adicional_ip
                elif classe_tensao == "15 kV":
                    adicional_caixa_classe = 0

                adicional_k = 0
                if fator_k_escolhido in percentuais_k:
                    adicional_k = preco_base1 * percentuais_k[fator_k_escolhido]
                
                preco_unitario = int(((preco_base1 + adicional_ip + adicional_k + adicional_caixa_classe) * (1 - 0.12)) / \
                                (1 - (st.session_state['difal'] / 100) - (st.session_state['f_pobreza'] / 100) - (st.session_state['icms'] / 100)))
                
                preco_total = calcular_preco_total(preco_unitario, quantidade)
                st.session_state['usinas'][i]['itens'][item_idx]['Preço Total'] = preco_total

                preco_total_conjunto= preco_unitario_2+preco_unitario+preco_transformador_auxiliar_total

                            # Adicionar valor de automação ao preço, se selecionado
                if automacao_selecionada == "Sim":
                    preco_total_conjunto += 16934.41
                else:
                    preco_total_conjunto += 0.00



                st.session_state['usinas'][i]['itens'][item_idx]['preco_unitario'] = preco_unitario
                preco_total = calcular_preco_total(preco_unitario, quantidade)
                st.session_state['usinas'][i]['itens'][item_idx]['preco_total'] = preco_total            

                # Obter o valor do kva
                kva = obter_kva_qgbt(df_solar, item_selecionado, potencia_escolhida, configuracao_bt_escolhida)

                # Criar a descrição do item com o valor do kva
                descricao_item = ""
                descricao_item += f"{item_selecionado} {potencia_escolhida} kVA\n"
                descricao_item += f"- Skid Estruturado Em Aço para {potencia_escolhida} kVA;\n"
                descricao_item += f"- Transformador Isolado a Seco {potencia_escolhida} kVA {classe_tensao};\n"
                descricao_item += f"- Perdas = {perdas}; K={fator_k_escolhido}; IP={ip_escolhido};\n"
                descricao_item += f"- QGBT {tensao_bt_escolhida}V {corrente_escolhida} {kva}kA"

                if len(st.session_state['usinas'][i]['itens']) < num_itens:
                    st.session_state['usinas'][i]['itens'].append({
                        # Parâmetros do Produto
                        "produto": item_selecionado,
                        "potencia": potencia_escolhida,
                        "tensao_mt": tensao_mt_escolhida,
                        "tensao_bt": tensao_bt_escolhida,
                        "configuracao_mt": configuracao_mt_escolhida,
                        "configuracao_bt": configuracao_bt_escolhida,
                        "corrente": corrente_escolhida,
                        "descricao": descricao_item,
                        "valor_unitario": preco_total_conjunto,
                        
                        # Detalhes do Transformador Principal
                        "potencia_transformador": detalhes_item['potencia'],       # potência do transformador
                        "classe_tensao": detalhes_item['classe_tensao'],           # classe de tensão do transformador
                        "perdas": detalhes_item['perdas'],                         # perdas do transformador
                        "descricao_transformador": descricao_escolhida,            # descrição do transformador
                        "fator_k": fator_k_escolhido,                              # fator K
                        "ip": ip_escolhido,                                        # IP
                        "quantidade": quantidade,   
                        "ka": kva,                               # quantidade do transformador principal

                        # Preço d Transformador Principal
                        "preco_unitario_transformador": preco_base1,               # preço base considerando variáveis fiscais e classe de tensão
                        "valor_unitario": preco_total_conjunto,                          # preço unitário do item completo
                        "preco_total": preco_total,                                # preço total (preco_unitario * quantidade)
                        
                        # Valores do Transformador Auxiliar
                        "transformador_auxiliar_kva": transformador_auxiliar_escolhido,
                        "quantidade_transformador_auxiliar": quantidade_transformador_auxiliar,
                        "order":1,
                        "id": item_idx
                    })
                else:
                    st.session_state['usinas'][i]['itens'][item_idx] = {
                        # Parâmetros do Produto
                        "produto": item_selecionado,
                        "potencia": potencia_escolhida,
                        "tensao_mt": tensao_mt_escolhida,
                        "tensao_bt": tensao_bt_escolhida,
                        "configuracao_mt": configuracao_mt_escolhida,
                        "configuracao_bt": configuracao_bt_escolhida,
                        "corrente": corrente_escolhida,
                        "descricao": descricao_item,
                        "valor_unitario": preco_total_conjunto,
                        "ka": kva,      
                        # Detalhes do Transformador Principal
                        "potencia_transformador": detalhes_item['potencia'],       # potência do transformador
                        "classe_tensao": detalhes_item['classe_tensao'],           # classe de tensão do transformador
                        "perdas": detalhes_item['perdas'],                         # perdas do transformador
                        "descricao_transformador": descricao_escolhida,            # descrição do transformador
                        "fator_k": fator_k_escolhido,                              # fator K
                        "ip": ip_escolhido,                                        # IP
                        "quantidade": quantidade,                                  # quantidade do transformador principal

                        # Preço do Transformador Principal
                        "preco_BASE_transformador": preco_base1,               # preço base considerando variáveis fiscais e classe de tensão
                        "preco_unitario_TRAFO": preco_unitario,                          # preço unitário do item completo
                        "preco_total": preco_total, 
                        "valor_unitario": preco_total_conjunto,                                # preço total (preco_unitario * quantidade)
                        
                        # Valores do Transformador Auxiliar
                        "transformador_auxiliar_kva": transformador_auxiliar_escolhido,
                        "quantidade_transformador_auxiliar": quantidade_transformador_auxiliar,
                        "order":1,
                        "id": item_idx
                    }

               


            # QGBT
            elif item_selecionado == "QGBT":

                item['produto'] = item_selecionado

                # Quantidade
                load_value(f'quantidade_{i}_{item_idx}')
                quantidade = st.number_input(
                    f"Quantidade para o item {item_idx + 1}:",
                    min_value=1,
                    step=1,
                    value=st.session_state.get(f'quantidade_{i}_{item_idx}', 1),
                    key=f"_quantidade_{i}_{item_idx}",
                    on_change=store_value,
                    args=[f'quantidade_{i}_{item_idx}']
                )

                # Potência
                potencias_disponiveis = df_solar[df_solar['produto'] == item_selecionado]['potencia'].unique()
                load_value(f'potencia_{i}_{item_idx}')
                potencia_escolhida = st.selectbox(
                    "Qual a potência do item? (kVA)", 
                    potencias_disponiveis,
                    key=f"_potencia_{i}_{item_idx}",
                    on_change=store_value,
                    args=[f'potencia_{i}_{item_idx}']
                )
                item['produto']=item_selecionado
                item['potencia'] = potencia_escolhida


                percentuais = st.session_state['percentuais']

                # Tensao BT
                load_value(f'tensao_bt_{i}_{item_idx}')
                tensao_bt_escolhida = st.selectbox(
                    "Qual a tensão na baixa? (V)", 
                    [800, 600],
                    key=f"_tensao_bt_{i}_{item_idx}",
                    on_change=store_value,
                    args=[f'tensao_bt_{i}_{item_idx}']
                )

                # configuracao BT
                load_value(f'configuracao_bt_{i}_{item_idx}')
                configuracao_bt_escolhida = st.selectbox(
                    "Escolha a configuração BT", 
                    df_solar[
                        (df_solar['produto'] == item_selecionado) & 
                        (df_solar['potencia'] == potencia_escolhida)
                    ]['qgbt'].unique(),
                    key=f"_configuracao_bt_{i}_{item_idx}",
                    on_change=store_value,
                    args=[f'configuracao_bt_{i}_{item_idx}']
                )
                correntes_disponiveis = df_solar[
                    (df_solar['produto'] == item_selecionado) & 
                    (df_solar['potencia'] == potencia_escolhida)
                ]['corrente'].unique()

                # Definir o valor da corrente (pode ser o primeiro valor da lista)
                corrente_escolhida = correntes_disponiveis[0] if len(correntes_disponiveis) > 0 else None

                # Configuração de Automação
                automacao_selecionada = st.radio(
                    "Automação", 
                    options=["Não", "Sim"], 
                    key=f"automacao_{i}_{item_idx}"
                )

                tensao_mt_escolhida = 0
                configuracao_mt_escolhida = "NA"

                #Preço do QGBT
                preco_base2 = obter_preco_solar(
                df=df_solar, 
                produto=item_selecionado, 
                potencia=potencia_escolhida, 
                tensao_mt=tensao_mt_escolhida, 
                configuracao_mt=configuracao_mt_escolhida, 
                configuracao_bt=configuracao_bt_escolhida, 
                corrente=corrente_escolhida
            )
                
                preco_com_percentuais= preco_base2/(1-percentuais)
                preco_unitario_2 = int((preco_com_percentuais) * (1 - 0.12)) / \
                                (1 - (st.session_state['difal'] / 100) - (st.session_state['f_pobreza'] / 100) - (st.session_state['icms'] / 100) )
               

                if automacao_selecionada == "Sim":
                    preco_unitario_2 += 13874.41
                else: 0.00

                # Obter o valor do kva
                kva = obter_kva_qgbt(df_solar, item_selecionado, potencia_escolhida, configuracao_bt_escolhida)
                descricao_item= "QGBT " + str(tensao_bt_escolhida) + "V " + str(corrente_escolhida) + str(kva) + " kA" 


                if len(st.session_state['usinas'][i]['itens']) < num_itens:
                    st.session_state['usinas'][i]['itens'].append({
                        # Parâmetros do Produto
                        "produto": item_selecionado,
                        "potencia": potencia_escolhida,
                        "tensao_bt": tensao_bt_escolhida,
                        "configuracao_bt": configuracao_bt_escolhida,
                        "corrente": corrente_escolhida,
                        "descricao": descricao_item,
                        "valor_unitario": preco_unitario_2,
                        "descricao": descricao_item,
                        "order": 2,
                        "id": item_idx,
                        "quantidade": quantidade
                    })
                else:
                    st.session_state['usinas'][i]['itens'][item_idx] = {
                        # Parâmetros do Produto
                        "produto": item_selecionado,
                        "potencia": potencia_escolhida,
                        "tensao_bt": tensao_bt_escolhida,
                        "configuracao_mt": configuracao_mt_escolhida,
                        "corrente": corrente_escolhida,
                        "descricao": descricao_item,
                        "valor_unitario": preco_unitario_2,
                        "descricao": descricao_item,
                        "order": 2,
                        "id": item_idx,
                        "quantidade": quantidade
                    }
                                
            elif item_selecionado == "Transformador Isolado a Seco":

                # Quantidade
                load_value(f'quantidade_{i}_{item_idx}')
                quantidade = st.number_input(
                    f"Quantidade para o item {item_idx + 1}:",
                    min_value=1,
                    step=1,
                    value=st.session_state.get(f'quantidade_{i}_{item_idx}', 1),
                    key=f"_quantidade_{i}_{item_idx}",
                    on_change=store_value,
                    args=[f'quantidade_{i}_{item_idx}']
                )
                
                fator_k_opcoes = [1, 4, 6, 8, 13]
                # Defina um valor padrão para 'fator_k', garantindo que seja um valor válido
                fator_k_default = st.session_state['usinas'][i]['itens'][item_idx].get('fator_k', fator_k_opcoes[0])

                # Verifique se o valor está na lista; se não estiver, use o primeiro valor da lista
                if fator_k_default not in fator_k_opcoes:
                    fator_k_default = fator_k_opcoes[0]

                # Carregar o valor do Fator K
                load_value(f'fator_k_{i}_{item_idx}')
                fator_k_escolhido = st.selectbox(
                    f"Selecione o Fator K para o item {item_idx + 1}:",
                    fator_k_opcoes,
                    index=fator_k_opcoes.index(fator_k_default),
                    key=f"_fator_k_{i}_{item_idx}",
                    on_change=store_value,
                    args=[f'fator_k_{i}_{item_idx}']
                )
                # Armazena o Fator K selecionado no session_state com a chave consistente 'fator_k'
                st.session_state['usinas'][i]['itens'][item_idx]['fator_k'] = fator_k_escolhido
                ip_opcoes = ['00', '21', '23', '54']

                # Obtém o valor de IP do session_state, ou usa o primeiro valor da lista como padrão
                ip_default = st.session_state['usinas'][i]['itens'][item_idx].get('ip', ip_opcoes[0])

                # Verifique se o valor de 'ip_default' está em 'ip_opcoes'
                if ip_default not in ip_opcoes:
                    ip_default = ip_opcoes[0]

                # Agora, use 'ip_default' ao definir o índice no selectbox
                ip_escolhido = st.selectbox(
                    f"Selecione o IP para o item {item_idx + 1}:",
                    ip_opcoes,
                    index=ip_opcoes.index(ip_default),
                    key=f"_ip_{i}_{item_idx}",
                    on_change=store_value,
                    args=[f'ip_{i}_{item_idx}']
                )

                # Carregar o valor da descrição do transformador a seco
                load_value(f'descricao_transformador_{i}_{item_idx}')
                descricao_opcoes = df_media_tensao['descricao'].unique().tolist()
                descricao_escolhida = st.selectbox(
                    f"Selecione a descrição do transformador para o item {item_idx + 1}:",
                    descricao_opcoes,
                    key=f"_descricao_transformador_{i}_{item_idx}",
                    on_change=store_value,
                    args=[f'descricao_transformador_{i}_{item_idx}']
                )

                # Verificar se todos os campos obrigatórios estão preenchidos
                if quantidade is not None and quantidade > 0 and \
                ip_escolhido is not None and ip_escolhido != "" and \
                fator_k_escolhido is not None and fator_k_escolhido > 0 and \
                descricao_escolhida is not None and descricao_escolhida != "":
                    
                    id_item = df_media_tensao[df_media_tensao['descricao'] == descricao_escolhida]['id'].values[0]
                    st.session_state['usinas'][i]['itens'][item_idx]['ID'] = id_item
                    st.session_state['usinas'][i]['itens'][item_idx]['Descrição'] = descricao_escolhida
                    detalhes_item = df_media_tensao[df_media_tensao['descricao'] == descricao_escolhida].iloc[0]
                    st.session_state['usinas'][i]['itens'][item_idx]['Potência'] = detalhes_item['potencia']
                    st.session_state['usinas'][i]['itens'][item_idx]['Perdas'] = detalhes_item['perdas']
                    st.session_state['usinas'][i]['itens'][item_idx]['classe_tensao'] = detalhes_item['classe_tensao']
                    valor_ip_baixo = detalhes_item['valor_ip_baixo']
                    valor_ip_alto = detalhes_item['valor_ip_alto']
                    p_caixa = detalhes_item['p_caixa']
                    preco_base = detalhes_item['preco']
                    p_trafo = detalhes_item['p_trafo']
                    preco_base1 = preco_base / (1 - p_trafo - percentuais)
        
                    opcoes_ip = ['00', '21', '23', '54']
                    perdas = st.session_state['usinas'][i]['itens'][item_idx]['Perdas'] = detalhes_item['perdas']
                    potencia_trafo = st.session_state['usinas'][i]['itens'][item_idx]['Potência']
                    potencia_equivalente = potencia_trafo
                # Se o Fator K for maior que 5, calcular a potência equivalente
                    if fator_k_escolhido > 5:
                        potencia_equivalente = potencia_trafo / (
                            (-0.000000391396 * fator_k_escolhido**6) +
                            (0.000044437349 * fator_k_escolhido**5) -
                            (0.001966117106 * fator_k_escolhido**4) +
                            (0.040938237195 * fator_k_escolhido**3) -
                            (0.345600795014 * fator_k_escolhido**2) -
                            (1.369407483908 * fator_k_escolhido) +
                            101.826204136368
                        ) / 100 * 10000  # Ajuste para multiplicar corretamente
                    
                        potencias_disponiveis = sorted(df_media_tensao['potencia'].values)
                        potencia_equivalente = next((p for p in potencias_disponiveis if p >= potencia_equivalente), potencias_disponiveis[-1])
                        st.session_state['usinas'][i]['itens'][item_idx]['Potência Equivalente'] = potencia_equivalente
                        detalhes_item_equivalente = df_media_tensao[df_media_tensao['potencia'] == potencia_equivalente].iloc[0]
                        valor_ip_baixo = detalhes_item_equivalente['valor_ip_baixo']
                        valor_ip_alto = detalhes_item_equivalente['valor_ip_alto']
                        p_caixa = detalhes_item_equivalente['p_caixa']
                    else:
                        # Usar os valores da potência original se o fator K for <= 5
                        valor_ip_baixo = detalhes_item['valor_ip_baixo']
                        valor_ip_alto = detalhes_item['valor_ip_alto']
                        p_caixa = detalhes_item['p_caixa']
                    # Cálculo do adicional IP baseado no IP escolhido e os valores adequados (potência original ou equivalente)
                    if ip_escolhido == '00':
                        adicional_ip = 0.0
                    else:
                        adicional_ip = valor_ip_baixo / (1 - percentuais - p_caixa) if int(ip_escolhido) < 54 else valor_ip_alto / (1 - percentuais - p_caixa)
                    classe_tensao = detalhes_item['classe_tensao']
                    adicional_caixa_classe = 0
                    if classe_tensao == "24 kV":
                        adicional_caixa_classe = p_caixa_24 * adicional_ip
                    elif classe_tensao == "36 kV":
                        adicional_caixa_classe = p_caixa_36 * adicional_ip
                    elif classe_tensao == "15 kV":
                        adicional_caixa_classe = 0
                    adicional_k = 0
                    if fator_k_escolhido in percentuais_k:
                        adicional_k = preco_base1 * percentuais_k[fator_k_escolhido]
                    
                    preco_unitario = int(((preco_base1 + adicional_ip + adicional_k + adicional_caixa_classe) * (1 - 0.12)) / \
                                    (1 - (st.session_state['difal'] / 100) - (st.session_state['f_pobreza'] / 100) - (st.session_state['icms'] / 100)))
                    
                    preco_total = calcular_preco_total(preco_unitario, quantidade)
                    st.session_state['usinas'][i]['itens'][item_idx]['Preço Total'] = preco_total
                    # Exibir os resultados

                    preco_transformador_auxiliar_total = 0
                    # Adicionando o transformador a seco como item separado quando estiver junto ao QGBT
                    preco_total_conjunto= preco_unitario
                                # Adicionar valor de automação ao preço, se selecionado


                    st.header(f"Preço Total conjunto: R$ {preco_total_conjunto:,.2f}")
                    st.session_state['usinas'][i]['itens'][item_idx]['preco_unitario'] = preco_unitario
                    preco_total = calcular_preco_total(preco_unitario, quantidade)
                    st.session_state['usinas'][i]['itens'][item_idx]['preco_total'] = preco_total

                    if len(st.session_state['usinas'][i]['itens']) < num_itens:
                        st.session_state['usinas'][i]['itens'].append({
                            # Detalhes do Transformador Principal
                            "produto": item_selecionado,                                # nome do produto
                            "potencia_transformador": detalhes_item['potencia'],       # potência do transformador
                            "classe_tensao": detalhes_item['classe_tensao'],           # classe de tensão do transformador
                            "perdas": detalhes_item['perdas'],                         # perdas do transformador
                            "descricao": descricao_escolhida,            # descrição do transformador
                            "fator_k": fator_k_escolhido,                              # fator K
                            "ip": ip_escolhido,                                        # IP
                            "quantidade": quantidade,                                  # quantidade do transformador principal
                            # Preço do Transformador Principal
                            "preco_unitario_transformador": preco_base1,               # preço base considerando variáveis fiscais e classe de tensão
                            "valor_unitario": preco_unitario,                          # preço unitário do item completo
                            "preco_total": preco_total_conjunto,  
                            "order": 2,                           # preço total (preco_unitario * quantidade)
                            "id": item_idx
                        })
                    else:
                        st.session_state['usinas'][i]['itens'][item_idx] = {
                            # Detalhes do Transformador Principal
                            "produto": item_selecionado, 
                            "potencia_transformador": detalhes_item['potencia'],       # potência do transformador
                            "classe_tensao": detalhes_item['classe_tensao'],           # classe de tensão do transformador
                            "perdas": detalhes_item['perdas'],                         # perdas do transformador
                            "descricao": descricao_escolhida,            # descrição do transformador
                            "fator_k": fator_k_escolhido,                              # fator K
                            "ip": ip_escolhido,                                        # IP
                            "quantidade": quantidade,                                  # quantidade do transformador principal
                            # Preço do Transformador Principal
                            "preco_unitario_transformador": preco_base1,               # preço base considerando variáveis fiscais e classe de tensão
                            "valor_unitario": preco_unitario,                          # preço unitário do item completo
                            "preco_total": preco_total_conjunto,
                            "order": 2   ,
                            "id": item_idx                        # preço total (preco_unitario * quantidade)
                        
                        }
                else : "Preenchencha todos os campos obrigatórios"


            elif item_selecionado == "Inversor":
                # Usa idx para identificar cada Inversor
                j = item_idx
                kit_item= item_selecionado  # idx é o índice do item

                load_value(f'quantidade_{i}_{item_idx}')
                quantidade = st.number_input(
                    f"Quantidade para o item {item_idx + 1}:",
                    min_value=1,
                    step=1,
                    value=st.session_state.get(f'quantidade_{i}_{item_idx}', 1),
                    key=f"_quantidade_{i}_{item_idx}",
                    on_change=store_value,
                    args=[f'quantidade_{i}_{item_idx}']
                )

                load_value(f'fabricante_{j}')
                fabricante = st.selectbox(
                    f"Escolha o fabricante do {kit_item} ({j + 1})", 
                    list(itens_kit[kit_item].keys()), 
                    key=f"_fabricante_{j}", 
                    on_change=store_value, 
                    args=[f'fabricante_{j}']
                )

                load_value(f'modelo_{j}')
                modelo_escolhido = st.selectbox(
                    f"Escolha o modelo do {kit_item} ({j + 1})", 
                    list(itens_kit[kit_item][fabricante].keys()), 
                    key=f"_modelo_{j}", 
                    on_change=store_value, 
                    args=[f'modelo_{j}']
                )

                # Define um valor padrão para o fator de importação
                fator_importacao_default = itens_kit[kit_item][fabricante][modelo_escolhido].get('fator_importacao', 1.0)
                load_value(f'fator_importacao_{j}')
                fator_importacao_input = st.number_input(
                    f"Fator de Importação para {item_selecionado} {i + 1}",
                    min_value=0.0,
                    step=0.01,
                    value=fator_importacao_default,
                    key=f"_fator_importacao_{j}",
                    on_change=store_value,
                    args=[f'fator_importacao_{j}']
                )

                valor_modelo = itens_kit[kit_item][fabricante][modelo_escolhido]["valor"]
                valor_unitario = quantidade * valor_modelo * fator_importacao_input * st.session_state['dolar']


                # Carregar o valor modificado se já existir no session_state
                load_value(f'valor_adicional_{kit_item}_{i}_{item_idx}')
                # Renderizar o widget com o valor carregado
                valor_modificado = st.number_input(
                    f"Valor adicional para {modelo_escolhido} ({item_idx + 1})",
                    value=st.session_state.get(f'valor_adicional_{kit_item}_{i}_{item_idx}', 0.00),
                    step=0.01,  # Incremento do valor
                    key=f"_valor_adicional_{kit_item}_{i}_{item_idx}",  
                    on_change=store_value,  # Chama a função store_value quando o valor é alterado
                    args=[f'valor_adicional_{kit_item}_{i}_{item_idx}']  # Passa a chave do session_state
                )

                valor_final= valor_unitario+valor_modificado

                # Configuração do inversor
                if len(st.session_state['usinas'][i]['itens']) < num_itens:
                    st.session_state['usinas'][i]['itens'].append({
                        # Parâmetros do Inversor
                        "produto": "Inversor",  # Nome do item
                        "modelo": modelo_escolhido,
                        "fabricante": fabricante,
                        "quantidade": quantidade,
                        "fator_importacao": fator_importacao_input,
                        "valor_unitario": valor_final,
                        "descricao": f"{item_selecionado} - {fabricante} - {modelo_escolhido}",
                        "order": 16,
                        "id": item_idx
                    })
                else:
                    # Atualiza o item existente com base no índice
                    st.session_state['usinas'][i]['itens'][item_idx] = {
                        # Parâmetros do Inversor
                        "produto": "Inversor",  # Nome do item
                        "modelo": modelo_escolhido,
                        "fabricante": fabricante,
                        "quantidade": quantidade,
                        "fator_importacao": fator_importacao_input,
                        "valor_unitario": valor_final,
                        "descricao": f"{item_selecionado} - {fabricante} - {modelo_escolhido}",
                        "order": 16,
                        "id": item_idx
                    }

            # Configuração para Logger
            elif item_selecionado == "Logger":
                j = item_idx
                kit_item= item_selecionado  

                load_value(f'quantidade_{i}_{item_idx}')
                quantidade = st.number_input(
                    f"Quantidade para o item {item_idx + 1}:",
                    min_value=1,
                    step=1,
                    value=st.session_state.get(f'quantidade_{i}_{item_idx}', 1),
                    key=f"_quantidade_{i}_{item_idx}",
                    on_change=store_value,
                    args=[f'quantidade_{i}_{item_idx}']
                )

                load_value(f'fabricante_{j}_{item_idx}')
                fabricante = st.selectbox(
                    f"Escolha o fabricante do {kit_item} ({j + 1})", 
                    list(itens_kit[kit_item].keys()), 
                    key=f"_fabricante_{j}_item_idx", 
                    on_change=store_value, 
                    args=[f'fabricante_{j}_item_idx']
                )

                load_value(f'modelo_{j}_item_idx')
                modelo_escolhido = st.selectbox(
                    f"Escolha o modelo do {kit_item} ({j + 1})", 
                    list(itens_kit[kit_item][fabricante].keys()), 
                    key=f"_modelo_{j}_item_idx", 
                    on_change=store_value, 
                    args=[f'modelo_{j}_item_idx']
                )

                # Define um valor padrão para o fator de importação
                fator_importacao_default = itens_kit[kit_item][fabricante][modelo_escolhido].get('fator_importacao', 1.0)
                load_value(f'fator_importacao_{j}_item_idx')
                fator_importacao_input = st.number_input(
                    f"Fator de Importação para {item_selecionado} {i + 1}",
                    min_value=0.0,
                    step=0.01,
                    value=fator_importacao_default,
                    key=f"_fator_importacao_{j}_item_idx",
                    on_change=store_value,
                    args=[f'fator_importacao_{j}_item_idx']
                )

                valor_modelo = itens_kit[kit_item][fabricante][modelo_escolhido]["valor"]
                valor_unitario = quantidade * valor_modelo * fator_importacao_input * st.session_state['dolar']

                # Carregar o valor modificado se já existir no session_state
                load_value(f'valor_adicional_{kit_item}_{i}_{item_idx}')
                # Renderizar o widget com o valor carregado
                valor_modificado = st.number_input(
                    f"Valor adicional para {modelo_escolhido} ({item_idx + 1})",
                    value=st.session_state.get(f'valor_adicional_{kit_item}_{i}_{item_idx}', 0.00),
                    step=0.01,  # Incremento do valor
                    key=f"_valor_adicional_{kit_item}_{i}_{item_idx}",  
                    on_change=store_value,  # Chama a função store_value quando o valor é alterado
                    args=[f'valor_adicional_{kit_item}_{i}_{item_idx}']  # Passa a chave do session_state
                )

                valor_final= valor_unitario +valor_modificado

                # Configuração do inversor
                if len(st.session_state['usinas'][i]['itens']) < num_itens:
                    st.session_state['usinas'][i]['itens'].append({
                        # Parâmetros do Inversor
                        "produto": "Logger",  # Nome do item
                        "modelo": modelo_escolhido,
                        "fabricante": fabricante,
                        "quantidade": quantidade,
                        "fator_importacao": fator_importacao_input,
                        "valor_unitario": valor_final,
                        "descricao": f"{item_selecionado} - {fabricante} - {modelo_escolhido}",
                        "id": item_idx
                    })
                else:
                    # Atualiza o item existente com base no índice
                    st.session_state['usinas'][i]['itens'][item_idx] = {
                        # Parâmetros do Inversor
                        "produto": "Logger",  # Nome do item
                        "modelo": modelo_escolhido,
                        "fabricante": fabricante,
                        "quantidade": quantidade,
                        "fator_importacao": fator_importacao_input,
                        "valor_unitario": valor_final,
                        "descricao": f"{item_selecionado} - {fabricante} - {modelo_escolhido}" ,
                        "id": item_idx
                    }

            # Configuração para Módulo
            elif item_selecionado == "Módulo":
                j = item_idx
                kit_item= item_selecionado

                fabricante=list(itens_kit["Módulo"].keys())[0]


                load_value(f'modelo_{j}')
                modelo_escolhido = st.selectbox(
                    f"Escolha o modelo do {kit_item} ({j + 1})", 
                    list(itens_kit[kit_item][fabricante].keys()), 
                    key=f"_modelo_{j}", 
                    on_change=store_value, 
                    args=[f'modelo_{j}']
                )

                load_value(f'quantidade_{i}_{item_idx}')
                quantidade = st.number_input(
                    f"Quantidade para o item {item_idx + 1}:",
                    min_value=1,
                    step=1,
                    value=st.session_state.get(f'quantidade_{i}_{item_idx}', 1),
                    key=f"_quantidade_{i}_{item_idx}",
                    on_change=store_value,
                    args=[f'quantidade_{i}_{item_idx}']
                )

                load_value(f'tipo_{j}')
                tipo_escolhido = st.text_input(
                    f"Escolha o tipo do {kit_item} ({j + 1})", 
                    key=f"_tipo_{j}", 
                    on_change=store_value, 
                    args=[f'tipo_{j}']
                )

                fator_importacao= 1.3598

                valor_wp = itens_kit[kit_item][fabricante][modelo_escolhido]["valor"]

                valor_unitario= float(fator_importacao)*float(valor_wp)*float(quantidade)*float(st.session_state['dolar'])*int(modelo_escolhido)

                pot_wp_unitaria= int(modelo_escolhido)*quantidade

                # Carregar o valor modificado se já existir no session_state
                load_value(f'valor_adicional_{kit_item}_{i}_{item_idx}')
                # Renderizar o widget com o valor carregado
                valor_modificado = st.number_input(
                    f"Valor adicional para {modelo_escolhido} ({item_idx + 1})",
                    value=st.session_state.get(f'valor_adicional_{kit_item}_{i}_{item_idx}', 0.00),
                    step=0.01,  # Incremento do valor
                    key=f"_valor_adicional_{kit_item}_{i}_{item_idx}",  
                    on_change=store_value,  # Chama a função store_value quando o valor é alterado
                    args=[f'valor_adicional_{kit_item}_{i}_{item_idx}']  # Passa a chave do session_state
                )

                valor_final= valor_unitario +valor_modificado

                if len(st.session_state['usinas'][i]['itens']) < num_itens:
                    st.session_state['usinas'][i]['itens'].append({
                        # Parâmetros do Inversor
                        "produto": "Módulo",  # Nome do item
                        "modelo": modelo_escolhido,
                        "fabricante": fabricante,
                        "quantidade": quantidade,
                        "fator_importacao": fator_importacao,
                        "valor_unitario": valor_final,
                        "pot_wp": pot_wp_unitaria,
                        "descricao": f"{item_selecionado} - Tier 1 - {modelo_escolhido} kVA - {tipo_escolhido}",
                        "order": 14,
                        "id": item_idx
                    })
                else:
                    # Atualiza o item existente com base no índice
                    st.session_state['usinas'][i]['itens'][item_idx] = {
                        # Parâmetros do Inversor
                        "produto": "Módulo",  # Nome do item
                        "modelo": modelo_escolhido,
                        "fabricante": fabricante,
                        "quantidade": quantidade,
                        "fator_importacao": fator_importacao,
                        "valor_unitario": valor_final,
                        "pot_wp": pot_wp_unitaria,
                        "descricao": f"{item_selecionado} - Tier 1 - {modelo_escolhido} kVA - {tipo_escolhido}",
                        "order": 14,
                        "id": item_idx
                    }


            # Configuração para Estrutura
            elif item_selecionado == "Estrutura":
                j = item_idx
                kit_item= item_selecionado  

                load_value(f'fabricante_{kit_item}_{i}_{j}')
                fabricante = st.selectbox(
                        f"Escolha o fabricante do {kit_item} ({j + 1})", 
                        list(itens_kit[kit_item].keys()), 
                        key=f"_fabricante_{kit_item}_{i}_{j}", 
                        on_change=store_value, 
                        args=[f'fabricante_{kit_item}_{i}_{j}']
                    )
                

                load_value(f'modelo_{j}')
                modelo_escolhido = st.selectbox(
                    f"Escolha o modelo do {kit_item} ({j + 1})", 
                    list(itens_kit[kit_item][fabricante].keys()), 
                    key=f"_modelo_{j}", 
                    on_change=store_value, 
                    args=[f'modelo_{j}']
                )


                                # Verifica o total de pot_wp da usina
                total_pot_wp = sum(item['pot_wp'] for item in st.session_state['usinas'][i]['itens'] if 'pot_wp' in item)

                # Se o total de pot_wp for 0, solicite ao usuário o valor
                if total_pot_wp == 0:
                    load_value(f'valor_wp_{kit_item}_{i}_{j}')
                    valor_wp = st.number_input(
                        f"Qual a o Wp da Usina? ",
                        min_value=0.0,
                        step=0.01,
                        key=f"_valor_wp_{kit_item}_{i}_{j}",
                        on_change=store_value,
                        args=[f'valor_wp_{kit_item}_{i}_{j}']
                    )
                else:
                    # Se pot_wp for maior que 0, utilize o valor total
                    valor_wp = total_pot_wp

                load_value(f'quantidade_{i}_{item_idx}')
                quantidade = st.number_input(
                    f"Quantidade para o item {item_idx + 1}:",
                    min_value=1,
                    step=1,
                    value=st.session_state.get(f'quantidade_{i}_{item_idx}', 1),
                    key=f"_quantidade_{i}_{item_idx}",
                    on_change=store_value,
                    args=[f'quantidade_{i}_{item_idx}']
                )

                valor_estrutura = itens_kit[kit_item][fabricante][modelo_escolhido]["valor"]

                # Calculo do valor_unitario
                valor_unitario = quantidade * valor_estrutura * valor_wp            

                valor_estrutrua = itens_kit[kit_item][fabricante][modelo_escolhido]["valor"]

                valor_unitario= quantidade* valor_estrutrua * valor_wp

                # Carregar o valor modificado se já existir no session_state
                load_value(f'valor_adicional_{kit_item}_{i}_{item_idx}')
                # Renderizar o widget com o valor carregado
                valor_modificado = st.number_input(
                    f"Valor adicional para {modelo_escolhido} ({item_idx + 1})",
                    value=st.session_state.get(f'valor_adicional_{kit_item}_{i}_{item_idx}', 0.00),
                    step=0.01,  # Incremento do valor
                    key=f"_valor_adicional_{kit_item}_{i}_{item_idx}",  
                    on_change=store_value,  # Chama a função store_value quando o valor é alterado
                    args=[f'valor_adicional_{kit_item}_{i}_{item_idx}']  # Passa a chave do session_state
                )

                valor_final= valor_unitario +valor_modificado

                if len(st.session_state['usinas'][i]['itens']) < num_itens:
                    st.session_state['usinas'][i]['itens'].append({
                        # Parâmetros do Inversor
                        "produto": "Estrutura",  # Nome do item
                        "modelo": modelo_escolhido,
                        "fabricante": fabricante,
                        "quantidade": quantidade,
                        "valor_unitario": valor_final,
                        "descricao": f"{item_selecionado} - {fabricante} - {modelo_escolhido}",
                        "order": 5,
                        "id": item_idx
                    })
                else:
                    # Atualiza o item existente com base no índice
                    st.session_state['usinas'][i]['itens'][item_idx] = {
                        # Parâmetros do Inversor
                        "produto": "Estrutura",  # Nome do item
                        "modelo": modelo_escolhido,
                        "fabricante": fabricante,
                        "quantidade": quantidade,
                        "valor_unitario": valor_final,
                        "descricao": f"{item_selecionado} - {fabricante} - {modelo_escolhido}",
                        "order": 15,
                        "id": item_idx
                    }
                            
            # Configuração para Cabos
            elif item_selecionado == "Cabo":
                j = item_idx
                kit_item = item_selecionado

                load_value(f'fabricante_{kit_item}_{i}_{j}')
                fabricante = st.selectbox(
                    f"Defina o segmento do {kit_item} ({j + 1})", 
                    list(itens_kit[kit_item].keys()), 
                    key=f"_fabricante_{kit_item}_{i}_{j}", 
                    on_change=store_value, 
                    args=[f'fabricante_{kit_item}_{i}_{j}']
                )

                if fabricante:
                    load_value(f'modelo_{j}')
                    modelo_escolhido = st.selectbox(
                        f"Escolha o modelo do {kit_item} ({j + 1})", 
                        list(itens_kit[kit_item][fabricante].keys()), 
                        key=f"_modelo_{j}", 
                        on_change=store_value, 
                        args=[f'modelo_{j}']
                    )

                    if modelo_escolhido:
                        load_value(f'quantidade_{i}_{item_idx}')
                        quantidade = st.number_input(
                            f"Quantidade para o item {item_idx + 1}:",
                            min_value=1,
                            step=1,
                            value=st.session_state.get(f'quantidade_{i}_{item_idx}', 1),
                            key=f"_quantidade_{i}_{item_idx}",
                            on_change=store_value,
                            args=[f'quantidade_{i}_{item_idx}']
                        )

                        load_value(f'metro_{i}_{item_idx}')
                        metros = st.number_input(
                            f"Qual a metragem para o item {item_idx + 1}?",
                            min_value=1,
                            step=1,
                            value=st.session_state.get(f'metro_{i}_{item_idx}', 1),
                            key=f"_metro_{i}_{item_idx}",
                            on_change=store_value,
                            args=[f'metro_{i}_{item_idx}']
                        )

                        # Verificar se quantidade e metros estão preenchidos
                        if quantidade is not None and metros is not None:
                            # Calcular valor_base
                            valor_metro_cabo = itens_kit[kit_item][fabricante][modelo_escolhido]["valor"]
                            valor_base = valor_metro_cabo * metros * quantidade

                            # Carregar o valor modificado se já existir no session_state
                            load_value(f'valor_modificado_{kit_item}_{i}_{item_idx}')

                            # Verificar se o valor_base mudou e atualizar o valor_unitario no session_state
                            if 'valor_modificado_{kit_item}_{i}_{item_idx}' in st.session_state:
                                if st.session_state[f'valor_modificado_{kit_item}_{i}_{item_idx}'] != valor_base:
                                    st.session_state[f'valor_modificado_{kit_item}_{i}_{item_idx}'] = valor_base
                            else:
                                st.session_state[f'valor_modificado_{kit_item}_{i}_{item_idx}'] = valor_base

                            # Renderizar o number_input para valor_unitario
                            valor_unitario = st.number_input(
                                f"Para modificar o valor final do {modelo_escolhido} ({item_idx + 1}), mude abaixo: ",
                                value=st.session_state[f'valor_modificado_{kit_item}_{i}_{item_idx}'],  # Valor inicial será o total calculado ou o que estiver no session_state
                                min_value=0.0,  # Valor mínimo permitido
                                step=10.00,  # Incremento do valor
                                key=f"valor_modificado_{kit_item}_{i}_{item_idx}",  
                                on_change=store_value,  # Chama a função store_value quando o valor é alterado
                                args=[f'valor_modificado_{kit_item}_{i}_{item_idx}']  # Passa a chave do session_state
                            )

                            if len(st.session_state['usinas'][i]['itens']) < num_itens:
                                st.session_state['usinas'][i]['itens'].append({
                                    # Parâmetros do Cabo
                                    "produto": "Cabo",  # Nome do item
                                    "modelo": modelo_escolhido,
                                    "fabricante": fabricante,
                                    "quantidade": quantidade,
                                    "metros": metros,
                                    "valor_unitario": valor_unitario,
                                    "descricao": f"{item_selecionado} - {fabricante} - {modelo_escolhido}",
                                    "order": 18,
                                    "id": item_idx
                                })
                            else:
                                # Atualiza o item existente com base no índice
                                st.session_state['usinas'][i]['itens'][item_idx] = {
                                    # Parâmetros do Cabo
                                    "produto": "Cabo",  # Nome do item
                                    "modelo": modelo_escolhido,
                                    "fabricante": fabricante,
                                    "quantidade": quantidade,
                                    "metros": metros,
                                    "valor_unitario": valor_unitario,
                                    "descricao": f"{item_selecionado} - {fabricante} - {modelo_escolhido}",
                                    "order": 18,
                                    "id": item_idx
                                }
                        else:
                            st.warning("Por favor, preencha os campos de quantidade e metros.")
                    else:
                        st.warning("Por favor, selecione um modelo.")
                else:
                    st.warning("Por favor, selecione o segmento do cabo.")



            elif item_selecionado == "Cabine":
                j = item_idx
                kit_item = item_selecionado  # idx é o índice do item

                # Carregar ou definir a quantidade
                quantidade = st.number_input(
                    f"Quantidade para o item {item_idx + 1}:",
                    min_value=1,
                    step=1,
                    value=st.session_state.get(f'quantidade_{i}_{item_idx}', 1),
                    key=f"quantidade_{i}_{item_idx}",
                    on_change=store_value,
                    args=[f'quantidade_{i}_{item_idx}']
                )

                # Carregar opções de fabricantes
                fabricante_opcoes = list(itens_kit[kit_item].keys()) + ["Outros"]

                # Carregar o valor do session_state se já existir
                load_value(f"fabricante_{i}_{item_idx}")

                load_value(f'fabricante_{j}')
                fabricante = st.selectbox(
                    f"Escolha o fabricante do {kit_item} ({j + 1})", 
                    list(itens_kit[kit_item].keys()), 
                    key=f"_fabricante_{j}", 
                    on_change=store_value, 
                    args=[f'fabricante_{j}']
                )

                load_value(f'modelo_{j}')
                modelo_escolhido = st.selectbox(
                    f"Escolha o modelo do {kit_item} ({j + 1})", 
                    list(itens_kit[kit_item][fabricante].keys()), 
                    key=f"_modelo_{j}", 
                    on_change=store_value, 
                    args=[f'modelo_{j}']
                )

                valor_cabine = itens_kit[kit_item][fabricante][modelo_escolhido]["valor"]

                # Calcular valor final
                valor_final = valor_cabine * quantidade

                # Adicionar o item ao session_state
                if len(st.session_state['usinas'][i]['itens']) < num_itens:
                    st.session_state['usinas'][i]['itens'].append({
                        "produto": item_selecionado,
                        "fabricante": fabricante ,
                        "modelo":  modelo_escolhido,
                        "quantidade": quantidade,
                        "valor_unitario": valor_final,
                        "valor_total": valor_final,
                        "descricao": f"{item_selecionado} - {fabricante} - {modelo_escolhido}",
                        "order": 17,
                        "id": item_idx
                    })
                else:
                    st.session_state['usinas'][i]['itens'][item_idx] = {
                        "produto": item_selecionado,
                        "fabricante": fabricante,
                        "modelo":  modelo_escolhido,
                        "quantidade": quantidade,
                        "valor_unitario": valor_final,
                        "valor_total": valor_final,
                        "descricao": f"{item_selecionado} - {fabricante} - {modelo_escolhido}",
                        "order": 17,
                        "id": item_idx
                    }
                        # Configuração para Módulo
            elif item_selecionado == "Outros":
                j = item_idx
                kit_item= item_selecionado

                fabricante=None
                item_selecionado_outros=None
                modelo_escolhido=None


                load_value(f'quantidade_{i}_{item_idx}')
                quantidade = st.number_input(
                    f"Quantidade para o item {item_idx + 1}:",
                    min_value=1,
                    step=1,
                    value=st.session_state.get(f'quantidade_{i}_{item_idx}', 1),
                    key=f"_quantidade_{i}_{item_idx}",
                    on_change=store_value,
                    args=[f'quantidade_{i}_{item_idx}']
                )

                opcoes_produtos_s_outros = ["Selecione", "SKID", "QGBT", "Transformador Isolado a Seco", "Inversor", "Logger","Módulo","Estrutura","Cabine","Cabo"]

                # Adicionar o valor inicial para manter a seleção ao mudar de página
                item_selecionado_outros = st.selectbox(
                    f"Selecione o tipo de produto para o Item {item_idx + 1} da Usina",
                    opcoes_produtos_s_outros,
                    index=opcoes_produtos.index(st.session_state.get(f'produto_outros_{j}', "Selecione")),
                    key=f"_produto_outros_{j}",
                    on_change=store_value,
                    args=[f'produto_outros_{j}']
                )
  
                load_value(f'fabricante_{j}')
                fabricante = st.text_input(
                    f"Escolha do produto {kit_item} ({j + 1})", 
                    key=f"_fabricante_{j}", 
                    on_change=store_value, 
                    args=[f'fabricante_{j}']
                )

                load_value(f'modelo_{j}')
                modelo_escolhido = st.text_input(
                    f"Escolha o modelo do {kit_item} ({j + 1})", 
                    key=f"_modelo_{j}", 
                    on_change=store_value, 
                    args=[f'modelo_{j}']
                )
                # Carregar o valor modificado se já existir no session_state
                load_value(f'valor_adicional_{kit_item}_{i}_{item_idx}')
                # Renderizar o widget com o valor carregado
                valor_modificado = st.number_input(
                    f"Valor:",
                    value=st.session_state.get(f'valor_adicional_{kit_item}_{i}_{item_idx}', 0.00),
                    step=0.01,  # Incremento do valor
                    key=f"_valor_adicional_{kit_item}_{i}_{item_idx}",  
                    on_change=store_value,  # Chama a função store_value quando o valor é alterado
                    args=[f'valor_adicional_{kit_item}_{i}_{item_idx}']  # Passa a chave do session_state
                )

                valor_final= valor_modificado

                if len(st.session_state['usinas'][i]['itens']) < num_itens:
                    st.session_state['usinas'][i]['itens'].append({
                        # Parâmetros do Inversor
                        "produto":item_selecionado_outros,  # Nome do item
                        "modelo": modelo_escolhido,
                        "fabricante": fabricante,
                        "quantidade": quantidade,
                        "valor_unitario": valor_final,
                        "order": 14,
                        "id": item_idx,
                        "descricao": f"{item_selecionado_outros} - {fabricante} - {modelo_escolhido}" ,
                        "order":1000                     
                    })
                else:
                    # Atualiza o item existente com base no índice
                    st.session_state['usinas'][i]['itens'][item_idx] = {
                        # Parâmetros do Inversor
                        "produto":item_selecionado_outros,  # Nome do item
                        "modelo": modelo_escolhido,
                        "fabricante": fabricante,
                        "quantidade": quantidade,
                        "valor_unitario": valor_final,
                        "order": 14,
                        "id": item_idx,
                        "descricao": f"{item_selecionado_outros} - {fabricante} - {modelo_escolhido}",
                        "order":1000
                    }

             # Linha separadora entre itens
            st.markdown("---")

# Função para excluir item
def excluir_item(usina_idx, item_idx):
    # Remove o item do session_state
    st.session_state['usinas'][usina_idx]['itens'].pop(item_idx)
    # Atualiza o número de itens
    st.session_state['num_itens'] = len(st.session_state['usinas'][usina_idx]['itens'])
    st.rerun()


for usina_idx, usina in enumerate(st.session_state['usinas']):
    st.subheader(f"Usina {usina_idx + 1}")
    
    # Criar uma lista de dicionários com os dados dos itens
    itens_data = [
        {
            "Descrição": item.get("descricao", ""),
            "Quantidade": int(item.get("quantidade", 0)),  # Garantir que a quantidade seja um inteiro
            "Valor": "{:,.2f}".format(item.get("valor_unitario", 0.0)).replace(",", "X").replace(".", ",").replace("X", "."),  # Formatação personalizada
            "Order": item.get("order", 0),
            "Index": item_idx  # Adiciona o índice do item para referência
        }
        for item_idx, item in enumerate(usina['itens'])
    ]
    
    # Criar um DataFrame a partir dos dados dos itens
    df_itens = pd.DataFrame(itens_data)
    
    # Calcular o total dos valores
    total_preco_total = sum(item.get("valor_unitario", 0.0) for item in usina['itens'])
    
    # Adicionar uma linha de total ao DataFrame
    total_row = pd.DataFrame([{
        "Descrição": "Total",
        "Quantidade": "",
        "Valor": "{:,.2f}".format(total_preco_total).replace(",", "X").replace(".", ",").replace("X", "."),  # Formatação personalizada
        "Order": float('inf'),  # Garantir que a linha de total fique no final
        "Index": float('inf')
    }])
    
    df_itens = pd.concat([df_itens, total_row], ignore_index=True)
    
    # Ordenar o DataFrame pelo campo 'Order'
    df_itens = df_itens.sort_values(by="Order")

    st.session_state['resumo_df'] = df_itens
    
    # Exibir a tabela sem a coluna 'Order' e 'Index'
    st.table(df_itens.drop(columns=["Order", "Index"]))

# Classificar a proposta como Estação Fotovoltaica ou Subestação Unitária
    classificar_proposta_estacao_subestacao()

    st.subheader("Valor total da usina: {}".format("{:,.2f}".format(total_preco_total).replace(",", "X").replace(".", ",").replace("X", ".")))
    st.subheader("Escopo de fornecimento: {}".format(st.session_state['classificacao_estacao_subestacao']))
    # Linha separadora entre usinas
    st.markdown("---")

