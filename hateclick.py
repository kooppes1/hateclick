import streamlit as st
from datetime import datetime
from fpdf import FPDF
import tempfile
import os
import openai
import json

# Initialise la clé API OpenAI
openai.api_key = st.secrets["openai_api_key"]

# Initialiser l'état de l'app
if 'current_screen' not in st.session_state:
    st.session_state.current_screen = 1

# 🔍 Analyse IA
def analyze_comment(comment_text, platform):
    prompt = f"""
Tu es un expert juridique spécialisé dans les propos haineux en ligne.

Voici un commentaire posté sur {platform} : "{comment_text}"

Analyse s'il contient :
- Une infraction (injure publique, incitation à la haine, diffamation, etc.)
- Son niveau de gravité (faible, moyen, élevé)
- Une qualification juridique claire
- Une recommandation ou conseil légal

Ta réponse doit être au format JSON avec les champs suivants :
{{
    "offenses": [...],
    "severity": "🟢 / 🟠 / 🔴",
    "legal_advice": "...",
    "reasoning": "..."
}}
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Tu es un juriste spécialisé en droit pénal et numérique."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        content = response["choices"][0]["message"]["content"]
        return json.loads(content)
    except Exception as e:
        st.error(f"Erreur d'analyse IA : {e}")
        return {
            "offenses": ["Erreur d’analyse"],
            "severity": "🟠",
            "legal_advice": "Une erreur est survenue. Réessayez.",
            "reasoning": ""
        }

# 📄 Générer un PDF
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
    
    pdf.multi_cell(0, 10, txt=f"Commentaire signalé : {comment_info['comment']}")
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Analyse juridique", ln=1)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Infractions détectées : {', '.join(analysis_result['offenses'])}", ln=1)
    pdf.cell(200, 10, txt=f"Niveau de gravité : {analysis_result['severity']}", ln=1)
    pdf.ln(5)
    pdf.multi_cell(0, 10, txt=f"Conseil : {analysis_result['legal_advice']}")
    pdf.ln(5)
    pdf.multi_cell(0, 10, txt=f"Analyse : {analysis_result.get('reasoning', '')}")
    
    pdf.ln(20)
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 10, txt="Document généré automatiquement par HateClick v0.1", ln=1, align='C')
    
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    pdf_path = temp_file.name
    pdf.output(pdf_path)
    temp_file.close()
    
    return pdf_path

# Écran 1 - Signalement
def screen_report():
    st.title("Signale un commentaire haineux en 2 minutes")
    
    with st.form("report_form"):
        url = st.text_input("Lien du post ou capture (URL ou image)")
        comment = st.text_area("Copier-coller du commentaire", height=150)
        platform = st.selectbox("Plateforme", ["TikTok", "Instagram", "X (Twitter)", "YouTube", "Facebook", "Autre"])
        author = st.text_input("Pseudo de l'auteur (optionnel)")
        screenshot = st.file_uploader("📎 Capture écran (optionnelle)", type=['png', 'jpg', 'jpeg'])
        
        submitted = st.form_submit_button("Analyser le commentaire")
        if submitted:
            if not comment:
                st.error("Veuillez saisir le commentaire.")
            else:
                st.session_state.user_input = {
                    "url": url,
                    "comment": comment,
                    "platform": platform,
                    "author": author,
                    "screenshot": screenshot
                }
                st.session_state.current_screen = 2

# Écran 2 - Analyse IA
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
    
    if "reasoning" in analysis_result and analysis_result["reasoning"]:
        st.caption(analysis_result["reasoning"])
    
    if st.button("Générer ma plainte"):
        st.session_state.analysis_result = analysis_result
        st.session_state.current_screen = 3

# Écran 3 - Génération de la plainte
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
        pdf_bytes = f.read()
    
    st.download_button(
        label="📥 Télécharger la plainte",
        data=pdf_bytes,
        file_name="plainte_hateclick.pdf",
        mime="application/pdf"
    )
    
    st.subheader("Options supplémentaires")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.button("🖨️ Imprimer")
    with col2:
        st.link_button("Envoyer à PHAROS", "https://www.internet-signalement.gouv.fr")
    with col3:
        st.link_button("Commissariat proche", "https://www.google.com/maps/search/commissariat")
    with col4:
        st.link_button("Contacter une asso", "https://www.e-enfance.org")
    
    if st.button("Retour à l'accueil"):
        st.session_state.current_screen = 1
        st.session_state.user_input = None
        st.session_state.analysis_result = None
        st.rerun()

# 🎬 Main app
def main():
    st.sidebar.title("HateClick v0.1")
    st.sidebar.markdown("""
Prototype de signalement intelligent de commentaires haineux.
    
Fonctionnalités :
- Analyse IA
- Qualification juridique
- PDF plainte à imprimer/envoyer
    """)
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
⚠️ **Disclaimer :**  
Cette application ne remplace pas un avocat. Les signalements anonymes ne sont pas recevables.
    """)
    
    if st.session_state.current_screen == 1:
        screen_report()
    elif st.session_state.current_screen == 2:
        screen_analysis()
    elif st.session_state.current_screen ==
