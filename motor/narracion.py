# Narración por partes. Reyes (protagonista) cuenta su visita + diálogo completo de Jaqueline, Daniela y Reyes.
# Siglas (CRM, ERP, LFPDPPP) fuera de la voz: solo salen escritas en pantalla.
PARTS = [
 ("s1", "Domingo en la Condesa. Quiero un café, pero voy con mi perro… y en todos lados: mascotas no."),
 ("s2", "Hasta que llego a Huellitas, en Zamora ciento sesenta y cinco: un café pet friendly donde entras con tu mascota y convives con ella."),
 ("s3", "Desde su app aparto mesa, veo el menú, pido, pago y sigo mi pedido hasta que está listo."),
 ("s4", "¡Hola a todos! Para entender la viabilidad comercial y operativa de Huellitas, nuestro café pet friendly en la Colonia Condesa, es fundamental analizar su arquitectura tecnológica. La tecnología no es solo un adorno, sino el motor que nos permite reducir tiempos de espera de diez a cinco minutos, escalar el modelo y cumplir con las normativas internacionales de protección de datos. ¿Cómo logramos esta integración en el punto de venta?"),
 ("s5", "Todo comienza en el ecosistema digital de cara al cliente. Implementamos una plataforma web interactiva y kioscos de pedidos rápidos respaldados por menús digitales con códigos QR. Esto optimiza la experiencia del consumidor al permitirle reservar mesas, consultar alérgenos y realizar pedidos sin fricciones. Además, en la parte posterior utilizamos un sistema para gestionar el Huellitas Club, una base de datos centralizada que registra perfiles de mascotas y automatiza cupones de cumpleaños. Desde la perspectiva de Negocios Internacionales, esto nos otorga una ventaja competitiva sostenible al fidelizar al segmento pet parent mediante la personalización masiva de servicios."),
 ("s6", "Exactamente, y en la trastienda operativa e industrial la tecnología es igual de crítica. Contamos con infraestructura de hardware especializada, como impresoras de comandas conectadas en tiempo real con la cocina, terminales de pago sin contacto y pasarelas digitales, que garantizan transacciones seguras bajo la Ley Federal de Protección de Datos Personales. Asimismo, el uso de software para el control de inventarios nos permite mantener el margen de merma por debajo del tres por ciento. En resumen, la sinergia entre nuestras herramientas digitales, la automatización de procesos y el cumplimiento normativo garantiza que Huellitas sea un modelo de negocio vanguardista, escalable y financieramente rentable."),
 ("s7", "Café, tu mascota y cero esperas, en un solo lugar. ¿A quién llevarías tú a Huellitas?"),
]

# Voz de cada parte (las que no están aquí usan la voz de Reyes, la que se pasa a tts.py)
VOICES = {
 "s4": "es-MX-DaliaNeural",    # Jaqueline
 "s5": "es-US-PalomaNeural",   # Daniela
}
