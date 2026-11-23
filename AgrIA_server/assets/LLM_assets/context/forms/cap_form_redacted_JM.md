# Formulario: Solicitud Única (Junta de Andalucía)

Este documento sirve como referencia contextual y estructurada para guiar a la persona usuaria en la cumplimentación de la **Solicitud Única de Ayudas PAC**.

---

## 1. Datos Generales

### Cabecera e Identificación
* **Organismo:** Junta de Andalucía – Consejería de Agricultura, Pesca, Agua y Desarrollo Rural.
* **Códigos de procedimientos:** 8318, 7058, 25231, 25232.
* **`numero_inscripcion`**: Nº de inscripción en el registro (Ej.: `005236/1`).
* **`numero_solicitud`**: Número único asignado a la solicitud.
* **`numero_expediente`**: Identificador del expediente administrativo.
* **`comunidad_autonoma`**: Comunidad Autónoma (Por defecto: `Andalucía`).
* **`provincia`**: Provincia de presentación.
* **`fecha_registro`**: Fecha oficial de entrada en el registro.
* **`num_exp_campana_anterior`**: Número de expediente de la campaña previa.
* **`cod_explotacion`**: Código REGA/REA de la explotación agraria.

---

### Datos Personales del Solicitante / Notificación Electrónica
* **`cif_nif`**: NIF o CIF del titular.
* **`nombre_razon_social`**: Nombre o razón social completa.
* **`primer_apellido`**: Primer apellido (si aplica).
* **`segundo_apellido`**: Segundo apellido (si aplica).
* **`f_nacimiento`**: Fecha de nacimiento (`DD/MM/AAAA`).
* **`genero`**: Género del solicitante.
* **`estado_civil`**: Estado civil (Ej.: `Casado/a`).
* **`regimen_matrimonial`**: Régimen económico matrimonial.
* **`telefono`**: Teléfono fijo de contacto.
* **`movil`**: Teléfono móvil principal.
* **`email`**: Correo electrónico de notificación.

#### Comunicación Vía SMS / Email
* **`autorizacion_sms`** *(Marcado: Sí / `true`)*: Autorización a la Administración para enviar información mediante SMS al teléfono consignado.
* **`autorizacion_email`** *(Marcado: Sí / `true`)*: Autorización a la Administración para enviar información mediante correo electrónico.

---

### Titularidad Compartida y Cónyuge
* **`titularidad_compartida`** *(Marcado: No / `false`)*: Indica si la explotación está inscrita bajo el régimen de titularidad compartida.
* **Cónyuge:**
  * **`cif_nif`**: NIF/CIF del cónyuge.
  * **`nombre`**: Nombre del cónyuge.
  * **`primer_apellido`**: Primer apellido.
  * **`segundo_apellido`**: Segundo apellido.
  * **`f_nacimiento`**: Fecha de nacimiento.
  * **`genero`**: Género.
  * **`regimen_matrimonial`**: Régimen económico matrimonial.

---

### Representante Legal
* **`cif_nif`**: NIF del representante.
* **`nombre`**: Nombre del representante.
* **`primer_apellido`**: Primer apellido.
* **`segundo_apellido`**: Segundo apellido.
* **`f_nacimiento`**: Fecha de nacimiento.
* **`genero`**: Género.
* **`movil`**: Teléfono móvil del representante.
* **`email`**: Correo electrónico del representante.

---

### Dirección de Notificación y Residencia
* **`tipo_via`**: Tipo de vía (Calle, Avenida, Plaza, etc.).
* **`nombre_via`**: Nombre de la vía pública.
* **`numero`**: Número del inmueble.
* **`bloque` / `portal` / `escalera` / `planta` / `puerta`**: Datos de detalle de la dirección.
* **`codigo_postal`**: Código postal.
* **`municipio` / `provincia` / `localidad`**: Datos territoriales de notificación.
* **`domicilio_igual_notificacion`** *(Marcado: Sí / `true`)*: Confirma que la residencia habitual coincide con el domicilio de notificación.

---

## 2. Datos Bancarios y Datos Fiscales

### Datos Bancarios
* **`iban`**: Código IBAN de la cuenta bancaria para el cobro de subvenciones.
* **`entidad`**: Código de la entidad bancaria.
* **`sucursal`**: Código de la sucursal.
* **`dc`**: Dígitos de control.

