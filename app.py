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
        url_mensajes = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=Mensajes_Recurrentes"
        df_c = pd.read_csv(url_clientes)
        df_p = pd.read_csv(url_config)
        df_m = pd.read_csv(url_mensajes)
        df_c.columns = df_c.columns.str.strip()
        df_c = df_c.dropna(subset=["Nombre_Local"])
        df_m.columns = df_m.columns.str.strip()
        df_m = df_m.dropna(subset=["Nombre_Mensaje"])
        prompt = df_p.columns[1]
        return df_c, prompt, df_m
    except Exception as e:
        st.error("Error de conexion: " + str(e))
        return None, None, None

df, prompt_maestro, df_mensajes = cargar_datos()

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

# 6. INSTRUCCIONES ESPECIFICAS POR TIPO DE MENSAJE RECURRENTE
def instruccion_mensaje_recurrente(nombre_mensaje, es_grupo):
    plural = es_grupo
    mensajes = {
        "Envio de Contenido Original": (
            "Has creado una publicacion de contenido original para el negocio del cliente.\n"
            "Redacta un mensaje informal y cercano enviandosela y preguntando si le gusta para subirla a su ficha de Google.\n"
            "Menciona de forma sencilla y sin tecnicismos que subir contenido original mejora la visibilidad en Google y atrae mas clientes.\n"
            "No uses palabras tecnicas. El cliente no es experto en marketing.\n"
        ),
        "Optimizacion de la ficha": (
            "Hemos realizado optimizaciones tecnicas en la ficha de Google Business del cliente.\n"
            "Redacta un mensaje cercano explicando que hemos estado trabajando en su ficha para mejorar su posicionamiento.\n"
            "Explica de forma simple y sin tecnicismos que estos cambios hacen que su negocio aparezca mas arriba en Google y gane mas visibilidad.\n"
            "Transmite que es un trabajo continuo que hacemos por ellos aunque no lo vean a simple vista.\n"
        ),
        "Respuesta a reseñas": (
            "Hemos contestado reseñas en la ficha de Google del cliente.\n"
            "Redacta un mensaje informando de que hemos gestionado y respondido las reseñas recibidas.\n"
            "Dale la enhorabuena por las valoraciones positivas y alaba el buen trabajo que esta haciendo con sus clientes.\n"
            "Transmite que responder reseñas mejora la imagen del negocio y su posicionamiento en Google.\n"
        ),
        "Subida de contenido": (
            "Hemos subido nuevo contenido a la ficha de Google Business del cliente.\n"
            "Redacta un mensaje avisando de que hemos publicado nuevo contenido en su ficha.\n"
            "Explica de forma sencilla que mantener la ficha activa con contenido fresco hace que Google la valore mas y atraiga mas clientes.\n"
        ),
        "Promo del negocio": (
            "Queremos crear una novedad o promocion para el negocio del cliente para subir a su ficha de Google.\n"
            "Redacta un mensaje solicitando al cliente informacion sobre alguna oferta, novedad, evento o promocion que quiera comunicar.\n"
            "Explica que publicar promociones en Google atrae clientes nuevos y mejora el SEO local de su negocio.\n"
            "El tono debe ser entusiasta y motivador, como si fuera una gran oportunidad para su negocio.\n"
        ),
        "Horarios festivos": (
            "Se acerca un festivo y necesitamos saber si el cliente va a modificar su horario.\n"
            "Redacta un mensaje preguntando al cliente si va a tener horario especial o va a cerrar en el proximo festivo.\n"
            "Explica que es importante tener los horarios actualizados en Google para que sus clientes no se lleven sorpresas.\n"
            "El tono debe ser de servicio y cuidado hacia el negocio del cliente.\n"
        ),
        "Recordatorio de uso de QR": (
            "El cliente tiene un QR de valorame5estrellas y queremos recordarle que lo use.\n"
            "Redacta un mensaje recordando al cliente que comparta el QR con sus clientes para conseguir mas reseñas en Google.\n"
            "Explica de forma simple que mas reseñas positivas significa mejor posicion en Google y mas clientes nuevos.\n"
            "Recuerda que el sistema filtra las opiniones negativas para que lleguen al dueno en privado y no manchen la ficha.\n"
        ),
        "Recordatorio de la tarjeta digital": (
            "El cliente tiene una Tarjeta Premier Digital y queremos recordarle que la use.\n"
            "Redacta un mensaje recordando al cliente que comparta su tarjeta digital por WhatsApp y redes sociales.\n"
            "Explica que la tarjeta digital es como una App personalizada de su negocio que sus clientes pueden llevar en el movil.\n"
            "Transmite que compartirla es la forma mas facil de conseguir visibilidad digital y que sus clientes recomienden el local.\n"
        ),
    }
    base = mensajes.get(nombre_mensaje, "Genera un mensaje recurrente profesional y cercano para este cliente.\n")
    if plural:
        base += "\nRECUERDA: Dirígete al EQUIPO en plural. Usa: vosotros, el equipo, juntos, chicos.\n"
    else:
        base += "\nRECUERDA: Dirígete a la persona de forma INDIVIDUAL. Usa: tu, tu negocio, [nombre].\n"
    return base


# 7. INTERFAZ
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
            tab1, tab2 = st.tabs(["Asistente Libre", "Mensajes Recurrentes"])

            with tab1:
                st.subheader("Asistente")
                tema = st.text_area("Que necesitas?", key="tema_libre")
                if st.button("Generar Mensaje", key="btn_libre"):
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

            with tab2:
                st.subheader("Mensajes Recurrentes")
                if df_mensajes is not None and not df_mensajes.empty:
                    opciones = df_mensajes["Nombre_Mensaje"].tolist()
                    mensaje_sel = st.selectbox(
                        "Selecciona el tipo de mensaje:",
                        options=opciones,
                        index=None,
                        placeholder="Elige un mensaje recurrente...",
                        key="sel_recurrente"
                    )

                    if mensaje_sel:
                        descripcion = df_mensajes[
                            df_mensajes["Nombre_Mensaje"] == mensaje_sel
                        ]["Descripcion"].values[0]
                        st.caption("Descripcion: " + str(descripcion))

                    if st.button("Generar Mensaje Recurrente", key="btn_recurrente"):
                        if mensaje_sel:
                            with st.spinner("Generando mensaje recurrente..."):
                                try:
                                    instruccion_especifica = instruccion_mensaje_recurrente(mensaje_sel, es_grupo)
                                    system_prompt = prompt_maestro + "\n\n" + instrucciones_extra
                                    user_prompt = (
                                        "Cliente: " + str(c.to_dict()) +
                                        "\n\nTipo de mensaje recurrente: " + mensaje_sel +
                                        "\n\nInstrucciones especificas para este mensaje:\n" +
                                        instruccion_especifica
                                    )
                                    respuesta = client.chat.completions.create(
                                        model="llama-3.3-70b-versatile",
                                        messages=[
                                            {"role": "system", "content": system_prompt},
                                            {"role": "user", "content": user_prompt}
                                        ],
                                        max_tokens=1024
                                    )
                                    st.success("Mensaje generado:")
                                    st.markdown(respuesta.choices[0].message.content)
                                except Exception as e:
                                    st.error("Error IA: " + str(e))
                        else:
                            st.warning("Selecciona un tipo de mensaje antes de generar.")
                else:
                    st.info("No se encontraron mensajes recurrentes en el Excel.")

else:
    st.info("Conectando con Google Sheets...")
