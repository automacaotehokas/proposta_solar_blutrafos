import os
from dotenv import load_dotenv
import streamlit as st
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from docx import Document
from sharepoint_code import SharePoint  # Certifique-se de ter este módulo
from replace import inserir_tabelas_word 
from replace import inserir_eventos_pagamento
from replace import inserir_impostos
import pandas as pd
  

st.set_page_config(layout="wide")

# Inicialização do session_state
for key in ['icms', 'contribuinte', 'lucro', 'frete', 'localentrega', 'difal', 'f_pobreza', 'comissao']:
    if key not in st.session_state:
        st.session_state[key] = 0.0 if 'f' in key or 'c' in key else ''  # Ajuste para valores padrão

# Função para verificar se os dados estão completos
def verificar_dados_completos():
    dados_iniciais = st.session_state.get('dados_iniciais', {})
    usinas = st.session_state.get('usinas', [])

    # Campos obrigatórios nos dados iniciais
    campos_obrigatorios = ['cliente', 'bt', 'dia', 'mes', 'ano', 'rev', 'localentrega',   'tipofrete', 'diasvalidade', 'mesesgarantia']

    # Verificar se todos os campos obrigatórios estão presentes nos dados iniciais
    for campo in campos_obrigatorios:
        if not dados_iniciais.get(campo):
            return False

    # Verificar se há pelo menos uma usina e se cada usina tem itens configurados
    if not usinas:
        return False

    for usina in usinas:
        if not usina.get('itens'):
            return False

    return True

# Função para baixar o template uma vez e reutilizá-lo
def get_template_file():
    # Verificar a classificação no session_state
    if 'classificacao_qgbt_skid' in st.session_state:
        classificacao = st.session_state['classificacao_qgbt_skid']
    else:
        classificacao = 'QGBT'  # Valor padrão caso não esteja no session_state

    # Selecionar o template com base na classificação
    if classificacao == 'QGBT':
        template_name = 'Template_QGBT.docx'
    elif classificacao == 'SKID':
        template_name = 'Template_SKID.docx'
    else:
        template_name = 'Template_SKID.docx'

    local_template_path = f"/tmp/{template_name}"
    
    if not os.path.exists(local_template_path):
        sp = SharePoint()
        local_template_path = sp.download_file(template_name)
    
    return local_template_path



def gerar_documento_word():
    st.write("Iniciando a geração do documento Word...")

    template_path = get_template_file()
    st.write(f"Template path: {template_path}")

    output_filename = f" Blutrafos - OR's 12.{st.session_state['dados_iniciais']['bt']}-24-C-REV{st.session_state['dados_iniciais']['rev']}.docx"
    st.write(f"Output filename: {output_filename}")
    
    replacements = {
        '{{OR}}': (st.session_state['dados_iniciais'].get('bt', '')),
        '{{CLIENTE}}': str(st.session_state['dados_iniciais'].get('cliente', '')),
        '{{REV}}': st.session_state['dados_iniciais'].get('rev', ''),
        '{{OBRA}}': str(st.session_state['dados_iniciais'].get('obra', ' ')) if st.session_state['dados_iniciais'].get('obra') else ' ',
        '{{DIA}}': str(st.session_state['dados_iniciais'].get('dia', '')),
        '{{MES}}': str(st.session_state['dados_iniciais'].get('mes', '')),
        '{{ANO}}': str(st.session_state['dados_iniciais'].get('ano', '')),
        '{{LOCAL}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}': "str(st.session_state['dados_iniciais'].get('localentrega', ''))  para aplicação para revenda ou industrialização.",
        '{{ICMS}}': str(st.session_state['icms']).replace('.', ',') + "%",
        '{{CONTRIBUINTE}}': st.session_state['outputcontribuinte'] ,
        '{{DOLAR}}': "$ "+str(st.session_state['dolar']) ,
        '{{TRANSPORTE}}': st.session_state['dados_iniciais'].get('tipofrete', 'CIF') ,
        '{{DIAVALIDADE}}': str(st.session_state['dados_iniciais'].get('diasvalidade', '')),
        '{{MESESGARANTIA}}': str(st.session_state['dados_iniciais'].get('mesesgarantia', '')),
    }


    usinas = st.session_state.get('usinas', [])


    itens_configurados = []

    for usina in usinas:
        for item in usina.get('itens', []):
            itens_configurados.append({
                "descricao": item.get("descricao", ""),
                "quantidade": int(item.get("quantidade", 0)),
                "valor_unitario": item.get("valor_unitario", item.get("preco_unitario_transformador", 0.0)),
                "valor_total": item.get("valor_unitario", item.get("preco_unitario_transformador", 0.0)) * item.get("quantidade", 0),
                "order": item.get("order", 0),
                "index": item.get("id", 0)
            })


    if not itens_configurados:
        st.error("Por favor, preencha todos os itens antes de gerar o documento.")
        return None, None

    buffer = BytesIO()

    try:

        doc = Document(template_path)

        doc = inserir_tabelas_word(doc, itens_configurados, '', replacements)

        # Pegue os dados de eventos_pagamento e classificacao_estacao_subestacao
        eventos_pagamento = st.session_state.get('eventos_pagamento', {})
        classificacao_estacao_subestacao = st.session_state.get('classificacao_estacao_subestacao', '')

        # Passar os parâmetros corretamente para a função
        inserir_impostos(doc, classificacao_estacao_subestacao)
        inserir_eventos_pagamento(doc, eventos_pagamento)


        doc.save(buffer)

        buffer.seek(0)

        return buffer, output_filename

    except Exception as e:
        st.error(f"Erro ao gerar o documento: {e}")
        st.write(f"Erro ao gerar o documento: {e}")
        return None, None


