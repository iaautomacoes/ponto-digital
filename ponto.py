# [inicio da folha 1 de 5 ## Interface do Funcionário e Captura de Foto]
import streamlit as st
import pandas as pd
from datetime import datetime
import os
import shutil

# Configuração da página e arquivos
st.set_page_config(page_title="Ponto Digital Pro", page_icon="⏰", layout="wide")
ARQUIVO_EXCEL = "registro_ponto.xlsx"
ARQUIVO_MATRICULAS = "cadastro_matriculas.xlsx"
PASTA_FOTOS = "fotos_ponto"

if not os.path.exists(PASTA_FOTOS):
    os.makedirs(PASTA_FOTOS)

DIAS_SEMANA = {0: "Segunda-feira", 1: "Terça-feira", 2: "Quarta-feira", 
               3: "Quinta-feira", 4: "Sexta-feira", 5: "Sábado", 6: "Domingo"}

# Inicializa as planilhas se não existirem
if not os.path.exists(ARQUIVO_EXCEL):
    pd.DataFrame(columns=["Matrícula", "Nome do Funcionário", "Data", "Dia da Semana", 
                          "Hora", "Tipo de Registro", "Observação", "Caminho da Foto"]).to_excel(ARQUIVO_EXCEL, index=False)

if not os.path.exists(ARQUIVO_MATRICULAS):
    pd.DataFrame(columns=["Matrícula", "Nome do Funcionário"]).to_excel(ARQUIVO_MATRICULAS, index=False)

st.title("⏰ Sistema de Ponto Digital Pro")
st.subheader("Identificação por Nome, Matrícula e Foto")

# Formulário para o funcionário
matricula_input = st.text_input("Digite o Número de Matrícula:").strip()
tipo_registro = st.selectbox("Selecione o tipo de registro:", ["Entrada", "Saída Almoço", "Retorno Almoço", "Saída"])
observacao = st.text_area("Observação / Justificativa (Opcional):", max_chars=200)

st.write("---")
st.write("📸 **Posicione-se para a foto de validação:**")
foto_capturada = st.camera_input("Tirar foto para o ponto")
# [final da folha 1 de 5 com 37 linhas]


## 2 =======================================================================================================================================================================


# [inicio da folha 2 de 5 ## Validação de Regras e Gravação do Ponto]
if st.button("Confirmar Registro de Ponto", type="primary"):
    df_validos = pd.read_excel(ARQUIVO_MATRICULAS)
    df_validos["Matrícula"] = df_validos["Matrícula"].astype(str).str.strip()
    
    if not matricula_input:
        st.error("❌ Por favor, preencha o campo de Matrícula.")
    elif matricula_input not in df_validos["Matrícula"].values:
        st.error("❌ Matrícula não cadastrada no sistema. Procure o Administrador.")
    elif foto_captured := (foto_capturada is None):
        st.error("❌ É obrigatório tirar a foto para validar o ponto.")
    else:
        nome_funcionario = str(df_validos[df_validos["Matrícula"] == matricula_input]["Nome do Funcionário"].values[0])
        agora = datetime.now()
        data_hoje = agora.strftime("%Y-%m-%d")
        dia_semana_nome = DIAS_SEMANA[agora.weekday()]
        hora_agora = agora.strftime("%H:%M:%S")
        timestamp_arquivo = agora.strftime("%Y%m%d_%H%M%S")
        
        df_atual = pd.read_excel(ARQUIVO_EXCEL)
        registros_hoje = df_atual[(df_atual["Matrícula"].astype(str) == matricula_input) & (df_atual["Data"] == data_hoje)]
        
        pode_registrar = True
        if tipo_registro in ["Saída Almoço", "Saída"]:
            tem_entrada = registros_hoje[registros_hoje["Tipo de Registro"].isin(["Entrada", "Retorno Almoço"])]
            if tem_entrada.empty:
                st.error("❌ Registro Negado: Você não pode registrar uma Saída sem ter registrado uma Entrada hoje.")
                pode_registrar = False
                
        if pode_registrar:
            nome_foto = f"{matricula_input}_{timestamp_arquivo}.jpg"
            caminho_foto = os.path.join(PASTA_FOTOS, nome_foto)
            with open(caminho_foto, "wb") as f:
                f.write(foto_capturada.getbuffer())
            
            novo_registro = {
                "Matrícula": matricula_input, "Nome do Funcionário": nome_funcionario, "Data": data_hoje,
                "Dia da Semana": dia_semana_nome, "Hora": hora_agora, "Tipo de Registro": tipo_registro,
                "Observação": observacao.strip() if observacao.strip() else "Nenhuma", "Caminho da Foto": caminho_foto
            }
            df_atual = pd.concat([df_atual, pd.DataFrame([novo_registro])], ignore_index=True)
            df_atual.to_excel(ARQUIVO_EXCEL, index=False)
            st.success(f"✅ Ponto de {nome_funcionario} registrado com sucesso às {hora_agora} ({dia_semana_nome})!")
            st.rerun()
