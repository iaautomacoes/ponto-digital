# [inicio da folha 1 de 5 ## Configurações Iniciais e Criação de Senhas]
import streamlit as st
import pandas as pd
from datetime import datetime
import os
import shutil
import urllib.parse

# Configuração da página e arquivos
st.set_page_config(page_title="Ponto Digital Pro", page_icon="⏰", layout="wide")
ARQUIVO_EXCEL = "registro_ponto.xlsx"
ARQUIVO_MATRICULAS = "cadastro_matriculas.xlsx"
PASTA_FOTOS = "fotos_ponto"

if not os.path.exists(PASTA_FOTOS):
    os.makedirs(PASTA_FOTOS, exist_ok=True)

DIAS_SEMANA = {0: "Segunda-feira", 1: "Terça-feira", 2: "Quarta-feira", 
               3: "Quinta-feira", 4: "Sexta-feira", 5: "Sábado", 6: "Domingo"}

if not os.path.exists(ARQUIVO_EXCEL):
    pd.DataFrame(columns=["Matrícula", "Nome do Funcionário", "Data", "Dia da Semana", 
                          "Hora", "Tipo de Registro", "Observação", "Caminho da Foto"]).to_excel(ARQUIVO_EXCEL, index=False)

if not os.path.exists(ARQUIVO_MATRICULAS):
    pd.DataFrame(columns=["Matrícula", "Nome do Funcionário", "Senha"]).to_excel(ARQUIVO_MATRICULAS, index=False)

st.title("⏰ Sistema de Ponto Digital Pro")
st.subheader("Acesso Restrito por Matrícula e Senha Individual")
# [final da folha 1 de 5 com 30 linhas]


## 2 =======================================================================================================================================================================


# [inicio da folha 2 de 5 ## Tela de Login e Interface do Funcionário]
st.sidebar.write("### 🔑 Área de Acesso do Colaborador")
login_matricula = st.sidebar.text_input("Digite sua Matrícula:").strip()
login_senha = st.sidebar.text_input("Digite sua Senha Pessoal:", type="password").strip()

logado = False
nome_funcionario = ""

if login_matricula and login_senha:
    df_validos = pd.read_excel(ARQUIVO_MATRICULAS)
    df_validos["Matrícula"] = df_validos["Matrícula"].astype(str).str.strip()
    df_validos["Senha"] = df_validos["Senha"].astype(str).str.strip()
    usuario_valido = df_validos[(df_validos["Matrícula"] == login_matricula) & (df_validos["Senha"] == login_senha)]
    
    if not usuario_valido.empty:
        logado = True
        nome_funcionario = str(usuario_valido.iloc[0]["Nome do Funcionário"])
        st.sidebar.success(f"🔓 Conectado: {nome_funcionario}")
    else:
        st.sidebar.error("❌ Matrícula ou Senha Incorreta.")

if logado:
    st.info(f"👋 Olá, **{nome_funcionario}**! Use o formulário abaixo para registrar seu horário.")
    tipo_registro = st.selectbox("Selecione o tipo de registro:", ["Entrada", "Saída Almoço", "Retorno Almoço", "Saída"])
    observacao = st.text_area("Observação / Justificativa (Opcional):", max_chars=200)
    st.write("---")
    st.write("📸 **Posicione-se para a foto de validação:**")
    foto_capturada = st.camera_input("Tirar foto para o ponto")
else:
    st.warning("👈 Por favor, faça login preenchendo sua Matrícula e Senha no menu ao lado para liberar o ponto.")
# [final da folha 2 de 5 com 31 linhas]


## 3 ======================================================================================================================================================================


# [inicio da folha 3 de 5 ## Processamento de Batida de Ponto Seguro]
if logado and st.button("Confirmar Registro de Ponto", type="primary"):
    if foto_capturada is None:
        st.error("❌ É obrigatório tirar a foto para validar o ponto.")
    else:
        agora = datetime.now()
        data_hoje = agora.strftime("%Y-%m-%d")
        dia_semana_nome = DIAS_SEMANA[agora.weekday()]
        hora_agora = agora.strftime("%H:%M:%S")
        timestamp_arquivo = agora.strftime("%Y%m%d_%H%M%S")
        
        df_atual = pd.read_excel(ARQUIVO_EXCEL)
        registros_hoje = df_atual[(df_atual["Matrícula"].astype(str) == login_matricula) & (df_atual["Data"] == data_hoje)]
        
        pode_registrar = True
        if tipo_registro in ["Saída Almoço", "Saída"]:
            tem_entrada = registros_hoje[registros_hoje["Tipo de Registro"].isin(["Entrada", "Retorno Almoço"])]
            if tem_entrada.empty:
                st.error("❌ Registro Negado: Você não pode registrar uma Saída sem ter registrado uma Entrada hoje.")
                pode_registrar = False
                
        if pode_registrar:
            nome_foto = f"{login_matricula}_{timestamp_arquivo}.jpg"
            caminho_foto = os.path.join(PASTA_FOTOS, nome_foto)
            with open(caminho_foto, "wb") as f:
                f.write(foto_capturada.getbuffer())
            
            novo_registro = {
                "Matrícula": login_matricula, "Nome do Funcionário": nome_funcionario, "Data": data_hoje,
                "Dia da Semana": dia_semana_nome, "Hora": hora_agora, "Tipo de Registro": tipo_registro,
                "Observação": observacao.strip() if observacao.strip() else "Nenhuma", "Caminho da Foto": caminho_foto
            }
            df_atual = pd.concat([df_atual, pd.DataFrame([novo_registro])], ignore_index=True)
            df_atual.to_excel(ARQUIVO_EXCEL, index=False)
            
            seu_numero_whats = "5534999999999" 
            texto_msg = f"⏰ *Alerta de Ponto Digital*\n\nO colaborador *{nome_funcionario}* (Matrícula: {login_matricula}) registrou *{tipo_registro}* às {hora_agora}."
            link_whatsapp = f"https://whatsapp.com{seu_numero_whats}&text={urllib.parse.quote(texto_msg)}"
            
            st.success(f"✅ Ponto registrado com sucesso às {hora_agora}!")
            st.markdown(f"[📲 Clique aqui para abrir a notificação no seu WhatsApp]({link_whatsapp})")
            st.balloons()
            st.rerun()
