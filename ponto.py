# [inicio da folha 1 de 5 ## Configurações e Conexão Permanente com GitHub]
import streamlit as st
import pandas as pd
from datetime import datetime
import os
import requests
import base64
import io

st.set_page_config(page_title="Ponto Digital Pro", page_icon="⏰", layout="wide")
REPO = "iaautomacoes/ponto-digital"
ARQUIVO_EXCEL = "registro_ponto.xlsx"
ARQUIVO_MATRICULAS = "cadastro_matriculas.xlsx"

TOKEN = st.secrets.get("GITHUB_TOKEN", "")

def ler_github(caminho):
    url = f"https://github.com{REPO}/contents/{caminho}"
    headers = {"Authorization": f"token {TOKEN}"} if TOKEN else {}
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            conteudo = r.json()
            dados_finais = base64.b64decode(conteudo["content"])
            df = pd.read_excel(io.BytesIO(dados_finais))
            return df, conteudo["sha"]
    except:
        pass
    return pd.DataFrame(), None

def salvar_github(df, camino, sha, msg="Update"):
    output = io.BytesIO()
    df.to_excel(output, index=False)
    conteudo_b64 = base64.b64encode(output.getvalue()).decode()
    url = f"https://github.com{REPO}/contents/{camino}"
    headers = {"Authorization": f"token {TOKEN}"}
    data = {"message": msg, "content": conteudo_b64}
    if sha: 
        data["sha"] = sha
    try:
        requests.put(url, json=data, headers=headers)
    except:
        pass
# [final da folha 1 de 5 com 44 linhas]

## 2  ============================================================================================================================================================================================

# [inicio da folha 2 de 5 ## Inicialização de Tabelas e Tela de Login]
DIAS_SEMANA = {0: "Segunda-feira", 1: "Terça-feira", 2: "Quarta-feira", 
               3: "Quinta-feira", 4: "Sexta-feira", 5: "Sábado", 6: "Domingo"}

st.title("⏰ Sistema de Ponto Digital Pro")
st.subheader("Acesso Restrito por Nome e Senha Individual")

st.sidebar.write("### 🔑 Área de Acesso do Colaborador")
login_nome = st.sidebar.text_input("Digite seu Nome Completo:").strip()
login_senha = st.sidebar.text_input("Digite sua Senha Pessoal:", type="password").strip()

logado = False
nome_funcionario = ""
matricula_funcionario = ""

if login_nome and login_senha:
    df_validos, _ = ler_github(ARQUIVO_MATRICULAS)
    if not df_validos.empty:
        if "Nome do Funcionário" in df_validos.columns and "Senha" in df_validos.columns:
            df_validos["Nome do Funcionário"] = df_validos["Nome do Funcionário"].astype(str).str.strip()
            df_validos["Senha"] = df_validos["Senha"].astype(str).str.strip()
            
            usuario_valido = df_validos[(df_validos["Nome do Funcionário"].str.lower() == login_nome.lower()) & (df_validos["Senha"].astype(str) == login_senha)]
            
            if not usuario_valido.empty:
                logado = True
                nome_funcionario = str(usuario_valido.iloc[0]["Nome do Funcionário"])
                matr_crua = usuario_valido.iloc[0]["Matrícula"]
                matricula_funcionario = str(int(float(matr_crua))) if pd.notna(matr_crua) else str(matr_crua)
                st.sidebar.success(f"🔓 Conectado: {nome_funcionario}")
            else:
                st.sidebar.error("❌ Nome ou Senha Incorreta.")

if logado:
    st.info(f"👋 Olá, {nome_funcionario.lower()}! Use o formulário abaixo para registrar seu horário.")
    tipo_registro = st.selectbox("Selecione o tipo de registro:", ["Entrada", "Saída Almoço", "Retorno Almoço", "Saída"])
    observacao = st.text_area("Observação / Justificativa (Opcional):", max_chars=200)
    st.write("")
    foto_capturada = st.camera_input("📸 Posicione-se para a foto de validação:")
else:
    st.warning("👈 Faça login no menu ao lado para liberar o formulário de ponto.")
# [final da folha 2 de 5 com 43 linhas]


## 3  ============================================================================================================================================================================================

