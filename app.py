import streamlit as st
import google.generativeai as genai
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Agencia IA Pro", layout="wide")

# 2. CONECTAR IA
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 3. CARGAR DATOS
@st.cache_data(ttl=60)
def cargar_datos():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)

        # Leer clientes
        df_c = conn.read(worksheet="Clientes", ttl=0, usecols=list(range(7)))
        df_c.columns = df_c.columns.str.strip()
        df_c = df_c.dropna(subset=["Nombre_Local"])

        # Leer configuracion — el prompt está en el HEADER de la columna 1
        df_p = conn.read(worksheet="Configuracion", ttl=0, header=0)
        prompt = df_p.columns[1]  # ← FIX CLAVE: el prompt está aquí

        return df_c, prompt
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None, None

df, prompt_maestro = cargar_datos()

# 4. INTERFAZ
st.title("🚀 Gestión Agencia IA Pro")

if df is not None:
    st.sidebar.header("Panel de Control")
    cliente_sel = st.sidebar.selectbox(
        "Selecciona un local:",
        options=df["Nombre_Local"].unique().tolist(),
        index=None,
        placeholder="Escribe el nombre..."
    )

    if cliente_sel:
        c = df[df["Nombre_Local"] == cliente_sel].iloc[0]
        col1, col2 = st.columns([1, 2])

        with col1:
            st.subheader("📋 Ficha del Cliente")
            st.info(f"**Dueño:** {c['Dueño']}")
            st.write(f"**Estatus:** {c.get('Estatus', 'N/A')}")
            st.write(f"**Fase:** {c.get('Fase_Protocolo', 'N/A')}")
            st.write(f"**Tipo:** {c.get('Tipo_Cliente', 'N/A')}")
            if str(c.get('Facturas_Pendientes', '')).lower() == "sí":
                st.warning("⚠️ Facturas Pendientes")
            if pd.notna(c.get('Notas_Criticas')):
                st.error(f"📌 Nota: {c['Notas_Criticas']}")

        with col2:
            st.subheader("🤖 Asistente")
            tema = st.text_area("¿Qué necesitas?")
            if st.button("Generar Mensaje"):
                if tema:
                    with st.spinner("Generando..."):
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        res = model.generate_content(
                            f"{prompt_maestro}\n\nCliente: {c.to_dict()}\n\nTarea: {tema}"
                        )
                    st.success("Sugerencia:")
                    st.markdown(res.text)
else:
    st.info("Conectando con Google Sheets...")
