# Script_Agrupacion_Poligonos_x_Puntos
Script para generar clusters de polígonos a partir de información de datos puntuales. Este script cuenta con dos versiones. Una versión de 32 bits que utiliza el procesamiento en memoria y los cursores da y una versión que también emplea procesamiento en memoria y los cursores [da](http://desktop.arcgis.com/en/arcmap/latest/analyze/python/data-access-using-cursors.htm), pero que adicionalmente hace uso del procesamiento en paralelo de 64 bits.


## Configuración

Como primera medida se debe descargar el repositorio, una vez realizada esta acción se encontrarán dos directorios: Datos_demo y Version_Arcgis10_5. El primer directorio contiene datos de prueba y el segundo contiene las dos versiones del script para **Arcgis Desktop 10.5** o versiones superiores.

![Archivos](Images\directorios.PNG)

Posteriormente se debe ingresar desde Arcmap al directorio Version_Arcgis10_5 tal y como se muestra en la siguiente imagen.

![Archivos_arcmap](Images\archivos_scripts_agrupacion.PNG)

Dentro de este folder encontraremos un Toolbox con las dos versiones del script la versión de 32bits o **Script_Cluster_In_Out_x_Area_Acumulada y la versión de 64bits** y procesamiento en paralelo **Script_Cluster_In_Out_x_Area_Acumuladax64**.

Para configurar la herramienta en sus dos versiones debemos primeramente hacer clic derecho sobre el script de 32 bits **Script_Cluster_In_Out_x_Area_Acumulada** y selecionamos la opción propiedades.

![fuente32](Images\propiedades_agrupacion.png)

Una vez se realice esta acción, se debe seleccionar la pestaña source del menú de propiedades.

![source32](Images\source_agrupacion.png)

Una vez en este menú, se debe hacer clic en el ícono de abrir y se debe localizar el script indicado en la siguiente imagen.

![script32](Images\script_32.png)

 Luego se debe hacer clic en abrir y posteriormente en aceptar.

 El mismo procedimiento se debe realizar para la herramienta de 64 bits.

 ![fuente64](Images\source_agrupacion64.png)

En el caso de la herramienta de 64 bits se seleccionará el script localizado en la siguiente imagen.

![script64](Images\script_64.png)

## Intrucciones de uso

### Herramienta de 32 bits (Script_Cluster_In_Out_x_Area_Acumulada)

En el repositorio de esta herramienta se suministraron unas capas de demostración, estas capas corresponden a una capa de puntos generadora de los Clusters  y una capa de polígonos que serán agrupados para formar estos Clusters.

![dostos_demo](Images\agrupacion_insumos.PNG)

Para emplear las herramientas se debe crear un nuevo modelo de geoprocesamiento, y cargar en el las capas de demostración suministradas en el repositorio, tal como lo muestran las siguientes imágenes.

![modeloinusmo1](Images\agrupacion_insumos_puntos.png)

![modeloinusmo2](Images\agrupacion_insumos_poligonos.png)

Posteriormente se sebe seleccionar el campo de área máxima de agrupación localizado en los puntos y el campo de área de agrupación localizado en los polígonos.

![parametromodelo](Images\agrupacion_parametros.png)

Por último se debe seleccionar la ruta y el nombre de la capa de salida. En esta ruta se almacenará adicionalmente el reporte de los resultados.

Una vez se tienen configurados todos estos parámetros, se debe ejecutar el modelo y esperar una ventana de ejecución tal y como se muestra en la siguiente imagen.

![resultado1](Images\agrupacion_proceso32_final.png)

Los resultados almacenados en la dirección suministrada son dos: una capa de polígonos resultante y un reporte asociado.

![resultado4](Images\agrupacion_resultados_gdb.png)

La capa resultante corresponde a una copia de la capa de polígonos inicial pero con un campo que indica si el polígono conforma un clúster o agrupación. Este campo de nombre **CLUSTER**, contiene el número del identificador del punto que generó la agrupación.

![resultado2](Images\Cluster_campo.PNG)


Si visualizamos la capa empleando el campo **CLUSTER** como generador de la simbología encontramos la siguiente vista:

![resultado3](Images\agrupacion_proceso32_final_capa.png)


El reporte generado de nombre BaseReporte contiene los siguientes campos:
+ **OBJECTID:** Identificador de los registros del reporte.
+ **Id_cluster:** El identificador del cluster.
+ **Acum_Max:** Área máxima que debía ser acumulada por el clúster.
+ **Mag_Acum_Total:** El área o magnitud acumulada total por el clúster.
+ **Area_Acum_Total:** La sumatoria de área de los polígonos que conforman el clúster.

![reporte](Images\agrupacion_reporte.PNG)

### Herramienta de 64 bits (Script_Cluster_In_Out_x_Area_Acumuladax64)

Todos los parámetros empleados en la herramienta de 32 bits son usados en la herramienta de 64 bits, la diferencia radica, en que la herramienta de 64 bits requiere tres parámetros adicionales que son:
+ El número de procesos a ejecutarse en paralelo
+ Un folder para almacenar los resultados intermedios
+ La opción de si desea conservar estos datos intermedios

![paramx64](Images\agrupacion_parametros_64.png)

La ejecución desplegará una ventana de ejecución de Arcgis pero adicionalmente desplegará un conjunto de ventanas de **CMD** acordes con el número de procesos en paralelo seleccionados. **(El número de ventanas no puede exceder el número de elementos de la capa de puntos)**

![ejecucionx64](Images\ejecucionx64.png)

Los resultados finales de la herramienta de 64 bits son iguales a los de la herramienta 32, la única diferencia se encuentra en que la herramienta de 64 produce resultados parciales que se almacenan en el folder suministrado como parámetro.

![parcialesx64](Images\resultados_parciales.PNG)
