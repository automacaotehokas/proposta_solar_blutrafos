import streamlit as st
from PIL import Image

# Função para normalizar o nome do produto
def normalizar_produto(produto):
    if produto in ["QGBT", "Transformador Isolado a Seco"]:
        return "QGBT/Transformador Isolado a Seco"
    return produto

# Função para carregar valores do session_state
def load_value(key):
    if key in st.session_state:
        return st.session_state[key]
    return ''

# Função para armazenar valores no session_state
def store_value(key, value):
    st.session_state[key] = value

# Função para configurar eventos de pagamento
def configurar_eventos_pagamento(produto):
    eventos_pagamento = {"produto": produto, "eventos": []}
    lista_eventos = ["Pedido", "Faturamento", "Contraembarque", "Aprovação dos Desenhos", "TAF", "Entrega do Equipamento"]

    # Eventos predefinidos
    eventos_predefinidos = [
        {"percentual": 25, "dias": 20, "evento": "Aprovação dos Desenhos"},
        {"percentual": 25, "dias": 30, "evento": "Aprovação dos Desenhos"},
        {"percentual": 25, "dias": 60, "evento": "Aprovação dos Desenhos"},
        {"percentual": 25, "dias": 0, "evento": "Entrega do Equipamento"}
    ]
    
    # Inicializa o session_state para eventos e recarregar, se necessário
    if f'eventos_{produto}' not in st.session_state:
        st.session_state[f'eventos_{produto}'] = eventos_predefinidos
    if 'recarregar' not in st.session_state:
        st.session_state['recarregar'] = False

    def atualizar_evento(produto, i, key, value):
        st.session_state[f'eventos_{produto}'][i][key] = value

    with st.expander(f"Configurar eventos de pagamento para {produto}"):
        eventos_atualizados = []
        for i, evento in enumerate(st.session_state[f'eventos_{produto}']):
            st.subheader(f"Evento {i+1} para {produto}")
            percentual = st.number_input(
                f"Percentual do evento {i+1} para {produto}:",
                min_value=0.0, max_value=100.0, step=1.0,
                value=float(evento["percentual"]),
                key=f"percentual_{produto}_{i}",
                on_change=atualizar_evento,
                args=(produto, i, "percentual", st.session_state.get(f"percentual_{produto}_{i}", float(evento["percentual"])))
            )
            dias = st.number_input(
                f"Número de dias do evento {i+1} para {produto}:",
                min_value=0, step=1,
                value=evento["dias"],
                key=f"dias_{produto}_{i}",
                on_change=atualizar_evento,
                args=(produto, i, "dias", st.session_state.get(f"dias_{produto}_{i}", evento["dias"]))
            )
            evento_base = st.selectbox(
                f"Evento base do evento {i+1} para {produto}:",
                lista_eventos,
                index=lista_eventos.index(evento["evento"]),
                key=f"evento_{produto}_{i}",
                on_change=atualizar_evento,
                args=(produto, i, "evento", st.session_state.get(f"evento_{produto}_{i}", evento["evento"]))
            )
            
            # Adiciona evento atualizado na lista temporária
            eventos_atualizados.append({
                "percentual": percentual,
                "dias": dias,
                "evento": evento_base
            })

            # Botão para excluir o evento
            if st.button(f"Excluir evento {i+1} para {produto}", key=f"excluir_{produto}_{i}"):
                eventos_atualizados.pop(i)  # Remove da lista temporária
                st.session_state['recarregar'] = True  # Define para recarregar

            st.markdown("---")
        
        # Atualiza a lista de eventos apenas após o loop
        if st.session_state['recarregar']:
            st.session_state[f'eventos_{produto}'] = eventos_atualizados
            st.session_state['recarregar'] = False
            st.rerun()  # Recarrega para refletir mudanças imediatamente

        # Botão para adicionar um novo evento
        if st.button(f"Adicionar novo evento para {produto}"):
            st.session_state[f'eventos_{produto}'].append({"percentual": 0, "dias": 0, "evento": lista_eventos[0]})
            st.rerun()  # Recarrega imediatamente após adicionar um novo evento
    
    eventos_pagamento["eventos"] = st.session_state[f'eventos_{produto}']
    return eventos_pagamento

