# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import pandas as pd
import numpy as np
import joblib
from sklearn.metrics.pairwise import cosine_similarity

app = FastAPI()

# Carregar modelo treinado e colunas
modelo = joblib.load("modelo_recomendador.pkl")
colunas_X = joblib.load("colunas_modelo.pkl")

# Carregar dataset de jogos
# preprocessamento.py
import pandas as pd

# Tratamento...
df_jogadores_final = pd.read_csv("jogadores_tratado.csv")  # ou qualquer origem
df_jogos = pd.read_json("jogos_tratado.json")

# Mapeamentos
genero_cols = joblib.load("genero_cols.pkl")
col_map = {
    'Action/Adventure': ['genre_Action', 'genre_Adventure'],
    'First-Person Shooter (FPS)': ['genre_Action'],
    'MMO (Massively Multiplayer Online)': ['genre_Massively Multiplayer'],
    'Puzzle/Strategy': ['genre_Strategy'],
    'Role-Playing Games (RPG)': ['genre_RPG'],
    'Simulation (e.g.': ['genre_Simulation', 'genre_Simuladores'],
    'Sports': ['genre_Sports'],
    'The Sims)': ['genre_Simulation']
}
genero_map = {
    'Action': 'Action/Adventure', 'Adventure': 'Action/Adventure', 'RPG': 'Role-Playing Games (RPG)',
    'Simulation': 'Simulation (e.g.', 'Strategy': 'Puzzle/Strategy', 'Puzzle': 'Puzzle/Strategy',
    'Sports': 'Sports', 'MMO': 'MMO (Massively Multiplayer Online)', 'Shooter': 'First-Person Shooter (FPS)'
}

class JogadorInput(BaseModel):
    respostas: List[float]
    jogo_favorito: str

def extrair_generos_do_favorito(nome, df_jogos):
    nome = str(nome).strip().lower()
    for _, row in df_jogos.iterrows():
        if nome in str(row['name']).lower():
            return set(row['genres']) if isinstance(row['genres'], list) else set()
    return set()

@app.post("/recomendar")
def recomendar_jogos(data: JogadorInput):
    jogador_input = pd.DataFrame([data.respostas], columns=colunas_X)
    y_pred_proba = modelo.predict_proba(jogador_input)
    y_pred_score = np.array([p[:, 1] for p in y_pred_proba]).flatten()
    vetor_pred = pd.Series(y_pred_score, index=genero_cols)

    generos_favorito = extrair_generos_do_favorito(data.jogo_favorito, df_jogos)
    for g in generos_favorito:
        mapped = genero_map.get(g)
        if mapped in vetor_pred:
            vetor_pred[mapped] = 1.0

    vetor_jogador_final = pd.Series(0, index=[col for sublist in col_map.values() for col in sublist])
    for genero, cols in col_map.items():
        if vetor_pred.get(genero, 0) > 0.5:
            for col in cols:
                vetor_jogador_final[col] = 1

    colunas_comparadas = vetor_jogador_final.index.tolist()
    df_jogos_validos = df_jogos[df_jogos[colunas_comparadas].sum(axis=1) > 0]
    matriz_jogos = df_jogos_validos[colunas_comparadas].values
    sim = cosine_similarity([vetor_jogador_final.values], matriz_jogos)[0]

    top_idxs = sim.argsort()[::-1][:5]
    top_recomendados = df_jogos_validos.iloc[top_idxs][['name', 'appid']].copy()
    top_recomendados['similaridade'] = sim[top_idxs]
    top_recomendados.reset_index(drop=True, inplace=True)

    return top_recomendados.to_dict(orient="records")
