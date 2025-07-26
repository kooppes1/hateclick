import streamlit as st
from datetime import datetime
from fpdf import FPDF
import base64
import tempfile
import os

# Initialize session state
if 'current_screen' not in st.session_state:
    st.session_state.current_screen = 1

# Mock AI analysis function
def analyze_comment(comment_text, platform):
    # This would be replaced with actual AI analysis
    offenses = []
    severity = "🟢"
    
    hate_keywords = ["haine", "race", "juif", "musulman", "salope", "pd", "pute", "nègre", "enculé"]
    if any(keyword in comment_text.lower() for keyword in hate_keywords):
        offenses.append("Incitation à la haine")
        severity = "🔴"
    
    insult_keywords = ["connard", "salope", "imbécile", "idiot", "débile"]
    if any(keyword in comment_text.lower() for keyword in insult_keywords):
        offenses.append("Injure publique")
        severity = "🟠"
        
    if len(offenses) == 0:
        offenses.append("Aucune infraction claire détectée")
        severity = "🟢"
    
    legal_advice = "Ce commentaire peut constituer une infraction selon l'article 29 de la loi de 1881 sur la liberté de la presse."
    
    return {
        "offenses": offenses,
        "severity": severity,
        "legal_advice": legal_advice
    }

# PDF generation function
def generate_pdf(user_info, comment_info, analysis_result):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Title
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Plainte pour propos haineux en ligne", ln=1, align='C')
    pdf.ln(10)
    
    # User information
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Informations du plaignant", ln=1)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Nom: {user_info.get('name', 'Non renseigné')}", ln=1)
    pdf.cell(200, 10, txt=f"Email: {user_info.get('email', 'Non renseigné')}", ln=1)
    pdf.cell(200, 10, txt=f"Téléphone: {user_info.get('phone', 'Non renseigné')}", ln=1)
    pdf.ln(10)
    
    # Incident information
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Détails de l'incident", ln=1)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Plateforme: {comment_info['platform']}", ln=1)
    pdf.cell(200, 10, txt=f"Auteur: {comment_info.get('author', 'Inconnu')}", ln=1)
    pdf.cell(200, 10, txt=f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=1)
    pdf.ln(5)
    
    # Comment
    pdf.multi_cell(0, 10, txt=f"Commentaire signalé: {comment_info['comment']}")
    pdf.ln(10)
    
    # Analysis
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Analyse juridique", ln=1)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Infractions potentielles: {', '.join(analysis_result['offenses'])}", ln=1)
    pdf.multi_cell(0, 10, txt=f"Conseil juridique: {analysis_result['legal_advice']}")
    
    # Footer
    pdf.ln(20)
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 10, txt="Document généré automatiquement par HateClick v0.1 - Ne remplace pas un conseil juridique professionnel", ln=1, align='C')
    
    # Save to temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    pdf_path = temp_file.name
    pdf.output(pdf_path)
    temp_file.close()
    
    return pdf_path

# Screen 1 - Report
def screen_report():
    st.title("Signale un commentaire haineux en 2 minutes")
    
    with st.form("report_form"):
        url = st.text_input("Lien du post ou screenshot (coller l'URL ou importer un screenshot)")
        comment = st.text_area("Copier-coller du commentaire", height=150)
        platform = st.selectbox("Plateforme", ["TikTok", "Instagram", "X (Twitter)", "YouTube", "Facebook", "Autre"])
        author = st.text_input("Pseudo de l'auteur (optionnel)")
        screenshot = st.file_uploader("📎 Pièce jointe : capture écran (optionnelle)", type=['png', 'jpg', 'jpeg'])
        
        submitted = st.form_submit_button("Analyser le commentaire")
        
        if submitted:
            if not comment:
                st.error("Veuillez saisir le commentaire à analyser")
            else:
                st.session_state.user_input = {
                    "url": url,
                    "comment": comment,
                    "platform": platform,
                    "author": author,
                    "screenshot": screenshot
                }
                st.session_state.current_screen = 2

# Screen 2 - Analysis
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
    st.info("Nous vous recommandons de conserver une copie et de générer une plainte.")
    
    if st.button("Générer ma plainte"):
        st.session_state.analysis_result = analysis_result
        st.session_state.current_screen = 3

# Screen 3 - Complaint
def screen_complaint():
    st.title("Voici ton document de plainte à imprimer ou envoyer")
    
    # Collect user information
    with st.expander("Vos coordonnées (optionnel)"):
        name = st.text_input("Nom Prénom")
        email = st.text_input("Email")
        phone = st.text_input("Téléphone")
    
    user_info = {
        "name": name,
        "email": email,
        "phone": phone
    }
    
    # Generate PDF
    pdf_path = generate_pdf(
        user_info,
        st.session_state.user_input,
        st.session_state.analysis_result
    )
    
    # Display PDF download link
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    
    st.download_button(
        label="📥 Télécharger la plainte",
        data=pdf_bytes,
        file_name="plainte_hateclick.pdf",
        mime="application/pdf"
    )
    
    st.subheader("Options")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.button("Imprimer")
    
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

# Main app logic
def main():
    st.sidebar.title("HateClick v0.1")
    st.sidebar.markdown("""
    Prototype d'outil de signalement de commentaires haineux en ligne.
    
    **Fonctionnalités :**
    - Analyse de commentaire
    - Qualification juridique
    - Génération de plainte PDF
    """)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    ⚠️ **Disclaimer :**  
    Cette application ne remplace pas un conseil juridique professionnel.  
    Les signalements anonymes ne sont pas recevables en justice.
    """)
    
    if st.session_state.current_screen == 1:
        screen_report()
    elif st.session_state.current_screen == 2:
        screen_analysis()
    elif st.session_state.current_screen == 3:
        screen_complaint()

if __name__ == "__main__":
    main()
