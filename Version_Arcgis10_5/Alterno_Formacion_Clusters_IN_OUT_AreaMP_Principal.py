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
from arcpy import env
env.overwriteOutput = True
arcpy.env.qualifiedFieldNames = False
env.wokspace = "in_memory"
ws = env.wokspace
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

def generar_reporte(): # función que crea el reportes de resultados
	fields = arcpy.ListFields(capaOrigenIrradiacion)
	# se crea un objeto de tipo field info
	fieldinfo = arcpy.FieldInfo()
	for field in fields:
		if field.name == campoAreaMax:
			fieldinfo.addField(field.name, "Acum_Max", "VISIBLE", "")
		else:
			fieldinfo.addField(field.name, field.name, "HIDDEN", "")
	tabla_basereporte = arcpy.MakeTableView_management (in_table=capaOrigenIrradiacion, out_view="basereporte", field_info=fieldinfo, workspace="in_memory")
	arcpy.CopyRows_management (in_rows=tabla_basereporte, out_table="in_memory\\BaseReporte")
	arcpy.AddField_management (in_table="in_memory\\BaseReporte", field_name="Id_cluster", field_type="LONG", field_alias="Id_cluster")
	arcpy.AlterField_management (in_table="in_memory\\BaseReporte", field="Acum_Max", new_field_alias="Acum_Max")
	arcpy.CalculateField_management (in_table="in_memory\\BaseReporte", field="Id_cluster", expression="float(!%s!)"%(capturarIdCapa("in_memory\\basereporte")), expression_type="PYTHON_9.3")
	arcpy.CopyRows_management (in_rows="in_memory\\BaseReporte", out_table=ruta_gdb+"\\"+"BaseReporte")
	arcpy.Statistics_analysis(in_table=capaFinalClusters, out_table="in_memory\\tabla_cluster", statistics_fields="%s SUM;Shape_Area SUM"%(campoAreaPoligono), case_field="CLUSTER")

	capa=Layer(ruta_gdb+"\\"+"BaseReporte",[],ws)# instancia un objeto de la clase Layer para aceder a sus propiedades
	arcpy.AlterField_management (in_table="in_memory\\tabla_cluster", field="SUM_%s"%(campoAreaPoligono), new_field_name="Mag_Acum_Total", new_field_alias="Mag_Acum_Total")
	arcpy.AlterField_management (in_table="in_memory\\tabla_cluster", field="SUM_Shape_Area", new_field_name="Area_Acum_Total", new_field_alias="Area_Acum_Total")
	capa.addjoinCursorMultiple("in_memory\\tabla_cluster","Id_cluster","CLUSTER",["Mag_Acum_Total","Area_Acum_Total"]) # realiza un addjoin cursor multiple entre las capas especificadas


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


class Layer(object):

        def __init__(self,inFeature,campos_visibles,ws):  # funcion que incializa la clase e instancia el objeto de tipo layer
            self.feature=r"%s"%inFeature # esta propiedad almacena el feature clas del objeto
            self.ruta="" # almacena la ruta del feature layer
            self.nombre=arcpy.Describe(self.feature).name # almacena el nombre de la capa
            self.camposFeature=arcpy.ListFields(self.feature) # almacena los campos del feature class
            self.camposLayer="" # almacena los campos del layer
            self.toLayer(campos_visibles) # almacena el workspace que en este caso es en memoria

        def toLayer(self,campos_visibles): # crea un objeto a partir del feature de entrada y los campos visibles
            fields= arcpy.ListFields(self.feature)
            fieldinfo = arcpy.FieldInfo()

            if campos_visibles!=[]:
                for field in fields:
                    if field.name in campos_visibles:
                        fieldinfo.addField(field.name, field.name, "VISIBLE", "")
                    else:
                        fieldinfo.addField(field.name, field.name, "HIDDEN", "")
            else:
                for field in fields:
                        fieldinfo.addField(field.name, field.name, "VISIBLE", "")

            if "in_memory" in ws:
                self.ruta=arcpy.MakeTableView_management(self.feature, self.nombre+"_"+str(random.randrange(0,5000))+".lyr",field_info=fieldinfo).getOutput(0)
            else:
                self.ruta=arcpy.MakeTableView_management(self.feature, self.nombre+".lyr",field_info=fieldinfo).getOutput(0)
            self.camposLayer=arcpy.ListFields(self.feature)

        def addjoinCursorMultiple(self,capajoin,llaveobjetivo,llavetabla,camposjoin): # realiza una add join entre dos capas empleando cursores, pero uniendo multiples campos
            targshp =self.ruta
            joinshp=capajoin
            joinfields =camposjoin
            joindict = {}
            campo_tipo={}
            camposjoin1=[]
            camposjoin1.append(llavetabla)
            for i in xrange(0,len(camposjoin)):
                    camposjoin1.append(camposjoin[i])
            camposjoin=camposjoin1
            with arcpy.da.SearchCursor(capajoin,camposjoin) as cursor:
             for row in cursor:
                llave=row[0]
                valor=[]
                for i in xrange(1,len(camposjoin)):
                    valor.append(row[i])
                joindict[llave]=valor
            camposupdate=[]
            camposupdate.append(llaveobjetivo)
            for i in xrange(1,len(camposjoin)):
                    camposupdate.append(camposjoin[i])
            campos_feature=arcpy.ListFields(capajoin)
            for campo in campos_feature:
                campo_tipo[campo.name]=[campo.type]

            clon=self.feature

            for i in xrange(1,len(camposupdate)):

                arcpy.AddField_management(clon, camposupdate[i],str(campo_tipo[camposupdate[i]][0]))

            with arcpy.da.UpdateCursor(clon, camposupdate) as recs:
                lim_i=len(joinfields)
                j=0
                for rec in recs:
                    keyval = rec[0]

                    if joindict.has_key(keyval):

                        for i in xrange(0,lim_i):
                            rec[i+1] = joindict[keyval][i]

                    recs.updateRow(rec)


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
    ruta_gdb= os.path.split(capaFinalClusters)[0]
    calculoNearGeneral(capaOrigenIrradiacion, capaObjetoCluster) # asigna a cada cuadro el punto más cercano
    capaOrigenIrradiacion = cambia_caracteres(capaOrigenIrradiacion) # codifica los carácteres especiales para enviarlos al script auxiliar
    capaObjetoCluster = cambia_caracteres(capaObjetoCluster)# codifica los carácteres especiales para enviarlos al script auxiliar
    campoAreaMax = cambia_caracteres(campoAreaMax)# codifica los carácteres especiales para enviarlos al script auxiliar
    campoAreaPoligono = cambia_caracteres(campoAreaPoligono)# codifica los carácteres especiales para enviarlos al script auxiliar
    FolderEntrada = cambia_caracteres(FolderEntrada)# codifica los carácteres especiales para enviarlos al script auxiliar
    principal() # ejecución de la función principal
    generar_reporte() # función que genera el reporte de loos resultados