---

### Datos Fiscales del Solicitante
* **`incorporacion_actividad_agraria`** *(Marcado: No / `false`)*: Marcar si el solicitante se incorpora por primera vez a la actividad agraria.
* **`forma_juridica`**: Forma jurídica del titular (Ej.: `Persona física`).
* **`ingresos_agrarios_2023` / `2022` / `2021`**: Cuantía de ingresos agrarios percibidos en dichos ejercicios fiscalmente declarados.
* **`ingresos_totales_2023` / `2022` / `2021`**: Ingresos totales percibidos en dichos ejercicios.
* **`cif_nif_integradora_ganado`**: CIF/NIF de la empresa integradora si opera bajo régimen de integración ganadera.
* **`costes_laborales_pagados`**: Importe de los costes laborales reales pagados el año anterior.

---

## 3. Líneas de Ayuda Solicitadas (`SOLICITA`)

### Pagos Directos a la Agricultura y Ganadería
* **Ayuda básica a la renta para la sostenibilidad (ABRS)** *(Marcado: Sí / `true`)*.
* **Ayuda complementaria redistributiva** *(Marcado: Sí / `true`)*.
* **`ayuda_jovenes_agricultores`** *(Marcado: No / `false`)*: Ayuda complementaria para jóvenes agricultores y agricultoras.

#### Ayudas Asociadas a Cultivos *(Todas no marcadas / `false` por defecto)*
* `proteinas_origen_vegetal`: Producción sostenible de proteínas de origen vegetal.
* `arroz`: Producción sostenible de arroz.
* `remolacha_azucarera`: Producción sostenible de remolacha azucarera.
* `tomate_transformacion`: Producción sostenible de tomate para transformación.
* `frutos_secos`: Productores de frutos secos en áreas con riesgo de desertificación.
* `uva_pasa`: Producción tradicional de uva pasa.
* `olivar_dificultades`: Olivar con dificultades específicas y alto valor medioambiental.
* `pago_especifico_algodon`: Pago específico al cultivo del algodón.

#### Ayudas Asociadas a la Ganadería *(Todas no marcadas / `false` por defecto)*
* Ganaderos extensivos de vacuno de carne.
* Engorde de terneros en la explotación de nacimiento.
* Engorde sostenible de terneros.
* Producción sostenible de leche de vaca.
* Ganaderos extensivos y semiextensivos de ovino y caprino de carne.
* Producción sostenible de leche de oveja y cabra.
* Ovino y caprino sin pastos a su disposición que pastorean rastrojeras y restos hortícolas.

---

### Eco Regímenes
* **`agricultura_carbono_pastos`** *(No marcado / `false`)*: Pastoreo extensivo, siega sostenible o islas de biodiversidad.
* **`agricultura_carbono_tierras_cultivo`** *(No marcado / `false`)*: Rotación de cultivos mejorantes o siembra directa.
* **`agricultura_carbono_cultivos_lenosos`** *(Marcado: Sí / `true`)*:
  * **`cubierta_vegetal_espontanea_sembrada`** *(Marcado: Sí / `true`)*.
  * `cubierta_inerte_restos_poda` *(No marcado / `false`)*.
* **`agroecologia_espacios_biodiversidad`** *(No marcado / `false`)*.

---

## 4. Derechos de Ayuda Básica (`DATOS DE DERECHOS`)

* **`solicita_todos_los_derechos`** *(Marcado: Sí / `true`)*: Solicita la activación de todos los derechos de los que sea titular.

| `id_derecho` | `origen` | `%_derecho` | `zona_reg` | `valor_nominal` | `solicita` | `tipo_derecho` | `valor_real` |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| DAB000033838240 | Conversión | 100,00 | 13 | 223,80 | | | |
| DAB000033838241 | Conversión | 100,00 | 13 | 223,80 | | | |
| DAB000033838238 | Conversión | 100,00 | 13 | 223,80 | M | | |
| DAB000033838244 | Conversión | 1,00 | 13 | 223,80 | | | |
| DAB000033838234 | Conversión | 100,00 | 13 | 223,80 | | | |
| DAB000033838235 | Conversión | 100,00 | 13 | 223,80 | | | |
| DAB000033838246 | Conversión | 68,00 | 13 | 236,11 | | | |

