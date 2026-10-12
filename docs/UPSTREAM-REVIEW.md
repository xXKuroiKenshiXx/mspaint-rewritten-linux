# Revisión del fork Windows

12 de octubre de 2026. Rama revisada: `ripDZL/mspaint-rewritten/fix/core-stability-phase1`, commit `93d0fb4`. Base de este fork: `2a1ac8a`. Se conservaron los 14 commits nuevos mediante fast-forward.

Es una recreación en Delphi del Paint de Windows 10: sirve para dibujar y editar imágenes raster, seleccionar, recortar, cambiar tamaño, rotar, añadir texto, usar portapapeles, imprimir y guardar. Es MIT; no es el Paint oficial de Microsoft ni incluye sus funciones generativas modernas.

El cambio neto afecta ocho archivos: 499 líneas añadidas y 251 eliminadas.

| Área | Cambios observados |
|---|---|
| Carga | Bitmaps temporales y transferencia de propiedad después del éxito; preservación del documento ante errores |
| Ventanas | Cierre con `caFree`, evitando destruir formularios dentro de su evento; uso de `FreeAndNil` |
| Documento nuevo | Reinicio de nombre, selección, estado de guardado y deshacer |
| Historial | Liberación de la rama de rehacer y límite aproximado de memoria/cantidad |
| Selección/portapapeles | Limpieza de temporales, manejo de errores y ampliación del lienzo al pegar |
| Transformaciones | Corrección de las inversiones horizontal y vertical |
| Propiedades | Tamaños positivos, máximo de 32767 por lado y 64 megapíxeles |
| Recientes | Captura de ruta antes de diálogos que pueden alterar índices y manejo de archivos ausentes |
| Fondo | Guardado de la versión actual antes de establecer el fondo |
| Diagnóstico | Reporte de fugas en Debug |

Los commits intermedios denominados “workflow” están en el historial; el árbol final revisado no contiene workflows de GitHub.

## Seguridad y problemas residuales

La inspección de los cambios no encontró descargas ocultas, persistencia, robo de credenciales ni ejecución automática de payloads. Las bibliotecas originales `Cod.*` incluyen utilidades de procesos, registro y consulta a random.org; su presencia no demuestra malware. La interfaz abre el sitio del autor mediante una acción explícita. El port Linux no importa esas bibliotecas Windows.

ClamAV 1.5.4, con 3.628.164 firmas, analizó inicialmente 56 archivos: cero infectados. Esto describe las detecciones de ese motor, no una garantía universal. No se analizó un ejecutable Delphi de terceros ni se realizó una auditoría formal de todas las dependencias.

Problemas pendientes en Windows:

- `FinishResize` comprueba positividad pero no aplica los límites del diálogo de propiedades y modifica el bitmap directamente.
- `CacheNew` conserva al menos dos bitmaps: puede superar 256 MiB. Calcula el límite con el tamaño actual aunque los estados históricos tengan tamaños distintos.
- `SaveFile` escribe directamente sobre el destino; un fallo puede dejar un archivo incompleto.

El núcleo Linux valida dimensiones, suma los bytes reales del historial y guarda mediante reemplazo atómico con `QSaveFile`.

## Windows 11

El proyecto apunta a Win64 y usa VCL/WinAPI. Su funcionamiento en Windows 11 queda **sin verificar**: aquí no están el compilador Delphi ni unidades de Codrut's Visual Library como `Cod.Visual.Button` y `Cod.Dialogs.PrintDlg`. Se necesita compilar con esas dependencias y probar archivos, herramientas, portapapeles e impresión en Windows 11.

Fuentes: [rama revisada](https://github.com/ripDZL/mspaint-rewritten/tree/fix/core-stability-phase1), [commit](https://github.com/ripDZL/mspaint-rewritten/commit/93d0fb4), [biblioteca visual](https://github.com/Codrax/CodrutsVisualLibrary).
