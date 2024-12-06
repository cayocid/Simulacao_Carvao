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

# Funções para calcular custos adicionais
def calculate_moisture_cost(pcs, moisture):
    if moisture <= 16:
        return 0
    adjustment = max(0, (moisture - 16) * 2)
    return round(adjustment * pcs / 1000, 2)

def calculate_ash_cost(ash):
    # Tabela de referência para custos de cinzas
    ash_cost_table = {
        8.00: 0.00,
        9.00: 0.00,
        9.10: 10.65,
        9.20: 20.78,
        9.30: 30.36,
        9.40: 39.42,
        9.50: 47.94,
        9.60: 55.80,
        9.70: 63.26,
        9.80: 70.05,
        9.90: 76.31,
        10.00: 82.04,
        10.10: 87.23,
        10.20: 91.76,
        10.30: 95.89,
        10.40: 99.35,
        10.50: 102.28,
        10.60: 104.68,
        10.70: 106.54,
        10.80: 107.87,
        10.90: 108.67,
        11.00: 108.80
    }

    # Interpolação linear para valores intermediários
    def interpolate_ash_cost(ash):
        sorted_keys = sorted(ash_cost_table.keys())
        for i in range(len(sorted_keys) - 1):
            if sorted_keys[i] <= ash <= sorted_keys[i + 1]:
                x1, y1 = sorted_keys[i], ash_cost_table[sorted_keys[i]]
                x2, y2 = sorted_keys[i + 1], ash_cost_table[sorted_keys[i + 1]]
                return round(y1 + (ash - x1) * (y2 - y1) / (x2 - x1), 2)
        return None

    # Extrapolação para valores acima de 11%
    def extrapolate_ash_cost(ash):
        # Assumindo tendência linear a partir do último ponto conhecido
        last_known_value = 11.00
        last_known_cost = 108.80
        slope = 2.0  # Taxa de aumento por 0,1% de cinza acima de 11%
        return round(last_known_cost + (ash - last_known_value) * slope, 2)

    if ash <= 9.0:
        return 0.0
    elif ash in ash_cost_table:
        return ash_cost_table[ash]
    elif 9.0 < ash <= 11.0:
        return interpolate_ash_cost(ash)
    else:  # ash > 11.0
        return extrapolate_ash_cost(ash)


def calculate_sulfur_cost(sulfur):
    # Tabela de referência para custos de enxofre
    sulfur_cost_table = {
        0.60: 0.00,
        0.61: 4.97,
        0.63: 5.05,
        0.66: 5.33,
        0.68: 5.45,
        0.69: 5.20
    }

    # Interpolação linear para valores intermediários
    def interpolate_sulfur_cost(sulfur):
        sorted_keys = sorted(sulfur_cost_table.keys())
        for i in range(len(sorted_keys) - 1):
            if sorted_keys[i] <= sulfur <= sorted_keys[i + 1]:
                x1, y1 = sorted_keys[i], sulfur_cost_table[sorted_keys[i]]
                x2, y2 = sorted_keys[i + 1], sulfur_cost_table[sorted_keys[i + 1]]
                return round(y1 + (sulfur - x1) * (y2 - y1) / (x2 - x1), 2)
        return None

    # Extrapolação para valores acima de 0,7%
    def extrapolate_sulfur_cost(sulfur):
        # Assumindo tendência linear a partir do último valor conhecido
        last_known_value = 0.69
        last_known_cost = 5.20
        slope = 0.15  # Taxa de aumento por 0,01% de enxofre acima de 0,69%
        return round(last_known_cost + (sulfur - last_known_value) * slope, 2)

    if sulfur <= 0.6:
        return 0
    elif sulfur in sulfur_cost_table:
        return sulfur_cost_table[sulfur]
    elif 0.6 < sulfur <= 0.7:
        return interpolate_sulfur_cost(sulfur)
    else:  # sulfur > 0.7
        return extrapolate_sulfur_cost(sulfur)

# Função para avaliar o carvão com base nos critérios configuráveis
def evaluate_coal(data):
    def evaluate(row):
        reasons_red = []
        reasons_yellow = []
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
        if status == "Verde":
            viability = "Carvão Tecnicamente Viável"
            justification = "Parâmetros dentro dos limites ideais."
        elif status == "Amarelo":
            viability = "Carvão com restrições técnicas"
            justification = f"{', '.join(reasons_yellow)} na zona amarela, podendo ser aceito sob determinadas condições. Contate a área técnica."
        elif status == "Vermelho":
            viability = "Carvão tecnicamente inviável"
            justification = f"Parâmetro(s) {', '.join(reasons_red)} fora do limite especificado. Não sendo recomendada a sua aquisição."

        return viability, justification, total_cost, moisture_cost, ash_cost, sulfur_cost

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
    st.markdown(f"**Viabilidade:** {df['Viabilidade'].iloc[0]}")
    st.markdown(f"**Justificativa:** {df['Justificativa'].iloc[0]}")
    st.markdown(f"**Custo Total Adicional (USD/t): {df['Custo Total Adicional (USD/t)'].iloc[0]:.2f}**")
    st.markdown(f"<p style='margin-left: 20px; font-size: 90%;'>Custo por Umidade (USD/t): {df['Custo Umidade (USD/t)'].iloc[0]:.2f}</p>", unsafe_allow_html=True)
    st.markdown(f"<p style='margin-left: 20px; font-size: 90%;'>Custo por Cinzas (USD/t): {df['Custo Cinzas (USD/t)'].iloc[0]:.2f}</p>", unsafe_allow_html=True)
    st.markdown(f"<p style='margin-left: 20px; font-size: 90%;'>Custo por Enxofre (USD/t): {df['Custo Enxofre (USD/t)'].iloc[0]:.2f}</p>", unsafe_allow_html=True)

# Frase no rodapé
st.markdown("---")
st.markdown(
    "<p style='text-align: center;'>Esta análise é baseada nos critérios de referência do carvão de performance.</p>",
    unsafe_allow_html=True,
)
