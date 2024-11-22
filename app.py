import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# Critérios configuráveis para avaliação
CRITERIA = {
    "PCS (kcal/kg)": {"green_min": 5800, "yellow_min": 5701, "red_max": 5700},
    "PCI (kcal/kg)": {"green_min": 5700, "yellow_min": 5601, "red_max": 5600},
    "% Cinzas": {"green_max": 9, "yellow_max": 9.9, "red_min": 10},
    "% Umidade": {"green_max": 16, "yellow_max": 16.9, "red_min": 17},
    "% Enxofre": {"green_max": 0.6, "yellow_max": 0.69, "red_min": 0.7},
}

# Tabelas de custos adicionais devido ao enxofre e cinzas (em USD/t)
SULFUR_COST_TABLE = {
    0.61: 4.97, 0.62: 5.01, 0.63: 5.05, 0.64: 5.14,
    0.65: 5.24, 0.66: 5.33, 0.67: 5.39, 0.68: 5.45, 0.69: 5.47,
}
ASH_COST_TABLE = {
    9.1: 10.54, 9.2: 21.08, 9.3: 31.62, 9.4: 42.15, 9.5: 52.69,
    9.6: 63.23, 9.7: 73.77, 9.8: 84.31, 9.9: 94.85, 10.0: 105.38,
}

# Função para determinar o aumento recomendado no PCS com base na umidade
def get_pcs_adjustment(humidity):
    if humidity <= 16:
        return 0
    adjustment = (humidity - 16) * 2  # Cada 1% acima de 16 aumenta o PCS necessário em 2%
    return round(adjustment, 2)

# Função para avaliar o carvão com base nos critérios configuráveis
def evaluate_coal(data):
    def evaluate(row):
        reasons_below = []  # Parâmetros abaixo do ideal
        reasons_above = []  # Parâmetros acima do ideal
        status = "Verde"
        sulfur_cost = None
        ash_cost = None
        pcs_adjustment = None

        # Avaliação de PCS
        if row["PCS (kcal/kg)"] < CRITERIA["PCS (kcal/kg)"]["red_max"]:
            status = "Vermelho"
            reasons_below.append("PCS")
        elif row["PCS (kcal/kg)"] < CRITERIA["PCS (kcal/kg)"]["green_min"]:
            if status == "Verde":
                status = "Amarelo"
            reasons_below.append("PCS")

        # Avaliação de PCI
        if row["PCI (kcal/kg)"] < CRITERIA["PCI (kcal/kg)"]["red_max"]:
            status = "Vermelho"
            reasons_below.append("PCI")
        elif row["PCI (kcal/kg)"] < CRITERIA["PCI (kcal/kg)"]["green_min"]:
            if status == "Verde":
                status = "Amarelo"
            reasons_below.append("PCI")

        # Avaliação de Cinzas
        if row["% Cinzas"] > CRITERIA["% Cinzas"]["red_min"]:
            status = "Vermelho"
            reasons_above.append("Cinzas")
        elif row["% Cinzas"] > CRITERIA["% Cinzas"]["green_max"]:
            if status == "Verde":
                status = "Amarelo"
            reasons_above.append("Cinzas")
            rounded_ash = round(row["% Cinzas"], 1)
            if rounded_ash in ASH_COST_TABLE:
                ash_cost = ASH_COST_TABLE[rounded_ash]

        # Avaliação de Umidade
        if row["% Umidade"] > CRITERIA["% Umidade"]["red_min"]:
            status = "Vermelho"
            reasons_above.append("Umidade")
            pcs_adjustment = get_pcs_adjustment(row["% Umidade"])
        elif row["% Umidade"] > CRITERIA["% Umidade"]["green_max"]:
            if status == "Verde":
                status = "Amarelo"
            reasons_above.append("Umidade")
            pcs_adjustment = get_pcs_adjustment(row["% Umidade"])

        # Avaliação de Enxofre
        if row["% Enxofre"] > CRITERIA["% Enxofre"]["red_min"]:
            status = "Vermelho"
            reasons_above.append("Enxofre")
        elif row["% Enxofre"] > CRITERIA["% Enxofre"]["green_max"]:
            if status == "Verde":
                status = "Amarelo"
            reasons_above.append("Enxofre")
            rounded_sulfur = round(row["% Enxofre"], 2)
            if rounded_sulfur in SULFUR_COST_TABLE:
                sulfur_cost = SULFUR_COST_TABLE[rounded_sulfur]

        # Construir justificativa otimizada
        reasons_text = []
        if reasons_below:
            reasons_text.append(f"{', '.join(reasons_below)} abaixo do ideal")
        if reasons_above:
            reasons_text.append(f"{', '.join(reasons_above)} acima do ideal")
        justification = (
            "; ".join(reasons_text)
            + ", podendo ser aceito sob determinadas condições. Contate a área técnica"
            if reasons_text
            else "Parâmetros dentro dos limites ideais."
        )

        return (
            status,
            justification,
            sulfur_cost,
            ash_cost,
            pcs_adjustment,
        )

    # Avaliar cada registro no DataFrame
    df = pd.DataFrame(data, index=[0])
    df["Viabilidade"], df["Justificativa"], df["Custo Enxofre (USD/t)"], df["Custo Cinzas (USD/t)"], df["Ajuste PCS (%)"] = zip(*df.apply(evaluate, axis=1))
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
pcs = st.number_input("PCS (kcal/kg)", min_value=0.0, step=100.0, value=5750.0)
pci = st.number_input("PCI (kcal/kg)", min_value=0.0, step=100.0, value=5620.0)
cinzas = st.number_input("% Cinzas", min_value=0.0, max_value=100.0, step=0.1, value=9.2)
umidade = st.number_input("% Umidade", min_value=0.0, max_value=100.0, step=0.1, value=16.5)
enxofre = st.number_input("% Enxofre", min_value=0.0, max_value=10.0, step=0.01, value=0.68)

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
