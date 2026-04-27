import streamlit as st
import pandas as pd
from groq import Groq

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Agencia IA Pro", layout="wide")

# 2. CONECTAR IA
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# 3. CARGAR DATOS
@st.cache_data(ttl=60)
def cargar_datos():
    try:
        sheet_id = "1I-xZ_0KapMCm6xDEX1GSC5z3L9sw0KPBH58c_HBtt44"
        url_clientes = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=Clientes"
        url_config = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=Configuracion"
        
        df_c = pd.read_csv(url_clientes)
        df_p = pd.read_csv(url_config)
        
        df_c.columns = df_c.columns.str.strip()
        df_c = df_c.dropna(subset=["Nombre_Local"])
        prompt = df_p.columns[1]
        
        return df_c, prompt
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None, None

df, prompt_maestro = cargar_datos()

# 4. FUNCIÓN PARA CONSTRUIR CONTEXTO ESPECIAL
def construir_contexto(cliente, tema):
    estatus = str(cliente.get('Estatus', '')).strip().lower()
    facturas = str(cliente.get('Facturas_Pendientes', '')).strip().lower()
    
    contexto_extra = ""

    if estatus == "baja":
        contexto_extra += """
        
⚠️ INSTRUCCIÓN ESPECIAL - CLIENTE DE BAJA:
Este cliente está dado de BAJA. Al final del mensaje DEBES incluir una coletilla natural 
para intentar reactivarlo. Usa el módulo de Recuperación de Bajas del prompt: recuérdale 
que su competencia está ganando terreno, que la Tarjeta Digital y el QR son herramientas 
que ahora mismo no está aprovechando, y pregunta si quiere reactivar el servicio.
"""

    if facturas == "sí":
        contexto_extra += """
        
⚠️ INSTRUCCIÓN ESPECIAL - FACTURAS PENDIENTES:
Este cliente tiene facturas pendientes de pago. Al final del mensaje DEBES incluir una 
coletilla delicada para recordárselo. Usa el módulo de Cobro Delicado del prompt: 
menciona que hay un pequeño desajuste administrativo con los últimos recibos y que es 
clave regularizarlo para no pausar el ritmo técnico ni perder el posicionamiento ganado.
"""

    if estatus == "baja" and facturas == "sí":
        contexto_extra += """
        
⚠️ NOTA ADICIONAL: El cliente está de baja Y tiene facturas pendientes. 
Prioriza primero el cobro de facturas y luego la reactivación del servicio.
"""

    return f"{prompt_maestro}{contexto_extra}\n\nCliente: {cliente.to_dict()}\n\nTarea: {tema}"


# 5. INTERFAZ
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

            estatus = str(c.get('Estatus', '')).strip().lower()
            facturas = str(c.get('Facturas_Pendientes', '')).strip().lower()

            if estatus == "baja":
                st.error("🔴 Cliente de BAJA — se añadirá coletilla de reactivación")
            if facturas == "sí":
                st.warning("⚠️ Facturas Pendientes — se añadirá coletilla de cobro")
            if pd.notna(c.get('Notas_Criticas')) and str(c.get('Notas_Criticas')) != 'nan':
                st.error(f"📌 Nota: {c['Notas_Criticas']}")

        with col2:
            st.subheader("🤖 Asistente")
            tema = st.text_area("¿Qué necesitas?")
            if st.button("Generar Mensaje"):
                if tema:
                    with st.spinner("Generando mensaje..."):
                        try:
                            prompt_final = construir_contexto(c, tema)
                            respuesta = client.chat.completions.create(
                                model="llama-3.3-70b-versatile",
                                messages=[
                                    {"role": "system", "content": prompt_final},
                                    {"role": "user", "content": tema}
                                ],
                                max_tokens=1024
                            )
                            st.success("Sugerencia:")
                            st.markdown(respuesta.choices[0].message.content)
                        except Exception as e:
                            st.error(f"Error IA: {type(e).__name__}: {e}")
                else:
                    st.warning("Escribe qué necesitas antes de generar.")
else:
    st.info("Conectando con Google Sheets...")
