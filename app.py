import streamlit as st
import pandas as pd

# Critérios configuráveis para avaliação
CRITERIA = {
    "PCS (kcal/kg)": {"green_min": 5800, "yellow_min": 5701, "red_max": 5300},
    "PCI (kcal/kg)": {"green_min": 5700, "yellow_min": 5601, "red_max": 5200},
    "% Cinzas": {"green_max": 9, "yellow_max": 9.9, "red_min": 12},
    "% Umidade": {"green_max": 16, "yellow_max": 16.9, "red_min": 18},
    "% Enxofre": {"green_max": 0.6, "yellow_min": 0.69, "red_min": 0.85},
}

def calculate_moisture_cost(pcs, moisture):
    # Tabela representando os valores de custo baseados em PCS e umidade
    moisture_cost_table = {
        5700: [0.00, 0.11, 0.22, 0.32, 0.43, 0.54, 0.92, 1.08, 1.23, 1.38, 1.54],
        5710: [0.00, 0.00, 0.09, 0.20, 0.30, 0.41, 0.86, 1.01, 1.17, 1.32, 1.47],
        5720: [0.00, 0.00, 0.00, 0.07, 0.18, 0.29, 0.80, 0.95, 1.10, 1.26, 1.41],
        5730: [0.00, 0.00, 0.00, 0.00, 0.05, 0.16, 0.73, 0.89, 1.04, 1.20, 1.35],
        5740: [0.00, 0.00, 0.00, 0.00, 0.00, 0.03, 0.67, 0.82, 0.98, 1.13, 1.29],
        5750: [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.61, 0.76, 0.92, 1.07, 1.22],
        5760: [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.60, 0.70, 0.85, 1.01, 1.16],
        5770: [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.60, 0.70, 0.80, 0.94, 1.10],
        5780: [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.60, 0.70, 0.80, 0.90, 1.03],
        5790: [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.60, 0.70, 0.80, 0.90, 1.00],
        5800: [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.60, 0.70, 0.80, 0.90, 1.00],
    }
    moisture_levels = [16.00, 16.10, 16.20, 16.30, 16.40, 16.50, 16.60, 16.70, 16.80, 16.90, 17.00]

    # Verificar se a umidade está abaixo do limite mínimo
    if moisture < 16.0:
        return 0.0

    # Verificar se o PCS está dentro dos limites da tabela
    pcs_keys = sorted(moisture_cost_table.keys())
    if pcs < pcs_keys[0]:
        pcs = pcs_keys[0]
    elif pcs > pcs_keys[-1]:
        pcs = pcs_keys[-1]

    # Encontra os PCS mais próximos para interpolação
    lower_pcs = max(k for k in pcs_keys if k <= pcs)
    upper_pcs = min(k for k in pcs_keys if k >= pcs)

    # Verificar se a umidade está dentro dos limites da tabela
    if moisture > max(moisture_levels):
        moisture = max(moisture_levels)

    lower_moisture_idx = max(i for i, v in enumerate(moisture_levels) if v <= moisture)
    upper_moisture_idx = min(i for i, v in enumerate(moisture_levels) if v >= moisture)

    # Valores de custo para os PCS e umidades mais próximas
    lower_cost_lower_pcs = moisture_cost_table[lower_pcs][lower_moisture_idx]
    upper_cost_lower_pcs = moisture_cost_table[lower_pcs][upper_moisture_idx]
    lower_cost_upper_pcs = moisture_cost_table[upper_pcs][lower_moisture_idx]
    upper_cost_upper_pcs = moisture_cost_table[upper_pcs][upper_moisture_idx]

    # Interpolação para os valores de PCS
    cost_lower_pcs = np.interp(
        moisture, [moisture_levels[lower_moisture_idx], moisture_levels[upper_moisture_idx]],
        [lower_cost_lower_pcs, upper_cost_lower_pcs]
    )
    cost_upper_pcs = np.interp(
        moisture, [moisture_levels[lower_moisture_idx], moisture_levels[upper_moisture_idx]],
        [lower_cost_upper_pcs, upper_cost_upper_pcs]
    )

    # Interpolação final entre os valores de PCS
    if lower_pcs != upper_pcs:  # Interpolação necessária
        final_cost = np.interp(pcs, [lower_pcs, upper_pcs], [cost_lower_pcs, cost_upper_pcs])
    else:  # Sem necessidade de interpolação
        final_cost = cost_lower_pcs

    return round(final_cost, 2)


def calculate_ash_cost(ash):
    ash_cost_table = {
        8.00: 0.00,
        9.00: 0.00,
        9.10: 10.65,
        11.00: 108.80,
    }

    def interpolate_ash_cost(ash):
        sorted_keys = sorted(ash_cost_table.keys())
        for i in range(len(sorted_keys) - 1):
            if sorted_keys[i] <= ash <= sorted_keys[i + 1]:
                x1, y1 = sorted_keys[i], ash_cost_table[sorted_keys[i]]
                x2, y2 = sorted_keys[i + 1], ash_cost_table[sorted_keys[i + 1]]
                return round(y1 + (ash - x1) * (y2 - y1) / (x2 - x1), 2)
        return 0.0  # Retorna 0.0 se não houver interpolação aplicável

    def extrapolate_ash_cost(ash):
        last_known_value = 11.00
        last_known_cost = 108.80
        slope = 4.5
        return round(last_known_cost + (ash - last_known_value) * slope, 2)

    if ash <= 9.0:
        return 0.0
    elif ash > 11.0:
        return extrapolate_ash_cost(ash)
    else:
        return interpolate_ash_cost(ash)