# Página para gerar o documento
def pagina_gerar_documento():
    st.title("Resumo")
    st.markdown("---")

    if 'dados_iniciais' not in st.session_state:
        st.error("Por favor, preencha os dados na Pag1 antes de gerar o documento.")
        return

    # Resumo da Pag1 como uma ficha
    st.write("**Cliente:**", st.session_state['dados_iniciais'].get('cliente', ''))
    st.write("**OR:**", st.session_state['dados_iniciais'].get('bt', ''))
    st.write("**Obra:**", st.session_state['dados_iniciais'].get('obra', ''))
    st.write("**Data:**", f"{st.session_state['dados_iniciais'].get('dia', '')}/{st.session_state['dados_iniciais'].get('mes', '')}/{st.session_state['dados_iniciais'].get('ano', '')}")
    st.write("**Revisão:**", st.session_state['dados_iniciais'].get('rev', ''))
    st.write(f"**Contribuinte:** {st.session_state['contribuinte']}")
    st.write(f"**Lucro:** {st.session_state['lucro']:.2f}%")
    st.write(f"**ICMS:** {st.session_state['icms']:.2f}%")
    st.write(f"**Frete:** {st.session_state['frete']:.2f}%")
    st.write(f"**Comissão:** {st.session_state['comissao']:.2f}%")
    st.write(f"**Difal:** {st.session_state['difal']:.2f}%")
    st.write(f"**F.pobreza:** {st.session_state['f_pobreza']:.2f}%")

    


    # Adicionar informação de percentual considerado para cada item
    itens_configurados = st.session_state.get('itens_configurados', [])
    voltage_class_percentage = {
        "15 kV": 0,
        "24 kV": 30,
        "36 kV": 50
    }
    for idx, item in enumerate(itens_configurados, start=1):
        classe_tensao = item.get('classe_tensao', '')
        percentual_considerado = voltage_class_percentage.get(classe_tensao, 'Não especificado')
        st.write(f"**% Caixa Item {idx}:** {percentual_considerado}%")

    st.write("---")

    



    # Mostrando os itens configurados
    st.subheader("Itens Configurados")
    for usina_idx, usina in enumerate(st.session_state['usinas']):
        st.subheader(f"Usina {usina_idx + 1}")
        
        # Criar uma lista de dicionários com os dados dos itens
        itens_data = [
            {
                "Descrição": item.get("descricao", ""),
                "Quantidade": int(item.get("quantidade", 0)),  # Garantir que a quantidade seja um inteiro
                "Valor": "{:,.2f}".format(item.get("valor_unitario", 0.0) * item.get("quantidade", 0)).replace(",", "X").replace(".", ",").replace("X", "."),  # Formatação personalizada
                "Order": item.get("order", 0),
                "Index": item_idx  # Adiciona o índice do item para referência
            }
            for item_idx, item in enumerate(usina['itens'])
        ]
        
        # Criar um DataFrame a partir dos dados dos itens
        df_itens = pd.DataFrame(itens_data)
        
        # Calcular o total dos valores
        total_preco_total = sum(item.get("valor_unitario", 0.0) * item.get("quantidade", 0) for item in usina['itens'])
        
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
 

    # Verificar se todos os dados obrigatórios estão preenchidos
    dados_completos = verificar_dados_completos()

    st.write("O botão abaixo estará disponível após o preenchimento de todos os dados anteriores")

    # Botão para Confirmar e gerar documentos
    if st.button('Confirmar', disabled=not dados_completos):
        if dados_completos:
            # Gerar o documento Word
            buffer_word, output_filename_word = gerar_documento_word()

            if buffer_word:
                st.success("Documentos gerados com sucesso.")

                # Armazenar os buffers e nomes dos arquivos no session_state
                st.session_state['buffer_word'] = buffer_word
                st.session_state['output_filename_word'] = output_filename_word
                st.session_state['downloads_gerados'] = True

            else:
                st.error("Erro ao gerar os documentos.")
        else:
            st.error("Por favor, preencha todos os campos obrigatórios antes de gerar os documentos.")

    # Exibir os botões de download se os documentos foram gerados
    if st.session_state.get('downloads_gerados'):
        st.markdown("### Documentos Gerados:")
        # Documento Word
        col1, col2 = st.columns([6,1])
        with col1:
            output_filename_word = st.session_state.get('output_filename_word', 'Documento Word')
            st.write(f"📄 {output_filename_word}")
        with col2:
            st.download_button(
                label="⬇️",
                data=st.session_state.get('buffer_word'),
                file_name=output_filename_word,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
    else:
        st.warning("Aperte no botão acima para gerar os documentos.")

# Chama a função da página
pagina_gerar_documento()