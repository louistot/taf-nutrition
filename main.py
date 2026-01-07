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
model = genai.GenerativeModel('gemini-1.5-flash')

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

def charger_historique():
    conn = sqlite3.connect('taf_data.db')
    try:
        df = pd.read_sql_query("SELECT date, nom, cal, prot, glu, lip FROM historique ORDER BY date DESC", conn)
    except:
        df = pd.DataFrame()
    conn.close()
    return df

# --- 3. NAVIGATION ---
st.sidebar.title("Menu TAF")
page = st.sidebar.radio("Aller vers :", ["Scanner mon plat", "Mon Historique"])

if page == "Scanner mon plat":
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
                    clean_res = response.text.replace('```json', '').replace('```', '').strip()
                    res = json.loads(clean_res)
                    sauvegarder_repas(res['plat'], res['calories'], res['proteines'], res['glucides'], res['lipides'])

                    # --- AFFICHAGE STYLE IMG_4319 ---
                    st.header(f"🍴 {res['plat']}")
                    
                    # Grand bloc Calories
                    st.container()
                    st.metric("TOTAL MANGÉES", f"{res['calories']} kcal")
                    
                    st.markdown("---")
                    
                    # Colonnes pour les Macros (Glucides, Protéines, Lipides)
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write("**Glucides**")
                        st.progress(min(res['glucides']/150, 1.0))
                        st.subheader(f"{res['glucides']}g")
                        
                    with col2:
                        st.write("**Protéines**")
                        st.progress(min(res['proteines']/80, 1.0))
                        st.subheader(f"{res['proteines']}g")
                        
                    with col3:
                        st.write("**Lipides**")
                        st.progress(min(res['lipides']/50, 1.0))
                        st.subheader(f"{res['lipides']}g")

                    st.success("Analyse terminée !")
                    st.markdown("---")

                    # Bloc des Notes (Étoiles)
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.write("**Perte de Poids**")
                        st.write("⭐" * res['note_perte'])
                    with col_b:
                        st.write("**Prise de Masse**")
                        st.write("⭐" * res['note_prise'])

                except:
                    st.error("Erreur d'analyse. Réessaie !")

else:
    st.title("📅 Mon Historique")
    historique = charger_historique()
    if not historique.empty:
        st.line_chart(historique.set_index('date')['cal'])
        st.dataframe(historique)
    else:
        st.write("Aucun repas enregistré.")