# [final da folha 2 de 5 com 46 linhas]


## 3 ======================================================================================================================================================================


# [inicio da folha 3 de 5 ## Painel ADM, Escala e Agrupamento do Banco de Horas]
st.write("---")
with st.expander("📊 Painel Administrativo Restrito (Apenas ADM)"):
    senha = st.text_input("Digite a senha master para acessar:", type="password")
    if senha == "admin123":
        aba_relatorios, aba_cadastros, aba_fotos, aba_manutencao = st.tabs([
            "📊 Relatórios e Filtros", "👥 Cadastrar Funcionários", "📸 Galeria Visual", "⚙️ Manutenção do Sistema"
        ])
        
        with aba_relatorios:
            st.write("### ⚙️ Configurações de Escala")
            jornada_editavel = st.slider("Defina a jornada padrão diária (Horas):", min_value=1.0, max_value=12.0, value=8.0, step=0.5)
            df_visualizar = pd.read_excel(ARQUIVO_EXCEL)
            
            if not df_visualizar.empty:
                st.write("### 🔍 Filtros de Busca")
                lista_funcionarios = ["Todos"] + list(df_visualizar["Nome do Funcionário"].unique())
                lista_datas = ["Todas"] + list(df_visualizar["Data"].unique())
                filtro_nome = st.selectbox("Filtrar por Funcionário:", lista_funcionarios)
                filtro_data = st.selectbox("Filtrar por Data:", lista_datas)
                
                relatorio_horas = []
                for (mat, nome, data), grupo in df_visualizar.groupby(["Matrícula", "Nome do Funcionário", "Data"]):
                    grupo = grupo.sort_values(by="Hora")
                    total_segundos = 0
                    hora_entrada = None
                    ultimas_observacoes = []
                    dia_da_semana_calculado = grupo["Dia da Semana"].values[0]
                    
                    for _, row in grupo.iterrows():
                        tipo = row["Tipo de Registro"]
                        h_obj = datetime.strptime(f"{data} {row['Hora']}", "%Y-%m-%d %H:%M:%S")
                        if str(row["Observação"]) != "Nenhuma" and str(row["Observação"]) != "nan":
                            ultimas_observacoes.append(str(row["Observação"]))
                        if tipo in ["Entrada", "Retorno Almoço"]:
                            hora_entrada = h_obj
                        elif tipo in ["Saída Almoço", "Saída"] and hora_entrada is not None:
                            total_segundos += (h_obj - hora_entrada).total_seconds()
                            hora_entrada = None
                    
                    horas_totais = total_segundos / 3600
                    saldo = horas_totais - jornada_editavel
                    status_saldo = f"+{saldo:.2f} hrs (Extra)" if saldo > 0 else (f"{saldo:.2f} hrs (Devendo)" if saldo < 0 else "0.00 hrs")
                    obs_consolidada = " | ".join(ultimas_observacoes) if ultimas_observacoes else "Nenhuma"
                    
                    relatorio_horas.append({"Matrícula": mat, "Funcionário": nome, "Data": data, "Dia da Semana": dia_da_semana_calculado,
                                            "Horas Trabalhadas": horas_totais, "Jornada Definida": f"{jornada_editavel:.1f} hrs",
                                            "Saldo do Dia": status_saldo, "Observações": obs_consolidada})
# [final da folha 3 de 5 com 47 linhas]


## 4 =======================================================================================================================================================================


