import streamlit as st
from datetime import datetime
from fpdf import FPDF
import tempfile
import json
import re
from openai import OpenAI

# Nettoyage des emojis et caractères incompatibles pour FPDF
def remove_emojis(text):
    text = text.replace('\x00', '')
    clean = re.sub(r'[^\x00-\x7F\xa0-\xffĀ-ſ\s.,!?;:\-()"\'/]+', '', text)
    return clean.strip()

# Initialise le client OpenAI avec la clé dans st.secrets
client = OpenAI(api_key=st.secrets["openai_api_key"])

if 'current_screen' not in st.session_state:
    st.session_state.current_screen = 1

# Analyse IA enrichie
def analyze_comment(comment_text, platform):
    prompt = f"""
Tu es un juriste expert en droit français, spécialisé dans les propos haineux en ligne.
Voici un commentaire posté sur {platform} : \"{comment_text}\"
Analyse s'il contient :
- Une infraction (injure publique, incitation à la haine, diffamation, etc.)
- Son niveau de gravité (faible, moyen, élevé)
- Une qualification juridique claire
- Une recommandation ou conseil légal
- Les sanctions prévues par la loi française
- Les conditions pour que ce soit reçu par un tribunal
- Les chances estimées de succès et le coût d’une procédure

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
            "penalty": {}
        }

# Génération du PDF judiciaire standard

def generate_pdf(user_info, comment_info, analysis_result):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)

    pdf.set_font("Arial", 'B', 14)
    pdf.multi_cell(0, 10, txt="Plainte pour injure publique en ligne")
    pdf.ln(5)

    pdf.set_font("Arial", '', 12)
    pdf.multi_cell(0, 10, txt="À l’attention du Procureur de la République")
    pdf.multi_cell(0, 10, txt="[Tribunal judiciaire compétent selon le lieu de l’infraction ou du domicile du plaignant]")

    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt="Je soussigné(e) :", ln=1)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, txt=f"Nom : {remove_emojis(user_info.get('name', 'Non renseigné'))}", ln=1)
    pdf.cell(0, 10, txt=f"Email : {remove_emojis(user_info.get('email', 'Non renseigné'))}", ln=1)
    pdf.cell(0, 10, txt=f"Téléphone : {remove_emojis(user_info.get('phone', 'Non renseigné'))}", ln=1)

    pdf.ln(10)
    pdf.multi_cell(0, 10, txt="Déclare avoir été victime d’un commentaire injurieux en ligne, constituant une infraction pénale au sens des articles 29 et 33 de la loi du 29 juillet 1881 sur la liberté de la presse.")

    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt="1. Informations sur l’infraction :", ln=1)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, txt=f"Plateforme : {remove_emojis(comment_info['platform'])}", ln=1)
    pdf.cell(0, 10, txt=f"Date des faits : {datetime.now().strftime('%d/%m/%Y')}", ln=1)
    pdf.cell(0, 10, txt=f"Auteur : {remove_emojis(comment_info.get('author', 'Inconnu'))}", ln=1)
    pdf.multi_cell(0, 10, txt=f"Commentaire incriminé : \"{remove_emojis(comment_info['comment'])}\"")

    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt="2. Qualification juridique :", ln=1)
    pdf.set_font("Arial", '', 12)
    pdf.multi_cell(0, 10, txt="L’expression citée constitue une injure publique, définie par l’article 29 alinéa 2 de la loi de 1881 comme : \n> Toute expression outrageante, terme de mépris ou invective qui ne renferme l'imputation d'aucun fait précis.")

    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt="3. Sanctions encourues :", ln=1)
    pdf.set_font("Arial", '', 12)
    penalty = analysis_result.get("penalty", {})
    pdf.multi_cell(0, 10, txt=remove_emojis(penalty.get("text", "Non précisé")))

    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt="4. Conditions juridiques de recevabilité :", ln=1)
    pdf.set_font("Arial", '', 12)
    for cond in penalty.get("conditions", []):
        pdf.multi_cell(0, 10, txt=f"- {remove_emojis(cond)}")

    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt="5. Chances et coûts estimés :", ln=1)
    pdf.set_font("Arial", '', 12)
    pdf.multi_cell(0, 10, txt=f"Chances estimées : {remove_emojis(penalty.get('chances', ''))}")
    pdf.multi_cell(0, 10, txt=f"Coût estimé : {remove_emojis(penalty.get('estimated_cost', ''))}")

    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt="6. Demande :", ln=1)
    pdf.set_font("Arial", '', 12)
    pdf.multi_cell(0, 10, txt="Je vous demande de bien vouloir enregistrer cette plainte pour injure publique en ligne et d’engager les poursuites appropriées contre l’auteur des faits.")

    pdf.ln(10)
    pdf.cell(0, 10, txt=f"Fait à [ville], le {datetime.now().strftime('%d/%m/%Y')}", ln=1)
    pdf.cell(0, 10, txt="Signature :", ln=1)

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    pdf.output(temp_file.name)
    return temp_file.name
