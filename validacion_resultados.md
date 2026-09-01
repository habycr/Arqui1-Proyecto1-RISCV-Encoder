# Validación del codificador RV32I

Fecha: 2026-09-01T15:50:30-06:00

Toolchain: `GNU assembler (2.42-1ubuntu1+6) 2.42`
Objdump: `GNU objdump (2.42-1ubuntu1+6) 2.42`

| # | Instrucción | Encoder | Toolchain | Resultado |
|---:|---|---:|---:|:---:|
| 1 | `add x0, x0, x0` | `0x00000033` | `0x00000033` | OK |
| 2 | `add x5, x6, x7` | `0x007302b3` | `0x007302b3` | OK |
| 3 | `add x31, x31, x31` | `0x01ff8fb3` | `0x01ff8fb3` | OK |
| 4 | `sub x0, x0, x0` | `0x40000033` | `0x40000033` | OK |
| 5 | `sub x5, x6, x7` | `0x407302b3` | `0x407302b3` | OK |
| 6 | `sub x31, x31, x31` | `0x41ff8fb3` | `0x41ff8fb3` | OK |
| 7 | `and x0, x0, x0` | `0x00007033` | `0x00007033` | OK |
| 8 | `and x5, x6, x7` | `0x007372b3` | `0x007372b3` | OK |
| 9 | `and x31, x31, x31` | `0x01ffffb3` | `0x01ffffb3` | OK |
| 10 | `or x0, x0, x0` | `0x00006033` | `0x00006033` | OK |
| 11 | `or x5, x6, x7` | `0x007362b3` | `0x007362b3` | OK |
| 12 | `or x31, x31, x31` | `0x01ffefb3` | `0x01ffefb3` | OK |
| 13 | `addi x5, x6, 12` | `0x00c30293` | `0x00c30293` | OK |
| 14 | `addi x10, x1, -12` | `0xff408513` | `0xff408513` | OK |
| 15 | `addi x0, x31, -2048` | `0x800f8013` | `0x800f8013` | OK |
| 16 | `andi x5, x6, 12` | `0x00c37293` | `0x00c37293` | OK |
| 17 | `andi x10, x1, -12` | `0xff40f513` | `0xff40f513` | OK |
| 18 | `andi x31, x0, 2047` | `0x7ff07f93` | `0x7ff07f93` | OK |
| 19 | `lw x5, 8(x6)` | `0x00832283` | `0x00832283` | OK |
| 20 | `lw x10, -12(x1)` | `0xff40a503` | `0xff40a503` | OK |
| 21 | `lw x31, 2047(x0)` | `0x7ff02f83` | `0x7ff02f83` | OK |
| 22 | `lb x5, 8(x6)` | `0x00830283` | `0x00830283` | OK |
| 23 | `lb x10, -12(x1)` | `0xff408503` | `0xff408503` | OK |
| 24 | `lb x0, -2048(x31)` | `0x800f8003` | `0x800f8003` | OK |
| 25 | `sw x5, 8(x6)` | `0x00532423` | `0x00532423` | OK |
| 26 | `sw x10, -12(x1)` | `0xfea0aa23` | `0xfea0aa23` | OK |
| 27 | `sw x31, 2047(x0)` | `0x7ff02fa3` | `0x7ff02fa3` | OK |
| 28 | `sb x5, 8(x6)` | `0x00530423` | `0x00530423` | OK |
| 29 | `sb x10, -12(x1)` | `0xfea08a23` | `0xfea08a23` | OK |
| 30 | `sb x0, -2048(x31)` | `0x800f8023` | `0x800f8023` | OK |
| 31 | `beq x1, x2, 8` | `0x00208463` | `0x00208463` | OK |
| 32 | `beq x5, x6, -4` | `0xfe628ee3` | `0xfe628ee3` | OK |
| 33 | `beq x31, x0, 4094` | `0x7e0f8fe3` | `0x7e0f8fe3` | OK |
| 34 | `bne x1, x2, 8` | `0x00209463` | `0x00209463` | OK |
| 35 | `bne x5, x6, -4` | `0xfe629ee3` | `0xfe629ee3` | OK |
| 36 | `bne x0, x31, -4096` | `0x81f01063` | `0x81f01063` | OK |

Resultado: **36/36 casos correctos**.
