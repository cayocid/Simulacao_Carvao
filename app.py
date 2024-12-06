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

# Dados da tabela de custo de enxofre
SULFUR_COST_DATA = {
    0.60: 0,
    0.61: 4.97,
    0.63: 5.05,
    0.66: 5.33,
    0.68: 5.45,
    0.69: 5.47,
}

# Função para calcular o custo adicional do enxofre
def custo_enxofre(s):
    # Ordenar os pontos da tabela
    pontos = sorted(SULFUR_COST_DATA.items())
    valores = np.array(pontos)
    enxofres = valores[:, 0]
    custos = valores[:, 1]
    
    # Se o valor de enxofre for menor ou igual ao limite mínimo
    if s <= enxofres[0]:
        return 0

    # Interpolação linear
    if enxofres[0] < s <= enxofres[-1]:
        return np.interp(s, enxofres, custos)

    # Extrapolação linear acima do maior ponto da tabela
    if s > enxofres[-1]:
        taxa = (custos[-1] - custos[-2]) / (enxofres[-1] - enxofres[-2])
        return custos[-1] + (s - enxofres[-1]) * taxa

# Função para avaliar o carvão com base nos critérios configuráveis
def evaluate_coal(data):
    def evaluate(row):
        reasons_below = []  # Parâmetros abaixo do ideal
        reasons_above = []  # Parâmetros acima do ideal
        reasons_red = []  # Parâmetros na zona vermelha
        status = "Verde"
        sulfur_cost = None
        ash_cost = None
        pcs_adjustment = None

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

        # Avaliação de Umidade
        if row["% Umidade"] > CRITERIA["% Umidade"]["red_min"]:
            status = "Vermelho"
            reasons_red.append("Umidade")
        elif row["% Umidade"] > CRITERIA["% Umidade"]["green_max"]:
            if status == "Verde":
                status = "Amarelo"
            reasons_above.append("Umidade")

        # Avaliação de Enxofre
        if row["% Enxofre"] > CRITERIA["% Enxofre"]["red_min"]:
            status = "Vermelho"
            reasons_red.append("Enxofre")
        elif row["% Enxofre"] > CRITERIA["% Enxofre"]["green_max"]:
            if status == "Verde":
                status = "Amarelo"
            reasons_above.append("Enxofre")
            sulfur_cost = custo_enxofre(row["% Enxofre"])

        # Construir justificativa
        if reasons_red:
            justification = (
                f"Carvão com o(s) parâmetro(s) {', '.join(reasons_red)} fora do limite especificado, "
                f"não sendo recomendada a sua aquisição."
            )
        else:
            reasons_text = []
            if reasons_below:
                reasons_text.append(f"{', '.join(reasons_below)} abaixo do ideal")
            if reasons_above:
                reasons_text.append(f"{', '.join(reasons_above)} acima do ideal")
            justification = (
                "; ".join(reasons_text)
                + ", podendo ser aceito sob determinadas condições. Contate a área técnica."
                if reasons_text
                else "Parâmetros dentro dos limites ideais. Enviar COA para análise completa."
            )

        total_cost = sulfur_cost if sulfur_cost else 0
        return (
            status,
            justification,
            sulfur_cost,
            total_cost,
        )

    # Avaliar cada registro no DataFrame
    df = pd.DataFrame(data, index=[0])
    df["Viabilidade"], df["Justificativa"], df["Custo Enxofre (USD/t)"], df["Custo Total Adicional"] = zip(*df.apply(evaluate, axis=1))
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
    st.write(f"Custo Total Adicional (USD/t): {df['Custo Total Adicional'].iloc[0]:.2f}")
    st.write(f"Custo por Enxofre (USD/t): {df['Custo Enxofre (USD/t)'].iloc[0]:.2f}")
