#!/usr/bin/env python3
"""
Esqueleto del Codificador Educativo de Instrucciones RISC-V.
CE4301 Arquitectura de Computadores I — Proyecto Individual — 2026-II

Este esqueleto ya implementa el contrato de línea de comandos y de salida
requerido por la especificación. Usted debe completar las dos funciones
marcadas con TODO; puede modificar el resto del archivo si lo necesita,
siempre que se preserve el contrato de invocación y la línea "HEX: 0x...".

No es obligatorio usar este esqueleto ni Python: puede implementar su
propia herramienta desde cero, en el lenguaje que prefiera, siempre que
respete el mismo contrato (ver especificación, sección "Modo de operación").
"""
import re
import sys

SOPORTADAS = ["add", "sub", "and", "or", "addi", "andi",
              "lw", "lb", "sw", "sb", "beq", "bne"]

# Datos tomados de la tabla "RV32I Base Instruction Set" del manual oficial.
# Las cuatro instrucciones comparten el opcode; funct3 y funct7 son los campos
# que permiten distinguir la operación concreta que debe realizar la ALU.

#Tabla de Instrucciones R según el manual oficial de RISC-V en 32 bits
R_INSTRUCTIONS = {
    "add": {"opcode": 0b0110011, "funct3": 0b000, "funct7": 0b0000000},
    "sub": {"opcode": 0b0110011, "funct3": 0b000, "funct7": 0b0100000},
    "and": {"opcode": 0b0110011, "funct3": 0b111, "funct7": 0b0000000},
    "or":  {"opcode": 0b0110011, "funct3": 0b110, "funct7": 0b0000000},
}

#Tabla de instrucciones aritméticas de formato I según el manual oficial de RISC-V en 32 bits
#Ambas instrucciones comparten el opcode, pero utilizan un funct3 diferente para indicar la operación
I_ARITHMETIC_INSTRUCTIONS = {
    "addi": {"opcode": 0b0010011, "funct3": 0b000},
    "andi": {"opcode": 0b0010011, "funct3": 0b111},
}

#Tabla de instrucciones de carga de formato I según el manual oficial de RISC-V en 32 bits
#lw carga una palabra de 32 bits y lb carga un byte, por eso utilizan un funct3 diferente
I_LOAD_INSTRUCTIONS = {
    "lw": {"opcode": 0b0000011, "funct3": 0b010},
    "lb": {"opcode": 0b0000011, "funct3": 0b000},
}

#Tabla de instrucciones de almacenamiento de formato S según el manual oficial de RISC-V en 32 bits
#sw guarda una palabra de 32 bits y sb guarda únicamente un byte, por eso utilizan un funct3 diferente
S_INSTRUCTIONS = {
    "sw": {"opcode": 0b0100011, "funct3": 0b010},
    "sb": {"opcode": 0b0100011, "funct3": 0b000},
}

#función para separar la instrucción en mnemónico y operandos, además de limpiar espacios innecesarios

#Ejemplo: Entra la instrucción "add x5, x6, x7" y retorna ("add", ["x5", "x6", "x7"])
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

#convierte el nombre de un registro a un número entero
#Ejemplo "x5" a 5
def _parse_register(register: str) -> int:
    if not register.startswith("x") or not register[1:].isdigit(): #verifica que el registro comience con "x" y que el resto sean dígitos
        raise ValueError(f"'{register}' no es un registro válido")

    number = int(register[1:]) #toma el número después de la x y lo convierte a entero
    if not 0 <= number <= 31:
        raise ValueError(
            f"el registro '{register}' está fuera del rango x0-x31"
        )

    return number

#convierte el inmediato escrito en la instrucción a un número entero y verifica que quepa en 12 bits con signo
#Ejemplo: "-12" se convierte a -12 y debe estar dentro del rango de -2048 a 2047
def _parse_immediate(immediate: str) -> int:
    try:
        number = int(immediate, 0) #convierte valores decimales y también permite escribir prefijos como 0x para hexadecimal
    except ValueError:
        raise ValueError(f"'{immediate}' no es un inmediato válido") from None

    if not -2048 <= number <= 2047:
        raise ValueError(
            f"el inmediato '{immediate}' está fuera del rango -2048 a 2047"
        )

    return number

#separa el desplazamiento y el registro base de un operando utilizado para acceder a memoria
#Ejemplo: "8(x6)" retorna el desplazamiento 8 y el número 6 correspondiente al registro x6
def _parse_memory_operand(operand: str) -> tuple[int, int]:
    match = re.fullmatch(r"(.+?)\s*\(\s*(x\d+)\s*\)", operand.strip())
    if not match:
        raise ValueError(
            f"'{operand}' no utiliza la forma desplazamiento(registro)"
        )

    offset = _parse_immediate(match.group(1).strip())
    base_register = _parse_register(match.group(2))

    return offset, base_register

