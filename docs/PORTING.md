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
| Texto/fuente/estilos | Diálogos de texto y fuente; se rasteriza al aceptar |
| Selección rectangular/libre/movimiento | Implementado con máscara de selección libre |
| Copiar/cortar/pegar/pegar archivo | Implementado; pegar puede ampliar el lienzo |
| Selección transparente | Color 2 como color transparente |
| Recortar/escalar selección | Acciones de menú |
| Cambiar tamaño/escalar lienzo | Dimensiones en píxeles; zonas nuevas con Color 2 |
| Rotar/voltear/sesgar/invertir | Selección o documento |
| Formas | Línea, curva con dos controles, elipse, rectángulos, polígono, triángulos, rombo, pentágono, hexágono, flechas y estrellas |
| Contorno/relleno | Color 1 y Color 2 |
| Zoom 10–1000%/ajuste a ventana | Implementado |
| Cuadrícula/reglas/miniatura/pantalla completa | Implementado; reglas como guías sobre el lienzo |
| Arrastrar y soltar | Un archivo local |
| Imprimir/vista previa/configurar página | Qt/CUPS; PDF probado, impresora física pendiente |
| Fondo de escritorio | Portal `SetWallpaperFile`; requiere backend compatible; pendiente de prueba GNOME/KDE real |
| Configuración | QSettings en ubicación XDG del usuario |

## Diferencias pendientes

La interfaz Qt no reproduce exactamente la cinta Windows. Texto y formas se rasterizan al confirmar, salvo la fase de control de curvas/polígonos. No se reproducen los tiradores para cambiar tamaño del lienzo ni la edición posterior de todos los nodos de formas. Las selecciones se escalan desde el menú. No se reproducen las unidades cm/pulgadas ni el modo monocromo del diálogo Windows. El portal de fondo usa la configuración del escritorio, no los estilos del registro Windows.

Por esas diferencias y las integraciones no verificadas, esta versión es **preview 0.1.0**, no equivalencia completa certificada.

## Uso

- Botón izquierdo: Color 1. Derecho: Color 2. `X` intercambia colores.
- `Shift` restringe proporciones de formas.
- Polígono: clics para vértices; `Enter` o botón derecho confirma.
- Curva: arrastrar extremos, luego hacer clic en dos puntos de control. `Enter` acepta, `Escape` cancela.
- Selección: arrastrar para crear; arrastrar dentro para mover. Las transformaciones afectan la selección existente.
- `Ctrl+Z` deshace; `Ctrl+Shift+Z` rehace.

## Compatibilidad

Binarios locales x86_64: Ubuntu 24.04, glibc 2.39 o posterior. AppImage no incluye drivers ni sustituye glibc. `.deb` es para Ubuntu 24.04/Debian 13 compatibles, no para Void. Flatpak usa Freedesktop 25.08 y no depende de la glibc del host.

Void glibc: AppImage/portable con bibliotecas gráficas, o Flatpak. Void musl: Flatpak. La [documentación oficial de Void](https://docs.voidlinux.org/config/external-applications.html) indica que AppImage no funciona en instalaciones musl. La prueba de este proyecto en Void fue en un contenedor **glibc**, no musl ni un escritorio completo.

Los scripts reconocen x86_64 y aarch64. La existencia de soporte de compilación no significa que cada arquitectura o distribución haya sido probada. Consulta VALIDATION.md.
