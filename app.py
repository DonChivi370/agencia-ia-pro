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

    # Casilla vacía = individual, activo, sin facturas
    es_baja = tipo == "baja"
    tiene_facturas = facturas == "si"
    es_grupo = estatus == "grupo"

    instrucciones = []

    # Tono grupo o individual
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

    # Coletillas baja y/o facturas
    if es_baja and tiene_facturas:
