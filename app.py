import streamlit as st
import google.generativeai as genai
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Agencia IA Pro", layout="wide")

# 2. CONECTAR GEMINI
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 3. CARGAR DATOS (Versión Ultra-Directa)
@st.cache_data(ttl=10) # Reducimos el tiempo de caché para que refresque rápido
def cargar_datos():
    try:
        # Usamos la conexión oficial
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # Obtenemos la URL de los secrets
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        
        # Leemos las hojas (Nombres exactos de tu archivo)
        df_clientes = conn.read(spreadsheet=url, worksheet="Clientes")
        df_config = conn.read(spreadsheet=url, worksheet="Configuracion")
        
        # Limpieza de datos
        df_clientes.columns = df_clientes.columns.str.strip()
        prompt = df_config.iloc[0, 1]
        
        return df_clientes, prompt
    except Exception as e:
        st.error(f"Error detectado: {e}")
        return None, None

df, prompt_maestro = cargar_datos()

# 4. INTERFAZ
st.title("🚀 Gestión Agencia IA Pro")

if df is not None:
    # Sidebar buscador
    st.sidebar.header("Menú de Control")
    # Buscamos la columna Nombre_Local que está en tu CSV
    opciones = df["Nombre_Local"].unique().tolist()
    
    cliente_sel = st.sidebar.selectbox(
        "Selecciona un cliente:",
        options=opciones,
        index=None,
        placeholder="Escribe el nombre del local..."
    )

    if cliente_sel:
        c = df[df["Nombre_Local"] == cliente_sel].iloc[0]
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("📋 Datos del Cliente")
            st.info(f"**Dueño:** {c['Dueño']}")
            st.write(f"**Estatus:** {c.get('Estatus', 'N/A')}")
            st.write(f"**Fase:** {c.get('Fase_Protocolo', 'N/A')}")
            
            if str(c.get('Facturas_Pendientes', '')).lower() == 'sí':
                st.warning("⚠️ Facturas Pendientes")

        with col2:
            st.subheader("🤖 Generador de Estrategia")
            consulta = st.text_area("¿Qué quieres escribirle al cliente?")
            
            if st.button("Generar Mensaje"):
                if consulta:
                    with st.spinner("Generando..."):
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        ctx = f"PROMPT:\n{prompt_maestro}\n\nCLIENTE:\n{c.to_dict()}\n\nTAREA:\n{consulta}"
                        res = model.generate_content(ctx)
                        st.success("Sugerencia de la IA:")
                        st.markdown(res.text)
                else:
                    st.warning("Escribe algo para poder ayudarte.")
else:
    st.info("Conectando con la base de datos de Google Sheets...")
