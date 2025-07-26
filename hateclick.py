import streamlit as st
from datetime import datetime
from fpdf import FPDF
import tempfile
import json
import re
from openai import OpenAI

# Configuration initiale
st.set_page_config(
    page_title="HateClick - Signalement Légal",
    page_icon="⚖️",
    layout="centered"
)

# Nettoyage des textes pour PDF
def clean_text(text):
    if not text:
        return ""
    text = text.replace('\x00', '')
    return re.sub(r'[^\x00-\x7F\xa0-\xffĀ-ſ\s.,!?;:\-()"\'/]+', '', text)

# Initialisation OpenAI
client = OpenAI(api_key=st.secrets["openai_api_key"])

if 'current_screen' not in st.session_state:
    st.session_state.current_screen = 1

# Analyse Juridique Complète
def analyze_content(content, platform):
    prompt = f"""
En tant que juriste expert français, analyse ce contenu posté sur {platform} :
\"{content}\"

Fournis une réponse STRUCTURÉE avec :

1. Infractions (articles précis)
2. Peines encourues (€ + prison)
3. Coûts pour la victime
4. Preuves nécessaires
5. Délais légaux
6. Chances de succès
7. Conseils stratégiques

Format JSON strict :
{{
  "infractions": [
    {{
      "article": "Art. 222-33-2-2 CP",
      "description": "Harcèlement sexuel en ligne",
      "peine": "2 ans prison + 30 000€ amende"
    }}
  ],
  "analyse": "Analyse détaillée...",
  "preuves": [
    "Capture écran datée",
    "Lien permanent"
  ],
  "couts": {{
    "plainte": "Gratuit",
    "avocat": "150-500€/h",
    "total": "500-5000€"
  }},
  "delais": {{
    "prescription": "6 ans",
    "instruction": "12-24 mois"
  }},
  "success_chance": "65%",
  "conseils": [
    "Faire constater par huissier",
    "Porter plainte sous 3 mois"
  ]
}}
Merci de répondre uniquement avec ce JSON.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Expert juridique français spécialisé en cybercriminalité"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        st.error(f"Erreur d'analyse : {str(e)}")
        return {
            "infractions": [{
                "article": "Erreur",
                "description": "Analyse indisponible",
                "peine": "Consulter un avocat"
            }],
            "analyse": "",
            "preuves": [],
            "couts": {},
            "delais": {},
            "success_chance": "N/A",
            "conseils": []
        }

# Génération du PDF Professionnel
def generate_legal_report(user_info, content_info, analysis):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # En-tête Juridique
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, "DOSSIER DE PLAINTE", ln=1, align='C')
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(190, 5, f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", ln=1, align='C')
    pdf.ln(15)
    
    # Section 1: Parties
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, "I. IDENTITÉ DES PARTIES", ln=1, border='B')
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(95, 8, "PLAIGNANT:", ln=0)
    pdf.cell(95, 8, "AUTEUR:", ln=1)
    
    pdf.set_font("Arial", '', 10)
    pdf.cell(95, 7, f"Nom: {clean_text(user_info.get('name'))}", ln=0)
    pdf.cell(95, 7, f"Pseudonyme: {clean_text(content_info.get('author'))}", ln=1)
    
    pdf.cell(95, 7, f"Adresse: {clean_text(user_info.get('address'))}", ln=0)
    pdf.cell(95, 7, f"Plateforme: {clean_text(content_info.get('platform'))}", ln=1)
    
    pdf.cell(95, 7, f"Contact: {clean_text(user_info.get('phone'))}", ln=0)
    pdf.cell(95, 7, f"Lien: {clean_text(content_info.get('url'))}", ln=1)
    pdf.ln(10)
    
    # Section 2: Faits
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, "II. EXPOSÉ DES FAITS", ln=1, border='B')
    
    pdf.set_font("Arial", '', 10)
    facts = f"""
Le {datetime.now().strftime('%d/%m/%Y')}, j'ai constaté la publication suivante sur {content_info['platform']} :

« {clean_text(content_info['comment'])} »

Ce contenu constitue selon moi les infractions détaillées ci-dessous.
"""
    pdf.multi_cell(190, 7, facts)
    pdf.ln(5)
    
    # Section 3: Analyse Juridique
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, "III. ANALYSE JURIDIQUE", ln=1, border='B')
    
    # Tableau des infractions
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(100, 8, "INFRACTION", border=1, ln=0)
    pdf.cell(90, 8, "PEINE ENCOURUE", border=1, ln=1)
    
    pdf.set_font("Arial", '', 9)
    for offense in analysis.get("infractions", []):
        pdf.cell(100, 7, f"{offense.get('article')} : {offense.get('description')}", border=1)
        pdf.cell(90, 7, offense.get("peine", "N/A"), border=1, ln=1)
    
    pdf.ln(5)
    
    # Détails complémentaires
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(95, 7, "CHANCES DE SUCCÈS:", ln=0)
    pdf.cell(95, 7, f"DELAI PRESCRIPTION:", ln=1)
    
    pdf.set_font("Arial", '', 9)
    pdf.cell(95, 7, analysis.get("success_chance", "N/A"), ln=0)
    pdf.cell(95, 7, analysis.get("delais", {}).get("prescription", "N/A"), ln=1)
    pdf.ln(5)
    
    # Section Preuves
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(190, 7, "PREUVES NÉCESSAIRES:", ln=1)
    
    pdf.set_font("Arial", '', 9)
    for proof in analysis.get("preuves", []):
        pdf.cell(190, 6, f"- {proof}", ln=1)
    
    pdf.ln(8)
    
    # Section Coûts
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(190, 7, "ESTIMATION DES COÛTS:", ln=1)
    
    costs = analysis.get("couts", {})
    pdf.set_font("Arial", '', 9)
    pdf.cell(95, 6, "Dépôt de plainte:", ln=0)
    pdf.cell(95, 6, costs.get("plainte", "Gratuit"), ln=1)
    
    pdf.cell(95, 6, "Honoraires avocat:", ln=0)
    pdf.cell(95, 6, costs.get("avocat", "Variable"), ln=1)
    
    pdf.cell(95, 6, "Coût total estimé:", ln=0)
    pdf.cell(95, 6, costs.get("total", "N/A"), ln=1)
    pdf.ln(10)
    
    # Signature
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(190, 7, "Fait à ____________________________________, le _________________________", ln=1, align='C')
    pdf.ln(15)
    pdf.cell(190, 7, "Signature précédée de la mention « Lu et approuvé »", ln=1, align='C')
    
    # Pied de page
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(190, 5, "Document généré par HateClick - Ne remplace pas une consultation juridique", ln=1, align='C')
    
    # Sauvegarde temporaire
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    pdf.output(temp_file.name)
    return temp_file.name

# Écrans Streamlit (inchangés)
def screen_report():
    # ... [inchangé]
    pass

def screen_analysis():
    # ... [inchangé]
    pass

def screen_complaint():
    # ... [inchangé]
    pass

# Navigation principale
def main():
    st.sidebar.title("⚖️ HateClick")
    st.sidebar.markdown("""
    **Outil officiel de signalement**  
    Conforme à la procédure pénale française  
    """)
    
    if st.session_state.current_screen == 1:
        screen_report()
    elif st.session_state.current_screen == 2:
        screen_analysis()
    elif st.session_state.current_screen == 3:
        screen_complaint()

if __name__ == "__main__":
    main()
