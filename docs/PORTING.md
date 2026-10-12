# Cobertura Linux

La raíz conserva el código Delphi. `linux/` contiene una implementación nueva con Python y Qt Widgets. No usa Wine, VCL ni el registro de Windows. El código de aplicación es MIT; las bibliotecas conservan sus licencias.

| Función | Implementación Linux |
|---|---|
| Nuevo, abrir, guardar, guardar como, recientes | Implementado; carga transaccional y guardado atómico |
| PNG, BMP, JPEG, GIF | Lectura/escritura; GIF estático de paleta mediante Pillow |
| Deshacer/rehacer | Máximo de 50 estados y 256 MiB de imágenes históricas; no incluye temporales de operaciones |
| Lápiz/grosor | Implementado |
| Pinceles normal, spray, círculo translúcido, línea translúcida y textura | Brush, Airbrush, Watercolor, Marker y Crayon; trazos Qt diferentes de GDI |
| Goma, rellenar, recoger color | Implementado |
| Texto/fuente/estilos | Editor sobre el lienzo con ocho tiradores, cinta contextual, fuente, tamaño, estilos y fondo transparente/opaco; se rasteriza al confirmar |
| Selección rectangular/libre/movimiento | Máscara de selección libre, movimiento y ocho tiradores para cambiar tamaño |
| Copiar/cortar/pegar/pegar archivo | Implementado; pegar puede ampliar el lienzo |
| Selección transparente | Color 2 como color transparente |
| Recortar/escalar selección | Acciones de menú |
| Cambiar tamaño/escalar lienzo | Tiradores del lienzo y propiedades en píxeles/cm/pulgadas; zonas nuevas con Color 2 |
| Rotar/voltear/sesgar/invertir | Selección o documento |
| Formas | Las 18 formas de la cinta original; figuras con tiradores antes de confirmar, curva con dos controles editables y vértices de polígono movibles |
| Contorno/relleno | Color 1 y Color 2 |
| Zoom 10–1000%/ajuste a ventana | Implementado |
| Cuadrícula/reglas/miniatura/pantalla completa | Reglas exteriores con indicador del cursor; miniatura en ventana independiente y pantalla completa de imagen |
| Arrastrar y soltar | Un archivo local |
| Imprimir/vista previa/configurar página | Qt/CUPS; PDF probado, impresora física pendiente |
| Fondo de escritorio | Portal `SetWallpaperFile`; requiere backend compatible; pendiente de prueba GNOME/KDE real |
| Configuración | QSettings en ubicación XDG del usuario |

## Diferencias pendientes

La interfaz reproduce las coordenadas y grupos del DFM, extrae sus iconos originales y conserva el diseño de Paint de la referencia: título con acceso rápido, pestañas File/Home/View, cinta, reglas, lienzo y barra de estado segmentada. `linux/scripts/extract-dfm-assets.py` y `assets/dfm-map.json` registran la procedencia. El texto se edita sobre el lienzo; las figuras siguen siendo editables hasta confirmar. Las fuentes libres Selawik y Carlito sustituyen las métricas de Segoe UI y Calibri cuando estas no están instaladas.

Quedan diferencias de rasterización Qt/GDI, fuentes y diálogos nativos de archivos/impresión. El DFM del fork no incluye el botón «Edit with Paint 3D» ni modo monocromo en propiedades; no se añade una aplicación Paint 3D ficticia. El portal de fondo usa la configuración del escritorio, no los estilos del registro Windows. No se certifica equivalencia píxel por píxel ni integración completa en todos los escritorios.

Por esas diferencias y las integraciones no verificadas, esta versión es **preview 0.1.0**, no equivalencia completa certificada.

## Uso

- Botón izquierdo: Color 1. Derecho: Color 2. `X` intercambia colores.
- `Shift` restringe proporciones de formas.
- Polígono: clics para vértices; `Enter` o botón derecho confirma.
- Curva: arrastrar extremos, hacer clic en dos puntos de control y arrastrarlos para ajustar. `Enter` acepta, `Escape` cancela.
- Selección: arrastrar para crear; arrastrar dentro para mover o sus tiradores para cambiar tamaño. Las transformaciones afectan la selección existente.
- Texto: arrastrar un rectángulo, escribir y ajustar desde la pestaña Text. Cambiar de herramienta o `Ctrl+Enter` confirma; `Escape` cancela.
- `Ctrl+Z` deshace; `Ctrl+Shift+Z` rehace.

## Compatibilidad

Binarios locales x86_64: Ubuntu 24.04, glibc 2.39 o posterior. AppImage no incluye drivers ni sustituye glibc. `.deb` es para Ubuntu 24.04/Debian 13 compatibles, no para Void. Flatpak usa Freedesktop 25.08 y no depende de la glibc del host.

Void glibc: AppImage/portable con bibliotecas gráficas, o Flatpak. Void musl: Flatpak. La [documentación oficial de Void](https://docs.voidlinux.org/config/external-applications.html) indica que AppImage no funciona en instalaciones musl. La prueba de este proyecto en Void fue en un contenedor **glibc**, no musl ni un escritorio completo.

Los scripts reconocen x86_64 y aarch64. La existencia de soporte de compilación no significa que cada arquitectura o distribución haya sido probada. Consulta VALIDATION.md.
