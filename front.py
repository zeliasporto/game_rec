import streamlit as st
import requests
import joblib

st.title("Quiz de Recomendação de Jogos")

# === Perguntas base ===
idade = st.slider("Qual a sua idade?", 10, 80, 25)

# Gênero
genero = st.radio("Qual o seu gênero?", ["Feminino", "Masculino", "Outro"])
genero_map = {
    "Feminino": "Female",
    "Masculino": "Male",
    "Outro": "Outro"
}

# Frequência
frequencia = st.selectbox("Com que frequência você joga?", [
    "Raramente", "Algumas vezes por semana", "Quase todo dia", "Todos os dias"])
frequencia_map = {
    "Raramente": 0,
    "Algumas vezes por semana": 1,
    "Quase todo dia": 2,
    "Todos os dias": 3
}

# Modo de jogo preferido
modo = st.selectbox("Qual modo você prefere?", ["Single-player", "Multiplayer", "Ambos"])
modo_map = {
    "Single-player": "Single-player",
    "Multiplayer": "Multiplayer",
    "Ambos": "Both"
}

# Dispositivos
dispositivos = {
    "PC": "PC", "Console": "Console", "PlayStation": "Console (PlayStation",
    "Nintendo Switch": "Handheld devices (Nintendo Switch",
    "Mobile": "Mobile", "Tablet": "Tablet", "Xbox": "Xbox", "Outro": "etc.)"
}
dispositivo_uso = st.multiselect("Quais dispositivos você usa para jogar?", list(dispositivos.keys()))

# Métodos de descoberta
formas_descoberta_pt = {
    "Recomendações de amigos/família": "Friends/Family Recommendations",
    "Blogs/revisões de jogos": "Game Reviews/Blogs",
    "Fóruns de jogos": "Gaming Forums",
    "Procuro por conta própria na loja de apps": "I search myself from playstore",
    "Redes sociais": "Social Media",
    "YouTube/Streaming (Twitch)": "YouTube/Streaming platforms (Twitch",
    "Outro (etc.)": "etc.)",
    "Meus próprios métodos": "my own ways!!!"
}
formas_descoberta = st.multiselect("Como você descobre novos jogos?", list(formas_descoberta_pt.keys()))

# Motivações
motivos_pt = {
    "Diversão/entretenimento": "For fun/entertainment",
    "Se não houver outra coisa melhor para fazer": "If no other better work",
    "Melhorar habilidades/competição": "To improve skills/competition",
    "Aliviar o estresse": "To relieve stress",
    "Socializar": "To socialize",
    "Jogar com amigos": "To socialize with friends",
    "Outro (etc.)": "etc",
    "Aprender como o jogo foi feito": "learning how it's designed"
}
motivos = st.multiselect("Por que você joga videogames?", list(motivos_pt.keys()))

# Nome do jogo favorito
jogo_favorito = st.text_input("Digite o nome de um jogo que você gosta muito:")

colunas_modelo = joblib.load("colunas_modelo.pkl")

def encode_respostas_alinhado():
    base = {}

    base["age"] = idade
    base["age_normalized"] = idade / 100

    base["frequency_num"] = frequencia_map[frequencia]

    # Gênero
    genero_en = genero_map[genero]
    base["gender_Female"] = int(genero_en == "Female")
    base["gender_Male"] = int(genero_en == "Male")
    base["gender_male"] = int(genero_en.lower() == "male")

    # Dispositivos
    for label, key in dispositivos.items():
        base[f"device_{key}"] = int(label in dispositivo_uso)

    # Modo de jogo
    for m in ["Single-player", "Multiplayer", "Both"]:
        base[f"preference_mode_{m}"] = int(m == modo_map[modo])

    # Descoberta
    for label, val in formas_descoberta_pt.items():
        base[f"discovery_methods_{val}"] = int(label in formas_descoberta)

    # Motivações
    for label, val in motivos_pt.items():
        base[f"motivation_{val}"] = int(label in motivos)

    # Gera vetor na ordem das colunas
    return [base.get(c, 0) for c in colunas_modelo]

# === Botão de envio ===
if st.button("Recomendar Jogos"):
    respostas = encode_respostas_alinhado()
    payload = {
        "respostas": respostas,
        "jogo_favorito": jogo_favorito
    }
    try:
        r = requests.post("http://localhost:8000/recomendar", json=payload)
        recomendacoes = r.json()

        st.subheader("Top 5 jogos recomendados:")
        for jogo in recomendacoes:
            st.markdown(f"**{jogo['name']}** (AppID: {jogo['appid']}) - Similaridade: {jogo['similaridade']:.2f}")
    except Exception as e:
        st.error(f"Erro ao conectar com a API: {e}")