# [inicio da folha 3 de 5 ## Gravação e Envio de Ponto com Hora Correta]
if logado and st.button("Confirmar Registro de Ponto", type="primary"):
    if foto_capturada is None:
        st.error("❌ É obrigatório tirar a foto para validar o ponto.")
    else:
        import datetime as dt_lib
        fuso_br = dt_lib.timezone(dt_lib.timedelta(hours=-3))
        agora = datetime.now(fuso_br)
        
        data_hoje = agora.strftime("%Y-%m-%d")
        dia_semana_nome = DIAS_SEMANA[agora.weekday()]
        hora_agora = agora.strftime("%H:%M:%S")
        
        df_atual, sha_ponto = ler_github(ARQUIVO_EXCEL)
        pode_registrar = True
        
        if df_atual.empty:
            df_atual = pd.DataFrame(columns=["Matrícula", "Nome do Funcionário", "Data", "Dia da Semana", "Hora", "Tipo de Registro", "Observação", "Caminho da Foto"])
        else:
            registros_hoje = df_atual[(df_atual["Matrícula"].astype(str) == matricula_funcionario) & (df_atual["Data"] == data_hoje)]
            if tipo_registro in ["Saída Almoço", "Saída"]:
                if registros_hoje[registros_hoje["Tipo de Registro"].isin(["Entrada", "Retorno Almoço"])].empty:
                    st.error("❌ Registro Negado: Sem Entrada registrada hoje.")
                    pode_registrar = False
                    
        if pode_registrar:
            novo_registro = {
                "Matrícula": matricula_funcionario, "Nome do Funcionário": nome_funcionario, "Data": data_hoje,
                "Dia da Semana": dia_semana_nome, "Hora": hora_agora, "Tipo de Registro": tipo_registro,
                "Observação": observacao.strip() if observacao.strip() else "Nenhuma", "Caminho da Foto": "Salva na Nuvem"
            }
            df_atual = pd.concat([df_atual, pd.DataFrame([novo_registro])], ignore_index=True)
            salvar_github(df_atual, ARQUIVO_EXCEL, sha_ponto, f"Ponto {tipo_registro} gravado")
            
            seu_numero_whats = "5534999999999" 
            texto_msg = f"⏰ *Alerta de Ponto*\n\nO colaborador *{nome_funcionario}* registrou *{tipo_registro}* às {hora_agora[:5]}."
            link_whatsapp = f"https://whatsapp.com{seu_numero_whats}&text={urllib.parse.quote(texto_msg)}"
            
            st.success(f"✅ Ponto registrado com sucesso às {hora_agora[:5]}!")
            st.markdown(f"[📲 Abrir Notificação no WhatsApp]({link_whatsapp})")
            st.balloons()
            st.rerun()
# [final da folha 3 de 5 com 43 linhas]


## 4  ============================================================================================================================================================================================

# [inicio da folha 4 de 5 ## Painel ADM, Escala e Relatórios por Dia]
st.write("---")
with st.expander("📊 Painel Administrativo Restrito (Apenas ADM)"):
    senha_adm = st.text_input("Digite a senha master:", type="password", key="adm_senha_final")
    if senha_adm == "admin123":
        aba_relatorios, aba_cadastros, aba_fotos, aba_manutencao = st.tabs([
            "📊 Relatórios e Filtros", "👥 Cadastrar Funcionários", "📸 Galeria Visual", "⚙️ Manutenção do Sistema"
        ])
        
        with aba_relatorios:
            df_visualizar, _ = ler_github(ARQUIVO_EXCEL)
            if not df_visualizar.empty:
                lista_funcionarios = ["Todos"] + list(df_visualizar["Nome do Funcionário"].unique())
                filtro_nome = st.selectbox("Filtrar por Funcionário:", lista_funcionarios, key="f_nome")
                
                df_visualizar["Data_Clean"] = df_visualizar["Data"].astype(str).str.strip()
                lista_datas = ["Todas"] + sorted(list(df_visualizar["Data_Clean"].unique()), reverse=True)
                filtro_data = st.selectbox("Filtrar por Data:", lista_datas, key="f_data")
                
                relatorio_dias = []
                for (mat, nome, data), grupo in df_visualizar.groupby(["Matrícula", "Nome do Funcionário", "Data_Clean"]):
                    total_batidas = len(grupo)
                    tem_entrada = not grupo[grupo["Tipo de Registro"] == "Entrada"].empty
                    tem_saida = not grupo[grupo["Tipo de Registro"] == "Saída"].empty
                    
                    if tem_entrada and tem_saida:
                        status_dia = "Presença Confirmada"
                        qtd_dias = 1.0
                    elif total_batidas > 0:
                        status_dia = "Ponto Incompleto"
                        qtd_dias = 0.5
                    else:
                        status_dia = "Sem Registro"
                        qtd_dias = 0.0
                        
                    try:
                        data_dt = datetime.strptime(data, "%Y-%m-%d")
                        data_br = data_dt.strftime("%d/%m/%Y")
                    except:
                        data_br = data
                    
                    relatorio_dias.append({
                        "Matrícula": mat, "Funcionário": nome, "Data": data_br,
                        "Dias Trabalhados": f"{qtd_dias:.1f} Dia", "Status do Dia": status_dia,
                        "Data_Raw": data
                    })
                    
                df_calculado = pd.DataFrame(relatorio_dias)
                if filtro_nome != "Todos": 
                    df_calculado = df_calculado[df_calculado["Funcionário"] == filtro_nome]
                if filtro_data != "Todas":
                    df_calculado = df_calculado[df_calculado["Data_Raw"] == filtro_data]
                    
                if not df_calculado.empty:
                    df_calculado["Dias_Num"] = df_calculado["Dias Trabalhados"].str.split().str.get(0).astype(float)
                    total_dias_periodo = df_calculado["Dias_Num"].sum()
                    st.metric("📆 Total de Dias Trabalhados no Período", f"{total_dias_periodo:.1f} Dias")
                    st.table(df_calculado.drop(columns=["Data_Raw", "Dias_Num"]))
            else:
                st.info("Nenhum ponto registrado no banco de dados.")
