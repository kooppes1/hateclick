# === Interface principale de l'app ===

def screen_report():
    st.title("Signale un commentaire haineux en 2 minutes")

    with st.form("report_form"):
        url = st.text_input("Lien du post (optionnel)")
        comment = st.text_area("Copier-coller du commentaire", height=150)
        platform = st.selectbox("Plateforme", ["TikTok", "Instagram", "X (Twitter)", "YouTube", "Facebook", "Autre"])
        author = st.text_input("Pseudo de l'auteur (optionnel)")
        screenshot = st.file_uploader("📎 Capture écran (optionnelle)", type=['png', 'jpg', 'jpeg'])

        submitted = st.form_submit_button("Analyser le commentaire")
        if submitted and comment:
            st.session_state.user_input = {
                "url": url,
                "comment": comment,
                "platform": platform,
                "author": author,
                "screenshot": screenshot
            }
            st.session_state.current_screen = 2
        elif submitted:
            st.error("Veuillez saisir un commentaire.")

def screen_analysis():
    st.title("Voici ce que nous avons détecté")

    user_input = st.session_state.user_input
    analysis_result = analyze_comment(user_input["comment"], user_input["platform"])

    st.session_state.analysis_result = analysis_result

    st.subheader("Type probable d'infraction")
    for offense in analysis_result["offenses"]:
        st.write(f"- {offense}")

    st.subheader("Niveau de gravité")
    st.write(analysis_result["severity"])

    st.subheader("Suggestions")
    st.info(analysis_result["legal_advice"])

    if analysis_result.get("reasoning"):
        st.caption(f"🧠 Analyse IA : {analysis_result['reasoning']}")

    penalty = analysis_result.get("penalty", {})
    if penalty:
        st.markdown("#### ⚖️ Sanctions légales")
        st.write(penalty.get("text", ""))
        st.markdown("**Conditions à remplir :**")
        for cond in penalty.get("conditions", []):
            st.markdown(f"- {cond}")
        st.markdown(f"**Chances estimées :** {penalty.get('chances', '')}")
        st.markdown(f"**Coût estimé :** {penalty.get('estimated_cost', '')}")

    if st.button("Générer ma plainte"):
        st.session_state.current_screen = 3

def screen_complaint():
    st.title("Voici ton document de plainte à imprimer ou envoyer")

    with st.expander("Vos coordonnées (optionnel)"):
        name = st.text_input("Nom Prénom")
        email = st.text_input("Email")
        phone = st.text_input("Téléphone")

    user_info = {"name": name, "email": email, "phone": phone}
    pdf_path = generate_pdf(user_info, st.session_state.user_input, st.session_state.analysis_result)

    with open(pdf_path, "rb") as f:
        st.download_button("📥 Télécharger la plainte", data=f.read(), file_name="plainte_hateclick.pdf", mime="application/pdf")

    st.markdown("---")
    st.markdown("**Options utiles :**")
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.button("🖨️ Imprimer")
    with col2: st.link_button("PHAROS", "https://www.internet-signalement.gouv.fr")
    with col3: st.link_button("Commissariat", "https://www.google.com/maps/search/commissariat")
    with col4: st.link_button("Contacter une asso", "https://www.e-enfance.org")

    if st.button("Retour à l'accueil"):
        st.session_state.current_screen = 1
        st.session_state.user_input = None
        st.session_state.analysis_result = None
        st.rerun()

def main():
    st.set_page_config(page_title="HateClick", layout="centered")
    st.sidebar.title("HateClick v0.1")
    st.sidebar.markdown("Prototype de signalement de propos haineux.\n\n**Fonctionnalités :**\n- Analyse juridique par IA 🤖\n- Génération de plainte PDF 📝\n- Conseils utiles 💡")
    st.sidebar.markdown("---")
    st.sidebar.warning("⚠️ Cette application ne remplace pas un conseil juridique professionnel.")

    if st.session_state.current_screen == 1:
        screen_report()
    elif st.session_state.current_screen == 2:
        screen_analysis()
    elif st.session_state.current_screen == 3:
        screen_complaint()

if __name__ == "__main__":
    main()
