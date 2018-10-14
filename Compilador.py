import os
import sys
from antlr4 import FileStream
from antlr4 import CommonTokenStream
from antlr4 import ParseTreeWalker
from Grammar.GramaticaLexer import GramaticaLexer
from Grammar.GramaticaParser import GramaticaParser
from Grammar.GramaticaListener import GramaticaListener
from Grammar.Listeners import CustomErrorListener
from Parser import *
from Instrucciones import instrucciones_diccionario
from Registros import registros
from Utils import *
from Export import *


def main(argv, debug, formato_export):
    print("Compilando " + argv + "...")
    path = os.getcwd() + '/Programas/'
    programa = path + argv

    input = FileStream(programa, encoding='utf8')
    lexer = GramaticaLexer(input)
    stream = CommonTokenStream(lexer)
    parser = GramaticaParser(stream)
    tree = parser.gramatica()
    listen = GramaticaListener()
    walker = ParseTreeWalker()
    walker.walk(listen, tree)

    print("Ningun error de sintaxis encontrado")

    instrucciones_indexadas = []

    # Parseo en tuplas y lista de instrucciones
    print("Parseando archivo...")
    with open(programa) as file:
        contador = 0
        for line in file:
            line = line.strip()
            if(line):
                instrucciones_indexadas.append(
                    extraerOperandos(line, contador))
                contador += 1

    # for instruccion in instrucciones_indexadas:
    #     print(instruccion)

    # # Se sustituyen las etiquetas
    print("Sustituyendo etiquetas...")
    posicion = 0
    for instruccion in instrucciones_indexadas:

        # Si la instruccion no es una etiqueta
        if(len(instruccion) > 2):
            nombre_instruccion = instruccion[1].lower()
            valor_instruccion_diccionario = instrucciones_diccionario[nombre_instruccion]

            # Si la instruccion tiene una etiqueta al final
            if(valor_instruccion_diccionario[3] == True):
                etiqueta = instruccion[-1]
                indice = encontrarEtiqueta(
                    instrucciones_indexadas, etiqueta)
                instrucciones_indexadas[posicion][-1] = indice

        posicion += 1

    # Se remueven las etiquetas
    print("Removiendo etiquetas...")
    removerEtiquetas(instrucciones_indexadas)

    # Se crea un nuevo indice para las instrucciones
    print("Indexando instrucciones...")
    instrucciones_indexadas = indexarInstrucciones(instrucciones_indexadas)

    # Se reajusta utilizando el primer indice cada instruccion de salto
    print("Reajustando indices...")
    posicion = 0
    for instruccion in instrucciones_indexadas:
        nombre_instruccion = instruccion[2].lower()
        valor_instruccion_diccionario = instrucciones_diccionario[nombre_instruccion]
        if(valor_instruccion_diccionario[3] == True):
            direccion = instruccion[-1]
            indice = encontrarEtiquetaReIndexada(
                instrucciones_indexadas, direccion)
            instrucciones_indexadas[posicion][-1] = indice - 1
        posicion += 1

    # Se remueven los indices temporales
    print("Removiendo indices temporales...")
    instrucciones_indexadas = removerIndicePreTags(instrucciones_indexadas)

    # for instruccion in instrucciones_indexadas:
    #     print(instruccion)

    # Compilado
    print("Realizando compilacion final...")
    instrucciones_compiladas = []
    for instruccion in instrucciones_indexadas:
        nombre_instruccion = instruccion[1].lower()
        valor_instruccion_diccionario = instrucciones_diccionario[nombre_instruccion]
        tipo_instruccion = valor_instruccion_diccionario[1]

        if(instruccion[0] == 170):
            print(instruccion)

        # Se requiere extraer el func
        if(tipo_instruccion == "R"):

            op_code = valor_instruccion_diccionario[0]
            funct = valor_instruccion_diccionario[2]

            if(valor_instruccion_diccionario[4] == False):
                # Los siguientes valores son binarios
                operando_rd = registros[instruccion[2]]
                operando_rs = registros[instruccion[3]]
                operando_rt = registros[instruccion[4]]
                shamt = "00000"
            else:
                operando_rd = registros[instruccion[2]]
                operando_rt = registros[instruccion[3]]
                shamt = str(binary(int(instruccion[4])))

                if(len(shamt) < 5):
                    shamt = extender5Bits(shamt)

            if(debug):
                instruccion_compilada = op_code + " " + operando_rs + " " + \
                    operando_rt + " " + operando_rd + " " + shamt + " " + funct
            else:
                instruccion_compilada = op_code + operando_rs + \
                    operando_rt + operando_rd + shamt + funct

            instrucciones_compiladas.append(instruccion_compilada)

        elif(tipo_instruccion == "I"):
            if(valor_instruccion_diccionario[5] == False):

                # Los siguientes valores son binarios
                op_code = valor_instruccion_diccionario[0]
                funct = valor_instruccion_diccionario[2]
                operando_rs = registros[instruccion[2]]
                operando_rt = registros[instruccion[3]]
                inmediate = binary(int(instruccion[4]))

                if(len(inmediate) < 16):
                    inmediate = extender16Bits(inmediate)

                if(debug):
                    instruccion_compilada = op_code + " " + operando_rt + " " + \
                        operando_rs + " " + inmediate
                else:
                    instruccion_compilada = op_code + operando_rs + \
                        operando_rt + inmediate

                instrucciones_compiladas.append(instruccion_compilada)
            else:
                # Los siguientes valores son binarios
                op_code = valor_instruccion_diccionario[0]
                funct = valor_instruccion_diccionario[2]
                operando_compuesto = instruccion[3]

                inmediate = operando_compuesto[0:operando_compuesto.find("(")]
                inmediate = binary(int(inmediate))

                operando_rt = operando_compuesto[operando_compuesto.find(
                    "(") + 1:operando_compuesto.find(")")]

                operando_rt = registros[operando_rt]

                if(len(inmediate) < 16):
                    inmediate = extender16Bits(inmediate)

                if(debug):
                    instruccion_compilada = op_code + " " + operando_rs + " " + \
                        operando_rt + " " + inmediate
                else:
                    instruccion_compilada = op_code + operando_rs + \
                        operando_rt + inmediate

                instrucciones_compiladas.append(instruccion_compilada)

        elif(tipo_instruccion == "J"):
            # Los siguientes valores son binarios
            op_code = valor_instruccion_diccionario[0]
            funct = valor_instruccion_diccionario[2]
            address = str(binary(instruccion[2]))

            if(len(address) < 26):
                address = extender26Bits(address)

            if(debug):
                instruccion_compilada = op_code + " " + address
            else:
                instruccion_compilada = op_code + address

            instrucciones_compiladas.append(instruccion_compilada)
        else:
            print("Error encontrando tipo de instruccion")
            sys.exit()

    # for instruccion in instrucciones_compiladas:
    #     print(instruccion)

    print("Exportando archivo... " + formato_export)
    if(formato_export == "MIF"):
        archivo = ExportMIF(instrucciones_compiladas, argv)
    else:
        archivo = ExportMem(instrucciones_compiladas, argv)

    print("Archivo " + formato_export + " " + archivo + " generado!")


if __name__ == "__main__":

    if(len(sys.argv) == 1):
        # NombreArchivo, DebugFlag, "Mem|MIF"
        main("ProgramaCompleto.asm", False, "Mem")
    else:
        main(sys.argv[1], sys.argv[2], sys.argv[3])