# [final da folha 4 de 5 com 53 linhas]


## 5  ============================================================================================================================================================================================

# [inicio da folha 5 de 5 ## Tabela Limpa de Cadastros, Galeria com Hora e Fechamento]
        with aba_cadastros:
            col1, col2, col3 = st.columns(3)
            with col1: nova_mat = st.text_input("Nova Matrícula:", key="c_mat").strip()
            with col2: novo_nome = st.text_input("Nome Completo do Funcionário:", key="c_nome").strip()
            with col3: nova_senha = st.text_input("Senha do Funcionário:", type="password", key="c_senha").strip()
            if st.button("Cadastrar Funcionário", type="secondary", key="btn_cad"):
                if nova_mat and novo_nome and nova_senha:
                    df_m, sha_mat = ler_github(ARQUIVO_MATRICULAS)
                    if df_m.empty:
                        df_m = pd.DataFrame(columns=["Matrícula", "Nome do Funcionário", "Senha"])
                    else:
                        df_m["Nome do Funcionário"] = df_m["Nome do Funcionário"].astype(str).str.strip()
                        
                    if novo_nome in df_m["Nome do Funcionário"].values: 
                        st.error("❌ Já cadastrado!")
                    else:
                        novo_func = pd.DataFrame([{"Matrícula": str(nova_mat), "Nome do Funcionário": novo_nome, "Senha": str(nova_senha)}])
                        df_m = pd.concat([df_m, novo_func], ignore_index=True)
                        salvar_github(df_m, ARQUIVO_MATRICULAS, sha_mat, "Novo Funcionario")
                        st.success("👥 Cadastrado com sucesso!")
                        st.rerun()
                else:
                    st.warning("⚠️ Preencha todos os campos para cadastrar.")
                    
            df_m_vis, _ = ler_github(ARQUIVO_MATRICULAS)
            if not df_m_vis.empty: 
                st.table(df_m_vis)

        with aba_fotos:
            df_pt_ft, _ = ler_github(ARQUIVO_EXCEL)
            if not df_pt_ft.empty:
                for idx, row in df_pt_ft.iloc[::-1].iterrows():
                    try:
                        data_original = datetime.strptime(str(row["Data"]).split(), "%Y-%m-%d")
                        data_formatada = data_original.strftime("%d/%m/%Y")
                    except:
                        data_formatada = str(row["Data"])
                    hora_formatada = str(row["Hora"])[:5]
                    st.markdown(f"👤 **{row['Nome do Funcionário']}** — {row['Tipo de Registro']} em **{data_formatada}** às **{hora_formatada}**")
                    st.write("---")

        with aba_manutencao:
            if st.button("Limpar Batidas de Ponto do Mês", key="btn_clear_all"):
                _, sha_ponto = ler_github(ARQUIVO_EXCEL)
                vazio = pd.DataFrame(columns=["Matrícula", "Nome do Funcionário", "Data", "Dia da Semana", "Hora", "Tipo de Registro", "Observação", "Caminho da Foto"])
                salvar_github(vazio, ARQUIVO_EXCEL, sha_ponto, "Limpeza Mensal")
                st.success("📦 Pontos limpos permanentemente!")
                st.rerun()
# [final da folha 5 de 5 com 44 linhas]

## fim  ============================================================================================================================================================================================
