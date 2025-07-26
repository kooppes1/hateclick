import streamlit as st
from datetime import datetime
from fpdf import FPDF
import tempfile
import json
import re
from openai import OpenAI

# 🔧 Nettoyage des emojis et caractères incompatibles pour FPDF

def remove_emojis(text):
    if not text:
        return ""
    text = text.replace('\x00', '')
    clean = re.sub(r'[^\x00-\x7F\xa0-\xffĀ-ſ\s.,!?;:\-()"\'/]+', '', text)
    return clean.strip()

# 🔐 Initialise le client OpenAI avec la clé dans st.secrets
client = OpenAI(api_key=st.secrets["openai_api_key"])

# 🧠 Analyse IA enrichie
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

# 📝 Génération du PDF (standard judiciaire)
def generate_pdf(user_info, comment_info, analysis_result):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.multi_cell(190, 10, txt="Plainte pour injure publique en ligne")
    pdf.multi_cell(190, 10, txt="À l’attention du Procureur de la République\n[Tribunal judiciaire compétent]")
    pdf.ln(5)

    pdf.cell(190, 10, txt="Je soussigné(e)", ln=1)
    pdf.cell(190, 10, txt=f"Nom : {remove_emojis(user_info.get('name', 'Non renseigné'))}", ln=1)
    pdf.cell(190, 10, txt=f"Email : {remove_emojis(user_info.get('email', 'Non renseigné'))}", ln=1)
    pdf.cell(190, 10, txt=f"Téléphone : {remove_emojis(user_info.get('phone', 'Non renseigné'))}", ln=1)
    pdf.ln(5)

    pdf.multi_cell(190, 10, txt="Déclare avoir été victime d’un commentaire injurieux en ligne, constituant une infraction pénale au sens des articles 29 et 33 de la loi du 29 juillet 1881 sur la liberté de la presse.")
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, txt="1. Informations sur l’infraction :", ln=1)
    pdf.set_font("Arial", size=12)
    pdf.cell(190, 10, txt=f"Plateforme : {remove_emojis(comment_info['platform'])}", ln=1)
    pdf.cell(190, 10, txt=f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=1)
    pdf.cell(190, 10, txt=f"Auteur : {remove_emojis(comment_info.get('author', 'Inconnu'))}", ln=1)
    pdf.multi_cell(190, 10, txt=f"Commentaire incriminé : {remove_emojis(comment_info['comment'])}")
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, txt="2. Qualification juridique :", ln=1)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(190, 10, txt=remove_emojis(analysis_result.get("reasoning", "")))

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, txt="3. Sanctions encourues :", ln=1)
    penalty = analysis_result.get('penalty', {})
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(190, 10, txt=remove_emojis(penalty.get('text', '')))

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, txt="4. Conditions juridiques :", ln=1)
    pdf.set_font("Arial", size=12)
    for cond in penalty.get('conditions', []):
        pdf.multi_cell(190, 10, txt=f"- {remove_emojis(cond)}")

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, txt="5. Chances et coût estimé :", ln=1)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(190, 10, txt=f"Chances de succès : {remove_emojis(penalty.get('chances', ''))}")
    pdf.multi_cell(190, 10, txt=f"Coût estimé : {remove_emojis(penalty.get('estimated_cost', ''))}")

    pdf.ln(10)
    pdf.multi_cell(190, 10, txt="Je vous demande de bien vouloir enregistrer cette plainte pour injure publique en ligne et d’engager les poursuites appropriées contre l’auteur des faits.")
    pdf.multi_cell(190, 10, txt=f"Fait à ..., le {datetime.now().strftime('%d/%m/%Y')}\nSignature : __________________")
    pdf.ln(10)
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(190, 10, txt="Document généré automatiquement par HateClick v0.1", ln=1, align='C')

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    pdf.output(temp_file.name)
    return temp_file.name

# 🖥️ Interface principale

def screen_report():
    st.title("Signale un commentaire haineux")
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
                st.rerun()

def screen_analysis():
    st.title("Voici ce que nous avons détecté")
    user_input = st.session_state.user_input
    analysis_result = analyze_comment(user_input["comment"], user_input["platform"])
    st.session_state.analysis_result = analysis_result

    st.subheader("Type probable d'infraction")
    for offense in analysis_result["offenses"]:
        st.write(f"- {offense}")

    st.subheader("Gravité")
    st.write(analysis_result["severity"])

    st.subheader("Conseils")
    st.info(analysis_result["legal_advice"])

    if analysis_result.get("reasoning"):
        st.caption("🧠 " + analysis_result["reasoning"])

    if st.button("Générer ma plainte"):
        st.session_state.current_screen = 3
        st.rerun()

def screen_complaint():
    st.title("Plainte générée")
    with st.expander("Vos coordonnées (optionnel)"):
        name = st.text_input("Nom Prénom")
        email = st.text_input("Email")
        phone = st.text_input("Téléphone")
    user_info = {
        "name": name,
        "email": email,
        "phone": phone
    }
    pdf_path = generate_pdf(user_info, st.session_state.user_input, st.session_state.analysis_result)
    with open(pdf_path, "rb") as f:
        st.download_button(
            label="📥 Télécharger la plainte PDF",
            data=f.read(),
            file_name="plainte_hateclick.pdf",
            mime="application/pdf"
        )
    if st.button("Retour à l'accueil"):
        st.session_state.current_screen = 1
        st.rerun()

def main():
    st.set_page_config(page_title="HateClick", layout="centered")
    st.sidebar.title("HateClick v0.1")
    st.sidebar.markdown("""
Prototype de signalement de propos haineux.

Fonctionnalités :
- Analyse juridique par IA 🤖
- Génération de plainte PDF 📝
- Conseils utiles 💡

⚠️ Cette application ne remplace pas un conseil juridique professionnel.
""")

    if 'current_screen' not in st.session_state:
        st.session_state.current_screen = 1

    if st.session_state.current_screen == 1:
        screen_report()
    elif st.session_state.current_screen == 2:
        screen_analysis()
    elif st.session_state.current_screen == 3:
        screen_complaint()

if __name__ == "__main__":
    main()
