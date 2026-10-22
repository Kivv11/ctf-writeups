# Vovka

[Español](README.md) | [English](README.en.md)

**Challenge 8 · PWN · Difficulty: Hard**

## Description

> Investigate the portal, uncover any hidden secrets, and gain access to the challenge's restricted credentials. Once inside, you will connect to a protected binary service where a second vulnerability awaits.
>
> Can you chain both vulnerabilities and retrieve the flag hidden behind the final layer of access control?

**Access:** [https://challenges.hackrocks.com/vovka](https://challenges.hackrocks.com/vovka)

## Flag

```
b4ck_t0_bl1nd_with_l1bc
```

## Solution

Upon accessing the challenge, a page containing a form that allows users to enter a name and generate a greeting is displayed.

By entering:

```
{{7*7}}
```

The server responds:

```
Hello, 49!
```

This confirms an **SSTI (Server-Side Template Injection)** vulnerability: the server is interpreting the input as a Jinja2 template expression instead of treating it as plain text.

This vulnerability is exploited to inspect the Flask configuration by entering:

```
{{config}}
```

Among the returned values is:

```
SECRET_KEY: 'ctfuser:vv_1ns3cur3!'
```

The key contains the credentials required to log in to the portal.

```
Usuario: ctfuser
Contraseña: vv_1ns3cur3!
```

The login page is accessed at:

[https://challenges.hackrocks.com/vovka/login](https://challenges.hackrocks.com/vovka/login)

Once logged in, the dashboard reveals the credentials for accessing the binary service:

```
HOST: challenges2.hackrocks.com
PORT: 1021
USERNAME: player
PASSWORD: Bl1nd_Fmt_Str1ng_G0!
```

A connection is established using Netcat:

```
nc challenges2.hackrocks.com 1021
```

After entering the credentials, the following appears:

```
username: player
password: Bl1nd_Fmt_Str1ng_G0!

Access granted.

log>
```

The service first requests a log entry (`log>`) and then a comment (`Comments>`).

Format specifiers can be entered at `log>`, such as:

```
AAAA.%p.%p.%p.%p
```

The program returns memory addresses, demonstrating a **Format String** vulnerability.

This vulnerability allows memory information to be leaked, which is necessary to bypass the executable's protections.

In particular, the following were used:

- `%47$p`: retrieves the **Stack Canary**.
- `%49$p`: leaks an address that allows the executable's base address (PIE) to be calculated.
- `%3$p`: retrieves the address of a buffer on the stack.
- `%30$.8s`: allows the contents of `puts@GOT` to be read in order to calculate the libc base address.

The second vulnerability appears at `Comments>`, where a **Buffer Overflow** exists.

It was determined that the canary begins after 328 bytes of input. This makes it possible to construct a payload that overwrites the return address without triggering the canary protection, provided that its original value is preserved.

Using the leaked addresses, a **ROP (Return-Oriented Programming)** chain can be constructed to call `system()` from libc.

The procedure consists of:

1. Leak the canary and PIE base address using the Format String vulnerability.
2. Exploit the Buffer Overflow to return to the login routine and obtain another `log>` input.
3. Leak the address of `puts` from the GOT and calculate the libc base address.
4. Construct a ROP chain that places the command in the argument passed to `system()`.
5. Execute a command to read the file containing the flag.

The offsets used in the exploit were:

| Element        | Offset           |
| -------------- | ---------------- |
| Canary         | 328 bytes        |
| Return address | 344 bytes        |
| Login re-entry | PIE + `0x10e0`   |
| `puts@GOT`     | PIE + `0x4000`   |
| `puts`         | libc + `0x77980` |
| `system`       | libc + `0x4c490` |
| `pop rdi; ret` | libc + `0x277e5` |
| `ret`          | libc + `0x27182` |

To automate the process, the final script [`vovka_termux_tail.py`](./vovka_termux_tail.py), provided by GPT, was used.

**Note:** The offsets correspond to the libc version identified during the challenge.

To execute it:

```
python3 vovka_termux_tail.py
```

### Retrieving the flag

Running the exploit successfully called `system()` and executed commands within the service.

First, command execution was verified:

```
[system, align=True, #1]
b'VOVKA_OK\nAccess denied.\n'

[+] EJECUCION CONFIRMADA.
```

The current directory was then inspected:

```
[CMD] pwd;ls${IFS}-la;ls${IFS}/

[RESPUESTA]
/home/ctf
```

The `flag.txt` file was found in that directory.

Finally:

```
cat${IFS}./flag*;cat${IFS}/flag*
```

`${IFS}` is used instead of spaces because the program's vulnerable input uses `scanf("%s")`, which stops reading when it encounters whitespace characters.

The obtained response was:

```
[RESPUESTA]
b4ck_t0_bl1nd_with_l1bc
cat: '/flag*': No such file or directory
Access denied.
```

The first command successfully read `/home/ctf/flag.txt`, retrieving the challenge flag.

## Conclusion

First, an **SSTI** vulnerability was exploited to retrieve the portal credentials and gain access to the binary service.

Next, a **Format String** vulnerability was used to leak memory addresses and bypass ASLR, PIE, and Stack Canary protections. Finally, a **Buffer Overflow** combined with a ROP chain was used to execute `system()` and read the file containing the flag.

## Glossary of Concepts

### Challenge Context and Web Application

- **SSTI (Server-Side Template Injection):** A vulnerability that occurs when untrusted input is incorporated into template code and evaluated by the server as instructions instead of being handled solely as data. Its effects depend on the template engine and the accessible objects.
- **Template Engine / Jinja2:** A component that combines a template with data to generate output, usually HTML. Jinja2 is a template engine commonly used with Flask.
- **Flask:** A Python web framework. Its configuration object stores application settings, and exposing it may reveal sensitive information.
- **SECRET_KEY:** A Flask secret key used, among other purposes, to sign session data.

### Remote Service and Data Representation

- **Binary:** A program compiled into machine instructions. Its behavior depends on its architecture, libraries, and execution environment.
- **Buffer:** A region of memory used to temporarily store data. Size limits must be respected to prevent overwriting neighboring memory regions.
- **Byte, Hexadecimal, and Pointer:** A byte contains 8 bits; hexadecimal notation represents values in base 16 and commonly uses the `0x` prefix. A pointer is a value representing a memory address.
- **Little-endian:** A storage order in which the least significant byte appears first. This is relevant when interpreting serialized addresses on architectures that use this byte order.
- **Null Byte (`\0`):** A byte with a value of zero that marks the end of a conventional C string.
- **Delimiters and Problematic Characters:** A delimiter separates inputs or fields. Certain bytes may terminate or transform input depending on how the program processes it.
- **`scanf` and `%s`:** In C, this conversion reads a sequence of characters until whitespace is encountered. Without an appropriate maximum width and a sufficiently large buffer, it can cause an out-of-bounds write.
- **`${IFS}`:** Expansion of a shell variable associated with field splitting. Its effect depends on the shell and the expansion context.

### Memory, Execution, and Protections

- **Stack:** A memory region that typically contains data associated with active function calls, such as local variables and return state. A **stack frame** is the portion associated with a particular function call.
- **Return Address:** The memory address where execution should continue after a function call finishes. On x86-64, **RIP** is the register that identifies the instruction being executed.
- **Buffer Overflow:** A read or write operation that exceeds the boundaries of a buffer. An out-of-bounds write can corrupt neighboring data and, under certain conditions, affect execution flow.
- **Format String:** A string that tells a formatting function how to interpret its arguments. A vulnerability occurs when untrusted data is used as the format string.
- **Leak:** The disclosure of internal data, such as memory addresses.
- **Offset and Base Address:** An offset is a displacement relative to a reference point, while the base address is the beginning of a loaded module or memory region. Offsets depend on the exact version of the binary or library.
- **ASLR:** A security mechanism that randomizes the locations of process memory regions to make addresses harder to predict.
- **PIE:** A Position-Independent Executable designed to be loaded at different base addresses and participate in system address randomization.
- **Stack Canary:** A verification value that can be placed on the stack and checked before returning from a function to detect certain types of memory corruption. It does not prevent all buffer overflows.
- **NX / DEP:** A security mechanism that prevents instructions from being executed in memory pages marked as non-executable.
- **ABI and Stack Alignment:** The ABI defines conventions such as argument passing and register preservation. The stack must maintain the required alignment when making function calls.

### Libraries and Code Reuse

- **libc:** The standard C library, which provides common functions used by programs. Its implementation and version affect memory addresses and behavior.
- **Dynamic Linking, GOT, and PLT:** Dynamic linking resolves library references during program loading or execution. The GOT (*Global Offset Table*) contains entries used for dynamic references, while the PLT (*Procedure Linkage Table*) contains code sequences involved in calls to external functions.
- **ROP (Return-Oriented Programming):** A technique that reuses existing code fragments to chain operations together and alter execution flow.
- **Gadget and ROP Chain:** A gadget is a short sequence of instructions that can be reused to perform an operation, frequently ending with a return instruction. A ROP chain combines these sequences with the data they consume.
- **`ret` and `pop`:** Machine instructions. `ret` retrieves the return destination from the stack, while `pop` extracts a value into its destination and updates the stack pointer.
- **`puts` and `system`:** C functions. `puts` prints a string and appends a newline, while `system` requests the execution of a command string through a command interpreter.
