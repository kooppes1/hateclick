import streamlit as st
from datetime import datetime
from fpdf import FPDF
import tempfile
import json
import re
from openai import OpenAI

# 🔐 Initialise le client OpenAI
client = OpenAI(api_key=st.secrets["openai_api_key"])

# 🧼 Fonction utilitaire pour nettoyer les emojis
def remove_emojis(text):
    return re.sub(r'[^\x00-\x7F\u00A0-\u00FF\u0100-\u017F]+', '', text)

# Initialise l'écran par défaut
if 'current_screen' not in st.session_state:
    st.session_state.current_screen = 1

# 🔍 Analyse IA enrichie
def analyze_comment(comment_text, platform):
    prompt = f"""
Tu es un juriste expert en droit français spécialisé dans les propos haineux en ligne.

Voici un commentaire posté sur {platform} : "{comment_text}"

Analyse s'il contient :
- Une ou plusieurs infractions (injure publique, incitation à la haine, diffamation, etc.)
- Le niveau de gravité (faible, moyen, élevé) sous forme d’emoji (🟢 / 🟠 / 🔴)
- Une qualification juridique claire
- Une recommandation légale
- Les sanctions pénales applicables (articles de loi, amendes, peines encourues)
- Les conditions juridiques à remplir pour que la plainte aboutisse
- Les chances estimées de succès (faible, moyenne, élevée)
- Une estimation du coût d’une procédure (plainte simple, avec ou sans avocat)

Réponds au format JSON :
{{
  "offenses": [...],
  "severity": "🟢 / 🟠 / 🔴",
  "legal_advice": "...",
  "reasoning": "...",
  "penalty": {{
    "text": "...",
    "conditions": [...],
    "chances": "...",
    "estimated_cost": "..."
  }}
}}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Tu es un juriste spécialisé en droit pénal et numérique."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        st.error(f"Erreur d'analyse IA : {e}")
        return {
            "offenses": ["Erreur d’analyse"],
            "severity": "🟠",
            "legal_advice": "Une erreur est survenue. Réessayez.",
            "reasoning": "",
            "penalty": {
                "text": "Non disponible",
                "conditions": [],
                "chances": "Inconnues",
                "estimated_cost": "Inconnu"
            }
        }

# 📄 Génération du PDF
def generate_pdf(user_info, comment_info, analysis_result):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Plainte pour propos haineux en ligne", ln=1, align='C')
    pdf.ln(10)

    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Informations du plaignant", ln=1)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Nom: {user_info.get('name', 'Non renseigné')}", ln=1)
    pdf.cell(200, 10, txt=f"Email: {user_info.get('email', 'Non renseigné')}", ln=1)
    pdf.cell(200, 10, txt=f"Téléphone: {user_info.get('phone', 'Non renseigné')}", ln=1)
    pdf.ln(10)

    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Détails de l'incident", ln=1)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Plateforme: {comment_info['platform']}", ln=1)
    pdf.cell(200, 10, txt=f"Auteur: {comment_info.get('author', 'Inconnu')}", ln=1)
    pdf.cell(200, 10, txt=f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=1)
    pdf.ln(5)
    pdf.multi_cell(0, 10, txt=f"Commentaire signalé : {remove_emojis(comment_info['comment'])}")
    pdf.ln(10)

    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Analyse juridique", ln=1)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Infractions détectées : {', '.join(analysis_result['offenses'])}", ln=1)

    # Nettoyage emoji gravité
    severity_clean = analysis_result['severity'].replace("🟢", "faible").replace("🟠", "moyenne").replace("🔴", "élevée")
    pdf.cell(200, 10, txt=f"Niveau de gravité : {severity_clean}", ln=1)
    pdf.ln(5)
    pdf.multi_cell(0, 10, txt=f"Conseil : {remove_emojis(analysis_result['legal_advice'])}")
    pdf.ln(5)
    pdf.multi_cell(0, 10, txt=f"Analyse IA : {remove_emojis(analysis_result.get('reasoning', ''))}")

    if "penalty" in analysis_result:
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="Informations complémentaires", ln=1)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, txt=f"Sanctions : {remove_emojis(analysis_result['penalty']['text'])}")

        conditions = analysis_result['penalty'].get('conditions', [])
        if conditions:
            pdf.cell(200, 10, txt="Conditions :", ln=1)
            for cond in conditions:
                pdf.multi_cell(0, 10, txt=remove_emojis(cond))

        pdf.cell(200, 10, txt=f"Chances de succès : {analysis_result['penalty']['chances']}", ln=1)
        pdf.cell(200, 10, txt=f"Coût estimé : {analysis_result['penalty']['estimated_cost']}", ln=1)

    pdf.ln(20)
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 10, txt="Document généré automatiquement par HateClick v0.1", ln=1, align='C')

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    pdf.output(temp_file.name)
    return temp_file.name

# Écran 1 - Signalement
def screen_report():
    st.title("Signale un commentaire haineux en 2 minutes")
    with st.form("report_form"):
        url = st.text_input("Lien du post (optionnel)")
        comment = st.text_area("Copier-coller du commentaire", height=150)
        platform = st.selectbox("Plateforme", ["TikTok", "Instagram", "X (Twitter)", "YouTube", "Facebook", "Autre"])
        author = st.text_input("Pseudo de l'auteur (optionnel)")
        screenshot = st.file_uploader("📎 Capture écran (optionnelle)", type=['png', 'jpg', 'jpeg'])

        submitted = st.form_submit_button("Analyser le commentaire")
        if submitted:
            if not comment:
                st.error("Veuillez saisir un commentaire.")
            else:
                st.session_state.user_input = {
                    "url": url,
                    "comment": comment,
                    "platform": platform,
                    "author": author,
                    "screenshot": screenshot
                }
                st.session_state.current_screen = 2

# Écran 2 - Résultat IA
def screen_analysis():
    st.title("Voici ce que nous avons détecté")
    user_input = st.session_state.user_input
    analysis_result = analyze_comment(user_input["comment"], user_input["platform"])

    st.subheader("Type probable d'infraction")
    for offense in analysis_result["offenses"]:
        st.write(f"- {offense}")

    st.subheader("Niveau de gravité")
    st.write(analysis_result["severity"])

    st.subheader("Suggestions")
    st.info(analysis_result["legal_advice"])

    if analysis_result.get("reasoning"):
        st.caption(f"🧠 Analyse IA : {analysis_result['reasoning']}")

    if analysis_result.get("penalty"):
        st.subheader("📚 Sanctions légales")
        st.write(analysis_result["penalty"]["text"])

        st.subheader("📌 Conditions à remplir")
        for c in analysis_result["penalty"]["conditions"]:
            st.write(f"- {c}")

        st.subheader("📈 Chances de succès")
        st.write(analysis_result["penalty"]["chances"])

        st.subheader("💸 Coût estimé")
        st.write(analysis_result["penalty"]["estimated_cost"])

    if st.button("Générer ma plainte"):
        st.session_state.analysis_result = analysis_result
        st.session_state.current_screen = 3

# Écran 3 - PDF final
def screen_complaint():
    st.title("Voici ton document de plainte à imprimer ou envoyer")

    with st.expander("Vos coordonnées (optionnel)"):
        name = st.text_input("Nom Prénom")
        email = st.text_input("Email")
        phone = st.text_input("Téléphone")

    user_info = {
        "name": name,
        "email": email,
        "phone": phone
    }

    pdf_path = generate_pdf(
        user_info,
        st.session_state.user_input,
        st.session_state.analysis_result
    )

    with open(pdf_path, "rb") as f:
        st.download_button(
            label="📥 Télécharger la plainte",
            data=f.read(),
            file_name="plainte_hateclick.pdf",
            mime="application/pdf"
        )

    st.subheader("Options utiles")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.button("🖨️ Imprimer")
    with col2:
        st.link_button("Envoyer à PHAROS", "https://www.internet-signalement.gouv.fr")
    with col3:
        st.link_button("Commissariat", "https://www.google.com/maps/search/commissariat")
    with col4:
        st.link_button("Contacter une asso", "https://www.e-enfance.org")

    if st.button("Retour à l'accueil"):
        st.session_state.current_screen = 1
        st.session_state.user_input = None
        st.session_state.analysis_result = None
        st.rerun()

# 🧠 App principale
def main():
    st.sidebar.title("HateClick v0.1")
    st.sidebar.markdown("""
Prototype de signalement de propos haineux.

Fonctionnalités :
- Analyse juridique par IA 🤖
- Génération de plainte PDF 📝
- Conseils utiles 💡
    """)
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
