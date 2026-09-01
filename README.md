# Codificador educativo de instrucciones RISC-V RV32I

**CE4301 Arquitectura de Computadores I, segundo semestre de 2026**

## Descripción

Este proyecto implementa una herramienta de línea de comandos capaz de convertir instrucciones de la ISA base **RV32I** a su representación binaria y hexadecimal de 32 bits.

Además de producir la codificación, el programa muestra los campos que forman la instrucción, el rango de bits que ocupa cada uno y una explicación breve de su propósito. De esta manera, la herramienta no funciona únicamente como codificador, sino también como apoyo para comprender los formatos R, I, S y B de RISC-V.

Por ejemplo, la instrucción:

```text
add x5, x6, x7
```

produce la palabra:

```text
HEX: 0x007302b3
```

## Instrucciones soportadas

El codificador implementa las 12 instrucciones solicitadas para el proyecto:

| Formato | Categoría | Instrucciones | Sintaxis general |
|---|---|---|---|
| R | Operaciones entre registros | `add`, `sub`, `and`, `or` | `instrucción rd, rs1, rs2` |
| I | Operaciones con inmediato | `addi`, `andi` | `instrucción rd, rs1, inmediato` |
| I | Cargas desde memoria | `lw`, `lb` | `instrucción rd, desplazamiento(rs1)` |
| S | Almacenamientos en memoria | `sw`, `sb` | `instrucción rs2, desplazamiento(rs1)` |
| B | Saltos condicionales | `beq`, `bne` | `instrucción rs1, rs2, desplazamiento` |

Los registros deben escribirse entre `x0` y `x31`. Los inmediatos y desplazamientos pueden ser positivos o negativos, siempre que se encuentren dentro del rango permitido por su formato.

## Requisitos

Para ejecutar el codificador se necesita:

- GNU/Linux.
- Python 3.10 o una versión posterior.
- Bash.

Para ejecutar la validación contra el toolchain oficial también se requiere:

- GNU Binutils para RISC-V (`riscv64-unknown-elf-as`, `ld` y `objdump`).

En Ubuntu puede instalarse con:

```bash
sudo apt update
sudo apt install binutils-riscv64-unknown-elf
```

## Uso

Primero debe darse permiso de ejecución al archivo de entrada:

```bash
chmod +x run.sh
```

Luego se pasa la instrucción completa como un único argumento entre comillas:

```bash
./run.sh "add x5, x6, x7"
```

También pueden codificarse instrucciones de los demás formatos:

```bash
./run.sh "addi x10, x1, -12"
./run.sh "lw x5, 8(x6)"
./run.sh "sw x10, -12(x1)"
./run.sh "beq x5, x6, -4"
```

La última línea siempre conserva el siguiente formato, requerido para la validación automática:

```text
HEX: 0xXXXXXXXX
```

## Estructura del proyecto

```text
Arqui1-Proyecto1-RISCV-Encoder/
├── encoder_skeleton.py
├── run.sh
├── README.md
├── vectores_ejemplo.txt
├── tests/
│   └── validate_against_toolchain.py
└── docs/
    └── validation-results.md
```

- `encoder_skeleton.py`: contiene el parser, las tablas de instrucciones, la codificación y la explicación visual.
- `run.sh`: punto de entrada requerido para ejecutar el programa.
- `vectores_ejemplo.txt`: contiene los ejemplos iniciales proporcionados con el kit del proyecto.
- `tests/validate_against_toolchain.py`: compara el encoder con las herramientas oficiales de RISC-V.
- `docs/validation-results.md`: conserva la evidencia generada durante la validación.

## Validación

El codificador fue comparado con GNU `as`, `ld` y `objdump` para RISC-V mediante tres casos distintos por instrucción. Los **36 casos de prueba** coincidieron con el toolchain oficial.

La validación puede repetirse con:

```bash
python3 tests/validate_against_toolchain.py \
  --report docs/validation-results.md
```

El detalle de los resultados se encuentra en [docs/validation-results.md](docs/validation-results.md).

## Fuente de la codificación

Los valores de `opcode`, `funct3`, `funct7` y la distribución de los inmediatos se obtuvieron de la tabla **RV32I Base Instruction Set** del manual oficial de la ISA RISC-V.
