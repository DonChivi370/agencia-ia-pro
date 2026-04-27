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
    contacto = normalizar(cliente.get('Contacto', ''))
    nombre = str(cliente.get('Dueño', '')).strip()
    acceso = normalizar(cliente.get('Acceso_Ficha', ''))
    verificada = normalizar(cliente.get('Ficha_Verificada', ''))

    es_baja = tipo == "baja"
    tiene_facturas = facturas == "si"
    es_grupo = contacto == "grupo" or normalizar(nombre) in ['', 'nan']
    tiene_acceso = acceso == "si"
    esta_verificada = verificada == "si"

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
            "Estas hablando con UNA persona individual. Su nombre es: " + nombre + "\n"
            "- Usa su nombre en el saludo: Hola " + nombre + "!\n"
            "- Usa siempre lenguaje en singular: tu, tu negocio\n"
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

    if not tiene_acceso:
        if es_grupo:
            instrucciones.append(
                "INSTRUCCION OBLIGATORIA - SIN ACCESO A FICHA:\n"
                "No tenemos acceso a la ficha de Google Business de este cliente.\n"
                "Al final del mensaje anade una coletilla amable indicando que necesitamos que nos den acceso a su ficha.\n"
                "Explica de forma sencilla que con acceso podemos optimizarla mejor, mejorar su visibilidad en Google y atraer mas clientes.\n"
                "Tono: cercano, como un paso importante que depende de ellos para que el servicio funcione al 100%.\n"
            )
        else:
            instrucciones.append(
                "INSTRUCCION OBLIGATORIA - SIN ACCESO A FICHA:\n"
                "No tenemos acceso a la ficha de Google Business de este cliente.\n"
                "Al final del mensaje anade una coletilla amable indicando que necesitamos que nos de acceso a su ficha.\n"
                "Explica de forma sencilla que con acceso podemos optimizarla mejor, mejorar su visibilidad en Google y atraer mas clientes.\n"
                "Tono: cercano, como un paso importante que depende de el para que el servicio funcione al 100%.\n"
            )

    if tiene_acceso and not esta_verificada:
        if es_grupo:
            instrucciones.append(
                "INSTRUCCION OBLIGATORIA - FICHA SIN VERIFICAR:\n"
                "Tenemos acceso a la ficha pero NO esta verificada en Google.\n"
                "Al final del mensaje anade una coletilla recordando que hay que pasar el proceso de verificacion.\n"
                "Explica de forma simple que sin verificacion el negocio no se muestra correctamente en Google,\n"
                "lo que reduce su visibilidad, su optimizacion y la captacion de nuevos clientes.\n"
                "Tono: urgente pero tranquilizador, algo que hay que resolver pronto y que nosotros les ayudamos a gestionar.\n"
            )
        else:
            instrucciones.append(
                "INSTRUCCION OBLIGATORIA - FICHA SIN VERIFICAR:\n"
                "Tenemos acceso a la ficha pero NO esta verificada en Google.\n"
                "Al final del mensaje anade una coletilla recordando que hay que pasar el proceso de verificacion.\n"
                "Explica de forma simple que sin verificacion el negocio no se muestra correctamente en Google,\n"
                "lo que reduce su visibilidad, su optimizacion y la captacion de nuevos clientes.\n"
                "Tono: urgente pero tranquilizador, algo que hay que resolver pronto y que nosotros le ayudamos a gestionar.\n"
            )

    return "\n".join(instrucciones), es_baja, tiene_facturas, es_grupo, tiene_acceso, esta_verificada


