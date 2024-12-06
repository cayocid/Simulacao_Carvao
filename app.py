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
    "% Enxofre": {"green_max": 0.6, "yellow_max": 0.69, "red_max": 0.85},
}

# Função para calcular custo adicional por umidade
def calculate_moisture_cost_table(pcs, humidity):
    # Tabela de referência
    table = {
        5700: [0, 0.11, 0.22, 0.32, 0.43, 0.54, 0.92, 1.08, 1.23, 1.38, 1.54],
        5710: [0, 0, 0.09, 0.2, 0.3, 0.41, 0.86, 1.01, 1.17, 1.32, 1.47],
        5720: [0, 0, 0, 0.07, 0.18, 0.29, 0.8, 0.95, 1.1, 1.26, 1.41],
        5730: [0, 0, 0, 0, 0.05, 0.16, 0.73, 0.89, 1.04, 1.2, 1.35],
        5740: [0, 0, 0, 0, 0, 0.03, 0.67, 0.82, 0.98, 1.13, 1.29],
        5750: [0, 0, 0, 0, 0, 0, 0.61, 0.76, 0.92, 1.07, 1.22],
        5760: [0, 0, 0, 0, 0, 0, 0.6, 0.7, 0.85, 1.01, 1.16],
        5770: [0, 0, 0, 0, 0, 0, 0.6, 0.7, 0.8, 0.94, 1.1],
        5780: [0, 0, 0, 0, 0, 0, 0.6, 0.7, 0.8, 0.9, 1.03],
        5790: [0, 0, 0, 0, 0, 0, 0.6, 0.7, 0.8, 0.9, 1.0],
        5800: [0, 0, 0, 0, 0, 0, 0.6, 0.7, 0.8, 0.9, 1.0],
    }
    humidities = [16.0, 16.1, 16.2, 16.3, 16.4, 16.5, 16.6, 16.7, 16.8, 16.9, 17.0]
    
    # Verificar limites da tabela
    if pcs < 5700 or pcs > 5800 or humidity < 16 or humidity > 17:
        return 0  # Fora dos limites da tabela

    # Interpolação nos limites do PCS
    pcs_keys = sorted(table.keys())
    for i in range(len(pcs_keys) - 1):
        if pcs_keys[i] <= pcs <= pcs_keys[i + 1]:
            pcs_low, pcs_high = pcs_keys[i], pcs_keys[i + 1]
            costs_low = table[pcs_low]
            costs_high = table[pcs_high]
            break
    else:
        return 0

    # Interpolação para os custos com base no PCS
    interpolated_costs = [
        np.interp(pcs, [pcs_low, pcs_high], [costs_low[j], costs_high[j]])
        for j in range(len(humidities))
    ]

    # Interpolação para o custo final com base na umidade
    final_cost = np.interp(humidity, humidities, interpolated_costs)
    return round(final_cost, 2)

# Função para avaliar o carvão com base nos critérios configuráveis
def evaluate_coal(data):
    def evaluate(row):
        status = "Verde"
        reasons_red = []
        total_cost = 0

        # Avaliação de PCS
        if row["PCS (kcal/kg)"] < CRITERIA["PCS (kcal/kg)"]["red_max"]:
            status = "Vermelho"
            reasons_red.append("PCS")

        # Avaliação de PCI
        if row["PCI (kcal/kg)"] < CRITERIA["PCI (kcal/kg)"]["red_max"]:
            status = "Vermelho"
            reasons_red.append("PCI")

        # Avaliação de Cinzas
        if row["% Cinzas"] > CRITERIA["% Cinzas"]["red_min"]:
            status = "Vermelho"
            reasons_red.append("Cinzas")
            # Calcular custo com base na função para cinzas

        # Avaliação de Umidade
        if row["% Umidade"] > CRITERIA["% Umidade"]["red_min"]:
            status = "Vermelho"
            reasons_red.append("Umidade")
            total_cost += calculate_moisture_cost_table(row["PCS (kcal/kg)"], row["% Umidade"])

        # Avaliação de Enxofre
        if row["% Enxofre"] > CRITERIA["% Enxofre"]["red_min"]:
            status = "Vermelho"
            reasons_red.append("Enxofre")

        # Construção da justificativa
        justification = (
            f"Carvão com o(s) parâmetro(s) {', '.join(reasons_red)} fora do limite especificado, "
            "não sendo recomendada a sua aquisição."
            if reasons_red
            else "Parâmetros dentro dos limites ideais."
        )

        return status, justification, total_cost

    df = pd.DataFrame(data, index=[0])
    df["Viabilidade"], df["Justificativa"], df["Custo Total Adicional"] = zip(*df.apply(evaluate, axis=1))
    return df

# Interface do Streamlit
st.title("Simulação de Viabilidade do Carvão Mineral")

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
    st.write(f"**Custo Total Adicional:** {df['Custo Total Adicional'].iloc[0]:.2f} USD/t")
