#Simulacao_de_Viabilidade_Carvao_Mineral
#Código sem auto-execução.
#Código para Github



# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Critérios configuráveis para avaliação
CRITERIA = {
    "PCS (kcal/kg)": {"green_min": 5800, "yellow_min": 5700, "red_max": 5700},
    "PCI (kcal/kg)": {"green_min": 5700, "yellow_min": 5600, "red_max": 5600},
    "% Cinzas": {"green_max": 9, "yellow_max": 10, "red_min": 10},
    "% Umidade": {"green_max": 16, "yellow_max": 17, "red_min": 17},
    "% Enxofre": {"green_max": 0.55, "yellow_max": 0.69, "red_min": 0.7},
}

COST_TABLE = {
    0.61: 4.97,
    0.62: 5.01,
    0.63: 5.05,
    0.64: 5.14,
    0.65: 5.24,
    0.66: 5.33,
    0.67: 5.39,
    0.68: 5.45,
    0.69: 5.45,
}

def evaluate_coal(data):
    def evaluate(row):
        reasons = []
        status = "Verde"
        additional_cost = None

        if row["PCS (kcal/kg)"] < CRITERIA["PCS (kcal/kg)"]["red_max"]:
            status = "Vermelho"
            reasons.append("PCS fora do limite permitido")
        elif row["PCS (kcal/kg)"] < CRITERIA["PCS (kcal/kg)"]["green_min"]:
            if status == "Verde": status = "Amarelo"
            reasons.append("PCS abaixo do ideal")

        if row["PCI (kcal/kg)"] < CRITERIA["PCI (kcal/kg)"]["red_max"]:
            status = "Vermelho"
            reasons.append("PCI fora do limite permitido")
        elif row["PCI (kcal/kg)"] < CRITERIA["PCI (kcal/kg)"]["green_min"]:
            if status == "Verde": status = "Amarelo"
            reasons.append("PCI abaixo do ideal")

        if row["% Cinzas"] > CRITERIA["% Cinzas"]["red_min"]:
            status = "Vermelho"
            reasons.append("Cinzas fora do limite permitido")
        elif row["% Cinzas"] > CRITERIA["% Cinzas"]["green_max"]:
            if status == "Verde": status = "Amarelo"
            reasons.append("Cinzas acima do ideal")

        if row["% Umidade"] > CRITERIA["% Umidade"]["red_min"]:
            status = "Vermelho"
            reasons.append("Umidade fora do limite permitido")
        elif row["% Umidade"] > CRITERIA["% Umidade"]["green_max"]:
            if status == "Verde": status = "Amarelo"
            reasons.append("Umidade acima do ideal")

        if row["% Enxofre"] > CRITERIA["% Enxofre"]["red_min"]:
            status = "Vermelho"
            reasons.append("Enxofre fora do limite permitido")
        elif row["% Enxofre"] > CRITERIA["% Enxofre"]["green_max"]:
            if status == "Verde": status = "Amarelo"
            reasons.append("Enxofre acima do ideal")
            rounded_sulfur = round(row["% Enxofre"], 2)
            if rounded_sulfur in COST_TABLE:
                additional_cost = COST_TABLE[rounded_sulfur]

        return (
            status,
            "; ".join(reasons) if reasons else "Todos os parâmetros estão dentro dos limites ideais.",
            additional_cost,
        )

    df = pd.DataFrame(data, index=[0])
    df["Viabilidade"], df["Justificativa"], df["Custo Adicional (USD/t)"] = zip(*df.apply(evaluate, axis=1))
    return df

def show_graph(df):
    color_map = {"Verde": "green", "Amarelo": "yellow", "Vermelho": "red"}
    df["Cor"] = df["Viabilidade"].map(color_map)

    plt.figure(figsize=(10, 6))
    for viability, color in color_map.items():
        subset = df[df["Viabilidade"] == viability]
        plt.scatter(subset["PCS (kcal/kg)"], subset["% Cinzas"],
                    label=viability, color=color, s=100, edgecolor="black")
        
    plt.title("Avaliacao de Viabilidade do Carvao Mineral", fontsize=14)
    plt.xlabel("PCS (kcal/kg)", fontsize=12)
    plt.ylabel("% Cinzas", fontsize=12)
    plt.axhline(y=CRITERIA["% Cinzas"]["green_max"], color="black", linestyle="--", label="Limite de Cinzas")
    plt.axvline(x=CRITERIA["PCS (kcal/kg)"]["green_min"], color="blue", linestyle="--", label="Limite de PCS")
    plt.legend(title="Viabilidade")
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.tight_layout()
    st.pyplot(plt)

st.title("Simulacao de Viabilidade do Carvao Mineral")
pcs = st.number_input("PCS (kcal/kg)", min_value=0, step=100)
pci = st.number_input("PCI (kcal/kg)", min_value=0, step=100)
cinzas = st.number_input("% Cinzas", min_value=0.0, max_value=100.0, step=0.1)
umidade = st.number_input("% Umidade", min_value=0.0, max_value=100.0, step=0.1)
enxofre = st.number_input("% Enxofre", min_value=0.0, max_value=10.0, step=0.01)

if st.button("Rodar Simulacao"):
    data = {
        "PCS (kcal/kg)": pcs,
        "PCI (kcal/kg)": pci,
        "% Cinzas": cinzas,
        "% Umidade": umidade,
        "% Enxofre": enxofre,
    }
    df = evaluate_coal(data)
    st.write(f"**Resultado:** {df['Viabilidade'][0]}")
    st.write(f"**Justificativa:** {df['Justificativa'][0]}")
    if df["Custo Adicional (USD/t)"].iloc[0]:
        st.write(f"**Custo Adicional devido ao enxofre:** {df['Custo Adicional (USD/t)'][0]:.2f} USD/t")
    show_graph(df)



