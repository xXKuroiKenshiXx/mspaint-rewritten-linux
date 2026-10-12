# Validación — preview 0.1.0

12 de octubre de 2026. Pruebas locales en WSL2 Ubuntu 24.04 x86_64. Python 3.12, Qt/PySide6 Essentials 6.12.0, Pillow 12.3.0 y PyInstaller 6.22.3.

## Resultados

- **49 pruebas pytest aprobadas**: herramientas de ratón y formas, controles de curva, texto, cancelación de descarte, copia/pegado/recorte, máscara transparente, movimiento de selección con deshacer, giro, zoom, miniatura y exportación PDF. El núcleo verifica archivos corruptos, PNG/BMP/JPEG/GIF/WebP, guardado fallido, historial tras guardar y bifurcar, relleno, límites, nuevo documento y ampliación al pegar.
- **Ejecutable empaquetado**: sus comprobaciones internas de formatos, deshacer/rehacer, relleno, cambiar tamaño, pegar y preservar el documento ante entrada corrupta pasan sin pytest ni Python instalado en el host.
- **X11/Xvfb**: arranque del ejecutable y captura de la interfaz aprobados.
- **AppImage**: extracción/ejecución sin FUSE y arranque aprobados. No se probó el montaje FUSE en WSL.
- **`.deb`**: instalado con apt en un contenedor Ubuntu 24.04 limpio; comprobaciones internas y arranque aprobados.
- **Flatpak**: instalación, comprobaciones internas y arranque offscreen aprobados. X11 también aprobado; WSL necesitó `--share=network` solo durante esa prueba porque su Xvfb utiliza un socket abstracto. El manifiesto distribuido no solicita red.
- **pip-audit**: sin vulnerabilidades conocidas en las dependencias Python de ejecución ni en el entorno de compilación final. Al comienzo encontró vulnerabilidades en pip 24.0 del venv; se actualizó a 26.2.1. Esta auditoría no cubre todas las bibliotecas C/C++ ni demuestra ausencia de fallos desconocidos.
- **ClamAV 1.5.4, 3.628.164 firmas**: análisis final de 647 archivos del ejecutable/artefactos, cero infectados. Datos analizados: 518,73 MiB; leídos: 962 MiB. El análisis inicial del checkout también tuvo cero detecciones. Se incluyen logs; los límites del motor se aplican y no se promete ausencia universal de malware.

## Contenedores de distribuciones

Cada prueba instala bibliotecas gráficas dentro de un contenedor oficial desechable, ejecuta `--self-test` del binario final y abre/cierra la ventana con el backend offscreen. No son pruebas de escritorio completas.

| Distribución | Formatos/edición interna y arranque |
|---|---|
| Ubuntu 24.04 | Aprobado |
| Debian 13 | Aprobado |
| Fedora 44 | Aprobado |
| Arch Linux, imagen consultada el 12/10/2026 | Aprobado |
| Void Linux glibc, imagen consultada el 12/10/2026 | Aprobado |

Los logs y hashes OCI están en `validation-logs` de la release. Las primeras pruebas Ubuntu/Debian/Fedora detectaron que faltaba instalar OpenGL en los contenedores; se corrigieron las dependencias del paquete/recetas y se repitieron las pruebas con éxito. También se corrigieron las bibliotecas X11 ausentes del entorno de compilación.

## Fuentes y licencias

La release incluye un espejo de fuentes de Qt/PySide6, ICU, Pillow y los paquetes Ubuntu distribuidos, más los avisos e inventarios en los binarios. Las bibliotecas Kerberos `krb5` de versión `1.20.1-6ubuntu2.8` usan licencia permisiva MIT Kerberos/BSD: no se pudo obtener su fuente exacto supersedido desde los índices y Launchpad no fue accesible. Sus avisos completos sí están incluidos; la excepción se registra en `unavailable-permissive-sources.json`. No se aplica esa excepción a bibliotecas GPL/LGPL.

## Sin verificar o fuera de la cobertura

- Windows 11 y la compilación Delphi original.
- Void musl y escritorios completos de cada distribución.
- Una sesión Wayland real, impresión física, configuración de fondo en GNOME/KDE y acceso a archivos externos a Pictures mediante portales.
- Arquitecturas ARM y versiones antiguas de Linux/glibc.
- Equivalencia completa de interacción con el original: consulta [PORTING.md](PORTING.md).

El workflow de GitHub permite repetir compilación, auditoría, paquetes y pruebas. Sus resultados remotos deben consultarse por ejecución; las pruebas locales anteriores no presumen que un futuro workflow pase.
