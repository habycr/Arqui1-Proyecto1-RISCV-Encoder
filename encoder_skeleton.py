#!/usr/bin/env python3
"""Codificador de las instrucciones RV32I solicitadas en el proyecto."""
import re
import sys

SOPORTADAS = ["add", "sub", "and", "or", "addi", "andi",
              "lw", "lb", "sw", "sb", "beq", "bne"]

# Valores de cada instrucción según la tabla RV32I Base Instruction Set.
R_INSTRUCTIONS = {
    "add": {"opcode": 0b0110011, "funct3": 0b000, "funct7": 0b0000000},
    "sub": {"opcode": 0b0110011, "funct3": 0b000, "funct7": 0b0100000},
    "and": {"opcode": 0b0110011, "funct3": 0b111, "funct7": 0b0000000},
    "or":  {"opcode": 0b0110011, "funct3": 0b110, "funct7": 0b0000000},
}

I_ARITHMETIC_INSTRUCTIONS = {
    "addi": {"opcode": 0b0010011, "funct3": 0b000},
    "andi": {"opcode": 0b0010011, "funct3": 0b111},
}

I_LOAD_INSTRUCTIONS = {
    "lw": {"opcode": 0b0000011, "funct3": 0b010},
    "lb": {"opcode": 0b0000011, "funct3": 0b000},
}

S_INSTRUCTIONS = {
    "sw": {"opcode": 0b0100011, "funct3": 0b010},
    "sb": {"opcode": 0b0100011, "funct3": 0b000},
}

B_INSTRUCTIONS = {
    "beq": {"opcode": 0b1100011, "funct3": 0b000},
    "bne": {"opcode": 0b1100011, "funct3": 0b001},
}

def _split_instruction(instruction: str) -> tuple[str, list[str]]:
    """Separa el mnemónico de sus operandos y limpia espacios innecesarios."""
    text = instruction.strip().lower()
    if not text:
        raise ValueError("la instrucción está vacía")

    parts = text.split(maxsplit=1)
    mnemonic = parts[0]

    if mnemonic not in SOPORTADAS:
        raise ValueError(f"la instrucción '{mnemonic}' no está soportada")

    operands = []
    if len(parts) == 2:
        operands = [operand.strip() for operand in parts[1].split(",")]

    if not operands or any(not operand for operand in operands):
        raise ValueError(f"faltan operandos en '{instruction}'")

    return mnemonic, operands

def _parse_register(register: str) -> int:
    """Convierte un registro como x5 al número 5 y valida su rango."""
    if not register.startswith("x") or not register[1:].isdigit():
        raise ValueError(f"'{register}' no es un registro válido")

    number = int(register[1:])
    if not 0 <= number <= 31:
        raise ValueError(
            f"el registro '{register}' está fuera del rango x0-x31"
        )

    return number

def _parse_immediate(immediate: str) -> int:
    """Lee y valida un inmediato de 12 bits con signo."""
    try:
        number = int(immediate, 0)
    except ValueError:
        raise ValueError(f"'{immediate}' no es un inmediato válido") from None

    if not -2048 <= number <= 2047:
        raise ValueError(
            f"el inmediato '{immediate}' está fuera del rango -2048 a 2047"
        )

    return number

def _parse_branch_offset(offset: str) -> int:
    """Lee el desplazamiento de un salto y comprueba su alineación."""
    try:
        number = int(offset, 0)
    except ValueError:
        raise ValueError(f"'{offset}' no es un desplazamiento válido") from None

    if not -4096 <= number <= 4094:
        raise ValueError(
            f"el desplazamiento '{offset}' está fuera del rango -4096 a 4094"
        )

    if number % 2 != 0:
        raise ValueError(
            f"el desplazamiento '{offset}' debe ser un número par"
        )

    return number

def _parse_memory_operand(operand: str) -> tuple[int, int]:
    """Separa un operando como 8(x6) en desplazamiento y registro base."""
    match = re.fullmatch(r"(.+?)\s*\(\s*(x\d+)\s*\)", operand.strip())
    if not match:
        raise ValueError(
            f"'{operand}' no utiliza la forma desplazamiento(registro)"
        )

    offset = _parse_immediate(match.group(1).strip())
    base_register = _parse_register(match.group(2))

    return offset, base_register


