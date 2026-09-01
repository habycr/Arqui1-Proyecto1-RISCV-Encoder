# Codificador educativo de instrucciones RISC-V RV32I

**CE4301 Arquitectura de Computadores I, segundo semestre de 2026**

**Estudiante:** Javier Hernández Castillo  
**Carné:** 2022321746  
**Profesor:** Dr.-Ing. Jeferson González Gómez  
**Institución:** Instituto Tecnológico de Costa Rica

## Descripción

Este proyecto consiste en un codificador de instrucciones de la ISA base **RV32I**. El programa recibe una instrucción escrita en la terminal y la convierte a su representación binaria y hexadecimal de 32 bits.

La idea no es mostrar únicamente el resultado final. También se imprimen los campos que forman la instrucción, los bits que ocupa cada uno y una explicación corta de para qué sirven. Esto permite revisar con más facilidad cómo se construyen los formatos R, I, S y B.

Los campos de codificación se consultaron en el manual oficial de RISC-V [1], mientras que el alcance y los requisitos del programa se tomaron de la especificación del proyecto [2].

Por ejemplo, la instrucción:

```text
add x5, x6, x7
```

produce la palabra:

```text
HEX: 0x007302b3
```

## Instrucciones soportadas

El subconjunto utilizado es exactamente el que se indica en la especificación del proyecto:

![Subconjunto de instrucciones solicitado](docs/img/ss1.png)

*Figura 1. Instrucciones que debe soportar el codificador según la especificación [2].*

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

La especificación también establece este punto de entrada y muestra ejemplos para los distintos formatos:

![Modo de operación indicado en la especificación](docs/img/ss2.png)

*Figura 2. Forma de ejecutar el programa y ejemplos proporcionados en la especificación [2].*

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
    ├── validation-results.md
    └── img/
        ├── ss1.png
        ├── ss2.png
        └── ss3.png
```

- `encoder_skeleton.py`: contiene el parser, las tablas de instrucciones, la codificación y la explicación visual.
- `run.sh`: punto de entrada requerido para ejecutar el programa.
- `vectores_ejemplo.txt`: contiene los ejemplos iniciales proporcionados con el kit del proyecto.
- `tests/validate_against_toolchain.py`: compara el encoder con las herramientas oficiales de RISC-V.
- `docs/validation-results.md`: conserva la evidencia generada durante la validación.
- `docs/img/`: contiene las capturas utilizadas en este documento.

## Arquitectura del programa

Todo el proceso principal está en `encoder_skeleton.py`. Para que el archivo no quedara como una sola función extensa, lo dividí en varias partes pequeñas.

Al inicio se encuentran las tablas de instrucciones. En ellas se guardan los valores fijos de cada mnemónico, como `opcode`, `funct3` y `funct7`. De esta forma no es necesario repetir esos valores dentro de cada función.

Después aparecen las funciones auxiliares que procesan la entrada:

- `_split_instruction()` separa el mnemónico de los operandos.
- `_parse_register()` convierte un registro como `x5` al número `5` y revisa que esté entre `x0` y `x31`.
- `_parse_immediate()` valida los inmediatos de 12 bits.
- `_parse_branch_offset()` valida los desplazamientos de los saltos y comprueba que sean pares.
- `_parse_memory_operand()` separa expresiones como `8(x6)` en desplazamiento y registro base.

La codificación se hace en funciones distintas para R, I, S y B. Decidí separar las instrucciones I aritméticas de las cargas porque, aunque usan el mismo formato de bits, su sintaxis no es igual. Por ejemplo, `addi` recibe tres operandos separados, mientras que `lw` utiliza la forma `desplazamiento(registro)`.

`encode_instruction()` funciona como coordinador: reconoce el mnemónico y envía los operandos al codificador correspondiente. Cada codificador coloca los campos en su posición mediante desplazamientos de bits y luego los une con operaciones OR.

Por último, `explain_instruction()` vuelve a separar la palabra codificada para mostrar sus campos. La función `main()` recibe el argumento enviado desde `run.sh`, controla los posibles errores e imprime la explicación, el binario y la línea `HEX`.

En resumen, el recorrido de una instrucción es:

```text
run.sh -> main() -> encode_instruction() -> codificador del formato
       -> explain_instruction() -> salida BIN y HEX
```

## Formatos de instrucción

Aunque todas las instrucciones terminan representadas por 32 bits, la posición de sus campos cambia según el formato. La distribución utilizada en el programa se tomó de la tabla **RV32I Base Instruction Set** [1].

### Formato R

Se utiliza en `add`, `sub`, `and` y `or`. Estas instrucciones trabajan únicamente con registros, por lo que no necesitan un inmediato. Los campos se acomodan en el siguiente orden: `funct7`, `rs2`, `rs1`, `funct3`, `rd` y `opcode`.

En `_encode_r()` cada valor se desplaza hasta el bit donde comienza su campo. Por ejemplo, `funct7` se mueve 25 posiciones y `rd` se mueve 7. Al final todos los campos se unen con operaciones OR.

### Formato I

Este formato se usa tanto para las operaciones aritméticas `addi` y `andi` como para las cargas `lw` y `lb`. Sus campos son `imm[11:0]`, `rs1`, `funct3`, `rd` y `opcode`.

El inmediato ocupa 12 bits. Antes de colocarlo se aplica la máscara `0xFFF`, lo que también permite conservar la representación en complemento a dos cuando el valor es negativo. Las cargas utilizan la misma distribución de bits, pero sus operandos se escriben como `desplazamiento(registro)`.

### Formato S

`sw` y `sb` utilizan este formato para almacenar datos en memoria. En este caso no existe `rd`, porque la instrucción no guarda un resultado en un registro destino. El dato se toma de `rs2` y la dirección se calcula a partir de `rs1` y el desplazamiento.

El inmediato de 12 bits se divide en dos partes. Los bits `imm[11:5]` se colocan en las posiciones 31 a 25 y `imm[4:0]` en las posiciones 11 a 7. Esta separación se realiza dentro de `_encode_s()`.

### Formato B

El formato B corresponde a `beq` y `bne`. Los registros `rs1` y `rs2` contienen los valores que se comparan y el inmediato indica cuánto debe desplazarse el contador de programa si se cumple la condición.

El desplazamiento debe ser par, ya que su bit menos significativo siempre vale cero y no se almacena. Los demás bits se reparten como `imm[12]`, `imm[10:5]`, `imm[4:1]` e `imm[11]`. Esta distribución es la parte más particular del formato y se construye explícitamente en `_encode_b()`.

## Ejemplos de salida

Los siguientes ejemplos fueron generados con el propio programa. Se incluye uno por cada formato solicitado.

### Ejemplo de formato R

```text
Instrucción: add x5, x6, x7
Formato: R

