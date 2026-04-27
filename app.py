import streamlit as st
import pandas as pd
from groq import Groq
import unicodedata

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

# 4. FUNCIÓN NORMALIZAR
def normalizar(texto):
    texto = str(texto).strip().lower()
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return texto

# 5. FUNCIÓN PARA CONSTRUIR PROMPT
def construir_prompt(cliente):
    tipo = normalizar(cliente.get('Tipo_Cliente', ''))
    facturas = normalizar(cliente.get('Facturas_Pendientes', ''))
    estatus = normalizar(cliente.get('Estatus', ''))

    # tipo_cliente: "baja" = baja, cualquier otra cosa (alta, individual, vacío) = individual activo
    es_baja = tipo == "baja"
    # facturas_pendientes: "si" = tiene facturas, "no" o cualquier otra cosa = sin facturas
    tiene_facturas = facturas == "si"
    # estatus: "grupo" = grupo, "individual" o cualquier otra cosa = individual
    es_grupo = estatus == "grupo"

    instrucciones = []

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

    if es_baja and tiene_facturas:
        instrucciones.append("""
INSTRUCCIÓN OBLIGATORIA - BAJA + FACTURAS PENDIENTES:
Este cliente está de BAJA y tiene FACTURAS PENDIENTES.
Añade DOS coletillas al final del mensaje:
1. Recuérdale amablemente las facturas pendientes y la importancia de regularizarlas.
2. Invítale a reactivar el servicio recordando que la competencia está ganando terreno
   y que tiene herramientas como la Tarjeta Digital y el QR sin aprovechar.
""" if not es_grupo else """
INSTRUCCIÓN OBLIGATORIA - BAJA + FACTURAS PENDIENTES:
El equipo está de BAJA y tiene FACTURAS PENDIENTES.
Añade DOS coletillas al final del mensaje:
1. Recuérdalles amablemente las facturas pendientes y la importancia de regularizarlas.
2. Invítales a reactivar el servicio recordando que la competencia está ganando terreno
   y que tienen herramientas como la Tarjeta Digital y el QR sin aprovechar.
""")
    elif es_baja:
        instrucciones.append("""
INSTRUCCIÓN OBLIGATORIA - CLIENTE DE BAJA:
Este cliente está de BAJA.
Al final del mensaje añade una coletilla para que reactive el servicio:
- Recuérdale que la competencia está ganando terreno
- Menciona que la Tarjeta Digital y el QR son armas que ahora no está aprovechando
- Pregunta si quiere reactivar
""" if not es_grupo else """
INSTRUCCIÓN OBLIGATORIA - CLIENTE DE BAJA:
El equipo está de BAJA.
Al final del mensaje añade una coletilla para que reactiven el servicio:
- Recuérdalles que la competencia está ganando terreno
- Menciona que la Tarjeta Digital y el QR son armas que ahora no están aprovechando
- Pregunta si quieren reactivar
""")
    elif tiene_facturas:
        instrucciones.append("""
INSTRUCCIÓN OBLIGATORIA - FACTURAS PENDIENTES:
Este cliente tiene FACTURAS PENDIENTES.
Al final del mensaje añade una coletilla delicada de cobro:
- Menciona que hay un pequeño desajuste administrativo con los últimos recibos
- Indica que es clave regularizarlo para no pausar el ritmo técnico
- Que no pierda el posicionamiento ganado hasta ahora
""" if not es_grupo else """
INSTRUCCIÓN OBLIGATORIA - FACTURAS PENDIENTES:
El equipo tiene FACTURAS PENDIENTES.
Al final del mensaje añade una coletilla delicada de cobro:
- Menciona que hay un pequeño desajuste administrativo con los últimos recibos
- Indica que es clave regularizarlo para no pausar el ritmo técnico
- Que no pierdan el posicionamiento ganado hasta ahora
""")

    return "\n".join(instrucciones), es_baja, tiene_facturas, es_grupo


# 6. INTERFAZ
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
                st.error(
