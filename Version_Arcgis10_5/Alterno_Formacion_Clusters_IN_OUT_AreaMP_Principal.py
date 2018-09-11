# -*- coding: utf-8 -*-
"""
Script Name:  Alterno_Formacion_Clusters_IN_OUT_AreaMP_Principal
Source Name: Alterno_Formacion_Clusters_IN_OUT_AreaMP_Principal.py
Version: ArcGIS 10.3 or Superior
Author: Carlos Javier Delgado - Carlos Mario Cano UPRA - Grupo TIC - Analisis de Informacion
"""

import arcpy
import time
import random
import os
import inspect
import string
import subprocess
import shutil
comandos=[] # arreglo que almacena los comandos a ejecutar por el script auxiliar
dic_acentos={" ":"---","\xc3\xa1":"***a***","\xc3\xa9":"***e***", "\xc3\xad":"***i***",
"\xc3\xb3": "***o***","\xc3\xba": "***u***","\xc3\xb1": "***n***","\xc3\x81":"***A***","\xc3\x89":"***E***",
"\xc3\x8d":"***I***", "\xc3\x93": "***O***","***\xc3\x9a***":"Ú","\xc3\x91": "***N***"}

# el max de campo area max dividido sobre el numero de procesos proporciona el número de los cortes


capaOrigenIrradiacion =arcpy.Describe(arcpy.GetParameterAsText(0)).catalogpath.decode('utf-8') # capa de puntos para crear cluster de polígonos
capaObjetoCluster = arcpy.Describe(arcpy.GetParameterAsText(1)).catalogpath.decode('utf-8') # capa de grilla o poligonos a agrupar
campoAreaMax = arcpy.GetParameterAsText(2).decode('utf-8') # viene de capaOrigenIrradiacion , area máxima para contruir el cluster
campoAreaPoligono = arcpy.GetParameterAsText(3).decode('utf-8') # Campo de área de los polígonos que se acumula para realizar la agrupación
FolderEntrada = r"%s"%arcpy.GetParameterAsText(4).decode('utf-8') # Folder donde se almacenarán los datos resultantes
procesossimultaneos = int(arcpy.GetParameterAsText(5)) # número de procesos que se ejecutarán de forma simultanea
capaFinalClusters = arcpy.GetParameterAsText(6).decode('utf-8') # capa resultado de los procesos
datos_intermedios = arcpy.GetParameterAsText(7) # opción de conservar o no los datos intermedios

#=========Funciones Auxiliares=====================#

def cambia_caracteres(infea): # función que codifica los caracteres especiales
    for xx in dic_acentos:# ciclo que reemplaza las letras por los carateres especiales
        infea=infea.replace(xx,dic_acentos[xx])
    return infea

def getPythonPath(): # función que localiza el directorio de instalación del interprete de python
    pydir = sys.exec_prefix
    pyexe = os.path.join(pydir, "python.exe")
    if os.path.exists(pyexe):
        return pyexe
    else:
        raise RuntimeError("python.exe no se encuentra instalado en {0}".format(pydir))

def listaanidada(lista,separador): #convierte un arreglo en una lista anidada
    seq = tuple(lista)
    texto_anidado=separador.join( seq )
    return texto_anidado

def creadirs(): # crea los directorios de salida del programa
    nombre="unificado"
    if not os.path.exists(FolderEntrada+"\\%s"%(nombre)):
        os.makedirs(FolderEntrada+"\\%s"%(nombre))
    return FolderEntrada+"\\%s"%nombre

def crearFGDB(ruta): # crea la geodatabase que almacena el resultado final
    arcpy.CreateFileGDB_management(ruta, "bd_unificado.gdb")
    return ruta+"\\"+"bd_unificado.gdb"

def chunkIt(seq, num): # función que parte una secuencia en un número de partes
  avg = len(seq) / float(num)
  out = []
  last = 0.0

  while last < len(seq):
    out.append(seq[int(last):int(last + avg)])
    last += avg

  return out

def pasarlista(lista): # función que transforma el rango para transferirlo al script auxiliar
    lista=str(lista)
    lista=lista.replace(", ","_") # convierte los espacios en _
    return lista

def directorioyArchivo (): # captura el directorio donde se encuentra almacenado el script y el nombre del script
    archivo=inspect.getfile(inspect.currentframe()) # script filename
    directorio=os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) # script directory
    return archivo, directorio

def capturarIdCapa(capaInteres): # función que encuentra el campo que almacena los ids
    campo_oid = [x.name for x in arcpy.Describe(capaInteres).fields if x.type == 'OID' ][0]
    return  campo_oid

def calculoNearGeneral(capaOrigenI, capaObjetoC): # asigna a cada cuadro el punto más cercano
    arcpy.AddMessage(time.strftime("%c") + " " + "Ejecutando Calculo Near...")
    capaNear = arcpy.Near_analysis(capaObjetoC, capaOrigenI, '#', 'NO_LOCATION', 'NO_ANGLE', 'PLANAR')
    arcpy.AddMessage("Finaliza Calculo Near")


### ------------------validación_de_requerimientos----------------------------

pyexe = getPythonPath()

if not "x64" in r"%s"%(pyexe): # valida que el python de 64 bits se encuentre instalado
    pyexe=pyexe.replace("ArcGIS","ArcGISx64")
if not arcpy.Exists(pyexe):
    arcpy.AddError("Usted no tiene instalado el Geoprocesamiento en segundo plano (64 bits)")
    raise RuntimeError("Usted no tiene instalado el Geoprocesamiento en segundo plano (64 bits) {0}".format(pyexe))
else:
    verPython64=pyexe
    scriptAuxiliar="Alterno_Formacion_Clusters_IN_OUT_AreaMP_Auxiliar.py" # script auxiliar que ejecuta el prceso de eliminate
    verPythonfinal=verPython64

