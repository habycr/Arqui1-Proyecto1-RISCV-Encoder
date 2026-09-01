#!/usr/bin/env python3
"""Compara el encoder del proyecto con el toolchain oficial de RISC-V."""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path


#Tres casos por cada una de las 12 instrucciones solicitadas en el proyecto
#Se incluyen registros comunes, valores negativos y límites de los inmediatos
TEST_VECTORS = [
    "add x0, x0, x0",
    "add x5, x6, x7",
    "add x31, x31, x31",
    "sub x0, x0, x0",
    "sub x5, x6, x7",
    "sub x31, x31, x31",
    "and x0, x0, x0",
    "and x5, x6, x7",
    "and x31, x31, x31",
    "or x0, x0, x0",
    "or x5, x6, x7",
    "or x31, x31, x31",
    "addi x5, x6, 12",
    "addi x10, x1, -12",
    "addi x0, x31, -2048",
    "andi x5, x6, 12",
    "andi x10, x1, -12",
    "andi x31, x0, 2047",
    "lw x5, 8(x6)",
    "lw x10, -12(x1)",
    "lw x31, 2047(x0)",
    "lb x5, 8(x6)",
    "lb x10, -12(x1)",
    "lb x0, -2048(x31)",
    "sw x5, 8(x6)",
    "sw x10, -12(x1)",
    "sw x31, 2047(x0)",
    "sb x5, 8(x6)",
    "sb x10, -12(x1)",
    "sb x0, -2048(x31)",
    "beq x1, x2, 8",
    "beq x5, x6, -4",
    "beq x31, x0, 4094",
    "bne x1, x2, 8",
    "bne x5, x6, -4",
    "bne x0, x31, -4096",
]

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUN_SCRIPT = PROJECT_ROOT / "run.sh"
TEXT_ADDRESS = 0x1000


class ValidationError(Exception):
    """Indica que no fue posible completar una etapa de la validación."""


#busca automáticamente una instalación común del toolchain cruzado de RISC-V
#También se puede indicar el prefijo manualmente con --prefix o RISCV_PREFIX
def find_toolchain(requested_prefix: str | None) -> dict[str, str]:
    prefixes = []
    if requested_prefix:
        prefixes.append(requested_prefix)

    prefixes.extend([
        "riscv64-unknown-elf-",
        "riscv32-unknown-elf-",
        "riscv64-linux-gnu-",
        "riscv32-linux-gnu-",
    ])

    for prefix in dict.fromkeys(prefixes):
        tools = {
            "as": shutil.which(f"{prefix}as"),
            "ld": shutil.which(f"{prefix}ld"),
            "objdump": shutil.which(f"{prefix}objdump"),
        }
        if all(tools.values()):
            tools["prefix"] = prefix
            return tools

    raise ValidationError(
        "No se encontró el toolchain de RISC-V. En Ubuntu puede instalarse "
        "con: sudo apt install binutils-riscv64-unknown-elf"
    )


#ejecuta un comando y transforma cualquier fallo en un mensaje fácil de interpretar
def run_command(command: list[str], cwd: Path) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        details = completed.stderr.strip() or completed.stdout.strip()
        raise ValidationError(
            f"falló el comando {' '.join(command)}\n{details}"
        )

    return completed.stdout


#ejecuta la entrada oficial del proyecto y extrae la línea obligatoria HEX
#Ejemplo: ./run.sh "add x5, x6, x7" retorna el entero 0x007302b3
def encode_with_project(instruction: str) -> int:
    if not RUN_SCRIPT.is_file():
        raise ValidationError(f"no se encontró {RUN_SCRIPT}")
    if not os.access(RUN_SCRIPT, os.X_OK):
        raise ValidationError(
            "run.sh no tiene permiso de ejecución; use: chmod +x run.sh"
        )

    output = run_command([str(RUN_SCRIPT), instruction], PROJECT_ROOT)
    match = re.search(r"^HEX: 0x([0-9a-fA-F]{8})$", output, re.MULTILINE)
    if not match:
        raise ValidationError(
            f"run.sh no produjo una línea HEX válida para: {instruction}"
        )

    return int(match.group(1), 16)


#crea el código ensamblador que se enviará a la herramienta oficial
#Para los saltos se coloca la etiqueta dentro de .text para evitar que el enlazador genere un salto largo
def build_assembly(instruction: str) -> str:
    mnemonic, operand_text = instruction.split(maxsplit=1)

    if mnemonic not in {"beq", "bne"}:
        return "\n".join([
            ".option norvc",
            ".option norelax",
            ".text",
            ".globl _start",
            "_start:",
            f"    {instruction}",
            "",
        ])

    operands = [operand.strip() for operand in operand_text.split(",")]
    offset = int(operands[2], 0)
    branch = f"    {mnemonic} {operands[0]}, {operands[1]}, branch_target"

    lines = [
        ".option norvc",
        ".option norelax",
        ".text",
    ]

    if offset < 0:
        #La etiqueta se coloca antes del salto y .space determina la distancia negativa
        lines.extend([
            "branch_target:",
            f"    .space {-offset}",
            ".globl _start",
            "_start:",
            branch,
        ])
    elif offset == 0:
        #La etiqueta y la instrucción ocupan la misma dirección
        lines.extend([
            ".globl _start",
            "_start:",
            "branch_target:",
            branch,
        ])
    else:
        if offset < 4:
            raise ValidationError(
                "el validador requiere un salto positivo de al menos 4 bytes"
            )

        #Después de los 4 bytes de la instrucción se completa el resto de la distancia
        lines.extend([
            ".globl _start",
            "_start:",
            branch,
            f"    .space {offset - 4}",
            "branch_target:",
        ])

    lines.append("")
    return "\n".join(lines)


