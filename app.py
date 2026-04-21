import streamlit as st
import google.generativeai as genai
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Configuración básica
st.set_page_config(page_title="Agencia IA Pro", layout="wide")

# 1. Conexión a la IA
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("Revisa la GEMINI_API_KEY en los Secrets de Streamlit.")

# 2. Conexión al Excel
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=60)
def cargar_datos():
    try:
        # Leemos las hojas
        df_c = conn.read(worksheet="Clientes", ttl=0)
        df_p = conn.read(worksheet="Configuracion", ttl=0)
        
        # Limpiamos nombres de columnas por si hay espacios invisibles
        df_c.columns = df_c.columns.str.strip()
        
        # Sacamos el prompt (Celda B1 de la hoja Configuracion)
        prompt = df_p.iloc[0, 1] 
        return df_c, prompt
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None, None

df, prompt_maestro = cargar_datos()

# 3. Interfaz
st.title("🚀 Gestión Agencia IA")

if df is not None:
    # Buscador en la barra lateral
    st.sidebar.header("Panel de Control")
    cliente_sel = st.sidebar.selectbox(
        "Buscar cliente:", 
        options=df["Nombre_Local"].tolist(),
        index=None,
        placeholder="Selecciona un local..."
    )

    if cliente_sel:
        # Datos del cliente
        c = df[df["Nombre_Local"] == cliente_sel].iloc[0]
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Datos del Cliente")
            st.info(f"**Dueño:** {c['Dueño']}")
            st.write(f"**Tipo:** {c.get('Tipo_Cliente', 'No definido')}")
            st.write(f"**Fase:** {c.get('Fase_Protocolo', 'No definido')}")
            
            # Verificación de facturas (manejando si la columna existe)
            if 'Facturas_Pendientes' in c and str(c['Facturas_Pendientes']).lower() == "sí":
                st.warning("⚠️ Tiene facturas pendientes")

        with col2:
            st.subheader("Generador de Respuestas")
            tema = st.text_area("¿Sobre qué quieres escribirle al cliente?")
            
            if st.button("Generar Mensaje con IA"):
                if tema:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    # Unimos toda la información para la IA
                    contexto = f"PROMPT MAESTRO: {prompt_maestro}\n\nDATOS CLIENTE: {c.to_dict()}\n\nPETICIÓN: {tema}"
                    
                    with st.spinner("Pensando respuesta estratégica..."):
                        res = model.generate_content(contexto)
                        st.success("Respuesta generada:")
                        st.write(res.text)
                else:
                    st.error("Escribe un tema o duda para poder generar el mensaje.")
else:
    st.info("Esperando conexión con Google Sheets...")