#función que codifica una instrucción de formato R en una palabra de 32 bits, o sea, extrae lo que da la función _parse_register 
# y lo acomoda en la posición correcta según el formato R de RISC-V

def _encode_r(mnemonic: str, operands: list[str]) -> int:
    """Codifica una instrucción de formato R en una palabra de 32 bits."""
    if len(operands) != 3:
        raise ValueError(
            f"{mnemonic} utiliza la forma: {mnemonic} rd, rs1, rs2"
        )

    rd, rs1, rs2 = (_parse_register(register) for register in operands)
    fields = R_INSTRUCTIONS[mnemonic]

    # Cada desplazamiento coloca un campo en su posición definitiva. El OR
    # combina los campos sin alterar los bits que ya fueron acomodados.
    word = (
        (fields["funct7"] << 25)
        | (rs2 << 20)
        | (rs1 << 15)
        | (fields["funct3"] << 12)
        | (rd << 7)
        | fields["opcode"]
    )

    return word #word ya es el entero de 32 bits que representa la instrucción codificada

#función que codifica una instrucción aritmética de formato I en una palabra de 32 bits
#Ejemplo: "addi x5, x6, -12" utiliza x5 como rd, x6 como rs1 y -12 como inmediato
def _encode_i_arithmetic(mnemonic: str, operands: list[str]) -> int:
    if len(operands) != 3:
        raise ValueError(
            f"{mnemonic} utiliza la forma: {mnemonic} rd, rs1, inmediato"
        )

    rd = _parse_register(operands[0])
    rs1 = _parse_register(operands[1])
    immediate = _parse_immediate(operands[2])
    fields = I_ARITHMETIC_INSTRUCTIONS[mnemonic]

    #La máscara conserva únicamente los 12 bits del inmediato. Cuando el valor es negativo,
    #esto produce automáticamente su representación en complemento a dos
    immediate_bits = immediate & 0b111111111111

    #El inmediato ocupa los bits 31-20 y reemplaza los campos funct7 y rs2 que tenía el formato R
    word = (
        (immediate_bits << 20)
        | (rs1 << 15)
        | (fields["funct3"] << 12)
        | (rd << 7)
        | fields["opcode"]
    )

    return word #word es el entero de 32 bits que representa la instrucción de formato I

#función que codifica una carga de formato I utilizando un registro base y un desplazamiento
#Ejemplo: "lw x5, 8(x6)" carga en x5 el dato ubicado en la dirección formada por x6 + 8
def _encode_i_load(mnemonic: str, operands: list[str]) -> int:
    if len(operands) != 2:
        raise ValueError(
            f"{mnemonic} utiliza la forma: {mnemonic} rd, desplazamiento(rs1)"
        )

    rd = _parse_register(operands[0])
    offset, rs1 = _parse_memory_operand(operands[1])
    fields = I_LOAD_INSTRUCTIONS[mnemonic]

    #El desplazamiento también es un inmediato de 12 bits. La máscara permite representar
    #correctamente los desplazamientos negativos mediante complemento a dos
    offset_bits = offset & 0b111111111111

    word = (
        (offset_bits << 20)
        | (rs1 << 15)
        | (fields["funct3"] << 12)
        | (rd << 7)
        | fields["opcode"]
    )

    return word #word representa la instrucción de carga completa como un entero de 32 bits

#función que codifica una instrucción de almacenamiento de formato S
#Ejemplo: "sw x5, 8(x6)" guarda el contenido de x5 en la dirección formada por x6 + 8
def _encode_s(mnemonic: str, operands: list[str]) -> int:
    if len(operands) != 2:
        raise ValueError(
            f"{mnemonic} utiliza la forma: {mnemonic} rs2, desplazamiento(rs1)"
        )

    rs2 = _parse_register(operands[0])
    offset, rs1 = _parse_memory_operand(operands[1])
    fields = S_INSTRUCTIONS[mnemonic]

    #El inmediato de 12 bits se representa en complemento a dos cuando es negativo
    #y después se divide porque el formato S lo coloca en dos zonas diferentes
    immediate_bits = offset & 0b111111111111
    immediate_high = (immediate_bits >> 5) & 0b1111111 #bits imm[11:5]
    immediate_low = immediate_bits & 0b11111 #bits imm[4:0]

    word = (
        (immediate_high << 25)
        | (rs2 << 20)
        | (rs1 << 15)
        | (fields["funct3"] << 12)
        | (immediate_low << 7)
        | fields["opcode"]
    )

    return word #word contiene ambas partes del inmediato en sus posiciones correspondientes


