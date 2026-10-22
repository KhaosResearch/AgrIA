# Análisis inicial de AYUDAS & SUPERFICIES
>Ejemplo 2023-2024

## División y cargado de datos
Para el análisis, vamos a tomar a los **20 primeros agricultores que hicieron la solicitud** de ayuda de la PAC según aparecen en el archivo de `PAC_AYUDAS_2023.csv`. Los identificadores son los siguientes:
```python
Selected SECUENCIALES:
[np.int64(638945), np.int64(1382847), np.int64(25519), np.int64(1382042), np.int64(1398501), np.int64(625002), np.int64(255217), np.int64(1406793), np.int64(1368318), np.int64(52429), np.int64(1409348), np.int64(202183), np.int64(133204), np.int64(1333614), np.int64(129074), np.int64(1393940), np.int64(383032), np.int64(1512802), np.int64(1420624), np.int64(290451)]
```
Para cada identificador, se han buscado todas las ocurrencias de cada uno, es decir, **todas las parcelas asociadas con cada agricultor**. El número total de entradas halladas cada archivo es el siguiente:
```python
Reading AYUDAS sample...
AYUDAS rows: 298

Reading SUPERFICIES sample...
SUPERFICIES rows: 160
```
Viendo las superficies, podemos determinar **una media de 8 parcelas por agricultor.** Llama la atención de que esta consistencia no se mantenga en las ayudas por lo que empezamos a sospechar que **cada agricultor está solicitando más de una ayuda para una misma parcela.**
```python
================ AYUDAS ================
   SECUENCIAL  ...                                           DESC_LNA
0      638945  ...             Cubierta vegetal espontánea o sembrada
1      638945  ...  Ayuda básica a la renta para la sostenibilidad...
2      638945  ...  Ayuda a los productores de frutos secos en áre...
3      638945  ...             Cubierta vegetal espontánea o sembrada
4     1382847  ...  Ayuda básica a la renta para la sostenibilidad...

[5 rows x 4 columns]

Columns:
['SECUENCIAL', 'REC_CODIGO', 'LNA_CODIGO', 'DESC_LNA']

================ SUPERFICIES ================
   SECUENCIAL        REC_CODIGO  ...  SUP_RIEGO_HA  SUP_TOTAL_HA
0      383032  1700000005116291  ...          0.51          0.51
1      383032  1700000005116298  ...          0.00          6.53
2      383032  1700000005116292  ...          0.43          0.43
3      383032  1700000005116293  ...          0.02          0.02
4      383032  1700000005116300  ...          0.00          0.76

[5 rows x 12 columns]

Columns:
['SECUENCIAL', 'REC_CODIGO', 'PRO_CODIGO', 'MSP_CODIGO', 'REC_POLIGONO', 'REC_PARCELA', 'REC_RECINTO', 'PRD_CODIGO', 'PRD_DESC', 'SUP_SECANO_HA', 'SUP_RIEGO_HA', 'SUP_TOTAL_HA']
```
Salvo las descripciones (`ZZZ_DESC`), todos los datos son numéricos: enteros y con punto decimal.

## Agrupación de datos
**Agrupamos los datos en base a su `REC_CODIGO`.** Se entiende que este es el código del recinto y **debería ser único para cada recinto** que incluye el agricultor en su solicitud.
```python
================ AYUDAS PER PARCEL ================
     SECUENCIAL        REC_CODIGO  N_AYUDAS
24       202183  1700000002965417         3
31       202183  1700000002965424         3
23       202183  1700000002965416         3
68      1368318          -1467273         3
71      1368318          -1467270         3
69      1368318          -1467272         3
74      1368318          -1467208         3
83      1368318           -566521         3
93      1368318           -148719         3
95      1368318           -148513         3
92      1368318           -148797         3
59      1333614           5481257         3
56       638945  1700000006371748         3
106     1393940  1700000004510864         3
132     1409348  1700000002735164         3
107     1393940  1700000004510865         3
65      1368318          -1467277         3
66      1368318          -1467276         3
67      1368318          -1467274         3
60      1333614           5481258         3
57       638945  1700000006371749         3
58       638945  1700000006371750         3
4         25519  1700000004453723         2
0         25519  1700000004453719         2
15        52429  1700000002756549         2
28       202183  1700000002965421         2
26       202183  1700000002965419         2
25       202183  1700000002965418         2
22       133204  1700000003084002         2
1         25519  1700000004453720         2
```
Observamos que, efectivamente, **se están solicitando varias ayudas que se aplican a la misma parcela.** Sabemos que los ecorregímenes no son compatibles dentro de una misma parcela, pero **hay otro tipo de ayudas incluidas que no necesariamente caen en la misma categoría y se podrían aplicar sobre una parcela con ecorregímenes**. Algunos ejemplos encontrados en las muestras son:
- ***Ayuda básica a la renta para la sostenibilidad (ABRS).***
- ***Ayuda a los productores de frutos secos en áreas con riesgo de desertificación.***

