# Señales secretas

[Español](README.md) | [English](README.en.md)

**Reto 4 · Reversing · Dificultad:**

## Reto

> Tu equipo interceptó un Dispositivo ESP32 comprometido durante un barrido de seguridad de red. El dispositivo estaba emitiendo señales intermitentes que no coincidían con ningún protocolo conocido. El análisis inicial mostró que estaba ejecutando firmware personalizado, pero el código fuente no aparecía por ninguna parte.
>
> Has logrado extraer el binario compilado de la memoria flash del dispositivo. Es un archivo ELF estándar, pero hay algo en él que resulta extraño. El binario es más grande de lo que debería, y el análisis estático revela miles de símbolos dispersos por toda su estructura. La mayoría pertenecen al framework ESP32, pero oculto entre ellos hay algo completamente distinto.
>
> Algo te sugiere que el dispositivo formaba parte de una red de comunicación que utilizaba codificación. Estás seguro de que el mensaje secreto está incrustado en algún lugar de este binario, esperando a ser descubierto.

[Archivo](challenge.elf)

## Flag

```text
YOUREVERSEDMYFIRMWARE
```

## Resolución

Se abre `challenge.elf` en Ghidra para estudiar el binario sin ejecutarlo. **Ghidra** es una herramienta de ingeniería inversa que permite examinar instrucciones, datos y símbolos sin disponer del código fuente.

### Identificar el archivo

La cabecera corresponde a un **ELF de 32 bits, little-endian, para Xtensa**, coherente con el ESP32. ELF es un formato de archivos ejecutables; little-endian indica que los bytes menos significativos se almacenan primero. El archivo conserva símbolos e información de depuración, útiles para reconocer funciones y datos.

### Buscar referencias a las señales

La pista del enunciado sobre señales intermitentes orientó la búsqueda hacia nombres como `morse`, `blink` y `transmit`. Los símbolos relevantes encontrados fueron:

```text
morse
blinkSymbol(char)
transmitLetter(char const*)
loop()
```

### Seguir la tabla morse

`morse` es una tabla situada en `0x3ffbdb60` que ocupa 84 bytes. Contiene **21 punteros de 4 bytes**. Un puntero almacena la dirección de otro dato; aquí cada entrada apunta a una cadena de puntos y rayas en `.flash.rodata`.

La función `loop()` recorre las 21 entradas y llama a `transmitLetter`, que lee cada cadena hasta el byte `00`. Esto permite establecer el orden y la cantidad de letras.

### Leer las cadenas

Se sigue la primera entrada hasta `0x3f400120`. Los bytes se leen hasta el terminador `00`:

```text
Bytes:  2d 2e 2d 2d 00
Morse:  -.--
Letra:  Y
```

En ASCII, `2e` representa un punto y `2d` una raya. La siguiente tabla ilustra lo que se comienza a obtener leyendo las siguientes entradas:

| Entrada | Dirección | Morse | Letra |
| ---: | --- | --- | :---: |
| 0 | `0x3f400120` | `-.--` | Y |
| 1 | `0x3f400125` | `---` | O |
| 2 | `0x3f40012a` | `..-` | U |
| 3 | `0x3f400137` | `.-.` | R |
| 4 | `0x3f400139` | `.` | E |

Se empieza a obtener `YOURE`. Se continúa con las restantes entradas, siguiendo los punteros en orden.

Las 21 entradas producen:

```text
-.-- --- ..- .-. . ...- . .-. ... . -.. -- -.-- ..-. .. .-. -- .-- .- .-. .
```

Al traducir cada secuencia con una tabla Morse se obtiene:

```text
YOUREVERSEDMYFIRMWARE
```