# [inicio da folha 4 de 5 ## Exibição de Relatórios Estilizados e Cadastro de Funcionários]
                df_calculado = pd.DataFrame(relatorio_horas)
                if filtro_nome != "Todos":
                    df_calculado = df_calculado[df_calculado["Funcionário"] == filtro_nome]
                if filtro_data != "Todas":
                    df_calculado = df_calculado[df_calculado["Data"] == filtro_data]
                
                def aplicar_alerta_vermelho(val):
                    return 'background-color: #ffcccc; color: black; font-weight: bold;' if isinstance(val, float) and val > 10.0 else ''
                
                df_estilizado = df_calculado.style.applymap(aplicar_alerta_vermelho, subset=["Horas Trabalhadas"]).format({"Horas Trabalhadas": "{:.2f} hrs"})
                st.dataframe(df_estilizado, use_container_width=True)
                
                if (df_calculado["Horas Trabalhadas"] > 10.0).any():
                    st.error("⚠️ ATENÇÃO ADM: Existem funcionários destacados em vermelho que ultrapassaram o limite de 10 horas!")
                
                with open(ARQUIVO_EXCEL, "rb") as file:
                    st.download_button(label="📥 Exportar Relatório Geral (Excel)", data=file, file_name="relatorio_geral_ponto.xlsx")
            else:
                st.info("Nenhum registro de ponto até o momento.")
                
        with aba_cadastros:
            st.write("### 👥 Gerenciar Matrículas Autorizadas")
            col1, col2 = st.columns(2)
            with col1: nova_mat = st.text_input("Nova Matrícula (Apenas Números):")
            with col2: novo_nome = st.text_input("Nome Completo do Colaborador:")
                
            if st.button("Cadastrar Funcionário"):
                if nova_mat.strip() and novo_nome.strip():
                    df_m = pd.read_excel(ARQUIVO_MATRICULAS)
                    df_m["Matrícula"] = df_m["Matrícula"].astype(str).str.strip()
                    if nova_mat.strip() in df_m["Matrícula"].values:
                        st.error("❌ Esta matrícula já está cadastrada!")
                    else:
                        df_m = pd.concat([df_m, pd.DataFrame([{"Matrícula": nova_mat.strip(), "Nome do Funcionário": novo_nome.strip()}])], ignore_index=True)
                        df_m.to_excel(ARQUIVO_MATRICULAS, index=False)
                        st.success(f"👥 {novo_nome} cadastrado com sucesso!")
                        st.rerun()
            
            df_m_visualizar = pd.read_excel(ARQUIVO_MATRICULAS)
            if not df_m_visualizar.empty: st.dataframe(df_m_visualizar)
# [final da folha 4 de 5 com 40 linhas]


## 5 =======================================================================================================================================================================


# [inicio da folha 5 de 5 ## Galeria Visual, Remoção de Ponto e Fechamento Mensal]
        with aba_fotos:
            st.write("### 📸 Conferência Visual das Batidas de Ponto")
            df_pontos_fotos = pd.read_excel(ARQUIVO_EXCEL)
            if not df_pontos_fotos.empty:
                df_pontos_fotos = df_pontos_fotos.iloc[::-1]
                for idx, row in df_pontos_fotos.iterrows():
                    caminho = row["Caminho da Foto"]
                    if os.path.exists(caminho):
                        col_img, col_info = st.columns([1, 4])
                        with col_img: st.image(caminho, width=120)
                        with col_info:
                            st.markdown(f"**Funcionário:** {row['Nome do Funcionário']} ({row['Matrícula']})")
                            st.markdown(f"**Registro:** {row['Tipo de Registro']} em {row['Data']} às {row['Hora']}")
                        st.write("---")

        with aba_manutencao:
            st.write("### 🛠️ Ferramentas de Controle e Manutenção")
            df_maint = pd.read_excel(ARQUIVO_EXCEL)
            
            # Recurso 1: Remover batida específica
            st.write("#### ❌ Deletar uma Batida Incorreta")
            if not df_maint.empty:
                linhas_formatadas = [f"[{i}] {r['Nome do Funcionário']} - {r['Tipo de Registro']} em {r['Data']} às {r['Hora']}" for i, r in df_maint.iterrows()]
                ponto_para_deletar = st.selectbox("Selecione o registro para excluir permanentemente:", linhas_formatadas)
                if st.button("Excluir Registro Selecionado", type="primary"):
                    idx_del = int(ponto_para_deletar.split("]")[0].replace("[", ""))
                    foto_del = df_maint.at[idx_del, "Caminho da Foto"]
                    if os.path.exists(foto_del): os.remove(foto_del)
                    df_maint = df_maint.drop(idx_del).reset_index(drop=True)
                    df_maint.to_excel(ARQUIVO_EXCEL, index=False)
                    st.success("✅ Registro e foto correspondente excluídos com sucesso!")
                    st.rerun()
            else: st.info("Nenhum registro disponível para exclusão.")
            
            # Recurso 2: Fechamento/Arquivamento mensal
            st.write("#### 📦 Fechamento Mensal (Limpar Histórico e Começar do Zero)")
            if st.button("Arquivar Mês Atual e Limpar Histórico"):
                if not df_maint.empty:
                    timestamp_backup = datetime.now().strftime("%Y%m%d_%H%M%S")
                    shutil.copy(ARQUIVO_EXCEL, f"registro_ponto_BACKUP_{timestamp_backup}.xlsx")
                    pd.DataFrame(columns=["Matrícula", "Nome do Funcionário", "Data", "Dia da Semana", 
                                          "Hora", "Tipo de Registro", "Observação", "Caminho da Foto"]).to_excel(ARQUIVO_EXCEL, index=False)
                    st.success("📦 Histórico arquivado em um arquivo de BACKUP e painel limpo com sucesso para o novo mês!")
                    st.rerun()
                else: st.warning("O banco de dados já está vazio.")
# [final da folha 5 de 5 com 47 linhas]


## =========================================================================================================================================================================