def encode_instruction(instruction: str) -> int:
    """
    Recibe una instrucción como texto, p. ej. "add x5, x6, x7", y debe retornar su codificación de 32 bits como entero (0 <= valor < 2**32).

    Debe soportar únicamente las instrucciones en SOPORTADAS. Los valores
    de opcode/funct3/funct7 de cada una NO se proveen aquí: deben
    investigarse en el manual oficial de la ISA RISC-V (ver referencia en
    la especificación) y documentarse en el README.
    """
    mnemonic, operands = _split_instruction(instruction) #llama la función que separa el mnemónico de los operandos y limpia espacios innecesarios

    if mnemonic in R_INSTRUCTIONS: #aquí es el caso para cuando el mnemónico es de tipo R, entonces llama a la función que codifica la instrucción de formato R
        return _encode_r(mnemonic, operands)

    if mnemonic in I_ARITHMETIC_INSTRUCTIONS: #si el mnemónico es addi o andi, utiliza la codificación del formato I aritmético
        return _encode_i_arithmetic(mnemonic, operands)

    if mnemonic in I_LOAD_INSTRUCTIONS: #si el mnemónico es lw o lb, utiliza el formato I con la sintaxis propia de memoria
        return _encode_i_load(mnemonic, operands)

    if mnemonic in S_INSTRUCTIONS: #si el mnemónico es sw o sb, utiliza la codificación del formato S
        return _encode_s(mnemonic, operands)

    # Los demás formatos se incorporarán por etapas. Mantener este error por
    # ahora evita producir una codificación incorrecta de forma silenciosa.
    raise NotImplementedError(
        f"la codificación de '{mnemonic}' todavía no está implementada"
    )

