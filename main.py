import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import sqlite3
import pandas as pd

# --- 1. CONFIGURATION SÉCURISÉE ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    API_KEY = "SECURED"

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# --- 2. FONCTIONS BASE DE DONNÉES ---
def sauvegarder_repas(nom, cal, prot, glu, lip):
    conn = sqlite3.connect('taf_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS historique
                 (date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, nom TEXT, cal INTEGER, prot REAL, glu REAL, lip REAL)''')
    c.execute("INSERT INTO historique (nom, cal, prot, glu, lip) VALUES (?, ?, ?, ?, ?)",
              (nom, cal, prot, glu, lip))
    conn.commit()
    conn.close()

# --- 3. INTERFACE UTILISATEUR ---
st.set_page_config(page_title="TAF : Analyseur", page_icon="🍎")
st.title("📸 TAF : Analyseur")

uploaded_file = st.file_uploader("Prends ton plat en photo...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Ton plat", use_column_width=True)
    
    if st.button("Calculer les calories 🚀"):
        with st.spinner("Analyse en cours..."):
            prompt = """
            Analyse l'image. Réponds UNIQUEMENT en JSON :
            {
                "plat": "nom", "calories": 400, "proteines": 25, 
                "glucides": 40, "lipides": 15, "note_perte": 4, "note_prise": 3
            }
            """
            response = model.generate_content([prompt, image])
            
            try:
                # Extraction et nettoyage du JSON
                clean_res = response.text.replace('```json', '').replace('```', '').strip()
                res = json.loads(clean_res)
                
                # Sauvegarde auto
                sauvegarder_repas(res['plat'], res['calories'], res['proteines'], res['glucides'], res['lipides'])

                # --- AFFICHAGE DES RÉSULTATS ---
                st.header(f"🍴 {res['plat']}")
                st.metric("TOTAL MANGÉES", f"{res['calories']} kcal")
                
                st.markdown("---")
                
                # BARRES DE PROGRESSION
                st.write(f"**Protéines :** {res['proteines']}g")
                st.progress(min(res['proteines']/60, 1.0))

                st.write(f"**Glucides :** {res['glucides']}g")
                st.progress(min(res['glucides']/100, 1.0))

                st.write(f"**Lipides :** {res['lipides']}g")
                st.progress(min(res['lipides']/50, 1.0))
                
                st.markdown("---")

                # NOTES
                col_a, col_b = st.columns(2)
                col_a.write(f"Perte de Poids\n{'⭐' * res['note_perte']}")
                col_b.write(f"Prise de Masse\n{'⭐' * res['note_prise']}")

            except:
                st.error("L'IA a eu un petit bug. Réessaie !")