# [final da folha 3 de 5 com 47 linhas]


## 4 =======================================================================================================================================================================


# [inicio da folha 4 de 5 ## Painel ADM, Escala e Relatórios com Filtro]
st.write("---")
with st.expander("📊 Painel Administrativo Restrito (Apenas ADM)"):
    senha_adm = st.text_input("Digite a senha master para acessar:", type="password")
    if senha_adm == "admin123":
        aba_relatorios, aba_cadastros, aba_fotos, aba_manutencao = st.tabs([
            "📊 Relatórios e Filtros", "👥 Cadastrar Funcionários", "📸 Galeria Visual", "⚙️ Manutenção do Sistema"
        ])
        with aba_relatorios:
            jornada_editavel = st.slider("Defina a jornada padrão diária (Horas):", min_value=1.0, max_value=12.0, value=8.0, step=0.5)
            df_visualizar = pd.read_excel(ARQUIVO_EXCEL)
            if not df_visualizar.empty:
                lista_funcionarios = ["Todos"] + list(df_visualizar["Nome do Funcionário"].unique())
                lista_datas = ["Todas"] + list(df_visualizar["Data"].unique())
                filtro_nome = st.selectbox("Filtrar por Funcionário:", lista_funcionarios)
                filtro_data = st.selectbox("Filtrar por Data:", lista_datas)
                relatorio_horas = []
                for (mat, nome, data), grupo in df_visualizar.groupby(["Matrícula", "Nome do Funcionário", "Data"]):
                    grupo = grupo.sort_values(by="Hora")
                    total_segundos, hora_entrada = 0, None
                    for _, row in grupo.iterrows():
                        if row["Tipo de Registro"] in ["Entrada", "Retorno Almoço"]: hora_entrada = datetime.strptime(f"{data} {row['Hora']}", "%Y-%m-%d %H:%M:%S")
                        elif row["Tipo de Registro"] in ["Saída Almoço", "Saída"] and hora_entrada is not None:
                            total_segundos += (datetime.strptime(f"{data} {row['Hora']}", "%Y-%m-%d %H:%M:%S") - hora_entrada).total_seconds()
                            hora_entrada = None
                    horas_totais = total_segundos / 3600
                    saldo = horas_totais - jornada_editavel
                    status_saldo = f"+{saldo:.2f} hrs (Extra)" if saldo > 0 else (f"{saldo:.2f} hrs (Devendo)" if saldo < 0 else "0.00 hrs")
                    relatorio_horas.append({"Matrícula": mat, "Funcionário": nome, "Data": data, "Horas Trabalhadas": horas_totais, "Saldo do Dia": status_saldo})
                df_calculado = pd.DataFrame(relatorio_horas)
                if filtro_nome != "Todos": df_calculado = df_calculado[df_calculado["Funcionário"] == filtro_nome]
                if filtro_data != "Todas": df_calculado = df_calculado[df_calculado["Data"] == filtro_data]
                st.dataframe(df_calculado)
# [final da folha 4 de 5 com 31 linhas]


## 5 =======================================================================================================================================================================


# [inicio da folha 5 de 5 ## Cadastro com Senha, Exclusão e Fechamento Mensal]
        with aba_cadastros:
            col1, col2, col3 = st.columns(3)
            with col1: nova_mat = st.text_input("Nova Matrícula:")
            with col2: novo_nome = st.text_input("Nome Completo:")
            with col3: nova_senha = st.text_input("Senha do Funcionário:", type="password")
            if st.button("Cadastrar Funcionário"):
                df_m = pd.read_excel(ARQUIVO_MATRICULAS)
                df_m = pd.concat([df_m, pd.DataFrame([{"Matrícula": nova_mat.strip(), "Nome do Funcionário": novo_nome.strip(), "Senha": nova_senha.strip()}])], ignore_index=True)
                df_m.to_excel(ARQUIVO_MATRICULAS, index=False)
                st.success("👥 Cadastrado!")
                st.rerun()
            df_m_vis = pd.read_excel(ARQUIVO_MATRICULAS)
            if not df_m_vis.empty: st.dataframe(df_m_vis)
        with aba_fotos:
            df_pt_ft = pd.read_excel(ARQUIVO_EXCEL)
            if not df_pt_ft.empty:
                for idx, row in df_pt_ft.iloc[::-1].iterrows():
                    if os.path.exists(str(row["Caminho da Foto"])):
                        st.image(str(row["Caminho da Foto"]), width=120)
                        st.markdown(f"**{row['Nome do Funcionário']}** - {row['Tipo de Registro']} em {row['Data']}")
        with aba_manutencao:
            df_maint = pd.read_excel(ARQUIVO_EXCEL)
            if st.button("Arquivar Mês e Limpar"):
                shutil.copy(ARQUIVO_EXCEL, f"registro_ponto_BACKUP_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
                pd.DataFrame(columns=["Matrícula", "Nome do Funcionário", "Data", "Dia da Semana", "Hora", "Tipo de Registro", "Observação", "Caminho da Foto"]).to_excel(ARQUIVO_EXCEL, index=False)
                st.success("📦 Arquivado!")
                st.rerun()
# [final da folha 5 de 5 com 27 linhas]


## =========================================================================================================================================================================