Bits    |  31-25   |  24-20   |  19-15   |  14-12   |   11-7   |   6-0
-------------------------------------------------------------------------
Campo   |  funct7  |   rs2    |   rs1    |  funct3  |    rd    |  opcode
Valor   | 0000000  |  00111   |  00110   |   000    |  00101   | 0110011

BIN: 00000000011100110000001010110011

Explicación de los campos:
- funct7: completa la selección de la operación (0000000).
- rs2: segundo registro fuente, x7.
- rs1: primer registro fuente, x6.
- funct3: selección principal de la operación (000).
- rd: registro donde se guarda el resultado, x5.
- opcode: identifica una operación entre registros (0110011).
HEX: 0x007302b3
```

### Ejemplo de formato I

```text
Instrucción: addi x10, x1, -12
Formato: I

Bits    |    31-20     |    19-15     |    14-12     |     11-7     |     6-0
----------------------------------------------------------------------------------
Campo   |  imm[11:0]   |     rs1      |    funct3    |      rd      |    opcode
Valor   | 111111110100 |    00001     |     000      |    01010     |   0010011

BIN: 11111111010000001000010100010011

Explicación de los campos:
- imm[11:0]: valor inmediato de 12 bits (-12).
- rs1: registro fuente, x1.
- funct3: identifica la operación aritmética (000).
- rd: registro donde se guarda el resultado, x10.
- opcode: identifica una operación con inmediato (0010011).
HEX: 0xff408513
```

### Ejemplo de formato S

```text
Instrucción: sw x10, -12(x1)
Formato: S

Bits    |   31-25    |   24-20    |   19-15    |   14-12    |    11-7    |    6-0
-------------------------------------------------------------------------------------
Campo   | imm[11:5]  |    rs2     |    rs1     |   funct3   |  imm[4:0]  |   opcode
Valor   |  1111111   |   01010    |   00001    |    010     |   10100    |  0100011

BIN: 11111110101000001010101000100011

Explicación de los campos:
- imm[11:5] e imm[4:0]: forman el desplazamiento de 12 bits (-12).
- rs2: contiene el dato que se guardará, x10.
- rs1: registro base utilizado para calcular la dirección, x1.
- funct3: indica que sw almacena una palabra de 32 bits (010).
- opcode: identifica un almacenamiento en memoria (0100011).
HEX: 0xfea0aa23
```

### Ejemplo de formato B

```text
Instrucción: beq x5, x6, -4
Formato: B

Bits    |     31     |   30-25    |   24-20    |   19-15    |   14-12    |    11-8    |     7      |    6-0
---------------------------------------------------------------------------------------------------------------
Campo   |  imm[12]   | imm[10:5]  |    rs2     |    rs1     |   funct3   |  imm[4:1]  |  imm[11]   |   opcode
Valor   |     1      |   111111   |   00110    |   00101    |    000     |    1110    |     1      |  1100011

BIN: 11111110011000101000111011100011

Explicación de los campos:
- inmediato: sus cuatro partes forman el desplazamiento del salto (-4).
- imm[0]: no se almacena porque siempre vale 0.
- rs1 y rs2: registros que se comparan, x5 y x6.
- funct3: el salto ocurre si los registros son iguales (000).
- opcode: identifica una instrucción de salto condicional (1100011).
HEX: 0xfe628ee3
```

## Validación

La especificación solicita al menos tres casos distintos para cada una de las 12 instrucciones:

![Requisito de validación contra herramientas oficiales](docs/img/ss3.png)

*Figura 3. Cantidad y tipo de pruebas solicitadas para la validación [2].*

Para cumplir este requisito, el codificador fue comparado con GNU `as`, `ld` y `objdump` para RISC-V. Los **36 casos de prueba** coincidieron con el toolchain oficial.

La validación puede repetirse con:

```bash
python3 tests/validate_against_toolchain.py \
  --report docs/validation-results.md
```

El detalle de los resultados se encuentra en [docs/validation-results.md](docs/validation-results.md).

## Fuentes consultadas

Los valores de `opcode`, `funct3`, `funct7` y la distribución de los inmediatos se obtuvieron de la tabla **RV32I Base Instruction Set** [1]. La especificación del proyecto [2] se utilizó para definir las instrucciones soportadas, el modo de ejecución y los casos que debían validarse.

## Referencias

[1] A. Waterman and K. Asanović, Eds., *The RISC-V Instruction Set Manual, Volume I: Unprivileged ISA*, document version 20191213. RISC-V Foundation, 2019, p. 130.

[2] J. González Gómez, “Proyecto Individual: Codificador Educativo de Instrucciones RISC-V,” especificación de proyecto, CE-4301 Arquitectura de Computadores I, Instituto Tecnológico de Costa Rica, 2026.
