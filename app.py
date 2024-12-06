import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# Critérios configuráveis para avaliação
CRITERIA = {
    "PCS (kcal/kg)": {"green_min": 5800, "yellow_min": 5701, "red_max": 5300},
    "PCI (kcal/kg)": {"green_min": 5700, "yellow_min": 5601, "red_max": 5200},
    "% Cinzas": {"green_max": 9, "yellow_max": 9.9, "red_min": 12},
    "% Umidade": {"green_max": 16, "yellow_max": 16.9, "red_min": 18},
    "% Enxofre": {"green_max": 0.6, "yellow_min": 0.61, "red_min": 0.85},
}

# Funções de custo para os parâmetros (interpolação/extrapolação)

def custo_umidade(pcs, umidade):
    tabela_umidade = {
        5800: [0, 0.6, 0.7, 0.8, 0.9, 1.0],
        5700: [0, 0.8, 0.92, 1.08, 1.23, 1.38],
    }
    valores_umidade = np.array(tabela_umidade[pcs])
    indices_umidade = np.linspace(16, 17, len(valores_umidade))
    if umidade < 16:
        return 0
    return np.interp(umidade, indices_umidade, valores_umidade)

def custo_cinzas(cinzas):
    tabela_cinzas = {
        9.1: 10.65, 9.2: 20.78, 9.3: 30.36, 9.4: 39.42,
        9.5: 47.94, 9.6: 55.80, 9.7: 63.26, 9.8: 70.05,
        9.9: 76.31, 10.0: 82.04, 10.1: 87.23, 11.0: 108.80,
    }
    pontos = sorted(tabela_cinzas.items())
    valores = np.array(pontos)
    cinzas_ref = valores[:, 0]
    custos = valores[:, 1]
    if cinzas <= 9.0:
        return 0
    return np.interp(cinzas, cinzas_ref, custos)

def custo_enxofre(s):
    tabela_enxofre = {
        0.60: 0, 0.61: 4.97, 0.63: 5.05, 0.66: 5.33,
        0.68: 5.45, 0.69: 5.47,
    }
    pontos = sorted(tabela_enxofre.items())
    valores = np.array(pontos)
    enxofres = valores[:, 0]
    custos = valores[:, 1]
    if s <= enxofres[0]:
        return 0
    return np.interp(s, enxofres, custos)

# Função para avaliar o carvão
def evaluate_coal(data):
    def evaluate(row):
        reasons_below = []  
        reasons_above = []  
        reasons_red = []  
        status = "Verde"
        sulfur_cost = 0
        ash_cost = 0
        moisture_cost = 0
        pcs_adjustment = 0

        # Avaliação de PCS
        if row["PCS (kcal/kg)"] < CRITERIA["PCS (kcal/kg)"]["red_max"]:
            status = "Vermelho"
            reasons_red.append("PCS")
        elif row["PCS (kcal/kg)"] < CRITERIA["PCS (kcal/kg)"]["green_min"]:
            if status == "Verde":
                status = "Amarelo"
            reasons_below.append("PCS")

        # Avaliação de PCI
        if row["PCI (kcal/kg)"] < CRITERIA["PCI (kcal/kg)"]["red_max"]:
            status = "Vermelho"
            reasons_red.append("PCI")
        elif row["PCI (kcal/kg)"] < CRITERIA["PCI (kcal/kg)"]["green_min"]:
            if status == "Verde":
                status = "Amarelo"
            reasons_below.append("PCI")

        # Avaliação de Cinzas
        if row["% Cinzas"] > CRITERIA["% Cinzas"]["red_min"]:
            status = "Vermelho"
            reasons_red.append("Cinzas")
        elif row["% Cinzas"] > CRITERIA["% Cinzas"]["green_max"]:
            if status == "Verde":
                status = "Amarelo"
            reasons_above.append("Cinzas")
            ash_cost = custo_cinzas(row["% Cinzas"])

        # Avaliação de Umidade
        if row["% Umidade"] > CRITERIA["% Umidade"]["red_min"]:
            status = "Vermelho"
            reasons_red.append("Umidade")
        elif row["% Umidade"] > CRITERIA["% Umidade"]["green_max"]:
            if status == "Verde":
                status = "Amarelo"
            reasons_above.append("Umidade")
            moisture_cost = custo_umidade(row["PCS (kcal/kg)"], row["% Umidade"])

        # Avaliação de Enxofre
        if row["% Enxofre"] > CRITERIA["% Enxofre"]["red_min"]:
            status = "Vermelho"
            reasons_red.append("Enxofre")
        elif row["% Enxofre"] > CRITERIA["% Enxofre"]["green_max"]:
            if status == "Verde":
                status = "Amarelo"
            reasons_above.append("Enxofre")
            sulfur_cost = custo_enxofre(row["% Enxofre"])

        total_cost = sulfur_cost + ash_cost + moisture_cost
        justification = (
            f"Carvão com restrições técnicas: {', '.join(reasons_above)} "
            if reasons_above
            else "Parâmetros dentro dos limites ideais."
        )

        return status, justification, moisture_cost, ash_cost, sulfur_cost, total_cost

    df = pd.DataFrame(data, index=[0])
    df["Viabilidade"], df["Justificativa"], df["Custo por Umidade"], df["Custo por Cinzas"], df["Custo por Enxofre"], df["Custo Total Adicional"] = zip(*df.apply(evaluate, axis=1))
    return df

# Interface do Streamlit
st.image("https://energiapecem.com/images/logo-principal-sha.svg", caption="Energia Pecém", use_container_width=True)
st.markdown("<h1 style='text-align: center;'>Simulação de Viabilidade do Carvão Mineral</h1>", unsafe_allow_html=True)

# Inputs
pcs = st.number_input("PCS (kcal/kg)", min_value=5700, step=10, value=5800)
pci = st.number_input("PCI (kcal/kg)", min_value=5200, step=10, value=5700)
cinzas = st.number_input("% Cinzas", min_value=8.0, max_value=12.0, step=0.1, value=9.0)
umidade = st.number_input("% Umidade", min_value=15.0, max_value=20.0, step=0.1, value=16.5)
enxofre = st.number_input("% Enxofre", min_value=0.5, max_value=1.0, step=0.01, value=0.61)

if st.button("Rodar Simulação"):
    data = {
        "PCS (kcal/kg)": pcs,
        "PCI (kcal/kg)": pci,
        "% Cinzas": cinzas,
        "% Umidade": umidade,
        "% Enxofre": enxofre,
    }
    df = evaluate_coal(data)

    st.write(f"**Viabilidade:** {df['Viabilidade'].iloc[0]}")
    st.write(f"**Justificativa:** {df['Justificativa'].iloc[0]}")
    st.write(f"**Custo Total Adicional (USD/t):** {df['Custo Total Adicional'].iloc[0]:.2f}")
    st.write(f"Custo por Umidade (USD/t): {df['Custo por Umidade'].iloc[0]:.2f}")
    st.write(f"Custo por Cinzas (USD/t): {df['Custo por Cinzas'].iloc[0]:.2f}")
    st.write(f"Custo por Enxofre (USD/t): {df['Custo por Enxofre'].iloc[0]:.2f}")
