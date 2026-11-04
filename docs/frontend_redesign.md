# Rediseño del frontend — Security Studio

Entrega local del 2026-11-02, sobre el MVP de Fase 3. Se conserva el comportamiento de
A/B/C, sus contratos, las restricciones de seguridad y el estado provisional del modelo.
No se inicia Fase 4 ni se alteran artefactos históricos.

## Qué cambió

La composición se reorganizó alrededor de la tarea principal:

- Cabecera compacta, sin el hero promocional y la fila de mensajes repetidos. El título
  identifica el espacio de trabajo; API, ayuda y tema permanecen accesibles.
- Una barra superior reúne selección A/B/C/ABC, explicación del enfoque seleccionado y
  acción principal. El usuario no necesita recordar las diferencias entre configuraciones
  ni buscar el botón debajo del editor.
- Editor y resultados son las dos superficies principales. Se eliminó el bloque inferior
  de tarjetas de selección y la decoración sobredimensionada del estado vacío.
- Sidebar más discreta con grupos claros, activo visible y nombres accesibles incluso
  cuando se compacta a iconos. El estado del sistema sigue disponible desde el encabezado.
- Editor con cabecera de archivo, botones de carga/ejemplo/limpieza, metadatos, números de
  línea y área de código ampliada. El arrastre reutiliza exactamente la validación UTF-8,
  tamaño y extensión de la carga existente; múltiples archivos se rechazan explícitamente.
- Resultados con resumen operativo, técnicas por autor y citas con una cadena de procedencia
  hacia el original. La comparación añade número de citas y recuperaciones 1A, y navegación
  con flechas/Home/End, sin inferencias adicionales ni métricas de calidad inventadas.

El selector de pipeline se extrajo a `PipelineSelector.tsx`. Los estilos se reconstruyeron
en `styles/tokens.css` y `styles/studio.css`, con una entrada `styles.css` pequeña. No es un
cambio limitado a variables: cambian estructura, distribución de controles, estado vacío,
inspección de evidencias e interacción de comparación.

## Sistema visual y legibilidad

Texto principal y explicaciones de **16 px**, código de **16 px en escritorio y 15 px en
móvil**, títulos de página de 30–40 px, encabezados de panel de 18 px y metadatos de 13–14 px.
Las excepciones de 12 px corresponden a captions y rótulos, no a código o explicaciones.
No se reduce el texto principal al llegar a laptop/tablet: se reorganiza el layout.

Paleta propia de azul tinta con menta como acción principal; azul/violeta distinguen B/C
junto con sus letras y nombres. Ámbar y rojo comunican parcialidad/rechazo mediante texto e
iconos, además del color. El selector añade una marca de selección visible. La sidebar y el
editor ofrecen superficies oscuras definidas también en claro; los paneles claros se separan
de un fondo azul grisáceo, evitando una pantalla plana enteramente blanca.

Se reducen sombras a overlays, se emplean bordes simples y las señales decorativas se limitan
a una cadena discreta de código → recuperación → evidencia en el estado vacío. No se añaden
gráficas, alertas o contadores ficticios. Las fuentes locales Inter y JetBrains Mono y los
iconos Lucide existentes se reutilizan; **no se añadieron dependencias ni recursos remotos**.