### ------------------------------------------------------------


def principal():
    secciones=[]
    verPython=verPythonfinal # asigna la versión de python que se va a usar 32 o 64 bits
    verPythonDir=verPython.replace("\\python.exe","") # obtiene la ruta del directorio que almacena el ejecutable de python
    script=directorioyArchivo() #
    script=script[1]+"\\"+scriptAuxiliar # almacena la ruta y nombre de archivo del script auxiliar
    #crea la base
    dirSalida= FolderEntrada
    numeroprocesos = int(arcpy.GetCount_management(capaOrigenIrradiacion)[0])
    cuadros=[num for num in xrange(1,numeroprocesos+1)]
    cuadros_ram=cuadros
##    random.shuffle(cuadros_ram)
    partes=chunkIt(cuadros_ram,procesossimultaneos)
    if procesossimultaneos!= len(partes): # valida que los procesos coincida con el numero de partes
        partes1=partes[:]
        partes1.pop(-1)
        partes1[-1].extend(partes[-1])
        del partes
        partes=partes1[:]
    for a in partes: # almacena los comandos en un arreglo+
        if len(a)>1:
            b=[a[0],a[-1]]
        else:
            b=a
        comandos.append(r"start %s %s %s %s %s %s %s %s"%(verPython, script, capaOrigenIrradiacion , capaObjetoCluster , campoAreaMax, campoAreaPoligono, FolderEntrada,
        pasarlista(b)))
        secciones.append(pasarlista(b))
    letras=string.ascii_letters # crea un listado de lestras que usará para almacenar la ejecución de los comandos
    instrucciones="" # incializa la cadena de texto que almacenará las instrucciones de ejecución de los multiples procesos
    instrucciones_espera="" # inicializa la variable que almacenará las instrucciones de espera de los procesos
    # este ciclo almacena las instrucciónes en una cadena de texto teniendo en cuenta el número de procesos simultaneos definidos
    for x in xrange(0,procesossimultaneos):

        if x==procesossimultaneos-1 :

            instrucciones+='%s = subprocess.Popen(comandos[%s],stdin=None,stdout=subprocess.PIPE,shell=True,env=dict(os.environ, PYTHONHOME=verPythonDir))'%(letras[x],str(x))
        else:
            instrucciones+='%s = subprocess.Popen(comandos[%s],stdin=None,stdout=subprocess.PIPE,shell=True,env=dict(os.environ, PYTHONHOME=verPythonDir));'%(letras[x],str(x))
    for x in xrange(0,procesossimultaneos):
        if x==procesossimultaneos-1 :
         instrucciones_espera+='astdout, astderr = %s.communicate()'%(letras[x])
        else:
         instrucciones_espera+='astdout, astderr = %s.communicate();'%(letras[x])

    instrucciones=compile(instrucciones, '<string>', 'exec') # compila el texto para que sea ejecutado de mejor forma por el interprete de python
    instrucciones_espera=compile(instrucciones_espera, '<string>', 'exec') # compila el texto para que sea ejecutado de mejor forma por el interprete de python
    exec(instrucciones) # ejecuta las instrucciones de ejecución compiladas
    exec(instrucciones_espera) # ejecuta las instrucciones compiladas de espera
        # la linea a continuación construye un arreglo de todos las partes procesadas
    arreglo_features=[r"%s"%FolderEntrada+"\\Partes\\"+str(numx).replace("[","").replace("]","")+"\\bd"+str(numx).replace("[","").replace("]","")+".gdb\\seccion_"+str(numx).replace("[","").replace("]","") for numx in secciones]
    output=capaFinalClusters


##    capa_fuente=r"%s"%FolderEntrada+"\\Partes\\"+str(1)+"\\bd"+str(1)+".gdb\\seccion_1" # nuevo
    capa_fuente =arreglo_features[0]

    no_existen,existen,i=[],[],1

    for capa in arreglo_features:
        if arcpy.Exists(capa):
            existen.append(i)
        else:
            no_existen.append(i)
        i+=1

    if len(no_existen)==0:
        arreglo_features=listaanidada(arreglo_features,";")
        ruta_unificado,nombre_salida =os.path.split(capaFinalClusters)
        arcpy.CreateFeatureclass_management(ruta_unificado,nombre_salida ,
                "POLYGON", capa_fuente, "SAME_AS_TEMPLATE", "SAME_AS_TEMPLATE", capa_fuente)
        arcpy.AddMessage(arreglo_features)
        arcpy.AddMessage(output)
        arcpy.Append_management (inputs=arreglo_features, target=output, schema_type="NO_TEST") # nuevo
        if datos_intermedios == "false":
            shutil.rmtree(r"%s"%FolderEntrada+"\\Partes")
    else:
        arcpy.AddError("no se pudieron procesar las secciones: "+str(no_existen))

if __name__ == '__main__':
    calculoNearGeneral(capaOrigenIrradiacion, capaObjetoCluster) # asigna a cada cuadro el punto más cercano
    capaOrigenIrradiacion = cambia_caracteres(capaOrigenIrradiacion) # codifica los carácteres especiales para enviarlos al script auxiliar
    capaObjetoCluster = cambia_caracteres(capaObjetoCluster)# codifica los carácteres especiales para enviarlos al script auxiliar
    campoAreaMax = cambia_caracteres(campoAreaMax)# codifica los carácteres especiales para enviarlos al script auxiliar
    campoAreaPoligono = cambia_caracteres(campoAreaPoligono)# codifica los carácteres especiales para enviarlos al script auxiliar
    FolderEntrada = cambia_caracteres(FolderEntrada)# codifica los carácteres especiales para enviarlos al script auxiliar
    principal() # ejecución de la función principal