def _parse_instruction(instruction: str) -> tuple[str, dict[str, int]]:
    """Reconoce la sintaxis y devuelve los operandos ya validados."""
    mnemonic, operands = _split_instruction(instruction)

    if mnemonic in R_INSTRUCTIONS:
        if len(operands) != 3:
            raise ValueError(
                f"{mnemonic} utiliza la forma: {mnemonic} rd, rs1, rs2"
            )

        return mnemonic, {
            "rd": _parse_register(operands[0]),
            "rs1": _parse_register(operands[1]),
            "rs2": _parse_register(operands[2]),
        }

    if mnemonic in I_ARITHMETIC_INSTRUCTIONS:
        if len(operands) != 3:
            raise ValueError(
                f"{mnemonic} utiliza la forma: {mnemonic} rd, rs1, inmediato"
            )

        return mnemonic, {
            "rd": _parse_register(operands[0]),
            "rs1": _parse_register(operands[1]),
            "immediate": _parse_immediate(operands[2]),
        }

    if mnemonic in I_LOAD_INSTRUCTIONS:
        if len(operands) != 2:
            raise ValueError(
                f"{mnemonic} utiliza la forma: "
                f"{mnemonic} rd, desplazamiento(rs1)"
            )

        offset, rs1 = _parse_memory_operand(operands[1])
        return mnemonic, {
            "rd": _parse_register(operands[0]),
            "rs1": rs1,
            "immediate": offset,
        }

    if mnemonic in S_INSTRUCTIONS:
        if len(operands) != 2:
            raise ValueError(
                f"{mnemonic} utiliza la forma: "
                f"{mnemonic} rs2, desplazamiento(rs1)"
            )

        offset, rs1 = _parse_memory_operand(operands[1])
        return mnemonic, {
            "rs2": _parse_register(operands[0]),
            "rs1": rs1,
            "immediate": offset,
        }

    if mnemonic in B_INSTRUCTIONS:
        if len(operands) != 3:
            raise ValueError(
                f"{mnemonic} utiliza la forma: "
                f"{mnemonic} rs1, rs2, desplazamiento"
            )

        return mnemonic, {
            "rs1": _parse_register(operands[0]),
            "rs2": _parse_register(operands[1]),
            "immediate": _parse_branch_offset(operands[2]),
        }

    raise NotImplementedError(
        f"la codificación de '{mnemonic}' todavía no está implementada"
    )


def _to_binary(value: int, width: int) -> str:
    """Convierte un valor a binario y lo completa al ancho indicado."""
    # Sumar 2^width produce el complemento a dos de un valor negativo.
    if value < 0:
        value += 2 ** width

    # En cada división, el residuo corresponde al siguiente bit.
    binary = ""
    for _ in range(width):
        binary = str(value % 2) + binary
        value //= 2

    return binary


def _encode_r(mnemonic: str, values: dict[str, int]) -> int:
    """Codifica los campos de una instrucción de formato R."""
    fields = R_INSTRUCTIONS[mnemonic]

    binary_fields = [
        _to_binary(fields["funct7"], 7),
        _to_binary(values["rs2"], 5),
        _to_binary(values["rs1"], 5),
        _to_binary(fields["funct3"], 3),
        _to_binary(values["rd"], 5),
        _to_binary(fields["opcode"], 7),
    ]

    return int("".join(binary_fields), 2)


def _encode_i(mnemonic: str, values: dict[str, int]) -> int:
    """Codifica instrucciones aritméticas y cargas de formato I."""
    if mnemonic in I_ARITHMETIC_INSTRUCTIONS:
        fields = I_ARITHMETIC_INSTRUCTIONS[mnemonic]
    else:
        fields = I_LOAD_INSTRUCTIONS[mnemonic]

    binary_fields = [
        _to_binary(values["immediate"], 12),
        _to_binary(values["rs1"], 5),
        _to_binary(fields["funct3"], 3),
        _to_binary(values["rd"], 5),
        _to_binary(fields["opcode"], 7),
    ]

    return int("".join(binary_fields), 2)


def _encode_s(mnemonic: str, values: dict[str, int]) -> int:
    """Codifica los campos de una instrucción de formato S."""
    fields = S_INSTRUCTIONS[mnemonic]

    immediate_bits = _to_binary(values["immediate"], 12)
    binary_fields = [
        immediate_bits[:7],
        _to_binary(values["rs2"], 5),
        _to_binary(values["rs1"], 5),
        _to_binary(fields["funct3"], 3),
        immediate_bits[7:],
        _to_binary(fields["opcode"], 7),
    ]

    return int("".join(binary_fields), 2)


