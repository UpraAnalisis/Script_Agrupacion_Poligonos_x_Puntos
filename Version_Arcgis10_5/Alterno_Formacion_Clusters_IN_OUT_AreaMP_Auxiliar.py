# -*- coding: utf-8 -*-
"""
Script Name: Alterno_Formacion_Clusters_IN_OUT_AreaMP_Auxiliar
Source Name: Alterno_Formacion_Clusters_IN_OUT_AreaMP_Auxiliar.py
Version: ArcGIS 10.3 or Superior
Author: Carlos Javier Delgado - Carlos Mario Cano UPRA - Grupo TIC - Analisis de Informacion
"""

import arcpy
import time
import os
import exceptions
from arcpy import env
env.overwriteOutput = True

dic={" ":"__","=":"igual", "<":"menor", ">": "mayor"} # diccionario que convierte los caracteres especiales en letras
comandos=[] # arreglo que almacena los comandos a ejecutar por el script auxiliar
dic_acentos={" ":"---","\xc3\xa1":"***a***","\xc3\xa9":"***e***", "\xc3\xad":"***i***",
"\xc3\xb3": "***o***","\xc3\xba": "***u***","\xc3\xb1": "***n***","\xc3\x81":"***A***","\xc3\x89":"***E***",
"\xc3\x8d":"***I***", "\xc3\x93": "***O***","***\xc3\x9a***":"Ú","\xc3\x91": "***N***"}

