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
    "% Enxofre": {"green_max": 0.6, "yellow_max": 0.69, "red_min": 0.85},
}

# Funções para calcular custos adicionais
def calculate_moisture_cost(pcs, moisture):
    if moisture <= 16:
        return 0
    adjustment = max(0, (moisture - 16) * 2)  # Extrapolação linear
    return round(adjustment * pcs / 1000, 2)  # Ajuste proporcional ao PCS

def calculate_ash_cost(ash):
    if ash <= 9:
        return 0
    excess = max(0, ash - 9)
    return round(10 * excess, 2)  # Exemplo de função linear para extrapolação

def calculate_sulfur_cost(sulfur):
    if sulfur <= 0.6:
        return 0
    excess = max(0, sulfur - 0.6)
    return round(50 * excess, 2)  # Exemplo de função linear para extrapolação

# Função para avaliar o carvão com base nos critérios configuráveis
def evaluate_coal(data):
    def evaluate(row):
        reasons_red = []  # Parâmetros na zona vermelha
        reasons_yellow = []  # Parâmetros na zona amarela
        status = "Verde"

        # Custos individuais
        moisture_cost = calculate_moisture_cost(row["PCS (kcal/kg)"], row["% Umidade"])
        ash_cost = calculate_ash_cost(row["% Cinzas"])
        sulfur_cost = calculate_sulfur_cost(row["% Enxofre"])
        total_cost = moisture_cost + ash_cost + sulfur_cost

        # Avaliação de PCS
        if row["PCS (kcal/kg)"] < CRITERIA["PCS (kcal/kg)"]["red_max"]:
            status = "Vermelho"
            reasons_red.append("PCS")
        elif row["PCS (kcal/kg)"] < CRITERIA["PCS (kcal/kg)"]["yellow_min"]:
            status = "Amarelo"
            reasons_yellow.append("PCS")

        # Avaliação de PCI
        if row["PCI (kcal/kg)"] < CRITERIA["PCI (kcal/kg)"]["red_max"]:
            status = "Vermelho"
            reasons_red.append("PCI")
        elif row["PCI (kcal/kg)"] < CRITERIA["PCI (kcal/kg)"]["yellow_min"]:
            status = "Amarelo"
            reasons_yellow.append("PCI")

        # Avaliação de Cinzas
        if row["% Cinzas"] > CRITERIA["% Cinzas"]["red_min"]:
            status = "Vermelho"
            reasons_red.append("Cinzas")
        elif row["% Cinzas"] > CRITERIA["% Cinzas"]["green_max"]:
            status = "Amarelo"
            reasons_yellow.append("Cinzas")

        # Avaliação de Umidade
        if row["% Umidade"] > CRITERIA["% Umidade"]["red_min"]:
            status = "Vermelho"
            reasons_red.append("Umidade")
        elif row["% Umidade"] > CRITERIA["% Umidade"]["green_max"]:
            status = "Amarelo"
            reasons_yellow.append("Umidade")

        # Avaliação de Enxofre
        if row["% Enxofre"] > CRITERIA["% Enxofre"]["red_min"]:
            status = "Vermelho"
            reasons_red.append("Enxofre")
        elif row["% Enxofre"] > CRITERIA["% Enxofre"]["green_max"]:
            status = "Amarelo"
            reasons_yellow.append("Enxofre")

        # Construir justificativa
        if reasons_red:
            justification = (
                f"Carvão com o(s) parâmetro(s) {', '.join(reasons_red)} fora do limite especificado, "
                f"não sendo recomendada a sua aquisição."
            )
        else:
            reasons_text = []
            if reasons_yellow:
                reasons_text.append(f"{', '.join(reasons_yellow)} na zona amarela")
            justification = (
                "; ".join(reasons_text)
                + ", podendo ser aceito sob determinadas condições. Contate a área técnica."
                if reasons_text
                else "Parâmetros dentro dos limites ideais."
            )

        return status, justification, total_cost, moisture_cost, ash_cost, sulfur_cost

    df = pd.DataFrame(data, index=[0])
    df["Viabilidade"], df["Justificativa"], df["Custo Total Adicional (USD/t)"], df["Custo Umidade (USD/t)"], df["Custo Cinzas (USD/t)"], df["Custo Enxofre (USD/t)"] = zip(*df.apply(evaluate, axis=1))
    return df

# Interface do Streamlit
st.image("https://energiapecem.com/images/logo-principal-sha.svg", caption="Energia Pecém", use_container_width=True)
st.markdown(
    """
    <h1 style='text-align: center;'>Simulação de Viabilidade do Carvão Mineral</h1>
    """,
    unsafe_allow_html=True,
)

# Inputs
pcs = st.number_input("PCS (kcal/kg)", min_value=0.0, step=100.0, value=5800.0)
pci = st.number_input("PCI (kcal/kg)", min_value=0.0, step=100.0, value=5700.0)
cinzas = st.number_input("% Cinzas", min_value=0.0, max_value=100.0, step=0.1, value=9.0)
umidade = st.number_input("% Umidade", min_value=0.0, max_value=100.0, step=0.1, value=16.0)
enxofre = st.number_input("% Enxofre", min_value=0.0, max_value=10.0, step=0.01, value=0.60)

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
    st.write(f"**Custo Total Adicional (USD/t):** {df['Custo Total Adicional (USD/t)'].iloc[0]:.2f}")
    st.write(f"**Custo por Umidade (USD/t):** {df['Custo Umidade (USD/t)'].iloc[0]:.2f}")
    st.write(f"**Custo por Cinzas (USD/t):** {df['Custo Cinzas (USD/t)'].iloc[0]:.2f}")
    st.write(f"**Custo por Enxofre (USD/t):** {df['Custo Enxofre (USD/t)'].iloc[0]:.2f}")

# Frase no rodapé
st.markdown("---")
st.markdown(
    "<p style='text-align: center;'>Esta análise é baseada nos critérios de referência do carvão de performance.</p>",
    unsafe_allow_html=True,
)