# 6. INSTRUCCIONES ESPECIFICAS POR TIPO DE MENSAJE RECURRENTE
def instruccion_mensaje_recurrente(nombre_mensaje, es_grupo):
    mensajes = {
        "Envio de Contenido Original": (
            "Hemos creado una publicacion de contenido original para el negocio del cliente.\n"
            "Redacta un mensaje BREVE, cercano y con 2-3 emojis relevantes.\n"
            "Dile que le enviamos una publicacion nueva y preguntale si le gusta para subirla a su ficha de Google.\n"
            "Menciona de forma muy simple que esto le da mas visibilidad. Sin tecnicismos.\n"
            "Maximo 5 lineas. Tono: como si le escribiera un amigo que le ayuda con su negocio.\n"
        ),
        "Optimizacion de la ficha": (
            "Hemos realizado mejoras tecnicas en la ficha de Google Business del cliente.\n"
            "Redacta un mensaje BREVE, cercano y con 2-3 emojis relevantes.\n"
            "Dile que hemos estado trabajando en su ficha para que aparezca mas arriba en Google.\n"
            "Transmite que es un trabajo que hacemos en silencio pero que tiene impacto real.\n"
            "Maximo 5 lineas. Tono: socio estrategico que cuida su negocio.\n"
        ),
        "Respuesta a reseñas": (
            "Hemos contestado las reseñas de la ficha de Google del cliente.\n"
            "Redacta un mensaje BREVE, cercano y con 2-3 emojis relevantes.\n"
            "Informale de que hemos gestionado sus reseñas y dale la enhorabuena por las valoraciones positivas.\n"
            "Alaba brevemente el buen trabajo que esta haciendo con sus clientes.\n"
            "Maximo 5 lineas. Tono: celebracion y apoyo, como un socio orgulloso.\n"
        ),
        "Subida de contenido": (
            "Hemos subido nuevo contenido a la ficha de Google Business del cliente.\n"
            "Redacta un mensaje BREVE, cercano y con 2-3 emojis relevantes.\n"
            "Avisale de que hemos publicado contenido nuevo en su ficha para mantenerla activa.\n"
            "Explica en una frase simple que esto hace que Google valore mas su negocio.\n"
            "Maximo 5 lineas. Tono: equipo trabajando por su exito.\n"
        ),
        "Promo del negocio": (
            "Queremos crear una promocion o novedad para publicar en la ficha del cliente.\n"
            "Redacta un mensaje BREVE, cercano y con 2-3 emojis relevantes.\n"
            "Pidele que te cuente si tiene alguna oferta, evento o novedad que quiera comunicar.\n"
            "Transmite entusiasmo: es una oportunidad para atraer clientes nuevos.\n"
            "Maximo 5 lineas. Tono: emocionado y motivador, como quien ve una oportunidad clara.\n"
        ),
        "Horarios festivos": (
            "Se acerca un festivo y necesitamos confirmar el horario del cliente.\n"
            "Redacta un mensaje BREVE, cercano y con 2-3 emojis relevantes.\n"
            "Preguntale si va a modificar su horario o cerrar durante el proximo festivo.\n"
            "Explica en una frase que tener el horario actualizado evita que sus clientes se lleven sorpresas.\n"
            "Maximo 5 lineas. Tono: servicio y cuidado, como quien vela por los detalles.\n"
        ),
        "Recordatorio de uso de QR": (
            "El cliente tiene un QR de valorame5estrellas y queremos que lo use mas.\n"
            "Redacta un mensaje BREVE, cercano y con 2-3 emojis relevantes.\n"
            "Recuerdale que comparta el QR con sus clientes para conseguir mas reseñas en Google.\n"
            "Menciona que mas reseñas positivas significa mejor posicion y mas clientes nuevos.\n"
            "Recuerda que las opiniones negativas le llegan a el en privado, no se publican en Google.\n"
            "Maximo 5 lineas. Tono: consejo de un socio que quiere que le vaya bien.\n"
        ),
        "Recordatorio de la tarjeta digital": (
            "El cliente tiene una Tarjeta Premier Digital y queremos que la comparta mas.\n"
            "Redacta un mensaje BREVE, cercano y con 2-3 emojis relevantes.\n"
            "Recuerdale que la comparta por WhatsApp y redes para ganar visibilidad digital.\n"
            "Explica en una frase que es como una App de su negocio que sus clientes llevan en el movil.\n"
            "Maximo 5 lineas. Tono: entusiasta, como quien le recuerda que tiene una herramienta potente sin usar.\n"
        ),
    }

    base = mensajes.get(nombre_mensaje, "Genera un mensaje recurrente breve, cercano y con emojis para este cliente.\n")

    if es_grupo:
        base += (
            "\nIMPORTANTE DE TONO:\n"
            "- Dirigete al EQUIPO en plural: vosotros, el equipo, juntos, chicos\n"
            "- Saluda como: Hola equipo!, Hola chicos!, Hola familia!\n"
            "- Cierra con energia de equipo: Seguimos juntos!, Vamos equipo!\n"
        )
    else:
        base += (
            "\nIMPORTANTE DE TONO:\n"
            "- Dirigete a la persona de forma INDIVIDUAL usando su nombre si lo tienes\n"
            "- Saluda de forma personal: Hola [nombre]!\n"
            "- Cierra con motivacion individual: Seguimos optimizando!, Vamos a por mas!\n"
        )

    base += (
        "\nREGLAS GENERALES DEL MENSAJE:\n"
        "- Usa entre 2 y 3 emojis repartidos de forma natural en el mensaje\n"
        "- El mensaje debe ser BREVE: maximo 5 lineas\n"
        "- Tono cercano y profesional a la vez, como un socio de confianza\n"
        "- Nada de tecnicismos ni palabras complicadas\n"
        "- Termina siempre con una frase motivadora corta\n"
        "- NO uses negritas, asteriscos ni formato markdown. Solo texto plano como un WhatsApp.\n"
    )

    return base