def calculate_sulfur_cost(sulfur):
    # Tabela de referência para custos de enxofre
    sulfur_cost_table = {
        0.60: 0.00,
        0.61: 4.97,
        0.63: 5.05,
        0.66: 5.33,
        0.68: 5.45,
        0.70: 5.47,  # Custo ajustado para 0.69 ser interpolado corretamente
    }

    def interpolate_sulfur_cost(sulfur):
        sorted_keys = sorted(sulfur_cost_table.keys())
        for i in range(len(sorted_keys) - 1):
            if sorted_keys[i] <= sulfur <= sorted_keys[i + 1]:
                x1, y1 = sorted_keys[i], sulfur_cost_table[sorted_keys[i]]
                x2, y2 = sorted_keys[i + 1], sulfur_cost_table[sorted_keys[i + 1]]
                return round(y1 + (sulfur - x1) * (y2 - y1) / (x2 - x1), 2)
        return 0.0

    def extrapolate_sulfur_cost(sulfur):
        last_known_value = 0.70
        last_known_cost = 5.47
        slope = 0.25  # Taxa de aumento por 0,01% de enxofre acima de 0.70%
        return round(last_known_cost + (sulfur - last_known_value) * slope, 2)

    # Verifica se o valor é próximo de um da tabela (para evitar problemas de precisão)
    for key in sulfur_cost_table.keys():
        if abs(sulfur - key) < 1e-6:  # Tolerância de precisão
            return sulfur_cost_table[key]

    # Interpolação ou extrapolação
    if sulfur <= 0.6:
        return 0.0
    elif sulfur > 0.7:
        return extrapolate_sulfur_cost(sulfur)
    else:
        return interpolate_sulfur_cost(sulfur)

def evaluate_coal(data):
    def evaluate(row):
        reasons_red = []
        reasons_yellow = []
        status = "Verde"

        moisture_cost = calculate_moisture_cost(row["PCS (kcal/kg)"], row["% Umidade"])
        ash_cost = calculate_ash_cost(row["% Cinzas"])
        sulfur_cost = calculate_sulfur_cost(row["% Enxofre"])

        # Garante que os custos sejam numéricos
        total_cost = float(moisture_cost or 0.0) + float(ash_cost or 0.0) + float(sulfur_cost or 0.0)

        # Avaliações de PCS, PCI, Cinzas, Umidade e Enxofre...
        if row["PCS (kcal/kg)"] < CRITERIA["PCS (kcal/kg)"]["red_max"]:
            status = "Vermelho"
            reasons_red.append("PCS")
        elif row["PCS (kcal/kg)"] < CRITERIA["PCS (kcal/kg)"]["yellow_min"]:
            status = "Amarelo"
            reasons_yellow.append("PCS")

        if row["PCI (kcal/kg)"] < CRITERIA["PCI (kcal/kg)"]["red_max"]:
            status = "Vermelho"
            reasons_red.append("PCI")
        elif row["PCI (kcal/kg)"] < CRITERIA["PCI (kcal/kg)"]["yellow_min"]:
            status = "Amarelo"
            reasons_yellow.append("PCI")

        if row["% Cinzas"] > CRITERIA["% Cinzas"]["red_min"]:
            status = "Vermelho"
            reasons_red.append("Cinzas")
        elif row["% Cinzas"] > CRITERIA["% Cinzas"]["green_max"]:
            status = "Amarelo"
            reasons_yellow.append("Cinzas")

        if row["% Umidade"] > CRITERIA["% Umidade"]["red_min"]:
            status = "Vermelho"
            reasons_red.append("Umidade")
        elif row["% Umidade"] > CRITERIA["% Umidade"]["green_max"]:
            status = "Amarelo"
            reasons_yellow.append("Umidade")

        if row["% Enxofre"] > CRITERIA["% Enxofre"]["red_min"]:
            status = "Vermelho"
            reasons_red.append("Enxofre")
        elif row["% Enxofre"] > CRITERIA["% Enxofre"]["green_max"]:
            status = "Amarelo"
            reasons_yellow.append("Enxofre")

        if status == "Verde":
            viability = "Carvão Tecnicamente Viável"
            justification = "Parâmetros dentro dos limites ideais."
        elif status == "Amarelo":
            viability = "Carvão com restrições técnicas"
            justification = f"{', '.join(reasons_yellow)} na zona amarela."
        else:
            viability = "Carvão tecnicamente inviável"
            justification = f"Parâmetro(s) {', '.join(reasons_red)} fora do limite especificado."

        return viability, justification, total_cost, moisture_cost, ash_cost, sulfur_cost

    df = pd.DataFrame(data, index=[0])
    df["Viabilidade"], df["Justificativa"], df["Custo Total Adicional (USD/t)"], df["Custo Umidade (USD/t)"], df["Custo Cinzas (USD/t)"], df["Custo Enxofre (USD/t)"] = zip(*df.apply(evaluate, axis=1))
    return df

# Interface do Streamlit
st.image("https://energiapecem.com/images/logo-principal-sha.svg", caption="Energia Pecém", use_container_width=True)
st.markdown("<h1 style='text-align: center;'>Simulação de Viabilidade do Carvão Mineral</h1>", unsafe_allow_html=True)

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

st.markdown("---")
st.markdown("<p style='text-align: center;'>Esta análise é baseada nos critérios de referência do carvão de performance.</p>", unsafe_allow_html=True)
