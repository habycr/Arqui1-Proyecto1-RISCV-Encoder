# Codificador de instrucciones RISC-V RV32I

Este proyecto recibe una instrucción del subconjunto RV32I solicitado y muestra su codificación binaria y hexadecimal de 32 bits, junto con el desglose de sus campos.

## Requisitos

Para ejecutar el codificador se necesita:

- GNU/Linux.
- Python 3.10 o una versión posterior.
- Bash.

## Descarga

Clona el repositorio y entra en la carpeta del proyecto:

```bash
git clone https://github.com/habycr/Arqui1-Proyecto1-RISCV-Encoder.git
cd Arqui1-Proyecto1-RISCV-Encoder
```

## Ejecución

La primera vez, se concede permiso de ejecución al archivo `run.sh`:

```bash
chmod +x run.sh
```

Luego se puede pasar una instrucción completa como un único argumento entre comillas, según el formato indicado:

```bash
./run.sh "add x5, x6, x7"
```

También se puede probar instrucciones de los otros formatos soportados:

```bash
./run.sh "addi x10, x1, -12"
./run.sh "sw x10, -12(x1)"
./run.sh "beq x5, x6, -4"
```

La última línea de una ejecución correcta tiene este formato:

```text
HEX: 0xXXXXXXXX
```


## Documentación

La explicación de la arquitectura del programa, los formatos de instrucción, la validación contra el toolchain oficial, las capturas de ejecución y las fuentes consultadas se encuentra en [documentacion.md](documentacion.md).

## Licencia

Este proyecto utiliza la licencia MIT.
