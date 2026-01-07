import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import sqlite3
import pandas as pd

# --- 1. CONFIGURATION SÉCURISÉE ---
# On récupère la clé depuis les secrets de Streamlit Cloud
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    # Si tu lances en local, il cherchera une clé manuelle
    API_KEY = "AIzaSyDtOzqo5bPUEAV4pNPhbtXaQvCXTVJhxPM"

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

# --- 3. INTERFACE & STYLE ---
st.set_page_config(page_title="TAF Nutrition", layout="centered")

st.markdown("""
    <style>
    .total-box { background-color: #f0f2f6; padding: 30px; border-radius: 20px; text-align: center; margin: 20px 0; }
    .score-box { background-color: #ffffff; border: 1px solid #e0e0e0; padding: 15px; border-radius: 15px; text-align: center; margin-top: 10px; }
    .macro-label { font-weight: bold; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

menu = st.sidebar.selectbox("Menu TAF", ["📷 Scanner mon plat", "📅 Mon Journal"])

if menu == "📷 Scanner mon plat":
    st.title("📸 TAF : Analyseur")
    uploaded_file = st.file_uploader("Partage ton plat avec tes amis...", type=['jpg', 'png', 'jpeg'])

    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, use_container_width=True)

        if st.button("Calculer les calories 🚀", use_container_width=True):
            try:
                with st.spinner("L'IA TAF analyse ton assiette..."):
                    prompt = """Analyse cette image. Réponds UNIQUEMENT en JSON : 
                    {"plat": "nom", "calories": 0, "proteines": 0, "glucides": 0, "lipides": 0, "note_perte_poids": 0, "note_prise_masse": 0}"""
                    response = model.generate_content([prompt, img])
                    data = json.loads(response.text.replace('```json', '').replace('```', '').strip())

                    # Affichage
                    st.markdown(f"<h2 style='text-align: center;'>{data['plat']}</h2>", unsafe_allow_html=True)
                    st.markdown(f'<div class="total-box"><p>TOTAL MANGÉES</p><h1>{data['calories']} kcal</h1></div>', unsafe_allow_html=True)

                    # Notes
                    c_a, c_b = st.columns(2)
                    c_a.markdown(f'<div class="score-box">Perte de Poids<br>{"⭐"*int(data["note_perte_poids"])}</div>', unsafe_allow_html=True)
                    c_b.markdown(f'<div class="score-box">Prise de Masse<br>{"⭐"*int(data["note_prise_masse"])}</div>', unsafe_allow_html=True)

                    sauvegarder_repas(data['plat'], data['calories'], data['proteines'], data['glucides'], data['lipides'])
                    st.success("Enregistré dans ton historique local !")
            except Exception as e:
                st.error(f"Erreur : {e}")

elif menu == "📅 Mon Journal":
    st.title("📅 Ton Journal")
    try:
        conn = sqlite3.connect('taf_data.db')
        df = pd.read_sql_query("SELECT * FROM historique ORDER BY date DESC", conn)
        st.metric("Total Journée", f"{df['cal'].sum()} kcal")
        st.dataframe(df)
        conn.close()
    except:
        st.info("Rien à afficher pour le moment.")