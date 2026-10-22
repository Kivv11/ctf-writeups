"""Busca derivaciones del ls_token de Sedice mediante comparaciones locales.
"""

import base64
import hashlib
import hmac
import itertools
import json
from getpass import getpass

SECRET = "s3cr3t_jwt_k3y_ananta_ctf"
SALT = "xG9AmK2$$pL"
SEPARATORS = ("", ":", "|", ".", "-", "_", "/", "::")


def token_parts(token):
    """Extrae los componentes que se combinarán como hipótesis."""
    header, payload, signature = token.split(".")
    padded = payload + "=" * (-len(payload) % 4)
    claims = json.loads(base64.urlsafe_b64decode(padded))
    return {
        "jwt": token,
        "header.payload": header + "." + payload,
        "header": header,
        "payload": payload,
        "signature": signature,
        **{name: str(claims.get(name, ""))
           for name in ("sub", "username", "role", "exp")},
        "salt": SALT,
        "secret": SECRET,
    }


def digest_variants(text):
    raw = text.encode("utf-8")
    yield "MD5", hashlib.md5(raw).hexdigest()
    for name, algorithm in (("SHA-256", hashlib.sha256), ("SHA-1", hashlib.sha1)):
        digest = algorithm(raw).hexdigest()
        yield f"{name}[:32]", digest[:32]
        yield f"{name}[-32:]", digest[-32:]
    for key_name, key in (("salt", SALT), ("secret", SECRET)):
        for name, algorithm in (("MD5", hashlib.md5), ("SHA-256", hashlib.sha256)):
            digest = hmac.new(key.encode("utf-8"), raw, algorithm).hexdigest()
            yield f"HMAC-{name}(clave={key_name})[:32]", digest[:32]
            yield f"HMAC-{name}(clave={key_name})[-32:]", digest[-32:]


def find_match(parts, original):
    """Prueba secuencias de uno a tres componentes, con repetición."""
    count = 0
    for size in (1, 2, 3):
        for separator in SEPARATORS:
            for names in itertools.product(parts, repeat=size):
                text = separator.join(parts[name] for name in names)
                for method, digest in digest_variants(text):
                    count += 1
                    if hmac.compare_digest(digest, original):
                        return (method, names, separator), count
    return None, count


def main():
    jwt = getpass("JWT original: ").strip()
    original = getpass("ls_token de la misma sesión: ").strip().lower()
    if len(original) != 32 or any(c not in "0123456789abcdef" for c in original):
        raise SystemExit("El ls_token debe contener 32 caracteres hexadecimales.")
    try:
        parts = token_parts(jwt)
    except (ValueError, TypeError, AttributeError, UnicodeError):
        raise SystemExit("JWT inválido: se requieren tres segmentos y un payload JSON.") from None

    match, count = find_match(parts, original)
    print(f"Comparadas {count} derivaciones locales.")
    if match is None:
        print("Sin coincidencias entre las hipótesis probadas.")
        return
    method, names, separator = match
    expression = (" + " if separator == "" else f" + {separator!r} + ").join(names)
    print(f"Coincidencia: {method}({expression})")
    print(f"Separador: {separator!r}")
    print("La coincidencia corresponde al par de tokens proporcionado.")


if __name__ == "__main__":
    main()
