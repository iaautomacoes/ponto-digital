# [inicio da folha 1 de 5 ## Configurações e Conexão Permanente com GitHub]
import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
import urllib.parse
import requests
import base64
import io

st.set_page_config(page_title="Ponto Digital Pro", page_icon="⏰", layout="wide")

REPO = "iaautomacoes/ponto-digital"
ARQUIVO_PONTO = "registro_ponto.xlsx"
ARQUIVO_MATRICULAS = "cadastro_matriculas.xlsx"
SEU_NUMERO_WHATS = "5534999999999"
SENHA_ADM_MASTER = "admin123"
TOKEN = st.secrets.get("GITHUB_TOKEN", "")

DIAS_SEMANA = {
    0: "Segunda-feira", 1: "Terça-feira", 2: "Quarta-feira",
    3: "Quinta-feira", 4: "Sexta-feira", 5: "Sábado", 6: "Domingo"
}

def ler_github(caminho):
    url = f"https://github.com{REPO}/contents/{caminho}"

    headers = {"Authorization": f"token {TOKEN}"} if TOKEN else {}
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            conteudo = r.json()
            dados_bytes = base64.b64decode(conteudo["content"])
            return pd.read_excel(io.BytesIO(dados_bytes)), conteudo["sha"]
    except Exception as e:
        st.error(f"Erro ao ler {caminho}: {e}")
    return pd.DataFrame(), None

def salvar_github(df, caminho, sha, msg="Atualização automática"):
    if not TOKEN:
        st.error("❌ Token do GitHub não configurado nos Secrets.")
        return False
    output = io.BytesIO()
    df.to_excel(output, index=False)
    conteudo_b64 = base64.b64encode(output.getvalue()).decode()
    url = f"https://github.com{REPO}/contents/{caminho}"
    headers = {"Authorization": f"token {TOKEN}"}
    data = {"message": msg, "content": conteudo_b64}
    if sha:
        data["sha"] = sha
    r = requests.put(url, json=data, headers=headers)
    if r.status_code in (200, 201):
        return True
    st.error(f"❌ Falha no GitHub ({r.status_code}): {r.json().get('message', '')}")
    return False
# [final da folha 1 de 5]

#=======================================================================================================================================================

# [inicio da folha 2 de 5 ## Tela de Login e Campos de Ponto]
st.title("⏰ Sistema de Ponto Digital Pro")
st.subheader("Acesso Restrito por Nome e Senha Individual")

st.sidebar.write("### 🔑 Área de Acesso do Colaborador")
login_nome = st.sidebar.text_input("Digite seu Nome Completo:", key="login_nome").strip()
login_senha = st.sidebar.text_input("Digite sua Senha Pessoal:", type="password", key="login_senha").strip()

logado = False
nome_funcionario = ""
matricula_funcionario = ""

if login_nome and login_senha:
    df_validos, _ = ler_github(ARQUIVO_MATRICULAS)
    if not df_validos.empty and {"Nome do Funcionário", "Senha", "Matrícula"}.issubset(df_validos.columns):
        df_validos["Nome do Funcionário"] = df_validos["Nome do Funcionário"].astype(str).str.strip()
        df_validos["Senha"] = df_validos["Senha"].astype(str).str.strip()
        usuario_valido = df_validos[
            (df_validos["Nome do Funcionário"].str.lower() == login_nome.lower()) &
            (df_validos["Senha"] == login_senha)
        ]
        if not usuario_valido.empty:
            logado = True
            nome_funcionario = str(usuario_valido["Nome do Funcionário"].values.item(0))
            matr_crua = usuario_valido["Matrícula"].values.item(0)
            try:
                matricula_funcionario = str(int(float(matr_crua)))
            except:
                matricula_funcionario = str(matr_crua).strip()
            st.sidebar.success(f"🔓 Conectado: {nome_funcionario}")
        else:
            st.sidebar.error("❌ Nome ou Senha Incorreta.")
    else:
        st.sidebar.warning("⚠️ Nenhum colaborador cadastrado ainda.")

if logado:
    st.info(f"👋 Olá, **{nome_funcionario}** (Matrícula: {matricula_funcionario})! Registre seu horário.")
    tipo_registro = st.selectbox("Selecione o tipo:", ["Entrada", "Saída Almoço", "Retorno Almoço", "Saída"], key="tipo_ponto")
    observacao = st.text_area("Observação (Opcional):", max_chars=200, key="obs_ponto")
    foto_capturada = st.camera_input("Tirar foto para o ponto", key="camera_ponto")