Esta suposición se confirma teniendo en cuenta que los datos sobre **las superficies incluyen información de uso de suelo de las parcelas individuales que cada agricultor tiene.** Esto parece mantenerse en todas las muestras
```python
================ SUPERFICIES PER PARCEL ================
    SECUENCIAL        REC_CODIGO  N_SUPERFICIES
0        25519  1700000004453719              1
1        25519  1700000004453720              1
2        25519  1700000004453721              1
3        25519  1700000004453722              1
4        25519  1700000004453723              1
5        25519  1700000004453724              1
6        52429  1700000002756540              1
7        52429  1700000002756541              1
8        52429  1700000002756542              1
9        52429  1700000002756543              1
10       52429  1700000002756544              1
11       52429  1700000002756545              1
12       52429  1700000002756546              1
13       52429  1700000002756547              1
14       52429  1700000002756548              1
15       52429  1700000002756549              1
16       52429  1700000002756550              1
17       52429  1700000002756551              1
18       52429  1700000002756552              1
19      129074  1700000002801751              1
20      129074  1700000002801752              1
21      129074  1700000002801753              1
22      133204  1700000003084002              1
23      202183  1700000002965416              1
24      202183  1700000002965417              1
25      202183  1700000002965418              1
26      202183  1700000002965419              1
27      202183  1700000002965420              1
28      202183  1700000002965421              1
29      202183  1700000002965422              1
```
```python
================ RELATIONSHIP ================
     SECUENCIAL        REC_CODIGO  N_AYUDAS  N_SUPERFICIES
23       202183  1700000002965416         3              1
24       202183  1700000002965417         3              1
31       202183  1700000002965424         3              1
56       638945  1700000006371748         3              1
57       638945  1700000006371749         3              1
58       638945  1700000006371750         3              1
59      1333614           5481257         3              1
60      1333614           5481258         3              1
65      1368318          -1467277         3              1
66      1368318          -1467276         3              1
67      1368318          -1467274         3              1
68      1368318          -1467273         3              1
69      1368318          -1467272         3              1
71      1368318          -1467270         3              1
74      1368318          -1467208         3              1
83      1368318           -566521         3              1
92      1368318           -148797         3              1
93      1368318           -148719         3              1
95      1368318           -148513         3              1
106     1393940  1700000004510864         3              1
107     1393940  1700000004510865         3              1
132     1409348  1700000002735164         3              1
0         25519  1700000004453719         2              1
1         25519  1700000004453720         2              1
2         25519  1700000004453721         2              1
3         25519  1700000004453722         2              1
4         25519  1700000004453723         2              1
5         25519  1700000004453724         2              1
6         52429  1700000002756540         2              1
7         52429  1700000002756541         2              1
15        52429  1700000002756549         2              1
22       133204  1700000003084002         2              1
25       202183  1700000002965418         2              1
26       202183  1700000002965419         2              1
27       202183  1700000002965420         2              1
28       202183  1700000002965421         2              1
29       202183  1700000002965422         2              1
30       202183  1700000002965423         2              1
36       290451          -1125324         2              1
37       290451  1700000005502561         2              1
38       290451  1700000005502564         2              1
39       383032          -1457973         2              1
40       383032          -1214607         2              1
41       383032  1700000005116290         2              1
42       383032  1700000005116291         2              1
43       383032  1700000005116292         2              1
44       383032  1700000005116293         2              1
45       383032  1700000005116294         2              1
46       383032  1700000005116296         2              1
47       383032  1700000005116297         2              1
```
## Correlación de datos:
A la hora de mergear los datos **vamos a tener una misma parcela con diferentes solicitudes de ayudas específicas.**
```python
================ EXAMPLE SURFACES ================
 SECUENCIAL       REC_CODIGO  PRO_CODIGO  MSP_CODIGO  REC_POLIGONO  REC_PARCELA  REC_RECINTO  PRD_CODIGO PRD_DESC  SUP_SECANO_HA  SUP_RIEGO_HA  SUP_TOTAL_HA
     638945 1700000006371748          18          99            16          457            1         104 ALMENDRO           0.49           0.0          0.49
     638945 1700000006371749          18          99            25           30            1         104 ALMENDRO           2.68           0.0          2.68
     638945 1700000006371750          18          99            25           66            1         104 ALMENDRO           1.50           0.0          1.50

================ EXAMPLE APPLICATION ================
 SECUENCIAL       REC_CODIGO  LNA_CODIGO                                                                       DESC_LNA
     638945 1700000006371748          18                          Ayuda básica a la renta para la sostenibilidad (ABRS)
     638945 1700000006371748         213 Ayuda a los productores de frutos secos en áreas con riesgo de desertificación
     638945 1700000006371748         510                                         Cubierta vegetal espontánea o sembrada
     638945 1700000006371749          18                          Ayuda básica a la renta para la sostenibilidad (ABRS)
     638945 1700000006371749         213 Ayuda a los productores de frutos secos en áreas con riesgo de desertificación
     638945 1700000006371749         510                                         Cubierta vegetal espontánea o sembrada
     638945 1700000006371750          18                          Ayuda básica a la renta para la sostenibilidad (ABRS)
     638945 1700000006371750         213 Ayuda a los productores de frutos secos en áreas con riesgo de desertificación
     638945 1700000006371750         510                                         Cubierta vegetal espontánea o sembrada

```
## Apéndice
### Ayudas por parcela en detalle
```python
================ MULTIPLE AIDS ================
Parcels with multiple aids: 116
    SECUENCIAL        REC_CODIGO  TOTAL_AIDS  ECOSCHEMES  OTHER_AIDS
0        25519  1700000004453719           2           1           1
1        25519  1700000004453720           2           1           1
2        25519  1700000004453721           2           1           1
3        25519  1700000004453722           2           1           1
4        25519  1700000004453723           2           1           1
5        25519  1700000004453724           2           1           1
6        52429  1700000002756540           2           1           1
7        52429  1700000002756541           2           1           1
15       52429  1700000002756549           2           1           1
22      133204  1700000003084002           2           0           2
23      202183  1700000002965416           3           1           2
24      202183  1700000002965417           3           1           2
25      202183  1700000002965418           2           1           1
26      202183  1700000002965419           2           1           1
27      202183  1700000002965420           2           1           1
28      202183  1700000002965421           2           1           1
29      202183  1700000002965422           2           1           1
30      202183  1700000002965423           2           1           1
31      202183  1700000002965424           3           1           2
36      290451          -1125324           2           0           2
37      290451  1700000005502561           2           0           2
38      290451  1700000005502564           2           0           2
39      383032          -1457973           2           1           1
40      383032          -1214607           2           1           1
41      383032  1700000005116290           2           1           1
42      383032  1700000005116291           2           1           1
43      383032  1700000005116292           2           1           1
44      383032  1700000005116293           2           1           1
45      383032  1700000005116294           2           1           1
46      383032  1700000005116296           2           1           1
47      383032  1700000005116297           2           1           1
48      383032  1700000005116298           2           1           1
49      383032  1700000005116299           2           1           1
50      383032  1700000005116300           2           1           1
51      625002  1700000005265011           2           1           1
52      625002  1700000005265012           2           1           1
53      625002  1700000005265013           2           1           1
54      625002  1700000005265014           2           1           1
55      625002  1700000005265015           2           1           1
56      638945  1700000006371748           3           1           2
57      638945  1700000006371749           3           1           2
58      638945  1700000006371750           3           1           2
59     1333614           5481257           3           1           2
60     1333614           5481258           3           1           2
61     1333614           5481276           2           1           1
62     1333614  1700000002265861           2           1           1
64     1368318          -1467309           2           1           1
65     1368318          -1467277           3           1           2
66     1368318          -1467276           3           1           2
67     1368318          -1467274           3           1           2

================ AID COMBINATIONS ================
    SECUENCIAL        REC_CODIGO            AIDS                                       DESCRIPTIONS
0        25519  1700000004453719       [18, 510]  [Ayuda básica a la renta para la sostenibilida...
1        25519  1700000004453720       [18, 510]  [Ayuda básica a la renta para la sostenibilida...
2        25519  1700000004453721       [18, 510]  [Ayuda básica a la renta para la sostenibilida...
3        25519  1700000004453722       [18, 510]  [Ayuda básica a la renta para la sostenibilida...
4        25519  1700000004453723       [18, 510]  [Ayuda básica a la renta para la sostenibilida...
5        25519  1700000004453724       [18, 510]  [Ayuda básica a la renta para la sostenibilida...
6        52429  1700000002756540       [18, 509]  [Ayuda básica a la renta para la sostenibilida...
7        52429  1700000002756541       [18, 509]  [Ayuda básica a la renta para la sostenibilida...
8        52429  1700000002756542            [18]  [Ayuda básica a la renta para la sostenibilida...
9        52429  1700000002756543            [18]  [Ayuda básica a la renta para la sostenibilida...
10       52429  1700000002756544            [18]  [Ayuda básica a la renta para la sostenibilida...
11       52429  1700000002756545            [18]  [Ayuda básica a la renta para la sostenibilida...
12       52429  1700000002756546            [18]  [Ayuda básica a la renta para la sostenibilida...
13       52429  1700000002756547            [18]  [Ayuda básica a la renta para la sostenibilida...
14       52429  1700000002756548            [18]  [Ayuda básica a la renta para la sostenibilida...
15       52429  1700000002756549       [18, 509]  [Ayuda básica a la renta para la sostenibilida...
16       52429  1700000002756550            [18]  [Ayuda básica a la renta para la sostenibilida...
17       52429  1700000002756551            [18]  [Ayuda básica a la renta para la sostenibilida...
18       52429  1700000002756552            [18]  [Ayuda básica a la renta para la sostenibilida...
19      129074  1700000002801751            [18]  [Ayuda básica a la renta para la sostenibilida...
20      129074  1700000002801752            [18]  [Ayuda básica a la renta para la sostenibilida...
21      129074  1700000002801753            [18]  [Ayuda básica a la renta para la sostenibilida...
22      133204  1700000003084002       [18, 215]  [Ayuda al olivar con dificultades específicas ...
23      202183  1700000002965416  [18, 215, 510]  [Ayuda al olivar con dificultades específicas ...
24      202183  1700000002965417  [18, 215, 510]  [Ayuda al olivar con dificultades específicas ...
25      202183  1700000002965418       [18, 510]  [Ayuda básica a la renta para la sostenibilida...
26      202183  1700000002965419       [18, 510]  [Ayuda básica a la renta para la sostenibilida...
27      202183  1700000002965420       [18, 510]  [Ayuda básica a la renta para la sostenibilida...
28      202183  1700000002965421       [18, 510]  [Ayuda básica a la renta para la sostenibilida...
29      202183  1700000002965422       [18, 510]  [Ayuda básica a la renta para la sostenibilida...
30      202183  1700000002965423       [18, 510]  [Ayuda básica a la renta para la sostenibilida...
31      202183  1700000002965424  [18, 215, 510]  [Ayuda al olivar con dificultades específicas ...
32      255217  1700000002796204            [18]  [Ayuda básica a la renta para la sostenibilida...
33      255217  1700000002796206            [18]  [Ayuda básica a la renta para la sostenibilida...
34      255217  1700000002796207            [18]  [Ayuda básica a la renta para la sostenibilida...
35      255217  1700000002796208            [18]  [Ayuda básica a la renta para la sostenibilida...
36      290451          -1125324       [18, 214]  [Ayuda a la producción tradicional de uva pasa...
37      290451  1700000005502561       [18, 214]  [Ayuda a la producción tradicional de uva pasa...
38      290451  1700000005502564       [18, 214]  [Ayuda a la producción tradicional de uva pasa...
39      383032          -1457973       [18, 509]  [Ayuda básica a la renta para la sostenibilida...
40      383032          -1214607       [18, 509]  [Ayuda básica a la renta para la sostenibilida...
41      383032  1700000005116290       [18, 509]  [Ayuda básica a la renta para la sostenibilida...
42      383032  1700000005116291       [18, 509]  [Ayuda básica a la renta para la sostenibilida...
43      383032  1700000005116292       [18, 509]  [Ayuda básica a la renta para la sostenibilida...
44      383032  1700000005116293       [18, 509]  [Ayuda básica a la renta para la sostenibilida...
45      383032  1700000005116294       [18, 509]  [Ayuda básica a la renta para la sostenibilida...
46      383032  1700000005116296       [18, 509]  [Ayuda básica a la renta para la sostenibilida...
47      383032  1700000005116297       [18, 510]  [Ayuda básica a la renta para la sostenibilida...
48      383032  1700000005116298       [18, 510]  [Ayuda básica a la renta para la sostenibilida...
49      383032  1700000005116299       [18, 510]  [Ayuda básica a la renta para la sostenibilida...
```