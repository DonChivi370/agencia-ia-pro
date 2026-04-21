import streamlit as st
import google.generativeai as genai
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Gestor Agencia IA", layout="wide")

# 1. LLAVE API (Configurada desde Secrets para seguridad)
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error("Error con la API Key de Gemini. Revisa los Secrets.")

# 2. CONEXIÓN AL EXCEL
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=300) # Caché de 5 minutos
def cargar_datos():
    try:
        # Forzamos la lectura de las pestañas específicas
        df_clientes = conn.read(worksheet="Clientes", ttl=0)
        df_config = conn.read(worksheet="Configuracion", ttl=0)
        
        # Validación de estructura
        if df_config.empty or "PROMPT_MAESTRO" not in df_config.columns:
            # Si no hay encabezados, intentamos leer la celda B1 directamente
            prompt = df_config.iloc[0, 1] 
        else:
            prompt = df_config["PROMPT_MAESTRO"].iloc[0]
            
        return df_clientes, prompt
    except Exception as e:
        st.error(f"Error crítico al conectar con Google Sheets: {e}")
        return None, None

df, prompt_maestro = cargar_datos()

# 3. INTERFAZ DE USUARIO
st.title("🚀 Panel de Control - Agencia IA")

if df is not None:
    # BARRA LATERAL
    st.sidebar.header("Menú de Navegación")
    modo = st.sidebar.radio("Acción:", ["Asistente de Soporte", "Administración (Cobros/Bajas)"])
    
    st.sidebar.markdown("---")
    
    # BUSCADOR PROFESIONAL
    cliente_nombre = st.sidebar.selectbox(
        "Selecciona un Cliente:",
        options=df["Nombre_Local"].unique(),
        index=None,
        placeholder="Escribe para buscar..."
    )

    if cliente_nombre:
        # Filtramos los datos del cliente seleccionado
        datos_cliente = df[df["Nombre_Local"] == cliente_nombre].iloc[0]
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Ficha del Cliente")
            st.write(f"**Dueño:** {datos_cliente['Dueño']}")
            st.write(f"**Tipo:** {datos_cliente['Tipo_Cliente']}")
            st.write(f"**Fase:** {datos_cliente['Fase_Protocolo']}")
            
            # Alertas visuales
            if datos_cliente['Facturas_Pendientes'].upper() == "SÍ":
                st.warning("⚠️ FACTURAS PENDIENTES")
            if datos_cliente['Estatus'].upper() == "BAJA":
                st.error("🚫 CLIENTE EN BAJA")

        with col2:
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            if modo == "Asistente de Soporte":
                st.subheader("Generador de Mensajes Estratégicos")
                consulta = st.text_area("¿Qué ha pasado o qué necesitas enviarle?")
                
                if st.button("Generar Respuesta Profesional"):
                    with st.spinner("La IA está analizando el protocolo..."):
                        contexto = f"CLIENTE: {datos_cliente.to_dict()}\nPROMPT: {prompt_maestro}\nCONSULTA: {consulta}"
                        response = model.generate_content(contexto)
                        st.success("Respuesta sugerida:")
                        st.code(response.text, language="markdown")

            elif modo == "Administración (Cobros/Bajas)":
                st.subheader("Gestión Administrativa")
                
                if datos_cliente['Facturas_Pendientes'].upper() == "SÍ":
                    if st.button("📩 Generar Mensaje de Cobro (Guante de Seda)"):
                        res = model.generate_content(f"{prompt_maestro}\nActúa como gestor. El cliente {cliente_nombre} debe facturas. Genera mensaje diplomático.")
                        st.code(res.text)
                
                if datos_cliente['Estatus'].upper() == "BAJA":
                    if st.button("🔄 Generar Mensaje de Recuperación"):
                        res = model.generate_content(f"{prompt_maestro}\nCliente en baja. Usa el miedo a la pérdida y menciona la Tarjeta Digital App.")
                        st.code(res.text)
else:
    st.warning("Configura correctamente el enlace del Excel en los Secrets para empezar.")