else:
    st.warning("👈 Faça login no menu ao lado para liberar o registro de ponto.")
# [final da folha 2 de 5]

#=======================================================================================================================================================

# [inicio da folha 3 de 5 ## Gravação e Envio de Ponto com Hora Correta]
if logado and st.button("Confirmar Registro de Ponto", type="primary", key="btn_confirmar"):
    if foto_capturada is None:
        st.error("❌ É obrigatório tirar a foto para validar o ponto.")
    else:
        fuso_br = timezone(timedelta(hours=-3))
        agora = datetime.now(fuso_br)
        data_hoje = agora.strftime("%Y-%m-%d")
        dia_semana_nome = DIAS_SEMANA[agora.weekday()]
        hora_agora = agora.strftime("%H:%M:%S")
        
        df_atual, sha_ponto = ler_github(ARQUIVO_PONTO)
        colunas_padrao = ["Matrícula", "Nome do Funcionário", "Data", "Dia da Semana", "Hora", "Tipo de Registro", "Observação", "Caminho da Foto"]
        pode_registrar = True
        
        if df_atual.empty or "Matrícula" not in df_atual.columns:
            df_atual = pd.DataFrame(columns=colunas_padrao)
        else:
            registros_hoje = df_atual[(df_atual["Matrícula"].astype(str) == matricula_funcionario) & (df_atual["Data"].astype(str) == data_hoje)]
            if tipo_registro in ["Saída Almoço", "Saída"]:
                if registros_hoje[registros_hoje["Tipo de Registro"].isin(["Entrada", "Retorno Almoço"])].empty:
                    st.error("❌ Registro Negado: Sem Entrada ou Retorno registrados hoje.")
                    pode_registrar = False
                    
        if pode_registrar:
            novo_registro = {
                "Matrícula": matricula_funcionario, "Nome do Funcionário": nome_funcionario, "Data": data_hoje,
                "Dia da Semana": dia_semana_nome, "Hora": hora_agora, "Tipo de Registro": tipo_registro,
                "Observação": observacao.strip() if observacao.strip() else "Nenhuma", "Caminho da Foto": "Validada via Câmera"
            }
            df_atual = pd.concat([df_atual, pd.DataFrame([novo_registro])], ignore_index=True)
            if salvar_github(df_atual, ARQUIVO_PONTO, sha_ponto, f"Ponto {tipo_registro} - {nome_funcionario}"):
                texto_msg = f"⏰ *Alerta de Ponto*\n\nO colaborador *{nome_funcionario}* registrou *{tipo_registro}* às {hora_agora[:5]}."
                link_whatsapp = f"https://wa.me{SEU_NUMERO_WHATS}?text={urllib.parse.quote(texto_msg)}"
                st.success(f"✅ Ponto registrado com sucesso às {hora_agora[:5]}!")
                st.markdown(f"[📲 Enviar Comprovante no WhatsApp]({link_whatsapp})")
                st.balloons()
# [final da folha 3 de 5]

#=======================================================================================================================================================

# [inicio da folha 4 de 5 ## Painel ADM, Escala e Relatórios]
st.write("---")
with st.expander("📊 Painel Administrativo Restrito (Apenas ADM)"):
    senha_adm = st.text_input("Digite a senha master:", type="password", key="senha_adm")
    if senha_adm == SENHA_ADM_MASTER:
        aba_relatorios, aba_cadastros, aba_historico, aba_manutencao = st.tabs([
            "📊 Relatórios e Filtros", "👥 Cadastrar Funcionários", "🕒 Histórico de Batidas", "⚙️ Manutenção"
        ])
        with aba_relatorios:
            df_vis, _ = ler_github(ARQUIVO_PONTO)
            if not df_vis.empty and "Nome do Funcionário" in df_vis.columns:
                lista_funcionarios = ["Todos"] + list(df_vis["Nome do Funcionário"].unique())
                filtro_nome = st.selectbox("Filtrar por Funcionário:", lista_funcionarios, key="filtro_adm")
                df_vis["Data_Clean"] = df_vis["Data"].astype(str).str.strip()
                relatorio_dias = []
                
                for (mat, nome, data), grupo in df_vis.groupby(["Matrícula", "Nome do Funcionário", "Data_Clean"]):
                    tem_entrada = not grupo[grupo["Tipo de Registro"] == "Entrada"].empty
                    tem_saida = not grupo[grupo["Tipo de Registro"] == "Saída"].empty
                    if tem_entrada and tem_saida:
                        status_dia, qtd_dias = "Presença Confirmada", 1.0
                    elif len(grupo) > 0:
                        status_dia, qtd_dias = "Ponto Incompleto", 0.5
                    else:
                        status_dia, qtd_dias = "Sem Registro", 0.0
                    try:
                        data_br = datetime.strptime(data.split().pop(0), "%Y-%m-%d").strftime("%d/%m/%Y")
                    except:
                        data_br = data
                    relatorio_dias.append({
                        "Matrícula": mat, "Funcionário": nome, "Data": data_br,
                        "Dias Trabalhados": f"{qtd_dias:.1f} Dia", "Status do Dia": status_dia
                    })
                df_calculado = pd.DataFrame(relatorio_dias)
                if filtro_nome != "Todos":
                    df_calculado = df_calculado[df_calculado["Funcionário"] == filtro_nome]
                st.dataframe(df_calculado, use_container_width=True)
            else:
                st.info("Nenhum registro de ponto encontrado ainda.")
