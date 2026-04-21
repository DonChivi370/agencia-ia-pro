import streamlit as st
import google.generativeai as genai
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Agencia IA Pro", layout="wide")

# 2. CONECTAR IA
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 3. CARGAR DATOS (Versión Blindada)
@st.cache_data(ttl=60)
def cargar_datos():
    try:
        # Extraemos la URL directamente para que no haya pérdida
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # Leemos especificando la URL en cada llamada (esto evita el 404)
        df_c = conn.read(spreadsheet=url, worksheet="Clientes", ttl=0)
        df_p = conn.read(spreadsheet=url, worksheet="Configuracion", ttl=0)
        
        # Limpieza de nombres de columnas
        df_c.columns = df_c.columns.str.strip()
        
        # Extraer Prompt (Celda B1 de Configuracion)
        prompt = df_p.iloc[0, 1] 
        return df_c, prompt
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None, None

df, prompt_maestro = cargar_datos()

# 4. INTERFAZ
st.title("🚀 Gestión Agencia IA Pro")

if df is not None:
    st.sidebar.header("Panel de Control")
    
    # Buscador de locales
    cliente_sel = st.sidebar.selectbox(
        "Selecciona un local:",
        options=df["Nombre_Local"].unique().tolist(),
        index=None,
        placeholder="Escribe el nombre del negocio..."
    )

    if cliente_sel:
        c = df[df["Nombre_Local"] == cliente_sel].iloc[0]
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("📋 Ficha del Cliente")
            st.info(f"**Dueño:** {c['Dueño']}")
            st.write(f"**Estatus:** {c.get('Estatus', 'N/A')}")
            st.write(f"**Fase:** {c.get('Fase_Protocolo', 'N/A')}")
            
            if str(c.get('Facturas_Pendientes', '')).lower() == "sí":
                st.warning("⚠️ Facturas Pendientes")

        with col2:
            st.subheader("🤖 Asistente Estratégico")
            tema = st.text_area("¿Sobre qué quieres escribirle?")
            
            if st.button("Generar Mensaje Profesional"):
                if tema:
                    with st.spinner("IA analizando protocolo..."):
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        contexto = f"PROMPT MAESTRO:\n{prompt_maestro}\n\nDATOS CLIENTE:\n{c.to_dict()}\n\nPETICIÓN:\n{tema}"
                        res = model.generate_content(contexto)
                        st.success("Mensaje sugerido:")
                        st.markdown(res.text)
                else:
                    st.warning("Escribe una duda o tema primero.")
else:
    st.info("Esperando conexión con Google Sheets...")
