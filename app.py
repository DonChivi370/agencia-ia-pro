import streamlit as st
import google.generativeai as genai
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Configuración de página
st.set_page_config(page_title="Agencia IA Pro", layout="wide")

# 1. Configurar IA
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Falta la clave GEMINI_API_KEY en los Secrets.")

# 2. Conexión a Google Sheets (Soporte directo para URL)
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=60)
def cargar_datos():
    try:
        # Obtenemos la URL de los secrets
        url_sheet = st.secrets["connections"]["gsheets"]["spreadsheet"]
        
        # Leemos las hojas usando la URL directa para evitar el Error 404
        df_c = conn.read(spreadsheet=url_sheet, worksheet="Clientes", ttl=0)
        df_p = conn.read(spreadsheet=url_sheet, worksheet="Configuracion", ttl=0)
        
        # Limpieza de nombres de columnas
        df_c.columns = df_c.columns.str.strip()
        
        # Extraer el Prompt Maestro (Celda B1 de la hoja Configuracion)
        prompt = df_p.iloc[0, 1] 
        return df_c, prompt
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None, None

df, prompt_maestro = cargar_datos()

# 3. Interfaz de Usuario
st.title("🚀 Gestión Agencia IA")

if df is not None:
    st.sidebar.header("Panel de Control")
    
    # Buscador de clientes
    cliente_sel = st.sidebar.selectbox(
        "Buscar cliente:", 
        options=df["Nombre_Local"].unique().tolist(),
        index=None,
        placeholder="Selecciona un local..."
    )

    if cliente_sel:
        # Extraer datos del cliente seleccionado
        c = df[df["Nombre_Local"] == cliente_sel].iloc[0]
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Ficha del Cliente")
            st.info(f"**Dueño:** {c['Dueño']}")
            st.write(f"**Estatus:** {c.get('Estatus', 'Activo')}")
            st.write(f"**Tipo:** {c.get('Tipo_Cliente', 'Individual')}")
            st.write(f"**Fase:** {c.get('Fase_Protocolo', 'N/A')}")
            
            if 'Facturas_Pendientes' in c and str(c['Facturas_Pendientes']).lower() == "sí":
                st.warning("⚠️ Facturas Pendientes")

        with col2:
            st.subheader("Asistente de Estrategia")
            tema = st.text_area("¿Qué necesitas comunicar o resolver?")
            
            if st.button("Generar Mensaje Profesional"):
                if tema:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    # Creamos el contexto completo para Gemini
                    contexto = f"PROMPT MAESTRO:\n{prompt_maestro}\n\nDATOS DEL CLIENTE:\n{c.to_dict()}\n\nSOLICITUD:\n{tema}"
                    
                    with st.spinner("IA analizando protocolo..."):
                        try:
                            res = model.generate_content(contexto)
                            st.success("Mensaje Sugerido:")
                            st.markdown(res.text)
                        except Exception as e:
                            st.error(f"Error de la IA: {e}")
                else:
                    st.warning("Por favor, escribe un tema antes de generar.")
else:
    st.info("Configura los Secrets para conectar con la base de datos.")
