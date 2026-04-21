import streamlit as st
import google.generativeai as genai
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Agencia IA Pro", layout="wide")

# 2. CONECTAR GEMINI
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 3. CARGAR DATOS
@st.cache_data(ttl=60)
def cargar_datos():
    try:
        # Usamos la conexión oficial de Streamlit
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # Leemos las hojas. spreadsheet=None hace que use el link de los Secrets automáticamente
        df_clientes = conn.read(worksheet="Clientes", ttl=0)
        df_config = conn.read(worksheet="Configuracion", ttl=0)
        
        df_clientes.columns = df_clientes.columns.str.strip()
        prompt = df_config.iloc[0, 1]
        
        return df_clientes, prompt
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None, None

df, prompt_maestro = cargar_datos()

# 4. INTERFAZ
st.title("🚀 Gestión Agencia IA Pro")

if df is not None:
    cliente_sel = st.sidebar.selectbox(
        "Selecciona un cliente:",
        options=df["Nombre_Local"].unique().tolist(),
        index=None,
        placeholder="Escribe para buscar..."
    )

    if cliente_sel:
        c = df[df["Nombre_Local"] == cliente_sel].iloc[0]
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("📋 Ficha")
            st.info(f"**Dueño:** {c['Dueño']}")
            st.write(f"**Tipo:** {c.get('Tipo_Cliente', 'N/A')}")
            if str(c.get('Facturas_Pendientes', '')).lower() == 'sí':
                st.warning("⚠️ Facturas Pendientes")

        with col2:
            st.subheader("🤖 Asistente")
            consulta = st.text_area("¿Qué necesitas resolver?")
            
            if st.button("Generar Respuesta"):
                if consulta:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    ctx = f"PROMPT:\n{prompt_maestro}\n\nCLIENTE:\n{c.to_dict()}\n\nTAREA:\n{consulta}"
                    res = model.generate_content(ctx)
                    st.success("Sugerencia:")
                    st.markdown(res.text)
else:
    st.info("Conectando con la base de datos...")
