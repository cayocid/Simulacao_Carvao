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
