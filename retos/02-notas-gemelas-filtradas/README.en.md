# Leaked Twin Notes

[Español](README.md) | [English](README.en.md)

**Challenge 2 · Cryptography · Difficulty: easy**

## Challenge

> Two ciphertext files have been leaked from a dump of script kiddie tools. Both messages have the same length and were XORed with a reused keystream.
>
> Recover the key inside!

[File](recovered_files_8VKotXN.zip)

The ZIP contains `memo_a.hex`, `memo_b.hex` and `README.txt`. The first two are 64-byte messages represented in hexadecimal. The README states that message A always begins with `MEMO-01:`.

## Flag

```text
flag{crypto_two_time_pad}
```

## Solution

When encrypting two messages with the same keystream `K`:

```text
Cₐ = Mₐ ⊕ K
Cᵦ = Mᵦ ⊕ K
```

Where:

```text
C : ciphertext
M : original message
⊕ : XOR operation
K : reused keystream
```

XOR is associative and commutative. In addition, a value XORed with itself gives zero, and a value XORed with zero remains unchanged. Therefore, combining the ciphertexts cancels out the key:

```text
Cₐ ⊕ Cᵦ = (Mₐ ⊕ K) ⊕ (Mᵦ ⊕ K) = Mₐ ⊕ Mᵦ
( K ⊕ K = 0)
```

Thus, knowing part of A allows the corresponding part of B to be recovered:

```text
Mᵦ = Cₐ ⊕ Cᵦ ⊕ Mₐ
```

## Solution in CyberChef

The theory can be reproduced in [CyberChef](https://gchq.github.io/CyberChef/). CyberChef is an open-source web tool for transforming and analyzing data through operations combined into a `recipe`. It allows conversion between text and hexadecimal, Base64 encoding and decoding, XOR operations, hash calculations and many other tasks.

1. Paste the first 16 hexadecimal characters of `memo_a.hex` and apply `From Hex`.
2. Add `XOR`, with the key in `Hex` format, using the first 16 characters of `memo_b.hex`.
3. Add another `XOR`, in `Hex` format, with the header `MEMO-01:`, represented as `4d454d4f2d30313a`. This produces `flag{cry`.
4. Try adding one more space per iteration (represented by `20`) to the hexadecimal header, extending both ciphertext fragments by two hexadecimal characters. The flag appears with 17 spaces. At that point, 25 bytes are being analyzed, equivalent to 50 hexadecimal characters.

[Recipe](https://gchq.github.io/CyberChef/#recipe=From_Hex('Auto')XOR(%7B'option':'Hex','string':'33c8652d69bc297deb6de5a3f7818dec88fffc39e2eaeb6575'%7D,'Standard',false)XOR(%7B'option':'Hex','string':'4d454d4f2d30313a2020202020202020202020202020202020'%7D,'Standard',false)&input=MThlMTQ5MDUzZmVmNmEzZWJiMzlhYWRjYTNkNmMyOTNkY2I2YjE3YzlkYmFhYTIxMjg)

## Conclusions

It is important not to reuse a keystream, since XOR allows it to be canceled out. A known fragment of one message can reveal the corresponding fragment of the other.
