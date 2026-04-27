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

# 4. FUNCIÓN PARA CONSTRUIR PROMPT
def construir_prompt(cliente):
    tipo = str(cliente.get('Tipo_Cliente', '')).strip().lower()
    facturas = str(cliente.get('Facturas_Pendientes', '')).strip().lower()
    estatus = str(cliente.get('Estatus', '')).strip().lower()

    es_baja = tipo == "baja"
    tiene_facturas = facturas in ["si", "sí"]
    es_grupo = estatus == "grupo"

    instrucciones = []

    # Trato individual vs grupo
    if es_grupo:
        instrucciones.append("""
INSTRUCCIÓN DE TONO - CLIENTE GRUPO:
Estás hablando con un EQUIPO, no con una persona individual.
- Usa siempre lenguaje en plural: "vosotros", "el equipo", "juntos"
- Saluda como: "¡Hola equipo!", "¡Hola familia!", "¡Hola chicos!"
- Cierra siempre con frases de equipo: "¡Vamos equipo!", "¡Juntos a por más!", "¡Seguimos creciendo juntos!"
- Transmite energía colectiva y sentido de comunidad en todo el mensaje
""")
    else:
        instrucciones.append("""
INSTRUCCIÓN DE TONO - CLIENTE INDIVIDUAL:
Estás hablando con UNA persona individual.
- Usa siempre lenguaje en singular: "tú", "tu negocio"
- Saluda de forma personal: "¡Hola [nombre]!"
- Cierra con frases individuales: "¡Tú puedes!", "¡Seguimos optimizando!", "¡Vamos a por más!"
- Transmite cercanía personal y confianza uno a uno
""")

    # Baja y facturas
    if es_baja and tiene_facturas:
        instrucciones.append(f"""
INSTRUCCIÓN OBLIGATORIA - BAJA + FACTURAS PENDIENTES:
{"El equipo está" if es_grupo else "Este cliente está"} de BAJA y tiene FACTURAS PENDIENTES.
Añade DOS coletillas al final del mensaje:
1. Recuérda{"les" if es_grupo else "le"} amablemente las facturas pendientes y la importancia de regularizarlas.
2. Invita{"les" if es_grupo else "le"} a reactivar el servicio recordando que la competencia está ganando terreno
   y que tienen herramientas como la Tarjeta Digital y el QR sin aprovechar.
""")
    elif es_baja:
        instrucciones.append(f"""
INSTRUCCIÓN OBLIGATORIA - CLIENTE DE BAJA:
{"El equipo está" if es_grupo else "Este cliente está"} de BAJA.
Al final del mensaje añade una coletilla para {"que reactiven" if es_grupo else "que reactive"} el servicio:
- Recuérda{"les" if es_grupo else "le"} que la competencia está ganando terreno
- Menciona que la Tarjeta Digital y el QR son armas que ahora no {"están" if es_grupo else "está"} aprovechando
- Pregunta si {"quieren" if es_grupo else "quiere"} reactivar con energía de equipo
""")
    elif tiene_facturas:
        instrucciones.append(f"""
INSTRUCCIÓN OBLIGATORIA - FACTURAS PENDIENTES:
{"El equipo tiene" if es_grupo else "Este cliente tiene"} FACTURAS PENDIENTES.
Al final del mensaje añade una coletilla delicada de cobro:
- Menciona que hay un pequeño desajuste administrativo con los últimos recibos
- Indica que es clave regularizarlo para no pausar el ritmo técnico
- Que no {"pierdan" if es_grupo else "pierda"} el posicionamiento ganado hasta ahora
""")

    return "\n".join(instrucciones), es_baja, tiene_facturas, es_grupo


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
        instrucciones_extra, es_baja, tiene_facturas, es_grupo = construir_prompt(c)

        col1, col2 = st.columns([1, 2])

        with col1:
            st.subheader("📋 Ficha del Cliente")
            st.info(f"**Dueño:** {c['Dueño']}")
            st.write(f"**Estatus:** {c.get('Estatus', 'N/A')}")
            st.write(f"**Fase:** {c.get('Fase_Protocolo', 'N/A')}")
            st.write(f"**Tipo:** {c.get('Tipo_Cliente', 'N/A')}")

            if es_grupo:
                st.info("👥 Cliente GRUPO — tono de equipo activado")
            else:
                st.info("👤 Cliente INDIVIDUAL — tono personal activado")
            if es_baja:
                st.error("🔴 Cliente de BAJA — se añadirá coletilla de reactivación")
            if tiene_facturas:
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
                            system_prompt = f"{prompt_maestro}\n\n{instrucciones_extra}"
                            user_prompt = f"Cliente: {c.to_dict()}\n\nTarea: {tema}"

                            respuesta = client.chat.completions.create(
                                model="llama-3.3-70b-versatile",
                                messages=[
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user", "content": user_prompt}
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