Referencias conceptuales consultadas, sin copiar marcas o pantallas:
[jerarquía y superficies de Linear](https://linear.app/now/how-we-redesigned-the-linear-ui),
[colores y bordes de Geist](https://vercel.com/geist/colors),
[contexto de plataforma de seguridad de Wiz](https://www.wiz.io/platform).

## Accesibilidad y adaptación

Controles principales de 44–48 px, foco visible, radios nativos con labels y descripción del
modo, tabs de detalle con teclado y comparación con foco móvil entre perspectivas. Escape
cierra el inspector del sistema y devuelve el foco a su botón. Se conserva movimiento reducido,
el diálogo nativo, regiones live, estados de carga y protección frente a solicitudes duplicadas.

Los breakpoints compactan la navegación y apilan paneles en lugar de comprimir la tipografía.
La comparación cambia a filas cuando su contexto necesita más espacio. El código largo conserva
scroll propio; las evidencias y los hashes permiten saltos de línea para evitar desbordamientos.

Se calcularon **46 combinaciones de color declaradas** en ambos temas: texto con mínimo 4,5:1
y bordes de controles con mínimo 3:1. Todas superan sus umbrales. Se usa la luminancia relativa
de [WCAG: contraste mínimo](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html).
[Resultados numéricos](../artifacts/redesign_v1/contrast_checks.json).
Esto valida esos pares opacos, **no certifica WCAG AA del producto completo**, ni sustituye
la comprobación de foco, layout, zoom y contraste finalmente renderizados.

## Pruebas y conexión real

| Comprobación | Resultado |
|---|---|
| Frontend | **28 aprobadas**, cero fallidas/omitidas: 24 existentes y 4 nuevas |
| Backend | **876 aprobadas**, conservando las 841 regresiones históricas y 35 de API |
| React + FastAPI por HTTP real | **1 aprobada**, pipeline A; muestra hallazgos y recuperación |
| TypeScript + Vite producción | Correctos |
| Contraste de tokens | 46 pares comprobados, cero fallos |
| HTTP local | HTML, JS, CSS y health responden 200; assets idénticos al build actual |
| Inferencias nuevas | **0** |

Las cuatro pruebas nuevas cubren arrastre válido sin inferencia, rechazo de múltiples archivos,
Escape/foco del inspector y navegación de comparación sin otra petición de análisis. Se
conservan pruebas de ambos temas, errores, parciales/rechazos, procedencia, coordenadas Unicode,
contratos serializados y ausencia de interpretación HTML del contenido no confiable.
El aviso previo de Starlette/TestClient sobre httpx permanece no bloqueante; no se modificaron
dependencias para ocultarlo.

Evidencias: [frontend](../artifacts/redesign_v1/frontend_tests.xml),
[backend](../artifacts/redesign_v1/backend_tests.xml),
[conexión React/API](../artifacts/redesign_v1/connected_tests.xml),
[HTTP y build servido](../artifacts/redesign_v1/http_smoke.json).

## Revisión visual: límite real

Se consultó el estado del navegador y se intentó abrir la aplicación local. Ambos intentos
informaron que el host no estaba disponible; el inventario también indicó ausencia del pipe
nativo. **No fue posible inspeccionar el resultado en un navegador real**, ni verificar
visualmente claro/oscuro o distintas resoluciones. No se presentan capturas ni se confunde
JSDOM con un navegador visual. Las reglas responsive y los estados están implementados y
probados funcionalmente; su inspección visual final permanece pendiente.

Para revisión manual: claro/oscuro en 1440×900 y 1366×768, luego 1024×768, 768×1024 y 390×844;
comprobar foco/zoom al 200 %, código largo, nombres largos de archivo, comparación con rechazo,
evidencia recuperada y arrastre. No se requiere usar el LLM para revisar el diseño.

## Archivos y conservación del trabajo previo

Modificados respecto al inicio de este encargo:

- `frontend/src/App.tsx`: shell, composición y cierre accesible del inspector.
- `frontend/src/components/Editor.tsx`: cabecera/metadatos y carga por arrastre validada.
- `frontend/src/components/Results.tsx`: vacío, cadena de evidencia y comparación accesible.
- `frontend/src/styles.css`: entrada del nuevo sistema de estilos.
- `frontend/src/test/App.test.tsx`: cuatro regresiones nuevas de interacción.

Nuevos: `PipelineSelector.tsx`, `styles/tokens.css`, `styles/studio.css`, este informe y recibos
en `artifacts/redesign_v1/`. El stylesheet previo se conserva allí para facilitar revisión de
un archivo que ya estaba sin staging antes de este encargo.

Los numerosos archivos untracked de la Fase 3 **ya existían al comenzar** y no se atribuyen a
este rediseño. Se tomó un inventario de 388 archivos previos, incluyendo tracked y untracked.
Se verifican hashes de backend, contratos, cliente API, hooks, modelos, fixtures, prompts,
pilotos y evidencias previas; se mantienen intactos. Índice e historial Git se comparan con
el inicio: todo sigue local en `develop`, sin staging, commits o push.

[Recibo final e inventario](../artifacts/redesign_v1/final_verification.json).

## Cómo revisar la aplicación

Se reutilizó el backend que ya estaba escuchando en **http://127.0.0.1:8000**; no se inició,
cerró ni reemplazó ese proceso. La comprobación HTTP confirma que sirve los assets del rediseño.
Recargar la página para obtener la nueva versión.

Si el servidor no está iniciado, desde la raíz:

```powershell
npm.cmd --prefix frontend run build
.\.venv\Scripts\python.exe -B -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Abrir http://127.0.0.1:8000. Para desarrollo con recarga: iniciar también
`npm.cmd --prefix frontend run dev` y abrir http://127.0.0.1:5173.
A funciona sin Ollama. La instalación y los límites operativos siguen en la
[guía local de Fase 3](phase3_local.md).