#recibe la palabra de 32 bits ya construida y vuelve a separar sus campos
def explain_instruction(instruction: str, word: int) -> str:
    """
    Debe retornar un texto (para imprimirse en pantalla) que muestre, de
    forma visual, los 32 bits de 'word' divididos en los campos del
    formato correspondiente (R, I, S o B) — indicando el rango de bits y
    el valor de cada campo — junto con una breve explicación de cada uno.
    El formato visual (colores, tabla, arte ASCII, etc.) queda a su
    criterio, siempre que sea claro.
    """
    mnemonic, _ = _split_instruction(instruction)

    if mnemonic in R_INSTRUCTIONS:
        #Se extraen los campos directamente de la palabra codificada. Las máscaras conservan
        #únicamente la cantidad de bits que pertenece a cada campo del formato R
        funct7 = (word >> 25) & 0b1111111
        rs2 = (word >> 20) & 0b11111
        rs1 = (word >> 15) & 0b11111
        funct3 = (word >> 12) & 0b111
        rd = (word >> 7) & 0b11111
        opcode = word & 0b1111111

        ranges = ["31-25", "24-20", "19-15", "14-12", "11-7", "6-0"]
        names = ["funct7", "rs2", "rs1", "funct3", "rd", "opcode"]
        values = [
            f"{funct7:07b}",
            f"{rs2:05b}",
            f"{rs1:05b}",
            f"{funct3:03b}",
            f"{rd:05b}",
            f"{opcode:07b}",
        ]

        def table_row_r(label: str, cells: list[str]) -> str:
            return f"{label:<7} | " + " | ".join(f"{cell:^8}" for cell in cells)

        table = [
            table_row_r("Bits", ranges),
            table_row_r("Campo", names),
            table_row_r("Valor", values),
        ]
        separator = "-" * len(table[0])

        explanation = [
            f"Instrucción: {instruction.strip()}",
            "Formato: R",
            "",
            table[0],
            separator,
            table[1],
            table[2],
            "",
            f"BIN: {word:032b}",
            "",
            "Explicación de los campos:",
            f"- funct7: completa la selección de la operación ({funct7:07b}).",
            f"- rs2: segundo registro fuente, x{rs2}.",
            f"- rs1: primer registro fuente, x{rs1}.",
            f"- funct3: selección principal de la operación ({funct3:03b}).",
            f"- rd: registro donde se guarda el resultado, x{rd}.",
            f"- opcode: identifica una operación entre registros ({opcode:07b}).",
        ]

        return "\n".join(explanation)

    if mnemonic in I_ARITHMETIC_INSTRUCTIONS or mnemonic in I_LOAD_INSTRUCTIONS:
        #En el formato I los 12 bits superiores contienen el inmediato en vez de funct7 y rs2
        immediate_bits = (word >> 20) & 0b111111111111
        rs1 = (word >> 15) & 0b11111
        funct3 = (word >> 12) & 0b111
        rd = (word >> 7) & 0b11111
        opcode = word & 0b1111111

        #Si el bit más significativo del inmediato es 1, se resta 2^12 para recuperar
        #el valor negativo que fue representado en complemento a dos
        immediate = immediate_bits
        if immediate_bits & 0b100000000000:
            immediate -= 1 << 12

        ranges = ["31-20", "19-15", "14-12", "11-7", "6-0"]
        names = ["imm[11:0]", "rs1", "funct3", "rd", "opcode"]
        values = [
            f"{immediate_bits:012b}",
            f"{rs1:05b}",
            f"{funct3:03b}",
            f"{rd:05b}",
            f"{opcode:07b}",
        ]

        def table_row_i(label: str, cells: list[str]) -> str:
            return f"{label:<7} | " + " | ".join(f"{cell:^12}" for cell in cells)

        table = [
            table_row_i("Bits", ranges),
            table_row_i("Campo", names),
            table_row_i("Valor", values),
        ]
        separator = "-" * len(table[0])

        if mnemonic in I_LOAD_INSTRUCTIONS:
            loaded_data = (
                "una palabra de 32 bits" if mnemonic == "lw"
                else "un byte con extensión de signo"
            )
            field_explanations = [
                f"- imm[11:0]: desplazamiento de 12 bits respecto a rs1 ({immediate}).",
                f"- rs1: registro base utilizado para calcular la dirección, x{rs1}.",
                f"- funct3: indica que {mnemonic} carga {loaded_data} ({funct3:03b}).",
                f"- rd: registro donde se guarda el dato leído, x{rd}.",
                f"- opcode: identifica una carga desde memoria ({opcode:07b}).",
            ]
        else:
            field_explanations = [
                f"- imm[11:0]: valor inmediato de 12 bits ({immediate}).",
                f"- rs1: registro fuente, x{rs1}.",
                f"- funct3: identifica la operación aritmética ({funct3:03b}).",
                f"- rd: registro donde se guarda el resultado, x{rd}.",
                f"- opcode: identifica una operación con inmediato ({opcode:07b}).",
            ]

        explanation = [
            f"Instrucción: {instruction.strip()}",
            "Formato: I",
            "",
            table[0],
            separator,
            table[1],
            table[2],
            "",
            f"BIN: {word:032b}",
            "",
            "Explicación de los campos:",
        ] + field_explanations

        return "\n".join(explanation)

    if mnemonic in S_INSTRUCTIONS:
        #El formato S reparte el inmediato entre los bits 31-25 y 11-7, por eso primero
        #se extraen ambas partes y después se vuelven a unir para mostrar su valor original
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

        ranges = ["31-25", "24-20", "19-15", "14-12", "11-7", "6-0"]
        names = ["imm[11:5]", "rs2", "rs1", "funct3", "imm[4:0]", "opcode"]
        values = [
            f"{immediate_high:07b}",
            f"{rs2:05b}",
            f"{rs1:05b}",
            f"{funct3:03b}",
            f"{immediate_low:05b}",
            f"{opcode:07b}",
        ]

        def table_row_s(label: str, cells: list[str]) -> str:
            return f"{label:<7} | " + " | ".join(f"{cell:^10}" for cell in cells)

        table = [
            table_row_s("Bits", ranges),
            table_row_s("Campo", names),
            table_row_s("Valor", values),
        ]
        separator = "-" * len(table[0])

        stored_data = (
            "una palabra de 32 bits" if mnemonic == "sw"
            else "el byte menos significativo"
        )
        explanation = [
            f"Instrucción: {instruction.strip()}",
            "Formato: S",
            "",
            table[0],
            separator,
            table[1],
            table[2],
            "",
            f"BIN: {word:032b}",
            "",
            "Explicación de los campos:",
            f"- imm[11:5] e imm[4:0]: forman el desplazamiento de 12 bits ({immediate}).",
            f"- rs2: contiene el dato que se guardará, x{rs2}.",
            f"- rs1: registro base utilizado para calcular la dirección, x{rs1}.",
            f"- funct3: indica que {mnemonic} almacena {stored_data} ({funct3:03b}).",
            f"- opcode: identifica un almacenamiento en memoria ({opcode:07b}).",
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