try:
    capaOrigenIrradiacion = arcpy.GetParameterAsText(0) # capa de puntos para crear cluster de polígonos
    capaObjetoCluster = arcpy.GetParameterAsText(1) # capa de grilla o poligonos a agrupar
    campoAreaMax = arcpy.GetParameterAsText(2) # viene de capaOrigenIrradiacion , area máxima para contruir el cluster
    campoAreaPoligono = arcpy.GetParameterAsText(3) # Campo de área de los polígonos que se acumula para realizar la agrupación
    FolderEntrada = arcpy.GetParameterAsText(4) # Folder donde se almacenarán los datos resultantes
    rango=arcpy.GetParameterAsText(5) # captura los cuadros que se van a procesar
    #=========Funciones Auxiliares=====================#

    def cambia_caracteres(infea):
        for xx in dic_acentos:# ciclo que reemplaza las letras por los carateres especiales
            infea=infea.replace(xx,dic_acentos[xx])
        return infea

    def recuperalista(lista): # función que recupera la lista de items a procesar
            b=[]
            c=[]
            rango=lista.replace("[","")
            rango=rango.replace("]","")
            rango = rango.split("_")
            b=map(int,rango)
            if len(b)>1:
                c=[x for x in xrange(b[0],b[-1]+1)]
            else:
                c=b[0]
            return c

    def creadirs(numero,ruta_raiz): # crea los directorios de salida del programa
        nombre="Partes"
        if not os.path.exists(ruta_raiz+"\\%s"%(nombre+"\\"+str(numero))):
            os.makedirs(ruta_raiz+"\\%s"%(nombre+"\\"+str(numero)))
        return ruta_raiz+"\\%s"%nombre+"\\"+str(numero)

    def crearFGDB(ruta,numero): # crea las filegeodatabse de los procesos parciales
        arcpy.CreateFileGDB_management(ruta, "bd"+str(numero)+".gdb")
        return ruta+"\\"+"bd"+str(numero)+".gdb"

    def calculoSortGeneral(capaObjetoC): # organiza la tabla objeto del cluster de forma ascendente por id de cluster y distancia al punto de irradiación
        print ("sort general %s "%(capaObjetoC))
    	print (time.strftime("%c") + " " + "Ejecutando Calculo Sort...")
    	capaOrdenada = "in_memory" + "\\capaClusterOrdenada"
    	arcpy.Sort_management(capaObjetoC, capaOrdenada , 'NEAR_FID ASCENDING;NEAR_DIST ASCENDING', 'UR').getOutput(0)
    	print("Finaliza Calculo Sort")
    	return capaOrdenada

    def ordenarPoligonosSegunID_Punto(capaOrdenar, capaOrigenI, campo_Area, campoAreaMax,capaFinalClusters):  # función que asigna el cluster a cada polígono
    	arcpy.AddMessage(time.strftime("%c") + " " +"Ejecutando Algoritmo de Cluster...")
        oid_capa_origen = capturarIdCapa(capaOrigenI)
        oid_capa_ordenar = capturarIdCapa(capaOrdenar)
    	idsNearTotales = list(set([row[0] for row in arcpy.da.SearchCursor(capaOrdenar, "NEAR_FID")]))
    	cont_ids = 0
        for i in idsNearTotales:
            areaMax_x_id = [row[0] for row in arcpy.da.SearchCursor(capaOrigenIrradiacion, campoAreaMax,oid_capa_origen + " = " + str(i))][0]
            contador = 0
            with  arcpy.da.UpdateCursor(capaOrdenar,[oid_capa_ordenar,"NEAR_FID","NEAR_DIST",campo_Area,"CLUSTER"],"NEAR_FID = " + str(i)) as cursor:
                for fila in cursor:
                    if contador == 0 and fila[3] >= areaMax_x_id:
                        fila[4] = i
                    contador+= fila[3]
                    if contador > 0 and contador <= areaMax_x_id:
                        fila[4] = i
                    cursor.updateRow(fila)
            cont_ids += 1

    	arcpy.AddMessage(time.strftime("%c") + " " +"Ejecutando Copia...")
    	arcpy.CopyFeatures_management(capaOrdenar,capaFinalClusters)

    def listaToCadena(listaInicial):
    	cadena = ""
    	cadena = ",".join(str(int(x)) for x in listaInicial)
    	return cadena

    def crearCampoCluster(capaObjeto):
    	arcpy.AddField_management(capaObjeto,"CLUSTER","LONG")

    def capturarIdCapa(capaInteres):
        campo_oid = [x.name for x in arcpy.Describe(capaInteres).fields if x.type == 'OID' ][0]
        return  campo_oid


    if __name__ == '__main__':
        rango=recuperalista(rango)
        capaOrigenIrradiacion = cambia_caracteres(capaOrigenIrradiacion)
        capaObjetoCluster = cambia_caracteres(capaObjetoCluster)
        campoAreaMax = cambia_caracteres(campoAreaMax)
        campoAreaPoligono = cambia_caracteres(campoAreaPoligono)
        FolderEntrada = cambia_caracteres(FolderEntrada)
        campo_oid = capturarIdCapa(capaOrigenIrradiacion) # captura el campo del object id

        if type(rango) == list: # verifica si son uno o mas procesos
            print "Procesando las secciones entre %s y %s "%(str(rango[0]),str(rango[-1]))
            ruta=creadirs("%s_%s"%(str(rango[0]),str(rango[-1])),FolderEntrada) # crea los directorios de los resultados parciales
            ruta=crearFGDB(ruta,"%s_%s"%(str(rango[0]),str(rango[-1]))) # crea las file geodatabse de los resultados parciales

            capaFinalClusters = ruta+"\\"+"seccion_%s_%s"%(str(rango[0]),str(rango[-1])) # nombra


            capaOrigenIrradiacionDummy = arcpy.Select_analysis (in_features= capaOrigenIrradiacion ,
            out_feature_class="in_memory\\seccion_%s_%s"%(str(rango[0]),str(rango[-1])), where_clause ="%s >= %s AND %s <= %s"%(capturarIdCapa(capaOrigenIrradiacion),str(rango[0]),
            capturarIdCapa(capaOrigenIrradiacion),str(rango[-1])))

            print "%s >= %s AND %s <= %s"%(capturarIdCapa(capaOrigenIrradiacion),str(rango[0]),
            capturarIdCapa(capaOrigenIrradiacion),str(rango[-1]))

            capaObjetoClusterDummy = arcpy.Select_analysis (in_features= capaObjetoCluster ,
            out_feature_class="in_memory\\near_seccion_%s_%s"%(str(rango[0]),str(rango[-1])), where_clause ="NEAR_FID >= %s AND NEAR_FID <= %s"%(str(rango[0]),str(rango[-1])))

            crearCampoCluster("in_memory\\near_seccion_%s_%s"%(str(rango[0]),str(rango[-1])))
            capaNearOrdenado = calculoSortGeneral("in_memory\\near_seccion_%s_%s"%(str(rango[0]),str(rango[-1])))
            ordenarPoligonosSegunID_Punto(capaNearOrdenado, "in_memory\\seccion_%s_%s"%(str(rango[0]),str(rango[-1])), campoAreaPoligono, campoAreaMax ,capaFinalClusters)


        else:
            rango = [rango]
            print "Procesando la seccion "+ str(rango[0])
            for numero in rango:
                ruta=creadirs(numero,FolderEntrada)
                ruta=crearFGDB(ruta,numero)

                capaFinalClusters = ruta+"\\"+"seccion_"+str(numero)

                capaOrigenIrradiacionDummy = arcpy.Select_analysis (in_features= capaOrigenIrradiacion ,
                out_feature_class="in_memory\\seccion_%s"%(str(numero)), where_clause ="%s = %s"%(capturarIdCapa(capaOrigenIrradiacion),(str(numero))))

                capaObjetoClusterDummy = arcpy.Select_analysis (in_features= capaObjetoCluster ,
                out_feature_class="in_memory\\near_seccion_%s"%(str(numero)), where_clause ="NEAR_FID = %s"%(str(numero)))

                crearCampoCluster("in_memory\\near_seccion_%s"%(str(numero)))
                capaNearOrdenado = calculoSortGeneral("in_memory\\near_seccion_%s"%(str(numero)))
                ordenarPoligonosSegunID_Punto(capaNearOrdenado, "in_memory\\seccion_%s"%(str(numero)), campoAreaPoligono, campoAreaMax ,capaFinalClusters)





except exceptions.Exception as e: # controla las fallas y las imprime en la consola del cmd
    print e.__class__, e.__doc__, e.message
    os.system("pause")