def _encode_b(mnemonic: str, values: dict[str, int]) -> int:
    """Codifica los campos de una instrucción de formato B."""
    fields = B_INSTRUCTIONS[mnemonic]

    # El inmediato tiene 13 bits; el bit 0 no se guarda porque siempre es cero.
    immediate_bits = _to_binary(values["immediate"], 13)
    binary_fields = [
        immediate_bits[0],
        immediate_bits[2:8],
        _to_binary(values["rs2"], 5),
        _to_binary(values["rs1"], 5),
        _to_binary(fields["funct3"], 3),
        immediate_bits[8:12],
        immediate_bits[1],
        _to_binary(fields["opcode"], 7),
    ]

    return int("".join(binary_fields), 2)


def encode_instruction(instruction: str) -> int:
    """Codifica una instrucción soportada y devuelve su palabra de 32 bits."""
    mnemonic, values = _parse_instruction(instruction)

    if mnemonic in R_INSTRUCTIONS:
        return _encode_r(mnemonic, values)

    if mnemonic in I_ARITHMETIC_INSTRUCTIONS or mnemonic in I_LOAD_INSTRUCTIONS:
        return _encode_i(mnemonic, values)

    if mnemonic in S_INSTRUCTIONS:
        return _encode_s(mnemonic, values)

    if mnemonic in B_INSTRUCTIONS:
        return _encode_b(mnemonic, values)

    raise NotImplementedError(
        f"la codificación de '{mnemonic}' todavía no está implementada"
    )


def _group_in_fours(binary_word: str) -> str:
    """Agrupa una palabra binaria para facilitar su conversión a hexadecimal."""
    return " ".join(
        binary_word[index:index + 4]
        for index in range(0, len(binary_word), 4)
    )