#localiza en la salida de objdump la palabra de 32 bits ubicada bajo la etiqueta _start
def extract_word_from_objdump(output: str) -> int:
    inside_start = False
    for line in output.splitlines():
        if "<_start>:" in line:
            inside_start = True
            continue

        if inside_start:
            match = re.match(
                r"^\s*[0-9a-fA-F]+:\s+([0-9a-fA-F]{8})(?:\s|$)",
                line,
            )
            if match:
                return int(match.group(1), 16)

    raise ValidationError("objdump no mostró la instrucción ubicada en _start")


#ensambla, enlaza y desensambla un caso individual para obtener la referencia oficial
def encode_with_toolchain(
    instruction: str,
    tools: dict[str, str],
    temporary_directory: Path,
    index: int,
) -> int:
    source = temporary_directory / f"case_{index:02}.S"
    object_file = temporary_directory / f"case_{index:02}.o"
    executable = temporary_directory / f"case_{index:02}.elf"

    source.write_text(build_assembly(instruction), encoding="utf-8")

    run_command([
        tools["as"],
        "-march=rv32i",
        "-mabi=ilp32",
        "-o",
        str(object_file),
        str(source),
    ], temporary_directory)

    run_command([
        tools["ld"],
        "-m",
        "elf32lriscv",
        "-Ttext",
        hex(TEXT_ADDRESS),
        "-e",
        "_start",
        "-o",
        str(executable),
        str(object_file),
    ], temporary_directory)

    objdump_output = run_command(
        [tools["objdump"], "-d", str(executable)],
        temporary_directory,
    )
    return extract_word_from_objdump(objdump_output)


def first_version_line(tool: str) -> str:
    """Obtiene la primera línea de versión sin interrumpir la validación."""
    try:
        return run_command([tool, "--version"], PROJECT_ROOT).splitlines()[0]
    except (ValidationError, IndexError):
        return Path(tool).name


#genera una tabla que puede utilizarse como evidencia en la documentación del proyecto
def write_report(
    report_path: Path,
    results: list[tuple[str, int, int, bool]],
    tools: dict[str, str],
) -> None:
    lines = [
        "# Validación del codificador RV32I",
        "",
        f"Fecha: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        "",
        f"Toolchain: `{first_version_line(tools['as'])}`",
        f"Objdump: `{first_version_line(tools['objdump'])}`",
        "",
        "| # | Instrucción | Encoder | Toolchain | Resultado |",
        "|---:|---|---:|---:|:---:|",
    ]

    for index, (instruction, encoder_word, official_word, passed) in enumerate(
        results,
        start=1,
    ):
        status = "OK" if passed else "FALLO"
        lines.append(
            f"| {index} | `{instruction}` | `0x{encoder_word:08x}` | "
            f"`0x{official_word:08x}` | {status} |"
        )

    passed_count = sum(result[3] for result in results)
    lines.extend([
        "",
        f"Resultado: **{passed_count}/{len(results)} casos correctos**.",
        "",
    ])

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compara los 36 casos del encoder con GNU as/ld/objdump para RV32I."
        )
    )
    parser.add_argument(
        "--prefix",
        default=os.environ.get("RISCV_PREFIX"),
        help="prefijo del toolchain, por ejemplo riscv64-unknown-elf-",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="ruta opcional para guardar la tabla Markdown de resultados",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="muestra los 36 vectores sin ejecutar el toolchain",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()

    if args.list:
        for index, instruction in enumerate(TEST_VECTORS, start=1):
            print(f"{index:02}. {instruction}")
        return 0

    try:
        tools = find_toolchain(args.prefix)
        results = []

        print(f"Toolchain detectado: {tools['prefix']}*")
        with tempfile.TemporaryDirectory(prefix="rv32i_validation_") as temp:
            temporary_directory = Path(temp)

            for index, instruction in enumerate(TEST_VECTORS, start=1):
                encoder_word = encode_with_project(instruction)
                official_word = encode_with_toolchain(
                    instruction,
                    tools,
                    temporary_directory,
                    index,
                )
                passed = encoder_word == official_word
                results.append(
                    (instruction, encoder_word, official_word, passed)
                )

                status = "OK" if passed else "FALLO"
                print(
                    f"[{index:02}/36] {status:<5} {instruction:<25} "
                    f"encoder=0x{encoder_word:08x} "
                    f"toolchain=0x{official_word:08x}"
                )

        if args.report:
            report_path = args.report
            if not report_path.is_absolute():
                report_path = PROJECT_ROOT / report_path
            write_report(report_path, results, tools)
            print(f"Reporte guardado en: {report_path}")

        failures = [result for result in results if not result[3]]
        print(f"\nResultado final: {len(results) - len(failures)}/36 correctos")
        return 1 if failures else 0

    except ValidationError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
