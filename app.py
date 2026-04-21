import streamlit as st
import google.generativeai as genai
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Agencia IA Pro", layout="wide")

# 1. Configurar IA (con manejo de errores)
if "GEMINI_API_KEY" in st.secrets:
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    except Exception as e:
        st.error(f"Error al configurar la API de Gemini: {e}")
else:
    st.error("Falta la clave GEMINI_API_KEY en los Secrets.")

# 2. Conexión a Google Sheets (Soporte directo para URL y multi-formato de secretos)
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=60)
def cargar_datos_seguro():
    try:
        # Detección automática del formato de secreto (Nuevo o Antiguo)
        url_sheet = None
        
        # Intentamos el formato nuevo y simplificado primero (Fuerza Bruta)
        try:
            url_sheet = st.secrets["connections"]["spreadsheet"]
        except (KeyError, Exception):
            # Intentamos el formato antiguo jerárquico si el nuevo falla
            try:
                url_sheet = st.secrets["connections"]["gsheets"]["spreadsheet"]
            except (KeyError, Exception):
                st.error("No se pudo encontrar la URL del Spreadsheet en los Secrets. Revisa el formato TOML.")
                return None, None

        # Si tenemos URL, intentamos leer las hojas explícitamente para evitar el 404
        if url_sheet:
            try:
                # Lectura de la hoja 'Clientes' con TTL=0 para ignorar caché local corrupta
                df_c = conn.read(spreadsheet=url_sheet, worksheet="Clientes", ttl=0)
                # Lectura de la hoja 'Configuracion'
                df_p = conn.read(spreadsheet=url_sheet, worksheet="Configuracion", ttl=0)
                
                # Limpieza de nombres de columnas
                df_c.columns = df_c.columns.str.strip()
                df_p.columns = df_p.columns.str.strip()
                
                # Validación de la hoja de configuración
                if df_p.empty:
                     st.error("La hoja 'Configuracion' está vacía.")
                     return None, None

                # Extraer el Prompt Maestro (Celda B1 de la hoja Configuracion)
                # Usamos .iloc[0, 1] que es más robusto si los encabezados cambian
                prompt = df_p.iloc[0, 1] 
                
                # Validación del prompt extraído
                if pd.isna(prompt) or str(prompt).strip() == "":
                    st.error("No se pudo extraer un Prompt Maestro válido de la hoja 'Configuracion'.")
                    return df_c, None

                return df_c, prompt
                
            except Exception as e:
                # Error específico al leer las hojas (ej: nombre de pestaña mal escrito en Excel)
                st.error(f"Error al leer las hojas del Spreadsheet. Verifica los nombres 'Clientes' y 'Configuracion' en Excel. Detalles: {e}")
                return None, None
        else:
            return None, None
            
    except Exception as e:
        # Error general de conexión
        st.error(f"Error crítico de conexión al Spreadsheet: {e}")
        return None, None

df, prompt_maestro = cargar_datos_seguro()

# 3. Interfaz de Usuario
st.title("🚀 Gestión Agencia IA Pro")

# Barra lateral para el buscador
st.sidebar.header("Panel de Control")

if df is not None:
    # Verificación de que la columna existe antes de crear la lista
    if "Nombre_Local" in df.columns:
        # Lista desplegable de clientes (Buscador)
        cliente_sel = st.sidebar.selectbox(
            "Buscar cliente:", 
            options=df["Nombre_Local"].unique().tolist(),
            index=None,
            placeholder="Selecciona un local o escribe para buscar..."
        )

        if cliente_sel:
            # Extraer datos del cliente seleccionado
            datos_cliente = df[df["Nombre_Local"] == cliente_sel].iloc[0]
            
            # Layout de dos columnas
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.subheader("📋 Ficha del Cliente")
                # Mostramos los datos clave con manejo de columnas opcionales
                st.info(f"👤 **Dueño:** {datos_cliente['Dueño']}")
                st.write(f"🏷️ **Estatus:** {datos_cliente.get('Estatus', 'Activo')}")
                st.write(f"🏢 **Tipo:** {datos_cliente.get('Tipo_Cliente', 'Individual')}")
                st.write(f"🔄 **Fase:** {datos_cliente.get('Fase_Protocolo', 'N/A')}")
                
                # Alertas administrativas
                if 'Facturas_Pendientes' in datos_cliente and str(datos_cliente['Facturas_Pendientes']).lower() == "sí":
                    st.warning("⚠️ **ATENCIÓN:** Tiene facturas pendientes de cobro.")
                if 'Estatus' in datos_cliente and str(datos_cliente['Estatus']).lower() == "baja":
                    st.error("🚫 **AVISO:** Este cliente ha solicitado la baja del servicio.")

            with col2:
                st.subheader("💡 Asistente de Estrategia Digital")
                
                if prompt_maestro:
                    tema = st.text_area("¿Qué necesitas resolver o comunicar hoy?", placeholder="Ej: Generar mensaje de cobro diplomático, o mensaje de bienvenida...")
                    
                    if st.button("Generar Mensaje con IA Strategist"):
                        if tema:
                            # Configuración del modelo de Gemini
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            
                            # Creamos el contexto completo para la IA, combinando Prompt Maestro, Datos Cliente y la Petición actual.
                            # Usamos formateo TOML o JSON para el cliente, que la IA entiende muy bien.
                            contexto = f"PROMPT MAESTRO DE AGENCIA:\n{prompt_maestro}\n\nDATOS DEL CLIENTE (Formato Clave-Valor):\n{datos_cliente.to_dict()}\n\nSOLICITUD ACTUAL DEL GESTOR DE LA AGENCIA:\n{tema}"
                            
                            with st.spinner("La IA está analizando el protocolo estratégico para generar tu respuesta..."):
                                try:
                                    res = model.generate_content(contexto)
                                    st.success("🤖 Mensaje Sugerido Generado:")
                                    # Mostramos la respuesta con markdown para que Gemini pueda formatear
                                    st.markdown(res.text)
                                except Exception as e:
                                    st.error(f"Error al generar contenido con la IA: {e}")
                                    st.info("Revisa la GEMINI_API_KEY en los Secrets.")
                        else:
                            st.warning("Por favor, escribe un tema o duda en el cuadro de texto antes de generar el mensaje.")
                else:
                    st.warning("No se ha cargado el Prompt Maestro, la IA no puede funcionar.")
    else:
        st.error("La hoja 'Clientes' no tiene la columna 'Nombre_Local'. Revisa los encabezados del Excel.")
else:
    # Mostramos este mensaje de ayuda si los datos no cargan
    st.info("Esperando conexión con la base de datos de Google Sheets...")
    st.markdown("""
    ### 📝 Checklist de Conexión:
    1.  Revisa que el secreto jerárquico esté así: `st.secrets["connections"]["spreadsheet"]`.
    2.  Verifica la **URL del Spreadsheet** en los Secrets. Debe ser el ID limpio (HBtt44).
    3.  Asegúrate de que en el Excel las pestañas se llamen **'Clientes'** y **'Configuracion'** (tal cual, con C mayúscula).
    4.  El Excel debe estar compartido como **'Cualquier persona con el enlace'** en modo **'Lector'**.
    """)
