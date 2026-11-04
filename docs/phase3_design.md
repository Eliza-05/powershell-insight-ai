# Diseño del Analysis Studio

La investigación de referencias se realizó por Internet antes de implementar el frontend.
Se buscaron dashboards SaaS, developer tools, interfaces de seguridad y patrones de comparación,
temas claro/oscuro, tarjetas, tabs y paneles divididos. No se reutilizaron marcas, pantallas,
logos, métricas ni imágenes de terceros en la aplicación.

## Referencias y decisiones propias

| Referencia pública | Patrón observado | Aplicación al producto |
|---|---|---|
| [Rediseño de Linear](https://linear.app/now/how-we-redesigned-the-linear-ui) | Jerarquía entre navegación, superficie y paneles; consistencia de temas | Sidebar de contexto, encabezado discreto, paneles de entrada y evidencia, tokens de color compartidos |
| [Geist: tabs](https://vercel.com/geist/tabs) | Tabs para vistas hermanas y foco/teclado predecibles | Cuatro vistas del mismo resultado; flechas/Home/End, ARIA y foco visible |
| [Snyk Analytics](https://snyk.io/blog/transform-your-appsec-program-with-the-power-of-snyk-analytics/) | Resumen antes del detalle y organización de información de seguridad | Resumen operativo y acceso a evidencias; sin importar sus métricas de vulnerabilidades al proyecto |

La consulta incluyó búsqueda de imágenes de interfaces de Linear/Snyk. La búsqueda de imágenes
y los artículos sirvieron como referencias generales; la identidad visual y composición son
propias. No se afirma haber clonado, inspeccionado una sesión privada ni validado el producto
en una cuenta de esas herramientas. El intento de abrir una imagen de Linear no pudo recuperarse;
se conservaron como fuentes sus materiales públicos y las referencias de búsqueda.

## Sistema visual

- Identidad: azul tinta, superficies de pizarra y acento menta para acciones/estado operativo.
  Ámbar para incertidumbre/provisionalidad y rojo para rechazo. Un estado verde de ejecución
  nunca se presenta como veredicto de benignidad.
- Tipografía local: Inter para producto y JetBrains Mono para fuente, IDs y evidencia.
  Paquetes fijados, sin Google Fonts ni solicitudes de fuentes en tiempo de uso a terceros.
- Layout: navegación persistente en escritorio, editor y configuración a la izquierda,
  resultados a la derecha. En anchos intermedios se compacta la navegación; en móvil se apilan
  paneles y el estado continúa accesible desde el encabezado.
- Vacío con diagrama propio de código y tres perspectivas; loading real sin porcentajes o
  etapas inventadas; errores con motivo y ausencia explícita de hallazgos aceptados.
- Comparación mediante tres tarjetas seleccionables, estados, autores y etiquetas. Las
  diferencias visibles describen salidas; no hay ranking, score de calidad ni métricas científicas.
- Evidencia primero: cada cita indica su origen; recuperación 1A separada de reconstrucción
  del LLM; riesgo del modelo rotulado; advertencias y respuesta rechazada en detalle bajo demanda.

## Accesibilidad y privacidad

Controles semánticos, radios nativos, labels, estados en texto además de color, tablist con
teclado, foco visible, enlace de salto, diálogo nativo, regiones live, `aria-busy` y respeto a
`prefers-reduced-motion`. Se aumentó contraste de texto secundario en ambos temas mediante
revisión numérica de tokens; no constituye auditoría WCAG completa. La preferencia se persiste;
las muestras y resultados no se guardan automáticamente.

Se renderiza texto mediante React, nunca HTML o Markdown no confiables. Las URLs del código
no se convierten en enlaces y el contenido recuperado no se ejecuta. El usuario puede exportar
un JSON completo de forma explícita. El editor es un textarea con líneas y selección de spans:
no se añadió Monaco ni ejecución embebida para el MVP.

## Límite de la comprobación visual

El host de navegador/computer-use de la sesión devolvió indisponibilidad al consultar y abrir
la aplicación. Se probaron DOM, accesibilidad semántica básica, estados, temas, selección y
conexión HTTP; se construyeron los assets. **No se obtuvieron capturas de pantalla ni una revisión
real de layout, scroll, responsive o contraste renderizado en navegador.** Se registra esta
verificación pendiente, sin confundir JSDOM con un navegador visual. Procedimiento manual en
[la guía local](phase3_local.md).
