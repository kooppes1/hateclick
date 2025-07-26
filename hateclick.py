def screen_analysis():
    st.title("Voici ce que nous avons détecté")

    user_input = st.session_state.user_input
    analysis_result = analyze_comment(user_input["comment"], user_input["platform"])

    st.subheader("Type probable d'infraction")
    for offense in analysis_result["offenses"]:
        st.write(f"- {offense}")

    st.subheader("Niveau de gravité")
    st.write(analysis_result["severity"])

    st.subheader("🧠 Analyse juridique")
    st.info(analysis_result["legal_advice"])

    if analysis_result.get("reasoning"):
        st.caption(f"🧠 Détail de l'analyse IA : {analysis_result['reasoning']}")

    if analysis_result.get("penalty"):
        st.subheader("⚖️ Peine légale encourue")
        st.write(analysis_result["penalty"]["text"])

        st.subheader("💸 Ce que cela peut lui coûter")
        st.write(f"L’agresseur encourt : {analysis_result['penalty']['text']}")

        st.subheader("✅ Conditions juridiques nécessaires")
        for cond in analysis_result["penalty"].get("conditions", []):
            st.write(f"- {cond}")

        st.subheader("📈 Chances estimées de succès")
        st.write(analysis_result["penalty"]["chances"])

        st.subheader("💼 Coût estimé d’une procédure")
        st.write(analysis_result["penalty"]["estimated_cost"])

    if st.button("Générer ma plainte"):
        st.session_state.analysis_result = analysis_result
        st.session_state.current_screen = 3