# [final da folha 4 de 5]

#=======================================================================================================================================================

# [inicio da folha 5 de 5 ## Cadastros, Histórico e Manutenção]
        with aba_cadastros:
            col1, col2, col3 = st.columns(3)
            with col1: nova_mat = st.text_input("Nova Matrícula:", key="cad_mat").strip()
            with col2: novo_nome = st.text_input("Nome Completo:", key="cad_nome").strip()
            with col3: nova_senha = st.text_input("Senha Individual:", type="password", key="cad_senha").strip()
            if st.button("Cadastrar Funcionário", key="btn_cad"):
                if nova_mat and novo_nome and nova_senha:
                    df_m, sha_mat = ler_github(ARQUIVO_MATRICULAS)
                    if df_m.empty or not {"Matrícula", "Nome do Funcionário", "Senha"}.issubset(df_m.columns):
                        df_m = pd.DataFrame(columns=["Matrícula", "Nome do Funcionário", "Senha"])
                    else:
                        df_m["Nome do Funcionário"] = df_m["Nome do Funcionário"].astype(str).str.strip()
                    if novo_nome.lower() in df_m["Nome do Funcionário"].str.lower().values:
                        st.error("❌ Este funcionário já está cadastrado!")
                    else:
                        novo_func = pd.DataFrame([{"Matrícula": str(nova_mat), "Nome do Funcionário": novo_nome, "Senha": str(nova_senha)}])
                        df_m = pd.concat([df_m, novo_func], ignore_index=True)
                        if salvar_github(df_m, ARQUIVO_MATRICULAS, sha_mat, f"Cadastro: {novo_nome}"):
                            st.success("👥 Colaborador cadastrado com sucesso!")
                            st.rerun()
                else:
                    st.warning("Preencha todos os campos antes de cadastrar.")
            df_m_vis, _ = ler_github(ARQUIVO_MATRICULAS)
            if not df_m_vis.empty:
                st.dataframe(df_m_vis, use_container_width=True)

        with aba_historico:
            df_hist, _ = ler_github(ARQUIVO_PONTO)
            if not df_hist.empty and "Data" in df_hist.columns:
                for _, row in df_hist.iloc[::-1].iterrows():
                    try:
                        data_fmt = datetime.strptime(str(row["Data"]).split().pop(0), "%Y-%m-%d").strftime("%d/%m/%Y")
                    except:
                        data_fmt = str(row["Data"])
                    st.markdown(f"**{row['Nome do Funcionário']}** — {row['Tipo de Registro']} em **{data_fmt}** às **{str(row['Hora'])[:5]}** *(Obs: {row.get('Observação', 'Nenhuma')})*")
                    st.divider()
            else:
                st.info("Histórico vazio.")

        with aba_manutencao:
            st.warning("⚠️ Atenção: Esta ação apaga todos os registros de ponto do mês na planilha.")
            if st.button("Limpar Batidas de Ponto do Mês", key="btn_limpeza"):
                _, sha_ponto = ler_github(ARQUIVO_PONTO)
                vazio = pd.DataFrame(columns=["Matrícula", "Nome do Funcionário", "Data", "Dia da Semana", "Hora", "Tipo de Registro", "Observação", "Caminho da Foto"])
                if salvar_github(vazio, ARQUIVO_PONTO, sha_ponto, "Limpeza Mensal"):
                    st.success("📦 Pontos limpos com sucesso!")
                    st.rerun()
# [final da folha 5 de 5]

#=======================================================================================================================================================
