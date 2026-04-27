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
        st.error(f"Error de conexion: {e}")
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

    es_baja = tipo == "baja"
    tiene_facturas = facturas == "si"
    es_grupo = estatus == "grupo"

    instrucciones = []

    if es_grupo:
        instrucciones.append(
            "INSTRUCCION DE TONO - CLIENTE GRUPO:\n"
            "Estas hablando con un EQUIPO, no con una persona individual.\n"
            "- Usa siempre lenguaje en plural: vosotros, el equipo, juntos\n"
            "- Saluda como: Hola equipo!, Hola familia!, Hola chicos!\n"
            "- Cierra siempre con frases de equipo: Vamos equipo!, Juntos a por mas!, Seguimos creciendo juntos!\n"
            "- Transmite energia colectiva y sentido de comunidad en todo el mensaje\n"
        )
    else:
        instrucciones.append(
            "INSTRUCCION DE TONO - CLIENTE INDIVIDUAL:\n"
            "Estas hablando con UNA persona individual.\n"
            "- Usa siempre lenguaje en singular: tu, tu negocio\n"
            "- Saluda de forma personal: Hola [nombre]!\n"
            "- Cierra con frases individuales: Tu puedes!, Seguimos optimizando!, Vamos a por mas!\n"
            "- Transmite cercania personal y confianza uno a uno\n"
        )

    if es_baja and tiene_facturas:
        if es_grupo:
            instrucciones.append(
                "INSTRUCCION OBLIGATORIA - BAJA + FACTURAS PENDIENTES:\n"
                "El equipo esta de BAJA y tiene FACTURAS PENDIENTES.\n"
                "Anade DOS coletillas al final del mensaje:\n"
                "1. Recuerdalles amablemente las facturas pendientes y la importancia de regularizarlas.\n"
                "2. Invitales a reactivar el servicio recordando que la competencia esta ganando terreno\n"
                "   y que tienen herramientas como la Tarjeta Digital y el QR sin aprovechar.\n"
            )
        else:
            instrucciones.append(
                "INSTRUCCION OBLIGATORIA - BAJA + FACTURAS PENDIENTES:\n"
                "Este cliente esta de BAJA y tiene FACTURAS PENDIENTES.\n"
                "Anade DOS coletillas al final del mensaje:\n"
                "1. Recuerdale amablemente las facturas pendientes y la importancia de regularizarlas.\n"
                "2. Invitale a reactivar el servicio recordando que la competencia esta ganando terreno\n"
                "   y que tiene herramientas como la Tarjeta Digital y el QR sin aprovechar.\n"
            )
    elif es_baja:
        if es_grupo:
            instrucciones.append(
                "INSTRUCCION OBLIGATORIA - CLIENTE DE BAJA:\n"
                "El equipo esta de BAJA.\n"
                "Al final del mensaje anade una coletilla para que reactiven el servicio:\n"
                "- Recuerdalles que la competencia esta ganando terreno\n"
                "- Menciona que la Tarjeta Digital y el QR son armas que ahora no estan aprovechando\n"
                "- Pregunta si quieren reactivar\n"
            )
        else:
            instrucciones.append(
                "INSTRUCCION OBLIGATORIA - CLIENTE DE BAJA:\n"
                "Este cliente esta de BAJA.\n"
                "Al final del mensaje anade una coletilla para que reactive el servicio:\n"
                "- Recuerdale que la competencia esta ganando terreno\n"
                "- Menciona que la Tarjeta Digital y el QR son armas que ahora no esta aprovechando\n"
                "- Pregunta si quiere reactivar\n"
            )
    elif tiene_facturas:
        if es_grupo:
            instrucciones.append(
                "INSTRUCCION OBLIGATORIA - FACTURAS PENDIENTES:\n"
                "El equipo tiene FACTURAS PENDIENTES.\n"
                "Al final del mensaje anade una coletilla delicada de cobro:\n"
                "- Menciona que hay un pequeno desajuste administrativo con los ultimos recibos\n"
                "- Indica que es clave regularizarlo para no pausar el ritmo tecnico\n"
                "- Que no pierdan el posicionamiento ganado hasta ahora\n"
            )
        else:
            instrucciones.append(
                "INSTRUCCION OBLIGATORIA - FACTURAS PENDIENTES:\n"
                "Este cliente tiene FACTURAS PENDIENTES.\n"
                "Al final del mensaje anade una coletilla delicada de cobro:\n"
                "- Menciona que hay un pequeno desajuste administrativo con los ultimos recibos\n"
                "- Indica que es clave regularizarlo para no pausar el ritmo tecnico\n"
                "- Que no pierda el posicionamiento ganado hasta ahora\n"
            )

    return "\n".join(instrucciones), es_baja, tiene_facturas, es_grupo


# 6. INTERFAZ
st.title("Gestion Agencia IA Pro")

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
            st.subheader("Ficha del Cliente")
            st.info("Dueno: " + str(c['Dueño']))
            st.write("Estatus: " + str(c.get('Estatus', 'N/A')))
            st.write("Fase: " + str(c.get('Fase_Protocolo', 'N/A')))
            st.write("Tipo: " + str(c.get('Tipo_Cliente', 'N/A')))

            if es_grupo:
                st.info("Cliente GRUPO - tono de equipo activado")
            else:
                st.info("Cliente INDIVIDUAL - tono personal activado")

            if es_baja:
                st.error("Cliente de BAJA - se anadira coletilla de reactivacion")

            if tiene_facturas:
                st.warning("Facturas Pendientes - se anadira coletilla de cobro")

            nota = str(c.get('Notas_Criticas', ''))
            if nota != '' and normalizar(nota) != 'nan':
                st.error("Nota: " + nota)

        with col2:
            st.subheader("Asistente")
            tema = st.text_area("Que necesitas?")
            if st.button("Generar Mensaje"):
                if tema:
                    with st.spinner("Generando mensaje..."):
                        try:
                            system_prompt = prompt_maestro + "\n\n" + instrucciones_extra
                            user_prompt = "Cliente: " + str(c.to_dict()) + "\n\nTarea: " + tema
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
                            st.error("Error IA: " + str(e))
                else:
                    st.warning("Escribe que necesitas antes de generar.")
else:
    st.info("Conectando con Google Sheets...")
