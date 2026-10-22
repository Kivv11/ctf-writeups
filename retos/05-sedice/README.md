# Sedice

[Español](README.md) | [English](README.en.md)

**Reto 5 · Hacking web · Dificultad: medio**

## Reto

>La plataforma se basa en tokens firmados y controles de acceso basados en roles para proteger las funciones administrativas, pero hay algo en la implementación que parece peligrosamente frágil.
Una investigación más exhaustiva ha descubierto una copia de seguridad de configuración olvidada que contenía secretos de autenticación confidenciales. Con estas credenciales, era posible falsificar identidades de confianza y acceder a áreas de la plataforma reservadas a los administradores.
>
>Tu objetivo es analizar el flujo de autenticación, aprovechar la vulnerabilidad y recuperar la flag protegida oculta tras la interfaz de administración.

[Enlace](https://challenges.hackrocks.com/sedice)

## Flag

```text
jwt_4nd_l0c4l_st0r4g3_t4mp3r1ng_g0es_brr
```

## Resolución con CyberChef y JWT.io

Se utiliza [CyberChef](https://gchq.github.io/CyberChef/) para decodificar el JWT con `JWT Decode` y calcular el `MD5` del segundo token. La firma del JWT se realiza con [JWT.io](https://www.jwt.io/), en su pestaña **JWT Encoder**.

La primera vulnerabilidad se encontraba en un archivo de configuración expuesto públicamente.
Para encontrarlo, se utilizó [**FFUF**](https://github.com/ffuf/ffuf), una herramienta de enumeración de directorios y archivos web, junto con la wordlist [env-backups.txt](./env-backups.txt), con 78 rutas relacionadas con archivos `.env` y copias de seguridad.

```
.\ffuf.exe -u https://challenges.hackrocks.com/sedice/FUZZ -w .\env-backups.txt -mc all -fc 404 -rate 5 -t 2
```

Los parámetros del comando son:

- `-u https://challenges.hackrocks.com/sedice/FUZZ`: define la URL objetivo. `FUZZ` es el marcador que se sustituye por cada ruta de la wordlist.
- `-w .\env-backups.txt`: indica el archivo de rutas que se probarán. El prefijo `.\` señala el directorio actual en Windows.
- `-mc all`: considera respuestas con cualquier código de estado HTTP.
- `-fc 404`: excluye de los resultados las respuestas HTTP 404 (recurso no encontrado). Combinado con `-mc all`, permite observar los demás códigos de estado.
- `-rate 5`: limita el ritmo a 5 peticiones por segundo.
- `-t 2`: utiliza 2 hilos concurrentes. Este límite de concurrencia y el de peticiones por segundo controlan la carga del escaneo.

`.\ffuf.exe` ejecuta el binario de FFUF ubicado en el directorio actual.

El escaneo encontró:

```
backup/.env.bak    [Status: 200, Size: 54]
```

El punto de partida es la configuración expuesta en `/sedice/backup/.env.bak`:

```text
SECRET_KEY=s3cr3t_jwt_k3y_ananta_ctf
SALT=xG9AmK2$$pL
```

La sesión utiliza un JWT y un segundo token llamado `ls_token`, cuya derivación identificada es:

```text
ls_token = MD5(JWT completo + SALT)
```

El signo `+` indica concatenar ambos textos sin separador. Un **JWT** contiene un encabezado, un payload con los datos del usuario y una firma. **HS256** utiliza HMAC-SHA256 y una clave secreta compartida para firmarlo y verificarlo.

### Fórmula del ls_token

Se tomaron el `jwt` y el `ls_token` originales de una misma sesión, antes de modificar el rol. Con el `SALT` y la `SECRET_KEY` del archivo expuesto, se probaron distintas combinaciones y se comparó cada resultado con el segundo token original, utilizando el [script](./sedice_check_ls.py) brindado por GPT.

### Modificar el rol y firmar el JWT

Para completar la firma se utiliza [JWT.io](https://www.jwt.io/). El resto del procedimiento puede seguir realizándose con CyberChef.

1. Obtener el JWT de una sesión normal desde DevTools, en el almacenamiento local del sitio (`localStorage`, clave `jwt`).
2. Pegar el token en CyberChef y aplicar `JWT Decode` para leer su payload.
3. Copiar el payload JSON y cambiar `"role":"user"` por `"role":"admin"`, conservando `sub` y `username`. El campo `exp` debe ser un timestamp Unix futuro, expresado en segundos.
4. Abrir JWT.io y seleccionar **JWT Encoder**. Elegir el algoritmo `HS256` y colocar el payload modificado en el editor correspondiente.
5. Usar el encabezado `{"alg":"HS256","typ":"JWT"}` e introducir en **Secret** `s3cr3t_jwt_k3y_ananta_ctf`.
6. Copiar el JWT firmado generado por JWT.io. Esa salida es el JWT administrativo que se utiliza para calcular el nuevo `ls_token`.
7. Volver a CyberChef y, en una *recipe* nueva, pegar el JWT recién firmado en JWT.io completo, seguido inmediatamente del salt:

```text
<JWT_ADMIN>xG9AmK2$$pL
```

Reemplazar el marcador por el token real. Aplicar `MD5`: su salida de 32 caracteres hexadecimales es el nuevo `ls_token`.

### Solicitar la flag

Desde la consola del navegador, estando en la página del reto, sustituir los dos marcadores por los valores obtenidos:

```javascript
fetch('/sedice/api/flag', {
  headers: {
    'Authorization': 'Bearer JWT_ADMIN',
    'X-LS-Token': 'LS_TOKEN'
  }
})
.then(response => response.json())
.then(console.log);
```

La respuesta exitosa registrada fue HTTP 200:

```json
{
  "flag": "jwt_4nd_l0c4l_st0r4g3_t4mp3r1ng_g0es_brr",
  "message": "Welcome, snow. You have root."
}
```


## Conclusiones

El problema fue que la clave de firma estaba expuesta, permitiendo falsificar el rol del JWT y recalcular el segundo token.
