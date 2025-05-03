import streamlit as st
import pandas as pd
import base64
import os
from PIL import Image
import pytesseract
import re
import requests
import google.generativeai as genai
import psycopg2
from io import BytesIO
from dotenv import load_dotenv
import plotly.express as px

# Carregar variáveis de ambiente
load_dotenv()

# Configurar caminho do Tesseract no Windows
pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

# Definir as credenciais da Twitch e Gemini
CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")
REDIRECT_URI = os.getenv("TWITCH_REDIRECT_URI")
GENAI_API_KEY = os.getenv("GENAI_API_KEY")
genai.configure(api_key=GENAI_API_KEY)

# Conexão com o banco de dados PostgreSQL
def connect_db():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )
        return conn
    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        return None

def fetch_all_data_from_db():
    conn = connect_db()
    if conn:
        cur = conn.cursor()
        query = "SELECT * FROM esports_fans ORDER BY nome"
        cur.execute(query)
        rows = cur.fetchall()
        colnames = [desc[0] for desc in cur.description]
        df = pd.DataFrame(rows, columns=colnames)
        cur.close()
        conn.close()
        return df
    return pd.DataFrame()

def analisar_com_gemini(prompt):
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Erro ao chamar Gemini: {e}"

def categorizar_canais(canais):
    if not canais:
        return []

    prompt = f"""
    Com base na seguinte lista de streamers seguidos na Twitch:
    {', '.join(canais)}

    Classifique os interesses do usuário em categorias de games, como:
    - FPS
    - MOBA
    - Battle Royale
    - Estratégia
    - Variedade
    - eSports Teams
    - Outros (caso aplicável)

    Responda apenas com uma lista simples e separada por vírgulas contendo as categorias identificadas, evite usar termos como variedades ou outros.
    Não inclua explicações ou justificativas, apenas as categorias, tente analisar cada seguidor.
    """

    resposta = analisar_com_gemini(prompt)
    categorias = [cat.strip() for cat in resposta.split(",") if cat.strip()]
    return categorias

def validar_links_com_ia(links_texto):
    links = [l.strip() for l in links_texto.strip().splitlines() if l.strip()]
    if not links:
        return "Nenhum link informado."

    prompt = f"""
    Você é um especialista em e-sports. Avalie cada link da lista a seguir e identifique **somente** os que pertencem a perfis relacionados diretamente ao cenário competitivo de e-sports. Isso inclui:

    - Jogadores profissionais
    - Organizações e equipes de e-sports
    - Plataformas oficiais como Liquipedia, HLTV, etc.
    - Canais de times ou ligas no Twitch, YouTube, etc.
    - Staff técnico ou figuras públicas reconhecidas no meio competitivo

    **Não inclua** usuários comuns, fãs, streamers casuais ou perfis irrelevantes.

    ### Lista de links:
    {chr(10).join(links)}

    ### Instruções de resposta:
    - Responda apenas com os links relevantes baseados nessa lista de interesses {chr(10).join(interesses)}.
    - Em caso de dúvida, nao classifique o link como relevante.
    - Responda apenas o link seguido de um hífen e a categoria correspondente.
    - Exemplo de resposta: `link - jogador profissional`
    - Para cada link relevante, escreva: `link - categoria (ex: jogador profissional, organização, etc.)`
    - Ignore completamente os que **não** forem relevantes.
    - Se **nenhum link for relevante**, responda exatamente com: `Nenhum link relevante identificado.`
    """

    return analisar_com_gemini(prompt)

def get_access_token(code):
    token_url = "https://id.twitch.tv/oauth2/token"
    token_params = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI
    }
    response = requests.post(token_url, params=token_params)
    return response.json()

def autenticar_com_twitch():
    auth_url = f"https://id.twitch.tv/oauth2/authorize?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=user:read:email+user:read:follows"
    st.markdown(f"[Clique aqui para conectar sua conta Twitch]({auth_url})")

# Sidebar para navegação
page = st.sidebar.selectbox("Navegue pelo app", ["Formulário", "Insights", "Banco de Dados"])

