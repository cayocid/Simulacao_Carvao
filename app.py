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

# Função para avaliar o carvão com base nos critérios configuráveis
def evaluate_coal(data):
    def evaluate(row):
        reasons = []
        status = "Verde"
        sulfur_cost = None
        ash_cost = None

        # Avaliação de PCS
        if row["PCS (kcal/kg)"] < CRITERIA["PCS (kcal/kg)"]["red_max"]:
            status = "Vermelho"
            reasons.append("PCS fora do limite permitido")
        elif row["PCS (kcal/kg)"] < CRITERIA["PCS (kcal/kg)"]["green_min"]:
            if status == "Verde": status = "Amarelo"
            reasons.append("PCS abaixo do ideal, podendo ser aceito sob determinadas condições. Contate a área técnica")

        # Avaliação de PCI
        if row["PCI (kcal/kg)"] < CRITERIA["PCI (kcal/kg)"]["red_max"]:
            status = "Vermelho"
            reasons.append("PCI fora do limite permitido")
        elif row["PCI (kcal/kg)"] < CRITERIA["PCI (kcal/kg)"]["green_min"]:
            if status == "Verde": status = "Amarelo"
            reasons.append("PCI abaixo do ideal, podendo ser aceito sob determinadas condições. Contate a área técnica")

        # Avaliação de Cinzas
        if row["% Cinzas"] > CRITERIA["% Cinzas"]["red_min"]:
            status = "Vermelho"
            reasons.append("Cinzas fora do limite permitido")
        elif row["% Cinzas"] > CRITERIA["% Cinzas"]["green_max"]:
            if status == "Verde": status = "Amarelo"
            reasons.append("Cinzas acima do ideal, podendo ser aceito sob determinadas condições. Contate a área técnica")
            rounded_ash = round(row["% Cinzas"], 1)
            if rounded_ash in ASH_COST_TABLE:
                ash_cost = ASH_COST_TABLE[rounded_ash]

        # Avaliação de Umidade
        if row["% Umidade"] > CRITERIA["% Umidade"]["red_min"]:
            status = "Vermelho"
            reasons.append("Umidade fora do limite permitido")
        elif row["% Umidade"] > CRITERIA["% Umidade"]["green_max"]:
            if status == "Verde": status = "Amarelo"
            reasons.append("Umidade acima do ideal, podendo ser aceito sob determinadas condições. Contate a área técnica")

        # Avaliação de Enxofre
        if row["% Enxofre"] > CRITERIA["% Enxofre"]["red_min"]:
            status = "Vermelho"
            reasons.append("Enxofre fora do limite permitido")
        elif row["% Enxofre"] > CRITERIA["% Enxofre"]["green_max"]:
            if status == "Verde": status = "Amarelo"
            reasons.append("Enxofre acima do ideal, podendo ser aceito sob determinadas condições. Contate a área técnica")
            rounded_sulfur = round(row["% Enxofre"], 2)
            if rounded_sulfur in SULFUR_COST_TABLE:
                sulfur_cost = SULFUR_COST_TABLE[rounded_sulfur]

        return (
            status,
            "; ".join(reasons) if reasons else "Parâmetros dentro dos limites ideais.",
            sulfur_cost,
            ash_cost,
        )

    # Avaliar cada registro no DataFrame
    df = pd.DataFrame(data, index=[0])
    df["Viabilidade"], df["Justificativa"], df["Custo Enxofre (USD/t)"], df["Custo Cinzas (USD/t)"] = zip(*df.apply(evaluate, axis=1))
    return df

# Função para plotar o gráfico de radar com zonas invertidas
def plot_radar_chart(data):
    variables = ["PCS (kcal/kg)", "PCI (kcal/kg)", "% Cinzas", "% Umidade", "% Enxofre"]
    max_limits = [5800, 5700, 10, 17, 0.7]
    min_limits = [5600, 5600, 8, 15, 0.5]

    normalized_values = [(data[var] - min_limits[i]) / (max_limits[i] - min_limits[i]) for i, var in enumerate(variables)]
    normalized_green = [0.4] * len(variables)
    normalized_yellow = [0.6] * len(variables)
    normalized_red = [0.8] * len(variables)

    angles = np.linspace(0, 2 * np.pi, len(variables), endpoint=False).tolist()
    angles += angles[:1]

    normalized_values += normalized_values[:1]
    normalized_green += normalized_green[:1]
    normalized_yellow += normalized_yellow[:1]
    normalized_red += normalized_red[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    ax.fill(angles, normalized_red, color="red", alpha=0.2, label="Zona Vermelha")
    ax.fill(angles, normalized_yellow, color="yellow", alpha=0.2, label="Zona Amarela")
    ax.fill(angles, normalized_green, color="green", alpha=0.2, label="Zona Verde")
    ax.plot(angles, normalized_values, color="blue", linewidth=2, label="Carvão Avaliado")
    ax.fill(angles, normalized_values, color="blue", alpha=0.3)

    ax.set_yticks([])
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(variables, fontsize=10)
    ax.set_title("Avaliação de Viabilidade do Carvão", fontsize=14, pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.2, 1.2))

    st.pyplot(fig)

# Interface do Streamlit
st.image("https://energiapecem.com/images/logo-principal-sha.svg", caption="Energia Pecém", use_container_width=True)
st.markdown(
    """
    <h1 style='text-align: center;'>Simulação de Viabilidade do Carvão Mineral</h1>
    """,
    unsafe_allow_html=True,
)

# Inputs
pcs = st.number_input("PCS (kcal/kg)", min_value=0, step=100, value=5750)
pci = st.number_input("PCI (kcal/kg)", min_value=0, step=100, value=5620)
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

    sulfur_cost = df["Custo Enxofre (USD/t)"].iloc[0]
    ash_cost = df["Custo Cinzas (USD/t)"].iloc[0]
    total_cost = 0
    if sulfur_cost:
        st.write(f"Custo adicional devido ao enxofre: {sulfur_cost:.2f} USD/t")
        total_cost += sulfur_cost
    if ash_cost:
        st.write(f"Custo adicional devido às cinzas: {ash_cost:.2f} USD/t")
        total_cost += ash_cost
    if total_cost > 0:
        st.write(f"**Custo Total Adicional:** {total_cost:.2f} USD/t")

    # Exibir gráfico de radar
    plot_radar_chart(data)

# Frase no rodapé
st.markdown("---")
st.markdown("<p style='text-align: center;'>Esta análise é baseada nos critérios de referência do carvão de performance.</p>", unsafe_allow_html=True)