def explain_instruction(instruction: str, word: int) -> str:
    """Genera el desglose visual y la explicación de la instrucción."""
    mnemonic, _ = _split_instruction(instruction)

    if mnemonic in R_INSTRUCTIONS:
        # Se extraen los campos de la misma palabra que se mostrará al usuario.
        funct7 = (word >> 25) & 0b1111111
        rs2 = (word >> 20) & 0b11111
        rs1 = (word >> 15) & 0b11111
        funct3 = (word >> 12) & 0b111
        rd = (word >> 7) & 0b11111
        opcode = word & 0b1111111

        field_values = [
            _to_binary(funct7, 7),
            _to_binary(rs2, 5),
            _to_binary(rs1, 5),
            _to_binary(funct3, 3),
            _to_binary(rd, 5),
            _to_binary(opcode, 7),
        ]
        field_lines = [
            f"- [31-25] funct7 = {field_values[0]}",
            f"- [24-20] rs2 = {field_values[1]}",
            f"- [19-15] rs1 = {field_values[2]}",
            f"- [14-12] funct3 = {field_values[3]}",
            f"- [11-7] rd = {field_values[4]}",
            f"- [6-0] opcode = {field_values[5]}",
        ]
        binary_word = _to_binary(word, 32)

        explanation = [
            f"Instrucción: {instruction.strip()}",
            "Formato: R",
            "",
            "Distribución de los 32 bits:",
            *field_lines,
            "",
            "Campos unidos:",
            " | ".join(field_values),
            "",
            f"BIN: {binary_word}",
            f"Grupos de 4 bits: {_group_in_fours(binary_word)}",
            "",
            "Explicación de los campos:",
            f"- funct7: completa la selección de la operación ({_to_binary(funct7, 7)}).",
            f"- rs2: segundo registro fuente, x{rs2}.",
            f"- rs1: primer registro fuente, x{rs1}.",
            f"- funct3: selección principal de la operación ({_to_binary(funct3, 3)}).",
            f"- rd: registro donde se guarda el resultado, x{rd}.",
            f"- opcode: identifica una operación entre registros ({_to_binary(opcode, 7)}).",
        ]

        return "\n".join(explanation)

    if mnemonic in I_ARITHMETIC_INSTRUCTIONS or mnemonic in I_LOAD_INSTRUCTIONS:
        # En el formato I los 12 bits superiores contienen el inmediato.
        immediate_bits = (word >> 20) & 0b111111111111
        rs1 = (word >> 15) & 0b11111
        funct3 = (word >> 12) & 0b111
        rd = (word >> 7) & 0b11111
        opcode = word & 0b1111111

        # Se resta 2^12 para recuperar un inmediato negativo.
        immediate = immediate_bits
        if immediate_bits & 0b100000000000:
            immediate -= 1 << 12

        field_values = [
            _to_binary(immediate_bits, 12),
            _to_binary(rs1, 5),
            _to_binary(funct3, 3),
            _to_binary(rd, 5),
            _to_binary(opcode, 7),
        ]
        field_lines = [
            f"- [31-20] imm[11:0] = {field_values[0]}",
            f"- [19-15] rs1 = {field_values[1]}",
            f"- [14-12] funct3 = {field_values[2]}",
            f"- [11-7] rd = {field_values[3]}",
            f"- [6-0] opcode = {field_values[4]}",
        ]
        binary_word = _to_binary(word, 32)

        if mnemonic in I_LOAD_INSTRUCTIONS:
            loaded_data = (
                "una palabra de 32 bits" if mnemonic == "lw"
                else "un byte con extensión de signo"
            )
            field_explanations = [
                f"- imm[11:0]: desplazamiento de 12 bits respecto a rs1 ({immediate}).",
                f"- rs1: registro base utilizado para calcular la dirección, x{rs1}.",
                f"- funct3: indica que {mnemonic} carga {loaded_data} "
                f"({_to_binary(funct3, 3)}).",
                f"- rd: registro donde se guarda el dato leído, x{rd}.",
                f"- opcode: identifica una carga desde memoria "
                f"({_to_binary(opcode, 7)}).",
            ]
        else:
            field_explanations = [
                f"- imm[11:0]: valor inmediato de 12 bits ({immediate}).",
                f"- rs1: registro fuente, x{rs1}.",
                f"- funct3: identifica la operación aritmética "
                f"({_to_binary(funct3, 3)}).",
                f"- rd: registro donde se guarda el resultado, x{rd}.",
                f"- opcode: identifica una operación con inmediato "
                f"({_to_binary(opcode, 7)}).",
            ]

        explanation = [
            f"Instrucción: {instruction.strip()}",
            "Formato: I",
            "",
            "Distribución de los 32 bits:",
            *field_lines,
            "",
            "Campos unidos:",
            " | ".join(field_values),
            "",
            f"BIN: {binary_word}",
            f"Grupos de 4 bits: {_group_in_fours(binary_word)}",
            "",
            "Explicación de los campos:",
        ] + field_explanations

        return "\n".join(explanation)

    if mnemonic in S_INSTRUCTIONS:
        # Las dos partes del inmediato se vuelven a unir para recuperar su valor.
        immediate_high = (word >> 25) & 0b1111111
        rs2 = (word >> 20) & 0b11111
        rs1 = (word >> 15) & 0b11111
        funct3 = (word >> 12) & 0b111
        immediate_low = (word >> 7) & 0b11111
        opcode = word & 0b1111111

        immediate_bits = (immediate_high << 5) | immediate_low
        immediate = immediate_bits
        if immediate_bits & 0b100000000000:
            immediate -= 1 << 12

        field_values = [
            _to_binary(immediate_high, 7),
            _to_binary(rs2, 5),
            _to_binary(rs1, 5),
            _to_binary(funct3, 3),
            _to_binary(immediate_low, 5),
            _to_binary(opcode, 7),
        ]
        field_lines = [
            f"- [31-25] imm[11:5] = {field_values[0]}",
            f"- [24-20] rs2 = {field_values[1]}",
            f"- [19-15] rs1 = {field_values[2]}",
            f"- [14-12] funct3 = {field_values[3]}",
            f"- [11-7] imm[4:0] = {field_values[4]}",
            f"- [6-0] opcode = {field_values[5]}",
        ]
        binary_word = _to_binary(word, 32)

        stored_data = (
            "una palabra de 32 bits" if mnemonic == "sw"
            else "el byte menos significativo"
        )
        explanation = [
            f"Instrucción: {instruction.strip()}",
            "Formato: S",
            "",
            "Distribución de los 32 bits:",
            *field_lines,
            "",
            "Campos unidos:",
            " | ".join(field_values),
            "",
            f"BIN: {binary_word}",
            f"Grupos de 4 bits: {_group_in_fours(binary_word)}",
            "",
            "Explicación de los campos:",
            f"- imm[11:5] e imm[4:0]: forman el desplazamiento de 12 bits ({immediate}).",
            f"- rs2: contiene el dato que se guardará, x{rs2}.",
            f"- rs1: registro base utilizado para calcular la dirección, x{rs1}.",
            f"- funct3: indica que {mnemonic} almacena {stored_data} "
            f"({_to_binary(funct3, 3)}).",
            f"- opcode: identifica un almacenamiento en memoria "
            f"({_to_binary(opcode, 7)}).",
        ]

        return "\n".join(explanation)

    if mnemonic in B_INSTRUCTIONS:
        # Las cuatro partes se acomodan nuevamente para recuperar el desplazamiento.
        immediate_12 = (word >> 31) & 0b1
        immediate_10_5 = (word >> 25) & 0b111111
        rs2 = (word >> 20) & 0b11111
        rs1 = (word >> 15) & 0b11111
        funct3 = (word >> 12) & 0b111
        immediate_4_1 = (word >> 8) & 0b1111
        immediate_11 = (word >> 7) & 0b1
        opcode = word & 0b1111111

        immediate_bits = (
            (immediate_12 << 12)
            | (immediate_11 << 11)
            | (immediate_10_5 << 5)
            | (immediate_4_1 << 1)
        )
        immediate = immediate_bits
        if immediate_bits & 0b1000000000000:
            immediate -= 1 << 13

        field_values = [
            _to_binary(immediate_12, 1),
            _to_binary(immediate_10_5, 6),
            _to_binary(rs2, 5),
            _to_binary(rs1, 5),
            _to_binary(funct3, 3),
            _to_binary(immediate_4_1, 4),
            _to_binary(immediate_11, 1),
            _to_binary(opcode, 7),
        ]
        field_lines = [
            f"- [31] imm[12] = {field_values[0]}",
            f"- [30-25] imm[10:5] = {field_values[1]}",
            f"- [24-20] rs2 = {field_values[2]}",
            f"- [19-15] rs1 = {field_values[3]}",
            f"- [14-12] funct3 = {field_values[4]}",
            f"- [11-8] imm[4:1] = {field_values[5]}",
            f"- [7] imm[11] = {field_values[6]}",
            f"- [6-0] opcode = {field_values[7]}",
        ]
        binary_word = _to_binary(word, 32)

        condition = (
            "son iguales" if mnemonic == "beq"
            else "son diferentes"
        )
        explanation = [
            f"Instrucción: {instruction.strip()}",
            "Formato: B",
            "",
            "Distribución de los 32 bits:",
            *field_lines,
            "",
            "Campos unidos:",
            " | ".join(field_values),
            "",
            f"BIN: {binary_word}",
            f"Grupos de 4 bits: {_group_in_fours(binary_word)}",
            "",
            "Explicación de los campos:",
            f"- inmediato: sus cuatro partes forman el desplazamiento del salto ({immediate}).",
            "- imm[0]: no se almacena porque siempre vale 0.",
            f"- rs1 y rs2: registros que se comparan, x{rs1} y x{rs2}.",
            f"- funct3: el salto ocurre si los registros {condition} "
            f"({_to_binary(funct3, 3)}).",
            f"- opcode: identifica una instrucción de salto condicional "
            f"({_to_binary(opcode, 7)}).",
        ]

        return "\n".join(explanation)

    raise NotImplementedError(
        f"la explicación de '{mnemonic}' todavía no está implementada"
    )


def main():
    if len(sys.argv) != 2:
        print(f'Uso: {sys.argv[0]} "<instruccion>"', file=sys.stderr)
        print(f'Ejemplo: {sys.argv[0]} "add x5, x6, x7"', file=sys.stderr)
        sys.exit(2)

    instruction = sys.argv[1]

    try:
        word = encode_instruction(instruction) & 0xFFFFFFFF
        explanation = explain_instruction(instruction, word)
    except (ValueError, NotImplementedError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)

    print(explanation)

    # No modificar el formato de la siguiente línea: la especificación la
    # requiere, literal, para permitir la validación automática.
    print(f"HEX: 0x{word:08x}")


if __name__ == "__main__":
    main()
