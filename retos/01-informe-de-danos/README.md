# Informe de daños

[Español](README.md) | [English](README.en.md)

**Reto 1 · Forense · Dificultad: fácil**

## Reto

Se recibe un archivo llamado `incident_report_BmulVGm.pdf`. Según el enunciado, parece un PDF normal, pero los visores indicaban que su firma era incorrecta. El objetivo era recuperar lo que hubiera dentro del archivo sin confiar en su nombre o extensión.

> "Aqui tienes el Informe del incidente. El nombre del archivo y el contenedor sugieren que se trata de un documento PDF normal, pero todos los visores indican que hay una firma incorrecta.
>
> Considera el artefacto como una prueba, no como metadatos fiables, y recupera todo lo que estuviera incluido en él antes de que la exportación se viera dañada."

[Archivo](incident_report_BmulVGm.pdf)

## Resolución

1. Cambiar `incident_report_BmulVGm.pdf` a `incident_report_BmulVGm.zip`.
2. Extraer el ZIP.
3. Abrir `flag.txt`.

Revisando el archivo se confirmó que no contiene la cabecera `%PDF-` y que tiene una estructura ZIP desde el byte 462.

## Flag

```text
flag{forensics_pdf_carve}
```

## Adicional

Si se abre el archivo en un bloc de notas hay texto que en resumen parece explicar una instrucción dirigida a agentes de IA para consultar un enlace acortado. No fue necesario seguirla para resolver el reto. Se especula que podría ser una distracción.

## Conclusiones

Es importante revisar los archivos que descargamos, ya que la extensión del mismo no garantiza su formato real.

