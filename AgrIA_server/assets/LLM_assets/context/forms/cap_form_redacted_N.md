# Formulario: Solicitud Única (Junta de Andalucía - Formulario N)

Este documento contiene la estructura e información de la **Solicitud Única de Ayudas PAC** correspondiente a la variante N.

---

## 1. Datos Generales

### Cabecera e Identificación
* **Organismo:** Junta de Andalucía – Consejería de Agricultura, Pesca, Agua y Desarrollo Rural.
* **Códigos de procedimientos:** 8318, 7058, 25231, 25232.
* **`numero_inscripcion`**: `005236/1`.
* **`numero_solicitud`**: Identificador asignado a la solicitud.
* **`numero_expediente`**: Código de expediente administrativo.
* **`comunidad_autonoma`**: `Andalucía`.
* **`provincia`**: `Málaga`.

---

### Datos Personales del Solicitante / Notificación Electrónica
* **`cif_nif`**: CIF/NIF del solicitante.
* **`nombre_razon_social`**: Nombre / Razón Social.
* **`estado_civil`**: `Casado/a`.
* **`regimen_matrimonial`**: `Sociedad de gananciales`.

#### Comunicación Vía SMS / Email
* **`autorizacion_sms`** *(Marcado: Sí / `true`)*: Autorización a la Administración para el envío de información mediante SMS.
* **`autorizacion_email`** *(Marcado: Sí / `true`)*: Autorización a la Administración para el envío de información mediante correo electrónico.

---

### Titularidad Compartida y Cónyuge
* **`titularidad_compartida`** *(Marcado: No / `false`)*: Explotación no registrada en régimen de titularidad compartida.
* **Cónyuge:**
  * **`regimen_matrimonial`**: `Sociedad de gananciales`.

---

### Dirección de Notificación y Residencia
* **`numero`**: `18`.
* **`domicilio_igual_notificacion`** *(Marcado: Sí / `true`)*: El domicilio de residencia es idéntico al de notificación.

---

## 2. Datos Fiscales y Financieros

* **`incorporacion_actividad_agraria`** *(Marcado: No / `false`)*: No se incorpora por primera vez a la actividad agraria.
* **`forma_juridica`**: `Persona física`.

---

## 3. Líneas de Ayuda Solicitadas (`SOLICITA`)

### Pagos Directos y Eco Regímenes
* **Ayuda básica a la renta para la sostenibilidad (ABRS)** *(Marcado: Sí / `true`)*.
* **Ayuda complementaria redistributiva** *(Marcado: Sí / `true`)*.
* **Eco Régimen:**
  * **`agricultura_carbono_cultivos_lenosos`** *(Marcado: Sí / `true`)*.
  * **`cubierta_vegetal_espontanea_sembrada`** *(Marcado: Sí / `true`)*.

---

## 4. Derechos de Ayuda Básica (`DATOS DE DERECHOS`)

* **`solicita_todos_los_derechos`** *(Marcado: Sí / `true`)*: Solicita todos los derechos de los que sea titular en la campaña.

| `id_derecho` | `origen` | `%_derecho` | `zona_reg` | `valor_nominal` | `solicita` |
| :--- | :--- | :---: | :---: | :---: | :---: |
| DAB0000305200 77 | Conversión | 100,00 | 13 | 245,09 | |
| DAB0000305200 78 | Conversión | 56,00 | 13 | 245,09 | |

*(Información según el cuadro de derechos del impreso N)*.

---

## 5. Declaraciones y Autorizaciones

* **`destino_consumo_propio_o_ganado`** *(Marcado: Sí / `true`)*: Las producciones agrícolas se destinan íntegramente al consumo doméstico o ganado propio.
* **`fitosanitarios_sobre_cubiertas`** *(Marcado: Sí / `true`)*: Declara no utilizar fitosanitarios sobre las cubiertas vegetales.
* **`autorizaciones_aeat_tgss_dgp_ovc`**: Todas autorizadas afirmativamente *(Marcado: Autoriza)*.

---

## 6. Datos de Responsabilidad Jurídica de la Explotación

* **`responsabilidad_juridica`**: Una persona física.
* **`titular_es_gerente`**: Sí.
* **`gerente_comparte_responsabilidad`**: No.
* **`porcentaje_jornadas_trabajo`**: `0% - <25%`.
* **`ano_inicio_gerente`**: `2010`.
* **`formacion_agraria_gerente`**: Sólo experiencia práctica agraria.
* **`cursos_perfeccionamiento_12_meses`**: No.

---

## 7. Datos de Recintos y Parcelas Agrícolas (`DATOS DE RECINTOS`)

| Prov (`cod_provincia`) | Mun (`cod_municipio`) | Pol (`cod_poligono`) | Par (`cod_parcela`) | Rec (`cod_recinto`) | Uso SIGPAC | Producto | Variedad | Sup. Declarada (ha) | Regimen |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 14 | 48 | 3 | 167 | 3 | OV | OLIVO | HOJIBLANCA | 1,76 | Secano |

* **Detalles adicionales del recinto:**
  * **Sistema de producción olivar:** Tradicional.
  * **Año de plantación:** `<2010`.
  * **Destino de restos vegetales:** Incorporación al suelo o distribución en parcela (100%).

---

## 8. Documentos Adjuntos (`CHECKLIST`)

*(Todas las casillas de documentación adjunta figuran sin marcar / `false`)*
