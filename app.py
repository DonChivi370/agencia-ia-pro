import streamlit as st
import google.generativeai as genai
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Agencia IA Pro", layout="wide")

# 2. CONFIGURACIÓN DE IA (Gemini)
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Falta la clave GEMINI_API_KEY en los Secrets de Streamlit.")

# 3. FUNCIÓN PARA CARGAR DATOS (Conexión Directa)
@st.cache_data(ttl=60)
def cargar_datos():
    try:
        # Extraemos la URL directamente del secreto
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        
        # Creamos la conexión
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # Leemos las hojas usando los nombres exactos de tu Excel
        df_clientes = conn.read(spreadsheet=url, worksheet="Clientes", ttl=0)
        df_config = conn.read(spreadsheet=url, worksheet="Configuracion", ttl=0)
        
        # Limpiamos espacios en blanco en los nombres de las columnas
        df_clientes.columns = df_clientes.columns.str.strip()
        
        # Obtenemos el Prompt Maestro (Celda B1 de la hoja Configuracion)
        # .iloc[0, 1] accede a la primera fila, segunda columna
        prompt = df_config.iloc[0, 1]
        
        return df_clientes, prompt
    except Exception as e:
        st.error(f"Error de conexión con Google Sheets: {e}")
        return None, None

# Ejecutamos la carga
df, prompt_maestro = cargar_datos()

# 4. INTERFAZ DE USUARIO
st.title("🚀 Gestión Agencia IA Pro")

if df is not None:
    st.sidebar.header("Panel de Control")
    
    # Buscador de clientes basado en la columna 'Nombre_Local'
    cliente_sel = st.sidebar.selectbox(
        "Selecciona un cliente:",
        options=df["Nombre_Local"].unique().tolist(),
        index=None,
        placeholder="Escribe para buscar..."
    )

    if cliente_sel:
        # Filtramos los datos del cliente seleccionado
        c = df[df["Nombre_Local"] == cliente_sel].iloc[0]
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("📋 Información del Cliente")
            st.info(f"**Dueño:** {c['Dueño']}")
            st.write(f"**Tipo:** {c.get('Tipo_Cliente', 'N/A')}")
            st.write(f"**Fase:** {c.get('Fase_Protocolo', 'N/A')}")
            
            # Alerta de facturas
            if 'Facturas_Pendientes' in c and str(c['Facturas_Pendientes']).lower() == "sí":
                st.warning("⚠️ Tiene facturas pendientes.")

        with col2:
            st.subheader("🤖 Asistente de Estrategia")
            consulta = st.text_area("¿Qué necesitas comunicar o resolver con este cliente?")
            
            if st.button("Generar Propuesta con IA"):
                if consulta:
                    with st.spinner("Analizando protocolo y generando respuesta..."):
                        try:
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            # Combinamos el Prompt Maestro con los datos del cliente y la duda actual
                            contexto = f"PROMPT ESTRATÉGICO:\n{prompt_maestro}\n\nDATOS CLIENTE:\n{c.to_dict()}\n\nCONSULTA:\n{consulta}"
                            
                            response = model.generate_content(contexto)
                            st.success("Respuesta Sugerida:")
                            st.markdown(response.text)
                        except Exception as e:
                            st.error(f"Error al generar con IA: {e}")
                else:
                    st.warning("Escribe una consulta para que la IA pueda ayudarte.")
else:
    st.info("Configura correctamente tus Secrets y el Excel para comenzar.")
