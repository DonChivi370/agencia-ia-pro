import streamlit as st
import google.generativeai as genai
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Agencia IA Pro", layout="wide")

# 1. Configurar IA
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("Falta la GEMINI_API_KEY en los Secrets.")

# 2. Conexión a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=60)
def cargar_datos():
    try:
        # Intentamos obtener la URL de varias formas por si acaso
        try:
            url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        except:
            url = st.secrets["spreadsheet"] # Ruta alternativa
        
        # Lectura directa
        df_c = conn.read(spreadsheet=url, worksheet="Clientes", ttl=0)
        df_p = conn.read(spreadsheet=url, worksheet="Configuracion", ttl=0)
        
        df_c.columns = df_c.columns.str.strip()
        prompt = df_p.iloc[0, 1] 
        return df_c, prompt
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None, None

df, prompt_maestro = cargar_datos()

# 3. Interfaz
st.title("🚀 Gestión Agencia IA")

if df is not None:
    cliente_sel = st.sidebar.selectbox(
        "Buscar cliente:", 
        options=df["Nombre_Local"].unique().tolist(),
        index=None,
        placeholder="Selecciona un local..."
    )

    if cliente_sel:
        c = df[df["Nombre_Local"] == cliente_sel].iloc[0]
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Ficha del Cliente")
            st.info(f"**Dueño:** {c['Dueño']}")
            st.write(f"**Estatus:** {c.get('Estatus', 'Activo')}")
            st.write(f"**Fase:** {c.get('Fase_Protocolo', 'N/A')}")
            
        with col2:
            st.subheader("Asistente de Estrategia")
            tema = st.text_area("¿Qué necesitas resolver?")
            
            if st.button("Generar Mensaje"):
                if tema:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    ctx = f"PROMPT:\n{prompt_maestro}\n\nCLIENTE:\n{c.to_dict()}\n\nTAREA:\n{tema}"
                    res = model.generate_content(ctx)
                    st.markdown(res.text)
else:
    st.info("Revisa la configuración de tus Secrets y la URL del Excel.")
