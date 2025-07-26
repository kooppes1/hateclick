import streamlit as st
from datetime import datetime
from fpdf import FPDF
import tempfile
import os
from fpdf.enums import XPos, YPos

# Initialize session state
if 'current_screen' not in st.session_state:
    st.session_state.current_screen = 1

# Safe text function for PDF generation
def safe_text(text):
    return text.encode('latin-1', 'replace').decode('latin-1') if text else ""

# Mock AI analysis function
def analyze_comment(comment_text, platform):
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

# PDF generation function with Unicode support
def generate_pdf(user_info, comment_info, analysis_result):
    pdf = FPDF()
    pdf.add_page()
    
    # Configure Unicode support
    pdf.set_font("Helvetica", size=12)
    
    # Header
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(0, 10, safe_text("Plainte pour propos haineux en ligne"), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.ln(15)
    
    # User information
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(0, 10, safe_text("Informations du plaignant"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 10, safe_text(f"Nom: {user_info.get('name', 'Non renseigné')}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 10, safe_text(f"Email: {user_info.get('email', 'Non renseigné')}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 10, safe_text(f"Téléphone: {user_info.get('phone', 'Non renseigné')}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(10)
    
    # Incident details
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(0, 10, safe_text("Détails de l'incident"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 10, safe_text(f"Plateforme: {comment_info['platform']}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 10, safe_text(f"Auteur: {comment_info.get('author', 'Inconnu')}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 10, safe_text(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)
    
    # Comment
    pdf.multi_cell(0, 10, safe_text(f"Commentaire signalé: {comment_info['comment']}"))
    pdf.ln(10)
    
    # Analysis
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(0, 10, safe_text("Analyse juridique"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 10, safe_text(f"Infractions potentielles: {', '.join(analysis_result['offenses'])}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.multi_cell(0, 10, safe_text(f"Conseil juridique: {analysis_result['legal_advice']}"))
    
    # Footer
    pdf.ln(20)
    pdf.set_font("Helvetica", 'I', 10)
    pdf.cell(0, 10, safe_text("Document généré automatiquement par HateClick v0.1 - Ne remplace pas un conseil juridique professionnel"), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    
    # Save PDF
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    pdf_path = temp_file.name
    pdf.output(pdf_path)
    temp_file.close()
    
    return pdf_path

# [Rest of your code remains exactly the same from screen_report() through main()]
