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

if __name__ == '__main__':
	principal()








