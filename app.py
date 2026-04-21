import streamlit as st
import google.generativeai as genai
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. LLAVE API (Sácala de Google AI Studio)
genai.configure(api_key=st.secrets["AIzaSyCBG9PgDrlI22tu4iuq7hjY5xisXYy_LSs"])

# 2. CONEXIÓN AL EXCEL (Lee las dos hojas)
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=600)
def cargar_todo():
    df_clientes = conn.read(worksheet="Clientes")
    df_config = conn.read(worksheet="Configuracion")
    prompt = df_config.iloc[0, 1] # Lee la celda B1 de Configuracion
    return df_clientes, prompt

df, prompt_maestro = cargar_todo()

# 3. INTERFAZ Y BUSCADOR
st.sidebar.title("Agencia Marketing Local")
menu = st.sidebar.radio("Menú:", ["Soporte y Crisis", "Recurrentes", "Cobros y Bajas"])

st.sidebar.markdown("---")
cliente_sel = st.sidebar.selectbox(
    "🔍 Buscar Cliente (escribe nombre):", 
    options=df["Nombre_Local"].tolist(), 
    index=None,
    placeholder="Escribe el nombre del local..."
)

if cliente_sel:
    datos = df[df["Nombre_Local"] == cliente_sel].iloc[0]
    
    if menu == "Soporte y Crisis":
        st.header(f"Gestión: {cliente_sel}")
        st.info(f"Fase: {datos['Fase_Protocolo']} | Tono: {datos['Tipo_Cliente']}")
        msg = st.text_area("Mensaje del cliente:")
        if st.button("Generar Respuesta"):
            model = genai.GenerativeModel('gemini-1.5-flash')
            res = model.generate_content(f"{prompt_maestro}\nContexto: {datos}\nCliente dice: {msg}")
            st.code(res.text)

    elif menu == "Cobros y Bajas":
        st.header("Gestión Administrativa")
        if datos['Facturas_Pendientes'] == "Sí":
            if st.button("🧧 Mensaje Cobro Delicado"):
                model = genai.GenerativeModel('gemini-1.5-flash')
                res = model.generate_content(f"{prompt_maestro}\nGenera un mensaje de cobro delicado para {datos['Dueño']}.")
                st.code(res.text)
        if datos['Estatus'] == "Baja":
            if st.button("🔄 Mensaje Recuperación"):
                model = genai.GenerativeModel('gemini-1.5-flash')
                res = model.generate_content(f"{prompt_maestro}\nGenera un mensaje para recuperar a este cliente resaltando la Tarjeta Digital estilo App.")
                st.code(res.text)
