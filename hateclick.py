import streamlit as st
from datetime import datetime
from fpdf import FPDF
import tempfile
import json
from openai import OpenAI
import os

# Configuration initiale
st.set_page_config(
    page_title="HateClick - Signalement de propos haineux",
    page_icon="⚠️",
    layout="centered"
)

# Initialise le client OpenAI
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Gestion des écrans
if 'current_screen' not in st.session_state:
    st.session_state.current_screen = 1

# 🔍 Analyse avec OpenAI (version optimisée)
def analyze_comment(comment_text, platform):
    prompt = {
        "role": "system",
        "content": """
        Tu es un juriste expert en droit français. Analyse les commentaires selon ces critères:
        1. Injure publique (article 29 loi 1881)
        2. Incitation à la haine (article 24)
        3. Diffamation (article 30)
        4. Harcèlement (article 222-33-2 CP)
        Réponds au format JSON strict :
        {
            "offenses": [],
            "severity": "🟢|🟠|🔴",
            "legal_advice": "texte concis",
            "reasoning": "analyse"
        }
        """
    }
    
    try:
        with st.spinner("Analyse juridique en cours..."):
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    prompt,
                    {"role": "user", "content": f"Plateforme: {platform}\nCommentaire: {comment_text}"}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
    except Exception as e:
        st.error(f"Erreur d'analyse : {str(e)[:200]}...")
        return {
            "offenses": ["Erreur technique"],
            "severity": "🟠",
            "legal_advice": "Veuillez réessayer ou contacter un juriste",
            "reasoning": ""
        }

# 📄 Génération PDF (version sécurisée)
def generate_pdf(user_info, comment_info, analysis_result):
    pdf = FPDF()
    pdf.add_page()
    
    # Configuration Unicode
    pdf.set_font("Helvetica", size=12)
    
    # En-tête
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(0, 10, "Plainte pour propos haineux en ligne", ln=1, align='C')
    pdf.ln(10)
    
    # Section plaignant
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(0, 10, "Informations du plaignant", ln=1)
    pdf.set_font("Helvetica", size=12)
    for field in ["Nom", "Email", "Téléphone"]:
        pdf.cell(0, 10, f"{field}: {user_info.get(field.lower(), 'Non renseigné')}", ln=1)
    pdf.ln(10)
    
    # Section commentaire
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(0, 10, "Détails du signalement", ln=1)
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 10, f"Plateforme: {comment_info['platform']}", ln=1)
    pdf.cell(0, 10, f"Auteur: {comment_info.get('author', 'Inconnu')}", ln=1)
    pdf.cell(0, 10, f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=1)
    pdf.multi_cell(0, 10, f"Commentaire: {comment_info['comment'][:1000]}")  # Limite de caractères
    pdf.ln(10)
    
    # Section analyse
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(0, 10, "Analyse juridique", ln=1)
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 10, f"Infractions: {', '.join(analysis_result['offenses'])}", ln=1)  # Correction ici
    pdf.cell(0, 10, f"Gravité: {analysis_result['severity']}", ln=1)
    pdf.multi_cell(0, 10, f"Conseil: {analysis_result['legal_advice']}")
    
    # Pied de page
    pdf.ln(15)
    pdf.set_font("Helvetica", 'I', 10)
    pdf.cell(0, 10, "Généré par HateClick - Ne constitue pas un avis juridique", ln=1, align='C')
    
    # Sauvegarde temporaire
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    pdf_path = temp_file.name
    pdf.output(pdf_path)
    temp_file.close()
    return pdf_path

# Écrans de l'application
def screen_report():
    st.title("Signaler un commentaire haineux")
    
    with st.form(key='report_form'):
        comment = st.text_area("Commentaire à analyser*", height=150, max_chars=2000)
        platform = st.selectbox("Plateforme*", ["Twitter/X", "Facebook", "Instagram", "YouTube", "Autre"])
        author = st.text_input("Auteur (optionnel)")
        url = st.text_input("Lien (optionnel)")
        
        if st.form_submit_button("Analyser"):
            if not comment or not platform:
                st.error("Champs obligatoires manquants")
            else:
                st.session_state.user_input = {
                    "comment": comment,
                    "platform": platform,
                    "author": author,
                    "url": url
                }
                st.session_state.current_screen = 2

def screen_analysis():
    st.title("Résultat de l'analyse")
    
    if 'user_input' not in st.session_state:
        st.error("Données manquantes")
        return
    
    result = analyze_comment(
        st.session_state.user_input["comment"],
        st.session_state.user_input["platform"]
    )
    
    st.subheader("Infractions détectées")
    if not result["offenses"]:
        st.success("Aucune infraction claire détectée")
    else:
        for offense in result["offenses"]:
            st.error(f"- {offense}")
    
    st.metric("Niveau de gravité", result["severity"])
    
    with st.expander("Conseil juridique"):
        st.info(result["legal_advice"])
        if result["reasoning"]:
            st.caption(result["reasoning"])
    
    if st.button("Générer la plainte"):
        st.session_state.analysis_result = result
        st.session_state.current_screen = 3

def screen_complaint():
    st.title("Votre plainte prête")
    
    with st.expander("Vos coordonnées (optionnel)"):
        user_info = {
            "name": st.text_input("Nom Prénom"),
            "email": st.text_input("Email"),
            "phone": st.text_input("Téléphone")
        }
    
    # Génération PDF
    pdf_path = generate_pdf(
        user_info,
        st.session_state.user_input,
        st.session_state.analysis_result
    )
    
    # Téléchargement
    with open(pdf_path, "rb") as f:
        st.download_button(
            label="📄 Télécharger la plainte",
            data=f,
            file_name="plainte_hateclick.pdf",
            mime="application/pdf"
        )
    os.unlink(pdf_path)  # Nettoyage du fichier temporaire
    
    # Options
    st.subheader("Prochaines étapes")
    cols = st.columns(3)
    with cols[0]:
        st.link_button("PHAROS", "https://www.internet-signalement.gouv.fr")
    with cols[1]:
        st.link_button("Commissariats", "https://www.google.com/maps/search/commissariat")
    with cols[2]:
        st.link_button("Associations", "https://www.e-enfance.org")
    
    if st.button("Nouveau signalement"):
        st.session_state.clear()
        st.rerun()

# Navigation
def main():
    st.sidebar.title("HateClick")
    st.sidebar.markdown("""
    **Protection contre les discours haineux en ligne**
    - Analyse juridique automatisée
    - Génération de plainte pré-remplie
    - Conseils personnalisés
    """)
    
    if st.session_state.current_screen == 1:
        screen_report()
    elif st.session_state.current_screen == 2:
        screen_analysis()
    elif st.session_state.current_screen == 3:
        screen_complaint()

if __name__ == "__main__":
    main()