# 7. COMPONENTE PARA COPIAR MENSAJE
def boton_copiar(texto, key):
    texto_js = texto.replace('\\', '\\\\').replace('`', '\\`').replace('\n', '\\n')
    componente = (
        "<script>"
        "function copiarTexto_" + key + "() {"
        "  const texto = `" + texto_js + "`;"
        "  navigator.clipboard.writeText(texto).then(function() {"
        "    document.getElementById('btn_" + key + "').innerText = 'Copiado!';"
        "    setTimeout(function() {"
        "      document.getElementById('btn_" + key + "').innerText = 'Copiar mensaje';"
        "    }, 2000);"
        "  });"
        "}"
        "</script>"
        "<button id='btn_" + key + "' onclick='copiarTexto_" + key + "()'"
        " style='background-color:#4CAF50;color:white;border:none;padding:8px 16px;"
        "border-radius:6px;cursor:pointer;font-size:14px;margin-top:8px;'>"
        "Copiar mensaje"
        "</button>"
    )
    st.components.v1.html(componente, height=50)


# 8. INTERFAZ
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

        # Limpiar mensajes al cambiar de cliente
        if st.session_state.get("cliente_anterior") != cliente_sel:
            st.session_state["mensaje_libre"] = ""
            st.session_state["mensaje_recurrente"] = ""
            st.session_state["cliente_anterior"] = cliente_sel

        c = df[df["Nombre_Local"] == cliente_sel].iloc[0]
        instrucciones_extra, es_baja, tiene_facturas, es_grupo, tiene_acceso, esta_verificada = construir_prompt(c)

        nombre_cliente = str(c.get('Dueño', '')).strip()
        nombre_mostrar = "Grupo / Sin nombre" if normalizar(nombre_cliente) in ['', 'nan'] else nombre_cliente

        col1, col2 = st.columns([1, 2])

        with col1:
            st.subheader("Ficha del Cliente")
            st.info("Nombre del cliente: " + nombre_mostrar)
            st.write("Contacto: " + str(c.get('Contacto', 'N/A')))
            st.write("Fase: " + str(c.get('Fase_Protocolo', 'N/A')))
            st.write("Tipo: " + str(c.get('Tipo_Cliente', 'N/A')))

            col_a, col_b = st.columns(2)
            with col_a:
                if tiene_acceso:
                    st.success("Acceso ficha: Si")
                else:
                    st.error("Acceso ficha: No")
            with col_b:
                if esta_verificada:
                    st.success("Verificada: Si")
                else:
                    st.error("Verificada: No")

            if es_grupo:
                st.info("Cliente GRUPO - tono de equipo activado")
            else:
                st.info("Cliente INDIVIDUAL - tono personal activado")
            if es_baja:
                st.error("Cliente de BAJA - se anadira coletilla de reactivacion")
            if tiene_facturas:
                st.warning("Facturas Pendientes - se anadira coletilla de cobro")
            if not tiene_acceso:
                st.warning("Sin acceso a ficha - se anadira coletilla de solicitud de acceso")
            if tiene_acceso and not esta_verificada:
                st.warning("Ficha sin verificar - se anadira coletilla de verificacion")

            nota = str(c.get('Notas_Criticas', ''))
            if nota != '' and normalizar(nota) != 'nan':
                st.error("Nota: " + nota)

        with col2:
            tab1, tab2 = st.tabs(["Asistente Libre", "Mensajes Recurrentes"])

            with tab1:
                st.subheader("Asistente")
                tema = st.text_area("Que necesitas?", key="tema_libre")

                solicitud_factura = False
                if tema:
                    palabras_factura = ["factura", "facturas", "recibo", "recibos", "cobro", "pago"]
                    for palabra in palabras_factura:
                        if palabra in normalizar(tema):
                            solicitud_factura = True
                            break

                if solicitud_factura:
                    st.info("El cliente solicita una factura. Se incluira la respuesta del departamento de facturacion.")

                if st.button("Generar Mensaje", key="btn_libre"):
                    if tema:
                        with st.spinner("Generando mensaje..."):
                            try:
                                instruccion_factura = ""
                                if solicitud_factura:
                                    instruccion_factura = (
                                        "\nINSTRUCCION ESPECIAL - SOLICITUD DE FACTURA:\n"
                                        "El cliente esta solicitando una factura o informacion sobre facturacion.\n"
                                        "Responde de forma amable indicando que trasladamos su solicitud al departamento de facturacion\n"
                                        "y que recibira la factura en su correo electronico en breve.\n"
                                        "Tono tranquilizador y eficiente. No prometas plazos concretos.\n"
                                    )

                                system_prompt = prompt_maestro + "\n\n" + instrucciones_extra + instruccion_factura
                                user_prompt = "Cliente: " + str(c.to_dict()) + "\n\nTarea: " + tema
                                respuesta = client.chat.completions.create(
                                    model="llama-3.3-70b-versatile",
                                    messages=[
                                        {"role": "system", "content": system_prompt},
                                        {"role": "user", "content": user_prompt}
                                    ],
                                    max_tokens=1024
                                )
                                st.session_state["mensaje_libre"] = respuesta.choices[0].message.content
                            except Exception as e:
                                st.error("Error IA: " + str(e))
                    else:
                        st.warning("Escribe que necesitas antes de generar.")

                if "mensaje_libre" in st.session_state and st.session_state["mensaje_libre"] != "":
                    st.success("Sugerencia:")
                    st.markdown(st.session_state["mensaje_libre"])
                    boton_copiar(st.session_state["mensaje_libre"], "libre")

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
                                        max_tokens=512
                                    )
                                    st.session_state["mensaje_recurrente"] = respuesta.choices[0].message.content
                                except Exception as e:
                                    st.error("Error IA: " + str(e))
                        else:
                            st.warning("Selecciona un tipo de mensaje antes de generar.")

                    if "mensaje_recurrente" in st.session_state and st.session_state["mensaje_recurrente"] != "":
                        st.success("Mensaje generado:")
                        st.markdown(st.session_state["mensaje_recurrente"])
                        boton_copiar(st.session_state["mensaje_recurrente"], "recurrente")
                else:
                    st.info("No se encontraron mensajes recurrentes en el Excel.")

else:
    st.info("Conectando con Google Sheets...")