*(Se enumeran todos los derechos según el cuadro del impreso oficial)*.

---

## 5. Declaraciones Específicas y Compromisos

### Venta de Producciones Agrícolas
* `venta_directa_o_canal_corto` *(No marcado / `false`)*: Venta directa al consumidor final o canal corto.
* `no_venta_directa` *(No marcado / `false`)*.
* **`destino_consumo_propio_o_ganado`** *(Marcado: Sí / `true`)*: Las producciones agrícolas de la explotación se destinan íntegramente al consumo doméstico privado o al ganado.

### Compromisos Ambientales y Buenas Prácticas
* **`fitosanitarios_sobre_cubiertas`** *(Marcado: Sí / `true`)*: Afirma no utilizar productos fitosanitarios sobre las cubiertas vegetales/inertes.

---

## 6. Autorizaciones (`AUTORIZA A`)

| Tipo de Autorización | Autoriza | Se opone |
| :--- | :---: | :---: |
| Acceder a datos de la AEAT para verificar la condición de agricultor activo | **X** | |
| Recabar de la Seguridad Social la declaración de costes laborales pagados | **X** | |
| Consulta de afiliación, alta y vida laboral en la TGSS | **X** | |
| Consulta de datos de identidad en la Dirección General de la Policía | **X** | |
| Entrada de controladores autorizados en la explotación declarada | **X** | |
| Consulta de datos catastrales a través de la Oficina Virtual del Catastro (OVC) | **X** | |
| Consulta de datos de identidad a través del Sistema GIRO de Hacienda | **X** | |
| Ceder datos a la entidad colaboradora / reconocida donde tramita la solicitud | **X** | |
| Verificación de la titularidad de cuentas bancarias en el sistema GIRO | **X** | |

*(Fuente de opciones tomadas de la sección oficial de Autorizaciones)*.

---

## 7. Declaración Responsable (Agricultor Activo)

* **`actividad_excluida_rd`**: Realiza alguna actividad excluida contemplada en la normativa *(Opción seleccionada: `NO`)*.
* `quiere_ser_considerado_agricultor_activo` *(No marcado / `false`)*.
* `cumplimiento_25_porciento_ingresos_agrarios` *(No marcado / `false`)*.

---

## 8. Responsabilidad Jurídica y Datos de la Explotación

* **`responsabilidad_juridica`**: Una persona física.
* **`titular_es_gerente`**: Sí.
* **`gerente_comparte_responsabilidad_familiar`**: No.
* **`porcentaje_jornadas_trabajo`**: `0% - <25%`.
* **`ano_inicio_gerente`**: `2010`.
* **`formacion_agraria_gerente`**: Sólo experiencia práctica agraria.
* **`cursos_perfeccionamiento_12_meses`**: No.

---

## 9. Datos de Recintos y Parcelas Agrícolas (`DATOS DE RECINTOS`)

| Prov (`cod_provincia`) | Mun (`cod_municipio`) | Pol (`cod_poligono`) | Par (`cod_parcela`) | Rec (`cod_recinto`) | Uso SIGPAC | Producto | Variedad | Sup. Declarada (ha) | Regimen / Riego |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 29 | 62 | 2 | 6 | 4 | FY | AGUACATE | HASS | 1,17 | Secano |
| 14 | 48 | 4 | 274 | 1 | OV | OLIVO | HOJIBLANCA | 0,34 | Secano |
| 29 | 15 | 4 | 27 | 1 | OV | OLIVO | HOJIBLANCA | 0,75 | Secano |
| 29 | 15 | 13 | 4 | 1 | OV | OLIVO | HOJIBLANCA | 9,22 | Secano |
| 29 | 15 | 13 | 44 | 3 | OV | OLIVO | HOJIBLANCA | 0,09 | Secano |

*(Recintos consolidados según las tablas de las páginas 11 y 12 del impreso)*.

---

## 10. Documentos Adjuntos (`CHECKLIST`)

*(Todos las casillas del listado de la documentación adjunta se encuentran sin marcar / `false` en la solicitud física de origen)*.
