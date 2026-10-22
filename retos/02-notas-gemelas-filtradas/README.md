# Notas gemelas filtradas

[Español](README.md) | [English](README.en.md)

**Reto 2 · Criptografía · Dificultad: fácil**

## Reto

> Se han filtrado dos Archivos de texto cifrado de un dump de herramientas de script kiddie. Ambos mensajes tienen la misma longitud y fueron sometidos a XOR con un flujo de clave reutilizado.
>
> ¡Recupera la clave que hay dentro!

[Archivo](recovered_files_8VKotXN.zip)

El ZIP contiene `memo_a.hex`, `memo_b.hex` y `README.txt`. Los dos primeros son mensajes de 64 bytes representados en hexadecimal. El README indica que el mensaje A siempre empieza por `MEMO-01:`.

## Flag

```text
flag{crypto_two_time_pad}
```

## Resolución

Al cifrar dos mensajes con el mismo flujo de clave `K`:

```text
Cₐ = Mₐ ⊕ K
Cᵦ = Mᵦ ⊕ K
```

Donde:

```text
C : texto cifrado
M : mensaje original
⊕ : operación XOR
K : flujo de clave reutilizado
```

XOR es asociativo y conmutativo. Además, un valor XOR consigo mismo da cero, y un valor XOR cero queda igual. Por eso, al combinar los cifrados, la clave se cancela:

```text
Cₐ ⊕ Cᵦ = (Mₐ ⊕ K) ⊕ (Mᵦ ⊕ K) = Mₐ ⊕ Mᵦ
( K ⊕ K = 0)
```

Por lo tanto, si se conoce una parte de A, se recupera la misma parte de B:

```text
Mᵦ = Cₐ ⊕ Cᵦ ⊕ Mₐ
```

## Resolución en CyberChef

Puede reproducirse la teoría en [CyberChef](https://gchq.github.io/CyberChef/). CyberChef es una herramienta web opensource para transformar y analizar datos mediante operaciones que se combinan en una `recipe`. Permite convertir entre texto y hexadecimal, codificar y decodificar Base64, aplicar XOR, calcular hashes y realizar muchas otras tareas.

1. Pegar los primeros 16 caracteres hexadecimales de `memo_a.hex` y aplicar `From Hex`.
2. Añadir `XOR`, con clave en formato `Hex`, usando los primeros 16 caracteres de `memo_b.hex`.
3. Añadir otro `XOR`, en formato `Hex`, con la cabecera `MEMO-01:`, representada como `4d454d4f2d30313a`. Se obtiene `flag{cry`.
4. Probar un espacio adicional por iteración (representado por `20`) a la cabecera hexadecimal y ampliando ambos fragmentos cifrados en dos caracteres hexadecimales. Con 17 espacios aparece la flag. En ese punto se están analizando 25 bytes, equivalentes a 50 caracteres hexadecimales.

[Recipe](https://gchq.github.io/CyberChef/#recipe=From_Hex('Auto')XOR(%7B'option':'Hex','string':'33c8652d69bc297deb6de5a3f7818dec88fffc39e2eaeb6575'%7D,'Standard',false)XOR(%7B'option':'Hex','string':'4d454d4f2d30313a2020202020202020202020202020202020'%7D,'Standard',false)&input=MThlMTQ5MDUzZmVmNmEzZWJiMzlhYWRjYTNkNmMyOTNkY2I2YjE3YzlkYmFhYTIxMjg)

## Conclusiones

Es importante no reutilizar un flujo de clave ya que permite cancelarla mediante XOR. El fragmento conocido de un mensaje puede revelar el fragmento correspondiente del otro.