if page == "Formulário":
    st.title("🎮 Know Your Esports Fan - Formulário")

    st.markdown("### Conectar com a Twitch para coletar interesses")

    if "code" in st.query_params:
        code = st.query_params["code"]
        token_data = get_access_token(code)

        if "access_token" in token_data:
            access_token = token_data["access_token"]
            st.success("Conectado com sucesso à Twitch!")

            user_info_resp = requests.get(
                "https://api.twitch.tv/helix/users",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Client-Id": CLIENT_ID
                }
            )
            user_info = user_info_resp.json()
            if "data" in user_info and len(user_info["data"]) > 0:
                user_id = user_info["data"][0]["id"]
                user_login = user_info["data"][0]["login"]
                st.write(f"Usuário conectado: {user_login}")

                follows_resp = requests.get(
                    "https://api.twitch.tv/helix/channels/followed",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Client-Id": CLIENT_ID
                    },
                    params={"user_id": user_id, "first": 40}
                )
                follows_data = follows_resp.json()

                if "data" in follows_data and len(follows_data["data"]) > 0:
                    canais_seguidos = [f["broadcaster_name"] for f in follows_data["data"]]
                    temas_interesses = categorizar_canais(canais_seguidos)
                    temas_formatado = ", ".join(temas_interesses)

                    st.session_state.twitch_interesses = temas_formatado
                    st.session_state.canais_seguidos = canais_seguidos
                else:
                    st.info("Não foram encontrados canais seguidos.")
            else:
                st.error("Não foi possível obter informações do usuário da Twitch.")
        else:
            st.error("Falha na autenticação com a Twitch.")
    else:
        autenticar_com_twitch()

    # Validações
    def validar_nome(nome):
        if not nome:
            return "O nome é obrigatório."
        if len(nome.split()) < 2:
            return "O nome deve conter pelo menos dois nomes."
        return None

    def validar_cpf(cpf):
        if len(cpf) <= 13:
            return "O CPF deve conter 14 dígitos."
        cpf = re.sub(r'\D', '', cpf)
        if cpf == cpf[0] * 11:
            return "CPF inválido."
        def calcular_dv(cpf, pesos):
            soma = sum(int(cpf[i]) * pesos[i] for i in range(len(pesos)))
            resto = soma % 11
            return 0 if resto < 2 else 11 - resto
        pesos1 = [10, 9, 8, 7, 6, 5, 4, 3, 2]
        pesos2 = [11, 10, 9, 8, 7, 6, 5, 4, 3, 2]
        dv1 = calcular_dv(cpf[:9], pesos1)
        dv2 = calcular_dv(cpf[:10], pesos2)
        if int(cpf[9]) != dv1 or int(cpf[10]) != dv2:
            return "CPF inválido."
        return None

    # Formulário
    with st.form("fan_form"):
        col1, col2 = st.columns(2)

        with col1:
            nome = st.text_input("Nome completo")
            nome_erro = validar_nome(nome)
            if nome:
                if nome_erro:
                    st.markdown(f"<span style='color:red'>{nome_erro}</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span style='color:green'>✔ Nome válido</span>", unsafe_allow_html=True)

        with col2:
            cpf = st.text_input("CPF (formato: 111.111.111-11)", max_chars=14)
            cpf_erro = validar_cpf(cpf)
            if cpf:
                if cpf_erro:
                    st.markdown(f"<span style='color:red'>{cpf_erro}</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span style='color:green'>✔ CPF válido</span>", unsafe_allow_html=True)

        endereco = st.text_input("Endereço")
        interesses = st.text_area("Interesses (separados por vírgula)", value=st.session_state.get("twitch_interesses", ""))
        eventos = st.text_area("Eventos que participou em 2024 (separados por vírgula)")
        compras = st.text_area("Compras relacionadas a e-sports em 2024 (separadas por vírgula)")
        links_perfis = st.text_area("Links de perfis relacionados a e-sports (um por linha)")
        arquivo = st.file_uploader("Upload de documento ou imagem", type=["png", "jpg", "jpeg", "pdf"])

        submitted = st.form_submit_button("Enviar")

        if submitted:
            if nome_erro:
                st.warning(f"Erro no nome: {nome_erro}")
            if cpf_erro:
                st.warning(f"Erro no CPF: {cpf_erro}")
            if nome_erro or cpf_erro:
                st.stop()

            # OCR + Validação
            texto_ocr = ""
            cpf_extraido = ""

            if arquivo:
                try:
                    image = Image.open(BytesIO(arquivo.read()))
                    texto_ocr = pytesseract.image_to_string(image)
                    cpf_match = re.search(r'\d{3}\.\d{3}\.\d{3}-\d{2}', texto_ocr)
                    cpf_extraido = cpf_match.group(0) if cpf_match else ""
                except Exception as e:
                    st.warning(f"Erro ao processar OCR: {e}")

            if not cpf_extraido:
                st.warning("CPF não encontrado no documento enviado.")
                st.stop()
            elif cpf != cpf_extraido:
                st.warning(f"O CPF digitado ({cpf}) não corresponde ao CPF da imagem ({cpf_extraido}).")
                st.stop()

            # Gravação no banco
            conn = connect_db()
            if conn:
                cur = conn.cursor()
                resposta_links = validar_links_com_ia(links_perfis)
                cur.execute(
                    """
                    INSERT INTO esports_fans (nome, cpf, endereco, interesses, eventos_2024, compras_2024, temas_detectados, streamers_seguidos, links_validados)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        nome, cpf, endereco, interesses, eventos, compras,
                        st.session_state.get("twitch_interesses", ""),
                        ", ".join(st.session_state.get("canais_seguidos", [])),
                        resposta_links
                    )
                )
                conn.commit()
                cur.close()
                conn.close()

                st.success("🎉 Dados enviados com sucesso!")
                st.balloons()
                st.markdown("#### Resultado da análise dos links fornecidos:")
                st.code(resposta_links)

elif page == "Insights":
    st.title("📊 Seus Insights Personalizados")

    df_all = fetch_all_data_from_db()

    if df_all.empty:
        st.info("Nenhum dado encontrado no banco de dados.")
    else:
        st.subheader("🔎 Métricas Gerais")
        total_usuarios = len(df_all)
        st.metric("Total de fãs cadastrados", total_usuarios)

        #CATEGORIAS DE INTERESSES
        st.subheader("🎮 Categorias de Interesse mais Populares")

        interesses_split = df_all["temas_detectados"].dropna().apply(lambda x: [i.strip() for i in x.split(",")])
        interesses_flat = [i for sublist in interesses_split for i in sublist]

        if interesses_flat:
            interesses_df = pd.DataFrame(interesses_flat, columns=["Categoria"])
            categoria_counts = interesses_df["Categoria"].value_counts().reset_index()
            categoria_counts.columns = ["Categoria", "Quantidade"]

            fig_categorias = px.bar(
                categoria_counts,
                x="Categoria", y="Quantidade",
                labels={"Categoria": "Categoria", "Quantidade": "Quantidade"},
                title="Distribuição de Interesses (classificados com IA)",
                color="Categoria"
            )
            st.plotly_chart(fig_categorias, use_container_width=True)
        else:
            st.info("Nenhum interesse detectado ainda.")

        #EVENTOS PARTICIPADOS
        st.subheader("📅 Eventos mais mencionados (2024)")
        eventos_split = df_all["eventos_2024"].dropna().apply(lambda x: [e.strip() for e in x.split(",")])
        eventos_flat = [e for sublist in eventos_split for e in sublist]

        if eventos_flat:
            eventos_df = pd.DataFrame(eventos_flat, columns=["Evento"])
            fig_eventos = px.pie(
                eventos_df, names="Evento",
                title="Participação em Eventos",
                hole=0.4
            )
            st.plotly_chart(fig_eventos, use_container_width=True)
        else:
            st.info("Nenhum evento registrado.")

        #STREAMERS MAIS SEGUIDOS
        st.subheader("📺 Streamers mais seguidos pelos fãs")
        streamers_split = df_all["streamers_seguidos"].dropna().apply(lambda x: [s.strip() for s in x.split(",")])
        streamers_flat = [s for sublist in streamers_split for s in sublist]

        if streamers_flat:
            streamers_df = pd.DataFrame(streamers_flat, columns=["Streamer"])
            top_streamers = streamers_df["Streamer"].value_counts().head(10).reset_index()
            top_streamers.columns = ["Streamer", "Quantidade"]

            fig_streamers = px.bar(
                top_streamers,
                x="Streamer", y="Quantidade",
                labels={"Streamer": "Streamer", "Quantidade": "Seguidores"},
                title="Top 10 Streamers Seguidos",
                color="Streamer"
            )
            st.plotly_chart(fig_streamers, use_container_width=True)
        else:
            st.info("Nenhum streamer seguido coletado.")

elif page == "Banco de Dados":
    st.title("🗃️ Banco de Dados dos Fãs")
    df_all = fetch_all_data_from_db()
    st.subheader("Dados coletados")
    st.dataframe(df_all, use_container_width=True)

    def convert_df_to_csv(df):
        return df.to_csv(index=False)

    csv_data = convert_df_to_csv(df_all)
    st.download_button("📥 Baixar CSV", data=csv_data, file_name="dados_fans.csv", mime="text/csv")
    st.download_button("📥 Baixar JSON", data=df_all.to_json(orient="records"), file_name="dados_fans.json", mime="application/json")