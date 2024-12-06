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
    "% Enxofre": {"green_max": 0.6, "yellow_min": 0.69, "red_min": 0.85},
}

# Função para calcular o custo adicional por umidade excedente
def calculate_moisture_cost(pcs, humidity):
    base_humidity = 16
    if humidity <= base_humidity:
        return 0
    excess_humidity = humidity - base_humidity
    cost = max(0, (pcs - 5700) / 100) * excess_humidity * 0.2
    return round(cost, 2)

# Função para calcular o custo adicional por cinzas excedentes
def calculate_ash_cost(ash):
    if ash <= 9:
        return 0
    excess_ash = ash - 9
    cost = 10 + (excess_ash * 10)
    return round(cost, 2)

# Função para calcular o custo adicional por enxofre excedente
def calculate_sulfur_cost(sulfur):
    if sulfur <= 0.6:
        return 0
    excess_sulfur = sulfur - 0.6
    cost = 5 + (excess_sulfur * 15)
    return round(cost, 2)

# Função para avaliar o carvão
def evaluate_coal(data):
    def evaluate(row):
        reasons_red = []  # Parâmetros na zona vermelha
        reasons_yellow = []  # Parâmetros na zona amarela
        status = "Verde"
        ash_cost = calculate_ash_cost(row["% Cinzas"])
        sulfur_cost = calculate_sulfur_cost(row["% Enxofre"])
        moisture_cost = calculate_moisture_cost(row["PCS (kcal/kg)"], row["% Umidade"])

        # Avaliação de PCS
        if row["PCS (kcal/kg)"] < CRITERIA["PCS (kcal/kg)"]["red_max"]:
            status = "Vermelho"
            reasons_red.append("PCS")
        elif row["PCS (kcal/kg)"] < CRITERIA["PCS (kcal/kg)"]["green_min"]:
            if status == "Verde":
                status = "Amarelo"
            reasons_yellow.append("PCS")

        # Avaliação de PCI
        if row["PCI (kcal/kg)"] < CRITERIA["PCI (kcal/kg)"]["red_max"]:
            status = "Vermelho"
            reasons_red.append("PCI")
        elif row["PCI (kcal/kg)"] < CRITERIA["PCI (kcal/kg)"]["green_min"]:
            if status == "Verde":
                status = "Amarelo"
            reasons_yellow.append("PCI")

        # Avaliação de Cinzas
        if row["% Cinzas"] >= CRITERIA["% Cinzas"]["red_min"]:
            status = "Vermelho"
            reasons_red.append("Cinzas")
        elif row["% Cinzas"] > CRITERIA["% Cinzas"]["green_max"]:
            if status == "Verde":
                status = "Amarelo"
            reasons_yellow.append("Cinzas")

        # Avaliação de Umidade
        if row["% Umidade"] >= CRITERIA["% Umidade"]["red_min"]:
            status = "Vermelho"
            reasons_red.append("Umidade")
        elif row["% Umidade"] > CRITERIA["% Umidade"]["green_max"]:
            if status == "Verde":
                status = "Amarelo"
            reasons_yellow.append("Umidade")

        # Avaliação de Enxofre
        if row["% Enxofre"] >= CRITERIA["% Enxofre"]["red_min"]:
            status = "Vermelho"
            reasons_red.append("Enxofre")
        elif row["% Enxofre"] > CRITERIA["% Enxofre"]["green_max"]:
            if status == "Verde":
                status = "Amarelo"
            reasons_yellow.append("Enxofre")

        justification = (
            f"Carvão com o(s) parâmetro(s) {', '.join(reasons_red + reasons_yellow)} acima dos limites ideais."
            if reasons_red or reasons_yellow
            else "Todos os parâmetros estão dentro dos limites ideais."
        )

        return status, justification, ash_cost, sulfur_cost, moisture_cost

    # Avaliar os registros
    df = pd.DataFrame(data, index=[0])
    df["Viabilidade"], df["Justificativa"], df["Custo Cinzas (USD/t)"], df["Custo Enxofre (USD/t)"], df["Custo Umidade (USD/t)"] = zip(*df.apply(evaluate, axis=1))
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

    ash_cost = df["Custo Cinzas (USD/t)"].iloc[0]
    sulfur_cost = df["Custo Enxofre (USD/t)"].iloc[0]
    moisture_cost = df["Custo Umidade (USD/t)"].iloc[0]

    st.write(f"Custo adicional devido às cinzas: {ash_cost:.2f} USD/t")
    st.write(f"Custo adicional devido ao enxofre: {sulfur_cost:.2f} USD/t")
    st.write(f"Custo adicional devido à umidade: {moisture_cost:.2f} USD/t")
    total_cost = ash_cost + sulfur_cost + moisture_cost
    st.write(f"**Custo Total Adicional:** {total_cost:.2f} USD/t")

# Frase no rodapé
st.markdown("---")
st.markdown("<p style='text-align: center;'>Esta análise é baseada nos critérios de referência do carvão de performance.</p>", unsafe_allow_html=True)
