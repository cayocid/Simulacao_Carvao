import streamlit as st
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
    if moisture <= CRITERIA["% Umidade"]["green_max"]:
        return 0
    adjustment = max(0, (moisture - CRITERIA["% Umidade"]["green_max"]) * 2)
    return round(adjustment * pcs / 1000, 2)

def calculate_ash_cost(ash):
    ash_cost_table = {
        8.00: 0.00,
        9.00: 0.00,
        9.10: 10.65,
        11.00: 108.80,
    }
    if ash <= 9.0:
        return 0.0
    elif ash > 11.0:
        return round(108.80 + (ash - 11.0) * 20, 2)
    else:
        return interpolate_cost(ash_cost_table, ash)

def calculate_sulfur_cost(sulfur):
    sulfur_cost_table = {
        0.60: 0.00,
        0.61: 4.97,
        0.69: 5.20,
    }
    if sulfur <= 0.6:
        return 0
    elif sulfur > 0.7:
        return round(5.20 + (sulfur - 0.7) * 15, 2)
    else:
        return interpolate_cost(sulfur_cost_table, sulfur)

def interpolate_cost(cost_table, value):
    sorted_keys = sorted(cost_table.keys())
    for i in range(len(sorted_keys) - 1):
        if sorted_keys[i] <= value <= sorted_keys[i + 1]:
            x1, y1 = sorted_keys[i], cost_table[sorted_keys[i]]
            x2, y2 = sorted_keys[i + 1], cost_table[sorted_keys[i + 1]]
            return round(y1 + (value - x1) * (y2 - y1) / (x2 - x1), 2)
    return None

# Função para avaliar o carvão
def evaluate_coal(data):
    reasons_red = []
    reasons_yellow = []
    status = "Verde"

    moisture_cost = calculate_moisture_cost(data["PCS (kcal/kg)"], data["% Umidade"])
    ash_cost = calculate_ash_cost(data["% Cinzas"])
    sulfur_cost = calculate_sulfur_cost(data["% Enxofre"])
    total_cost = moisture_cost + ash_cost + sulfur_cost

    for key, limits in CRITERIA.items():
        value = data[key]
        if key in ("% Cinzas", "% Umidade", "% Enxofre"):
            if value > limits["red_min"]:
                status = "Vermelho"
                reasons_red.append(key)
            elif value > limits["green_max"]:
                status = "Amarelo"
                reasons_yellow.append(key)
        else:
            if value < limits["red_max"]:
                status = "Vermelho"
                reasons_red.append(key)
            elif value < limits["yellow_min"]:
                status = "Amarelo"
                reasons_yellow.append(key)

    if status == "Verde":
        viability = "Carvão Tecnicamente Viável"
        justification = "Parâmetros dentro dos limites ideais."
    elif status == "Amarelo":
        viability = "Carvão com restrições técnicas"
        justification = f"{', '.join(reasons_yellow)} na zona amarela."
    else:
        viability = "Carvão tecnicamente inviável"
        justification = f"Parâmetro(s) {', '.join(reasons_red)} fora do limite especificado."

    return pd.DataFrame([{
        "Viabilidade": viability,
        "Justificativa": justification,
        "Custo Total Adicional (USD/t)": total_cost,
        "Custo Umidade (USD/t)": moisture_cost,
        "Custo Cinzas (USD/t)": ash_cost,
        "Custo Enxofre (USD/t)": sulfur_cost,
    }])

# Interface do Streamlit
st.image("https://energiapecem.com/images/logo-principal-sha.svg", caption="Energia Pecém", use_container_width=True)
st.markdown("<h1 style='text-align: center;'>Simulação de Viabilidade do Carvão Mineral</h1>", unsafe_allow_html=True)

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
    
    # Exibição dos resultados no formato anterior
    st.markdown(f"**Viabilidade:** {df['Viabilidade'].iloc[0]}")
    st.markdown(f"**Justificativa:** {df['Justificativa'].iloc[0]}")
    st.markdown(f"**Custo Total Adicional (USD/t): {df['Custo Total Adicional (USD/t)'].iloc[0]:.2f}**")
    
    # Custos adicionais detalhados
    st.markdown(
        f"<p style='margin-left: 20px; font-size: 90%;'>Custo por Umidade (USD/t): {df['Custo Umidade (USD/t)'].iloc[0]:.2f}</p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='margin-left: 20px; font-size: 90%;'>Custo por Cinzas (USD/t): {df['Custo Cinzas (USD/t)'].iloc[0]:.2f}</p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='margin-left: 20px; font-size: 90%;'>Custo por Enxofre (USD/t): {df['Custo Enxofre (USD/t)'].iloc[0]:.2f}</p>",
        unsafe_allow_html=True,
    )

# Rodapé
st.markdown("---")
st.markdown(
    "<p style='text-align: center;'>Esta análise é baseada nos critérios de referência do carvão de performance.</p>",
    unsafe_allow_html=True,
)

