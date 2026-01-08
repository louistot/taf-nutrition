import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import sqlite3
import pandas as pd
from streamlit_option_menu import option_menu

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="TAF Nutrition", page_icon="🍎", layout="centered")

# Récupération sécurisée de la clé
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    API_KEY = "SECURED"

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# --- 2. BASE DE DONNÉES ---
def sauvegarder_repas(nom, cal, prot, glu, lip):
    conn = sqlite3.connect('taf_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS historique
                 (date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, nom TEXT, cal INTEGER, prot REAL, glu REAL, lip REAL)''')
    c.execute("INSERT INTO historique (nom, cal, prot, glu, lip) VALUES (?, ?, ?, ?, ?)",
              (nom, cal, prot, glu, lip))
    conn.commit()
    conn.close()

# --- 3. BARRE DE NAVIGATION (STYLE APPLE EN BAS) ---
# Ce composant crée la barre horizontale comme sur ton image 4320
selected = option_menu(
    menu_title=None, 
    options=["Scanner", "Historique"], 
    icons=["camera", "clock-history"], 
    menu_icon="cast", 
    default_index=0, 
    orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background-color": "#0E1117", "border-radius": "0px"},
        "icon": {"color": "white", "font-size": "20px"}, 
        "nav-link": {"font-size": "16px", "text-align": "center", "margin":"0px", "--hover-color": "#262730"},
        "nav-link-selected": {"background-color": "#FF4B4B"},
    }
)

# --- PAGE SCANNER ---
if selected == "Scanner":
    st.title("📸 TAF : Analyseur")
    uploaded_file = st.file_uploader("Charge ton plat...", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, use_column_width=True)
        
        if st.button("Calculer les calories 🚀", use_container_width=True):
            with st.spinner("Analyse par l'IA..."):
                try:
                    prompt = """
                Tu es un nutritionniste expert. Analyse cette photo de repas.
                1. Identifie chaque aliment et estime son poids en grammes.
                2. Calcule les calories et macros (P, G, L) basés sur ces poids.

                Réponds UNIQUEMENT au format JSON strict : {'plat': 'nom', 'calories': 0, 'proteines': 0, 'glucides': 0, 'lipides': 0, 'note_perte': 0, 'note_prise': 0}"
                    response = model.generate_content([prompt, image])
                    res = json.loads(response.text.replace('```json', '').replace('```', '').strip())
                    
                    sauvegarder_repas(res['plat'], res['calories'], res['proteines'], res['glucides'], res['lipides'])

                    # AFFICHAGE STYLE IMG_4319
                    st.header(f"🍴 {res['plat']}")
                    st.metric("TOTAL MANGÉES", f"{res['calories']} kcal")
                    st.markdown("---")
                    
                    # Les 3 colonnes de Macros
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.caption("Glucides")
                        st.progress(min(res['glucides']/200, 1.0))
                        st.subheader(f"{res['glucides']}g")
                    with col2:
                        st.caption("Protéines")
                        st.progress(min(res['proteines']/100, 1.0))
                        st.subheader(f"{res['proteines']}g")
                    with col3:
                        st.caption("Lipides")
                        st.progress(min(res['lipides']/80, 1.0))
                        st.subheader(f"{res['lipides']}g")

                    st.markdown("---")
                    # Les notes étoiles
                    c1, c2 = st.columns(2)
                    c1.write(f"**Perte de Poids**\n{'⭐' * res['note_perte']}")
                    c2.write(f"**Prise de Masse**\n{'⭐' * res['note_prise']}")

                except Exception as e:
                    st.error("Limite atteinte ou erreur réseau. Réessaie plus tard !")

# --- PAGE HISTORIQUE ---
else:
    st.title("📅 Mon Historique")
    conn = sqlite3.connect('taf_data.db')
    try:
        df = pd.read_sql_query("SELECT * FROM historique ORDER BY date DESC", conn)
        if not df.empty:
            st.line_chart(df.set_index('date')['cal'])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Aucun repas enregistré.")
    except:
        st.info("Historique vide.")
    finally:
        conn.close()
