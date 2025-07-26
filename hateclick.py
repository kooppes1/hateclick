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

Voici un commentaire posté sur {platform} : \"{comment_text}\"

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
                safe_cond = remove_emojis(cond).strip()
                if len(safe_cond) > 0:
                    try:
                        pdf.multi_cell(0, 10, txt=safe_cond)
                    except:
                        pdf.multi_cell(0, 10, txt="[⚠️ Texte non imprimable supprimé]")

        pdf.cell(200, 10, txt=f"Chances de succès : {analysis_result['penalty']['chances']}", ln=1)
        pdf.cell(200, 10, txt=f"Coût estimé : {analysis_result['penalty']['estimated_cost']}", ln=1)

    pdf.ln(20)
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 10, txt="Document généré automatiquement par HateClick v0.1", ln=1, align='C')

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    pdf.output(temp_file.name)
    return temp_file.name
