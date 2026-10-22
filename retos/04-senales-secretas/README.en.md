# Secret Signals

[Español](README.md) | [English](README.en.md)

**Challenge 4 · Reversing · Difficulty:**

## Challenge

> Your team intercepted a compromised ESP32 device during a network security sweep. The device was emitting intermittent signals that did not match any known protocol. Initial analysis showed that it was running custom firmware, but the source code was nowhere to be found.
>
> You managed to extract the compiled binary from the device's flash memory. It is a standard ELF file, but something about it seems strange. The binary is larger than it should be, and static analysis reveals thousands of symbols scattered throughout its structure. Most belong to the ESP32 framework, but something completely different is hidden among them.
>
> Something suggests that the device was part of a communication network that used encoding. You are certain that the secret message is embedded somewhere in this binary, waiting to be discovered.

[File](challenge.elf)

## Flag

```text
YOUREVERSEDMYFIRMWARE
```

## Solution

Open `challenge.elf` in Ghidra to study the binary without executing it. **Ghidra** is a reverse engineering tool that allows instructions, data and symbols to be examined without access to the source code.

### Identify the file

The header corresponds to a **32-bit, little-endian ELF for Xtensa**, consistent with the ESP32. ELF is an executable file format; little-endian means that the least significant bytes are stored first. The file retains symbols and debugging information, which are useful for recognizing functions and data.

### Search for references to the signals

The clue in the challenge statement about intermittent signals guided the search toward names such as `morse`, `blink` and `transmit`. The relevant symbols found were:

```text
morse
blinkSymbol(char)
transmitLetter(char const*)
loop()
```

### Follow the Morse table

`morse` is a table located at `0x3ffbdb60` that occupies 84 bytes. It contains **21 pointers of 4 bytes each**. A pointer stores the address of another piece of data; here, each entry points to a string of dots and dashes in `.flash.rodata`.

The `loop()` function iterates over the 21 entries and calls `transmitLetter`, which reads each string up to byte `00`. This establishes the order and number of letters.

### Read the strings

Follow the first entry to `0x3f400120`. Read the bytes up to the `00` terminator:

```text
Bytes:  2d 2e 2d 2d 00
Morse:  -.--
Letter: Y
```

In ASCII, `2e` represents a dot and `2d` a dash. The following table illustrates the beginning of the result obtained by reading the subsequent entries:

| Entry | Address | Morse | Letter |
| ---: | --- | --- | :---: |
| 0 | `0x3f400120` | `-.--` | Y |
| 1 | `0x3f400125` | `---` | O |
| 2 | `0x3f40012a` | `..-` | U |
| 3 | `0x3f400137` | `.-.` | R |
| 4 | `0x3f400139` | `.` | E |

The result begins with `YOURE`. Continue with the remaining entries, following the pointers in order.

The 21 entries produce:

```text
-.-- --- ..- .-. . ...- . .-. ... . -.. -- -.-- ..-. .. .-. -- .-- .- .-. .
```

Translating each sequence using a Morse code table gives:

```text
YOUREVERSEDMYFIRMWARE
```
