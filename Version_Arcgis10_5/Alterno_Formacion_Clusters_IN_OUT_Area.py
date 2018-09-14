# -*- coding: utf-8 -*-
"""
Script Name:  Formacion_Clusters_IN_OUT_Area
Source Name: Formacion_Clusters_IN_OUT_Area.py
Version: ArcGIS 10.3 or Superior
Author: Carlos Javier Delgado - UPRA - Grupo TIC - Analisis de Informacion
"""

import arcpy
import time
import os
import random
from arcpy import env
env.overwriteOutput = True
arcpy.env.qualifiedFieldNames = False
env.wokspace = "in_memory"
ws = env.wokspace

capaOrigenIrradiacion = arcpy.GetParameterAsText(0).decode('utf-8') # capa de puntos para crear cluster de polígonos
capaObjetoCluster = arcpy.GetParameterAsText(1).decode('utf-8') # capa de grilla o poligonos a agrupar
campoAreaMax = arcpy.GetParameterAsText(2).decode('utf-8') # viene de capaOrigenIrradiacion , area máxima para contruir el cluster
campoAreaPoligono = arcpy.GetParameterAsText(3).decode('utf-8') # Campo de área de los polígonos que se acumula para realizar la agrupación
capaFinalClusters = arcpy.GetParameterAsText(4).decode('utf-8')  # capa resultado de los procesos

def principal(): # función principal

	capaObjetoNear = calculoNearGeneral(capaOrigenIrradiacion, capaObjetoCluster) # función que asigna a cada uno de los poligonos de la grilla el punto más cercano
	crearCampoCluster(capaObjetoNear) # crea el campo donde se asigna el cluster
	capaNearOrdenado = calculoSortGeneral(capaObjetoNear)
	ordenarPoligonosSegunID_Punto(capaNearOrdenado, capaOrigenIrradiacion, campoAreaPoligono, campoAreaMax)


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



def calculoNearGeneral(capaOrigenI, capaObjetoC): # función que asigna a cada uno de los poligonos de la grilla el punto más cercano
	arcpy.AddMessage(time.strftime("%c") + " " + "Ejecutando Calculo Near...")
	capaNear = arcpy.Near_analysis(capaObjetoC, capaOrigenI, '#', 'NO_LOCATION', 'NO_ANGLE', 'PLANAR')
	arcpy.AddMessage("Finaliza Calculo Near")
	return capaNear

def calculoSortGeneral(capaObjetoC): # organiza la tabla objeto del cluster de forma ascendente por id de cluster y distancia al punto de irradiación
	arcpy.AddMessage(time.strftime("%c") + " " + "Ejecutando Calculo Sort...")
	capaOrdenada = "in_memory" + "\\capaClusterOrdenada"
	aa = arcpy.Sort_management(capaObjetoC, capaOrdenada , 'NEAR_FID ASCENDING;NEAR_DIST ASCENDING', 'UR').getOutput(0)
	arcpy.AddMessage("Finaliza Calculo Sort")
	return capaOrdenada

def ordenarPoligonosSegunID_Punto(capaOrdenar, capaOrigenI, campo_Area, campo_Area_Max): # función que asigna el cluster a cada polígono
	arcpy.AddMessage(time.strftime("%c") + " " +"Ejecutando Algoritmo de Cluster...")
	oid_capa_origen = capturarIdCapa(capaOrigenI)
	oid_capa_ordenar = capturarIdCapa(capaOrdenar)
	idsNearTotales = list(set([row[0] for row in arcpy.da.SearchCursor(capaOrdenar, "NEAR_FID")]))

	cont_ids = 0

	for i in idsNearTotales:
		areaMax_x_id = [row[0] for row in arcpy.da.SearchCursor(capaOrigenI, campo_Area_Max, oid_capa_origen + " = " + str(i))][0]
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
		if cont_ids in [1, 10, 100,1000,5000,10000,20000,30000,50000,75000,100000,150000]:
			arcpy.AddMessage(time.strftime("%c") + " Iteracion: " +str(cont_ids))

	arcpy.AddMessage(time.strftime("%c") + " " +"Ejecutando Copia...")
	arcpy.CopyFeatures_management(capaOrdenar,capaFinalClusters)

def crearCampoCluster(capaObjeto):  # crea el campo donde se asigna el cluster
	arcpy.AddField_management(capaObjeto,"CLUSTER","LONG")

def capturarIdCapa(capaInteres): # función que encuentra el campo que almacena los ids
	campo_oid = [x.name for x in arcpy.Describe(capaInteres).fields if x.type == 'OID' ][0]
	return	campo_oid


def capturarIdCapa(capaInteres):
    campo_oid = [x.name for x in arcpy.Describe(capaInteres).fields if x.type == 'OID' ][0]
    return  campo_oid


def retornaValor(capa,campoid,campovalor1,campovalor2,idBuscado):
    valor_Encontrado1=None
    valor_Encontrado2=None
    with arcpy.da.SearchCursor(capa,[campoid,campovalor1,campovalor2]) as cursor2:
        for filac2 in cursor2:
            if filac2[0] == idBuscado:
                valor_Encontrado1=filac2[1]
                valor_Encontrado2=filac2[2]


    return valor_Encontrado1,valor_Encontrado2


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


if __name__ == '__main__':
	ruta_gdb= os.path.split(capaFinalClusters)[0]
	principal()
	generar_reporte()