# Função para verificar se o produto ainda está presente e removê-lo se não estiver
def verificar_produtos_presentes(produtos_presentes):
    produtos_no_session_state = list(st.session_state['eventos_pagamento'].keys())
    for produto in produtos_no_session_state:
        if produto not in produtos_presentes:
            del st.session_state['eventos_pagamento'][produto]



    # Verificar se a proposta possui QGBT ou SKID
    if "SKID" in produtos_presentes :
        st.session_state['classificacao_qgbt_skid'] = "SKID"
    else:
        st.session_state['classificacao_qgbt_skid'] = "QGBT"


# Inicializar session_state para eventos de pagamento
if 'eventos_pagamento' not in st.session_state:
    st.session_state['eventos_pagamento'] = {}

# Iterar sobre as usinas e itens para identificar produtos únicos
produtos_unicos = set()
for usina in st.session_state.get('usinas', []):
    for item in usina.get('itens', []):
        produto = item.get('produto')
        if produto:
            produtos_unicos.add(normalizar_produto(produto))

# Verificar se os produtos ainda estão presentes
verificar_produtos_presentes(produtos_unicos)



st.subheader("Configuração de Eventos de Pagamento")

# Configurar eventos de pagamento para cada produto único
for produto in produtos_unicos:
    st.session_state['eventos_pagamento'][produto] = configurar_eventos_pagamento(produto)
st.markdown("---")


# st.subheader("Configuração do responsável pela proposta")
# st.text("")

# # def selecionar_proponente():
# #     proponentes = {
# #         "Gabrielle": "gab.jpg",
# #         "Bernardo": "bernardo.jpg",
# #         "Marlon": "marlon.jpg"
# #     }

#     # Inicializa o session_state para proponente se não existir
#     if 'proponente' not in st.session_state:
#         st.session_state['proponente'] = "Gabrielle"

#     # Exibir as imagens dos proponentes em três colunas com checkboxes
#     col1, col2, col3 = st.columns(3)

#     with col1:
#         st.image(Image.open(proponentes["Gabrielle"]), caption="Gabrielle", width=100)
#         if st.button("Selecione Gabrielle"):
#             st.session_state['proponente'] = "Gabrielle"

#     with col2:
#         st.image(Image.open(proponentes["Bernardo"]), caption="Bernardo", width=100)
#         if st.button("Selecione Bernardo"):
#             st.session_state['proponente'] = "Bernardo"

#     with col3:
#         st.image(Image.open(proponentes["Marlon"]), caption="Marlon", width=100)
#         if st.button("Selecione Marlon"):
#             st.session_state['proponente'] = "Marlon"

#     st.text("")
#     # Exibir o proponente selecionado
#     st.subheader(f"Responsável selecionado: {st.session_state['proponente']}")

# # Chama a função para exibir a interface
# selecionar_proponente()

# # Inputs para prazos
# st.header("Prazos")
# prazo_desenhos = st.text_input("Prazo Desenhos para aprovação", value=load_value('prazo_desenhos'))
# prazo_aprovacao_cliente = st.text_input("Prazo para aprovação do cliente", value=load_value('prazo_aprovacao_cliente'))

# # Salvar os valores no session_state
# store_value('prazo_desenhos', prazo_desenhos)
# store_value('prazo_aprovacao_cliente', prazo_aprovacao_cliente)


# # Inputs para prazos específicos de cada produto
# st.header("Prazos Específicos por Produto")
# for produto in produtos_unicos:
#     if f'prazo_{produto}' not in st.session_state:
#         load_value(f'prazo_{produto}')
#     st.text_input(f"Prazo para {produto}", value=st.session_state['prazos'][f'prazo_{produto}'], key=f"f'prazo_{produto}",on_change=store_value) 


# st.session_state['prazos']['prazo_desenhos'] = prazo_desenhos
# st.session_state['prazos']['prazo_aprovacao_cliente'] = prazo_aprovacao_cliente

# # Exibir todos os prazos salvos
# st.write("Todos os prazos salvos:", st.session_state['prazos'])

