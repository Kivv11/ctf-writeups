# IO HO FIRM 2.0

[Español](README.md) | [English](README.en.md)

**Reto 9 · Exploiting · Dificultad: Difícil**

## Descripción

>En las profundidades de la sede central de IO_HO_FIRM, los ingenieros presentaron con orgullo la última versión de su plataforma operativa patentada: IO_HO_FIRM 2.0. Comercializado como un avance revolucionario en la gestión segura de infraestructuras, el firmware se encargaba de proteger los activos más sensibles de la empresa, desde credenciales internas hasta archivos de investigación clasificados. Se aseguró a los empleados que, incluso si un atacante lograba acceder al sistema, múltiples capas de aislamiento impedirían cualquier compromiso significativo.
>
>Sin embargo, oculto dentro de un controlador personalizado incluido como parte del firmware, se encontraba un sutil error de implementación.
>
>Al estudiar cuidadosamente el controlador personalizado y manipular el comportamiento interno del sistema, descubriste una forma de influir en componentes que nunca debían ser tocados por usuarios ordinarios.
>
>Un paso llevó a otro a medida que las estructuras de confianza eran remodeladas silenciosamente y los controles de acceso perdían gradualmente su autoridad. Los archivos que deberían haber estado protegidos pasaron a ser escribibles, las restricciones se disolvieron, y las identidades antes reservadas para administradores podían asumirse a voluntad.
>
>Finalmente, el camino llevó a un archivo bloqueado en lo profundo de los servidores de la empresa.
>
>Todo se encuentra en la conexión de abajo, ¡recupera el archivo confidencial antes de que otro atacante robe y abuse de esta vulnerabilidad!

***Nota**: la instancia se reinicia cada 20 minutos.*

**Conexión:**

```
nc ch4ll3ng3s.hackrocks.com 6767
```

## Flag

```
p4g3j4ck_h1ts_d1ff
```

## Resolución

Al conectarse al servicio se obtiene una terminal Linux. Para identificar el entorno se ejecutan:

```
id
uname -a
ls -la /dev
ls -la /
```

Se observa que el sistema utiliza el kernel Linux `6.13.0` y que la sesión pertenece al usuario `ctf`, sin privilegios administrativos.

```
uid=1000(ctf) gid=1000 groups=1000
Linux (none) 6.13.0 #3 x86_64 GNU/Linux
```

Entre los archivos y dispositivos disponibles destacan:

```
/dev/ioho_kd
/ioho_kd.ko
/flag
```

El archivo `/flag` pertenece a `root` y tiene permisos `600`, por lo que no puede leerse desde la cuenta actual.

Sin embargo, el dispositivo `/dev/ioho_kd` tiene permisos `666`, permitiendo que un usuario sin privilegios interactúe con el controlador del kernel.

El archivo `ioho_kd.ko` corresponde al módulo vulnerable. Para analizarlo se utilizan herramientas como:

```
readelf -sW ioho_kd.ko
objdump -drwC -Mintel ioho_kd.ko
```

El desensamblado permite identificar dos operaciones `ioctl`:

| Operación | Función                         |
| --------- | ------------------------------- |
| `0xF000`  | Reserva un bloque de 1024 bytes |
| `0xF001`  | Copia datos al bloque reservado |

La vulnerabilidad se encuentra en la segunda operación.

El controlador permite copiar hasta `0x400` bytes, pero después escribe un byte nulo en la posición indicada por el tamaño.

Su comportamiento puede representarse mediante el siguiente pseudocódigo:

```
copy_from_user(obj, buffer, size);
obj[size] = '\0';
```

Cuando `size = 0x400`, se produce la escritura:

```
obj[0x400] = '\0';
```

Sin embargo, un buffer de 1024 bytes solo admite posiciones entre `0` y `0x3FF`.

Esto provoca que se escriba un byte fuera de los límites del buffer, dando lugar a un **Off-by-One NULL Byte Overflow**.

Para aprovechar esta vulnerabilidad se utiliza una técnica conocida como **PageJack**, orientada a manipular estructuras internas del kernel mediante corrupción de memoria.

La estrategia aplicada consiste en:

1. Preparar el heap del kernel utilizando objetos `kmalloc-1024`.
2. Reservar un bloque mediante `ioctl(0xF000)`.
3. Ejecutar `ioctl(0xF001)` con un tamaño de `0x400` para provocar el desbordamiento.
4. Aprovechar la corrupción de estructuras relacionadas con los pipes para manipular una página de memoria.
5. Reutilizar dicha página como parte de una estructura `struct file` asociada a `/etc/passwd`.
6. Modificar `/etc/passwd` para permitir el acceso a la cuenta `root` sin contraseña.

La entrada utilizada para este último paso es:

```
root::0:0:root:/root:/bin/sh
```

Al conseguir modificar `/etc/passwd`, se puede utilizar `su` para ejecutar comandos con privilegios de administrador y acceder al archivo `/flag`.

Para realizar la explotación se utiliza el ejecutable [`ioho_exploit_v3`](https://github.com/Kivv11/ctf-writeups/blob/main/retos/09-io-ho-firm-2/ioho_exploit_v3) brindado por GPT.

Como el entorno no dispone de un compilador accesible, el ejecutable se transfiere codificado mediante **Base64 y gzip**.

El payload completo de transferencia está disponible en [`exploit_v3_transferencia.sh`](https://github.com/Kivv11/ctf-writeups/blob/main/retos/09-io-ho-firm-2/exploit_v3_transferencia.sh).

Una vez transferido el contenido Base64 a `/tmp/v3.b64`, se reconstruye el ejecutable:

```
busybox base64 -d /tmp/v3.b64 | busybox gzip -dc > /tmp/ioho_v3
```

Se comprueba que el archivo contiene 9944 bytes:

```
wc -c /tmp/ioho_v3
```

Finalmente, se conceden permisos de ejecución y se ejecuta:

```
chmod +x /tmp/ioho_v3
/tmp/ioho_v3
```

La salida obtenida es:

```
[*] Preparando heap kmalloc-1024...
[*] ioctl ALLOC: 0
[*] Activando el null-byte overflow...
[*] ioctl WRITE: 0

[+] pipe corrupto: 80
[+] identificador de la pagina compartida: 79

[*] Liberando pagina compartida...
[*] Reutilizando pagina como struct file para /etc/passwd...

[*] archivos abiertos: 640
[*] escrituras via pipe: 4

[+] /etc/passwd modificado usando descriptor 10
```

Los mensajes del exploit indican que ambas operaciones `ioctl` finalizaron correctamente y que se consiguió modificar `/etc/passwd`.

Después de modificar `/etc/passwd`, el exploit intenta utilizar `su` para acceder al archivo protegido.

La salida registrada es:

```
[+] Intentando leer flag inmediatamente con su...

p4g3j4ck_h1ts_d1ff
```

De esta forma se obtiene la flag del desafío.

Sin embargo, inmediatamente después se produce un error del kernel:

```
kernel tried to execute NX-protected page - exploit attempt? (uid: 0)

Kernel panic - not syncing: Fatal exception in interrupt
```

Esto se debe a que la corrupción de memoria deja estructuras internas del kernel en un estado inconsistente.

Aunque la explotación no es estable y termina provocando un *kernel panic*, la flag se recuperó correctamente antes de que el sistema falle.

## Conclusión

Una escritura de un solo byte fuera de los límites de un buffer puede comprometer la seguridad de un sistema cuando ocurre dentro del kernel.
