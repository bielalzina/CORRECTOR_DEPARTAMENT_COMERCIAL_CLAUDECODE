# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

# App de Correcció "Empresa a l'Aula"

## Descripció del projecte

Eina de suport per a dos professors de Formació Professional (branca d'Administració) que han de corregir setmanalment les operacions comercials dels seus alumnes dins el projecte simulat "Empresa a l'Aula".

L'app té dues funcions principals:
1. **Recollida de llistats**: els alumnes pugen els seus fitxers xlsx exportats des d'ODOO. L'app els valida formalment i els emmagatzema identificant alumne, grup, tasca i tipus de llistat.
2. **Correcció automàtica**: l'app fa tot el procés de correcció sense intervenció manual del professor. El professor supervisa els resultats i pot validar o modificar casos ambigus que l'app li presenti.

---

## Professors i grups

| Professor | Correu | Grup |
|---|---|---|
| Margalida Font | mfont@cifpjoantaix.cat | ADG21 |
| Gabriel Alzina | bielalzina@cifpjoantaix.cat | ADG32 |

Les correccions dels dos grups són completament independents. Cada professor accedeix únicament a les dades del seu grup.

---

## Alumnes i empreses

La llista d'alumnes és **orientativa** (curs 25-26). L'app s'implantarà el curs **26-27** amb alumnes nous. Per tant:
- La llista d'alumnes ha de ser **gestionable dinàmicament** (alta, baixa, modificació) des de l'app, sense tocar el codi.
- Cada alumne pertany a un grup (ADG21 o ADG32).
- L'expedient de l'alumne són els 4 primers dígits del correu electrònic i també apareix a la raó social de l'empresa.

### Alumnes actuals (orientatius, curs 25-26, grup ADG32)

| Llinatges, Nom | Correu electrònic | Expedient | Raó Social | CIF |
|---|---|---|---|---|
| SACARES MORAGUES, NADAL | 5796.nsacares@cifpjoantaix.cat | 5796 | ADG32 5796 NSACARES SL | B00214783 |
| MORENO VIVES, SERGI XAVIER | 6265.smoreno@a.cifpjoantaix.cat | 6265 | ADG32 6265 SMORENO SL | B00324764 |
| NAVARRO QUETGLAS, MARGARITA | 6320.mnavarro@a.cifpjoantaix.cat | 6320 | ADG32 6320 MNAVARRO SL | B00325043 |
| AANANOU AANANOU, SANAE | 6352.saananou@a.cifpjoantaix.cat | 6352 | ADG32 6352 SAANANOU SL | B00324889 |
| AANANOU AANANOU, WAFA | 6356.waananou@a.cifpjoantaix.cat | 6356 | ADG32 6356 WAANANOU SL | B00324715 |
| MORAGUES MARIN, JOAN MANEL | 6366.jmoragues@a.cifpjoantaix.cat | 6366 | ADG32 6366 JMORAGUES SL | B00324855 |
| PIZA BIMBELA, LUCIA | 6368.lpiza@a.cifpjoantaix.cat | 6368 | ADG32 6368 LPIZA SL | B00324798 |
| MASTRANGELO, VERONA | 6369.vmastrangelo@a.cifpjoantaix.cat | 6369 | ADG32 6369 VMASTRANGELO SL | B00324723 |
| ANANOU EL HANNATI, NAWAL | 6427.nananou@a.cifpjoantaix.cat | 6427 | ADG32 6427 NANANOU SL | B00324749 |
| BOUBAL CHOUAY, ASIA | 6428.aboubal@a.cifpjoantaix.cat | 6428 | ADG32 6428 ABOUBAL SL | B00324772 |
| ZOUGGAGHI SALHI, GHIZLANE | 6431.gzouggaghi@a.cifpjoantaix.cat | 6431 | ADG32 6431 GZOUGGAGHI SL | B00325027 |
| CHANTAH KASMI, WISSAM | 6467.wchantah@a.cifpjoantaix.cat | 6467 | ADG32 6467 WCHANTAH SL | B00324707 |
| BAUZÁ MARCH, CATALINA | 6478.cbauza@a.cifpjoantaix.cat | 6478 | ADG32 6478 CBAUZA SL | B00325050 |
| FORNÉS FUENTES, NEUS | 6702.nfornes@a.cifpjoantaix.cat | 6702 | ADG32 6702 NFORNES SL | B00214916 |
| SUIYHI BACHRI, NABIL | 6706.nsuiyhi@a.cifpjoantaix.cat | 6706 | ADG32 6706 NSUIYHI SL | B00214775 |
| OUAZINE LABBOUA, M'HAMED | 6707.mouazine@a.cifpjoantaix.cat | 6707 | ADG32 6707 MOUAZINE SL | B00324780 |
| CARBONELL PIERAS, BERNAT | 6713.bcarbonell@a.cifpjoantaix.cat | 6713 | ADG32 6713 BCARBONELL SL | B00324830 |
| ABOLAFIO DIAZ, LORENA | 6734.labolafio@a.cifpjoantaix.cat | 6734 | ADG32 6734 LABOLAFIO SL | B00324756 |
| LLADÓ POL, ESPERANÇA | 6746.ellado@a.cifpjoantaix.cat | 6746 | ADG32 6746 ELLADO SL | B00214791 |
| GARCIA DOMINGO, JAVIER | 6777.jgarcia@a.cifpjoantaix.cat | 6777 | ADG32 6777 JGARCIA SL | B00214700 |
| CAPÓ CRESPÍ, PERE | 6792.pcapo@a.cifpjoantaix.cat | 6792 | ADG32 6792 PCAPO SL | B00214882 |
| TRAMULLAS TORRES, TOMEU | 6844.ttramullas@a.cifpjoantaix.cat | 6844 | ADG32 6844 TTRAMULLAS SL | B00325035 |

### Alumnes de prova

Cal habilitar 1 o 2 alumnes de prova (un per grup) per verificar que la correcció automàtica funciona correctament abans de posar l'app en producció.

---

## Autenticació i control d'accés

- Els alumnes s'autentiquen amb el seu correu electrònic del workspace Google (`@cifpjoantaix.cat` o `@a.cifpjoantaix.cat`).
- Tots els alumnes pertanyen al grup de seguretat: `simulaempresa@cifpjoantaix.cat`.
- Un alumne **no pot pujar llistats en nom d'un altre alumne**.
- Els professors tenen accés complet a les dades del seu grup.
- Els professors **no accedeixen a les dades de l'altre grup**.

---

## Numeració de tasques

Les tasques setmanals segueixen aquesta nomenclatura:
- Tasca setmana 01: `02.01`
- Tasca setmana 02: `02.02`
- ...
- Tasca darrera setmana: `02.99`

(No totes les setmanes tindran tasca, però la numeració ha d'admetre fins a 02.99)

---

## Nomenclatura dels fitxers

Un cop validat, l'app anomena el fitxer seguint aquest patró:
```
[Núm_tasca]-[Expedient_alumne]-[Nom_llistat]
Exemple: 02.02-5796-01_COMANDES_COMPRES.xlsx
```

---

## Termini d'entrega

- El termini és cada **divendres a les 24:00**.
- L'app accepta llistats fora de termini però ho **notifica explícitament** a l'alumne.
- El professor es reserva el dret de corregir o no les tasques fora de termini.
- Es permet l'**entrega parcial**: si l'alumne lliura menys de 8 llistats, es corregiran els que hagi lliurat, amb penalització pels que falten.

---

## Flux de recollida de llistats (part de l'alumne)

1. L'alumne s'autentica amb el seu correu Google.
2. Selecciona el **grup** al qual pertany (ADG21 o ADG32).
3. Selecciona el **número de tasca** (02.01 a 02.99).
4. Puja els fitxers xlsx (un per cada llistat, fins a 8).
5. L'app valida cada fitxer (Pas 1 — validació d'estructura).
6. Si el fitxer és vàlid: l'app l'accepta, afegeix les columnes `Expedient_alumne` i `Num_ordre_tasca`, i el guarda amb la nomenclatura correcta.
7. Si el fitxer no és vàlid: l'app informa l'alumne dels errors concrets i no l'accepta fins que es corregeixi.

---

## Flux de correcció automàtica (part de l'app)

Un cop finalitzat el termini d'entrega, **l'app fa tot el procés de forma automàtica**:

1. Agrupa tots els llistats del mateix tipus de tots els alumnes d'un grup.
2. Afegeix les columnes d'identificació (`Expedient_alumne`, `Num_ordre_tasca`).
3. Executa la correcció per blocs: **COMPRES** (01, 02, 03) → **VENDES** (04, 05, 06) → **MAGATZEM** (07, 08).
4. Detecta errors, els classifica per gravetat i calcula la nota de cada alumne.
5. En cas de situacions ambigües (ex: número d'emissió incorrecte però inferable), **presenta el cas al professor** per confirmar abans de continuar.
6. Genera l'informe de correcció per alumne i el resum del grup.
7. El professor revisa i pot exportar els resultats.

---

## Estructura dels 8 llistats (capçaleres obligatòries)

Els alumnes exporten els llistats directament des d'ODOO en format `.xlsx`. Les capçaleres han de coincidir **exactament** (majúscules, accents, espais).

### 01_COMANDES_COMPRES
`Referencia del pedido` · `Fecha límite del pedido` · `Referencia de proveedor` · `Data comanda` · `Proveedor` · `Base imponible` · `Total` · `Estado` · `Estado de facturación`

### 02_RECEPCIONS (Albarans de compra)
`Referencia` · `Fecha de traslado` · `Numero albarà` · `Data albarà` · `Contacto` · `Documento de origen` · `Pedidos de compra/Total` · `Estado`

### 03_FACTURES_COMPRA
`Número` · `Nombre de la empresa a mostrar en la factura` · `Referencia` · `Fecha de factura` · `Fecha de vencimiento` · `Origen` · `Base imponible en la moneda firmada` · `Impuesto firmado` · `Total con signo en moneda` · `Estado en pago`

### 04_COMANDES_VENDES
`Referencia del pedido` · `Fecha de creación` · `Data comanda` · `Numero comanda` · `Cliente` · `Base imponible` · `Impuestos` · `Total` · `Estado` · `Estado de la factura`

### 05_ENTREGUES (Albarans de venda)
`Referencia` · `Fecha de traslado` · `Contacto` · `Documento de origen` · `Pedido de venta/Total` · `Estado`

### 06_FACTURES_VENDA
`Número` · `Fecha de factura` · `Fecha de vencimiento` · `Nombre de la empresa a mostrar en la factura` · `Origen` · `Base imponible en la moneda firmada` · `Impuesto firmado` · `Total con signo en moneda` · `Estado en pago` · `Enviado`

### 07_STOCK
`Nombre para mostrar` · `Coste promedio` · `Valor total` · `Cantidad real` · `Cantidad disponible` · `Entrante` · `Saliente`

### 08_HISTORIAL_ENTRADES_SORTIDES
`Producto` · `Fecha` · `Referencia` · `Desde` · `A` · `Cantidad` · `Estado`

---

## Validació d'estructura (Pas 1)

Per a cada fitxer pujat, verificar:
1. Totes les capçaleres obligatòries presents i escrites exactament igual.
2. Cap columna obligatòria completament buida.
3. Cap fila intermèdia buida.
4. Mínim de files esperades: 2 compres, 3 vendes.
5. **Detecció d'esborranys**: alertar si `Estado` conté "Borrador" o "Presupuesto".

Si no passa la validació → informar l'alumne dels errors concrets i **no acceptar el fitxer**.

---

## Validació de contingut (Pas 2) — COMPRES

### Dades de referència: DADES_COMPRES_REALS

| Camp | Descripció |
|------|-----------|
| `R_EMPRESA_C` | Raó social de l'empresa de l'alumne |
| `R_PROVEEDOR_C` | Proveïdor (ALUBIX SL o ROCALLA SA) |
| `R_FECHA_EMISION_C` | Data d'emissió (comanda i albarà: disponibles el mateix dia; factura: disponible l'endemà) |
| `R_NUMERO_CP` | Número identificatiu de la comanda de compra |
| `R_NUMERO_CA` | Número identificatiu de l'albarà de compra |
| `R_NUMERO_CF` | Número identificatiu de la factura de compra |
| `R_IMPORTE_C` | Import total (amb impostos) |
| `R_DATA_ENTREGA_TASCA` | Data de lliurament del llistat 03_FACTURES_COMPRA |

### Traçabilitat compra

| Llistat | Camp de traçabilitat |
|---------|---------------------|
| 01_COMANDES_COMPRES | `Referencia del pedido` |
| 02_RECEPCIONS | `Documento de origen` |
| 03_FACTURES_COMPRA | `Origen` |

Per cada operació: 1 comanda → 1 albarà → 1 factura.

### Correcció 01_COMANDES_COMPRES

| Camp alumne | Referència | Comprovació |
|---|---|---|
| `Referencia de proveedor` | `R_NUMERO_CP` | Han de coincidir (1 a 1) |
| `Data comanda` | `R_FECHA_EMISION_C` | Han de coincidir |
| `Proveedor` | `R_PROVEEDOR_C` | Han de coincidir |
| `Total` | `R_IMPORTE_C` | Han de coincidir |
| `Estado` | — | Ha de ser = "Pedido de compra" |
| `Estado de facturación` | `R_DATA_ENTREGA_TASCA` vs `R_FECHA_EMISION_C` | Si entrega > emissió → "Totalmente facturado"; si entrega = emissió → "Facturas en espera" |
| `Fecha límite del pedido` | — | Ha de ser >= `Data comanda` |

Casuístiques: duplicats, operacions oblidades, número incorrecte (si es pot inferir sense ambigüitat → avisar professor, esperar confirmació, aplicar i deixar constància).

### Correcció 02_RECEPCIONS

| Camp alumne | Referència | Comprovació |
|---|---|---|
| `Numero albarà` | `R_NUMERO_CA` | Han de coincidir |
| `Data albarà` | `R_FECHA_EMISION_C` | Han de coincidir |
| `Contacto` | `R_PROVEEDOR_C` | Han de coincidir |
| `Pedidos de compra/Total` | `R_IMPORTE_C` | Han de coincidir |
| `Estado` | — | "Hecho" = correcte; "Listo" = no recepcionat (error); "Cancelado" = ignorar |
| `Fecha de traslado` | — | Ha de ser >= `Data albarà` |

### Correcció 03_FACTURES_COMPRA

⚠️ ODOO representa els imports de les factures de compra com a **negatius**. Cal convertir-los a positius per a la correcció.

| Camp alumne | Referència | Comprovació |
|---|---|---|
| `Nombre de la empresa a mostrar en la factura` | `R_PROVEEDOR_C` | Han de coincidir |
| `Referencia` | `R_NUMERO_CF` | Han de coincidir |
| `Fecha de factura` | `R_FECHA_EMISION_C` | Han de coincidir |
| `Fecha de vencimiento` | — | Ha de ser = `R_FECHA_EMISION_C` + 7 dies |
| `Total con signo en moneda` (en positiu) | `R_IMPORTE_C` | Han de coincidir |
| `Estado en pago` | — | Ha de ser = "Publicado" o "Pagada" |
| — | `R_DATA_ENTREGA_TASCA` | Si entrega = emissió → factura no disponible → **error greu** |

---

## Validació de contingut (Pas 2) — VENDES

### Context

- 3 comandes setmanals (dilluns, dimarts, dimecres) de BIGCORP SL i/o COMERCIAL CALCO SA (distribució aleatòria).
- L'alumne ha de tenir estoc suficient abans de generar l'albarà. Si no en té, ha de comprar primer.
- No es permeten albarans parcials ni estocs negatius.
- Termini: divendres de cada setmana.

### Mode de facturació (el professor l'indica a l'app cada setmana)

- **Individual**: 1 comanda → 1 albarà → 1 factura.
- **Recapitulativa**: 1 comanda → 1 albarà, factures agrupades per client (1 factura pot incloure 2 o 3 comandes).

### Dades de referència: DADES_VENDES_REALS

| Camp | Descripció |
|------|-----------|
| `R_EMPRESA_V` | Raó social de l'empresa de l'alumne |
| `R_FECHA_EMISION_VP` | Data d'emissió de la comanda |
| `R_NUMERO_VP` | Número identificatiu de la comanda (únic, autoincremental) |
| `R_CLIENTE_V` | Client (BIGCORP SL o COMERCIAL CALCO SA) |
| `R_IMPORTE_V` | Import total (amb impostos) |
| `R_FECHA_MAX_FACTURACION_V` | Data límit per facturar (divendres) |

### Traçabilitat venda

| Llistat | Camp de traçabilitat |
|---------|---------------------|
| 04_COMANDES_VENDES | `Referencia del pedido` |
| 05_ENTREGUES | `Documento de origen` |
| 06_FACTURES_VENDA | `Origen` (en recapitulativa: referències separades per comes) |

### Correcció 04_COMANDES_VENDES

| Camp alumne | Referència | Comprovació |
|---|---|---|
| `Data comanda` | `R_FECHA_EMISION_VP` | Han de coincidir |
| `Numero comanda` | `R_NUMERO_VP` | Han de coincidir (1 a 1) |
| `Cliente` | `R_CLIENTE_V` | Han de coincidir |
| `Total` | `R_IMPORTE_V` | Han de coincidir |
| `Estado` | — | Ha de ser = "Pedido de venta" |
| `Estado de la factura` | — | Ha de ser = "Completamente facturado" |
| `Fecha de creación` | — | Ha de ser <= `Fecha de traslado` (05) |

### Correcció 05_ENTREGUES

| Camp alumne | Referència | Comprovació |
|---|---|---|
| `Contacto` | `R_CLIENTE_V` | Han de coincidir |
| `Pedido de venta/Total` | `R_IMPORTE_V` | Han de coincidir |
| `Estado` | — | Ha de ser = "Hecho" |
| `Fecha de traslado` | — | >= `Fecha de creación` (04) i <= `Fecha de factura` (06) |

### Correcció 06_FACTURES_VENDA

| Camp alumne | Referència | Comprovació |
|---|---|---|
| `Nombre de la empresa a mostrar en la factura` | `R_CLIENTE_V` | Han de coincidir |
| `Total con signo en moneda` | `R_IMPORTE_V` | En recapitulativa: suma dels imports de les comandes incloses |
| `Fecha de factura` | `R_FECHA_MAX_FACTURACION_V` | Ha de ser <= divendres de la setmana |
| `Fecha de vencimiento` | — | Ha de ser = `Fecha de factura` + 7 dies |
| `Estado en pago` | — | Ha de ser = "Publicado" o "Pagada" |
| `Enviado` | — | Per regla general = "No enviado" |

Comprovació de seqüència de dates:
`Fecha de creación` (04) <= `Fecha de traslado` (05) <= `Fecha de factura` (06)

### Numeració de factures de venda

Format: `FV-1/[ANY]/[ORDRE]` (ex: `FV-1/2025/00001`)
- `FV-1`: per a BIGCORP SL i COMERCIAL CALCO SA
- `FV-2`: per a la resta de clients

Errors a detectar:
- Salt en la numeració (ex: falta el 00007) → error greu.
- Data d'una factura posterior a una factura amb número superior → error greu.

---

## Validació de contingut (Pas 2) — MAGATZEM

### Correcció 07_STOCK

| Comprovació | Detall |
|---|---|
| Valor total del magatzem | Suma de `Valor total` de tots els articles <= **1.000 €** |
| Estoc sense pendents | Per a cada article: `Cantidad real` = `Cantidad disponible` (implica `Entrante` = 0 i `Saliente` = 0) |

### Correcció 08_HISTORIAL_ENTRADES_SORTIDES

Objectiu: detectar estocs negatius en qualsevol moment.

Algorisme:
1. Ordenar per empresa → per producte → per `Fecha` (de més antic a més recent).
2. Determinar si cada operació és entrada (`A` = `MGZ01/Stock`) o sortida (`Desde` = `MGZ01/Stock`).
3. Assignar signe: entrada = positiu, sortida = negatiu.
4. Acumular `Cantidad` en una nova columna `Estoc`.
5. Si `Estoc` < 0 en algun moment → **error greu**: informar quina operació ho provoca i quan.
6. Només computar operacions amb `Estado` = "Hecho".

Output: resum per producte i per empresa (estoc sempre positiu, o estoc negatiu amb detall).

---

## Classificació d'errors i penalitzacions

| Prioritat | Tipus d'error | Gravetat | Penalització |
|-----------|--------------|----------|--------------|
| 1 | Operació que falta completament | Molt greu | -1 punt |
| 2 | Proveïdor o client incorrecte | Greu | -1 punt |
| 3 | Import incorrecte | Greu | -1 punt |
| 4 | Quantitat incorrecta | Greu | -1 punt |
| 5 | Factura registrada abans de tenir-la disponible | Greu | -1 punt |
| 6 | Estoc negatiu | Greu | -1 punt |
| 7 | Data incorrecta | Lleu | -0.5 punts |
| 8 | Número de document incorrecte | Lleu | -0.5 punts |

- **Nota base: 10 punts** · Nota mínima: 0
- Penalitzacions configurables pel professor des de l'app

---

## Output esperat

- Informe per alumne: errors, gravetat, penalitzacions i nota final
- Resum del grup: taula comparativa de notes
- Exportable a Excel i/o PDF

---

## Principis de desenvolupament

- **Correcció automàtica**: l'app fa la feina, el professor supervisa
- **Simplicitat**: interfície mínima i clara
- **Pas a pas**: l'usuari sap sempre on és i què ha de fer
- **Català**: tota la interfície i els informes en català
- **Codi mínim**: no afegir funcionalitats no demanades
- **No modificar originals**: mai tocar els fitxers dels alumnes
- **Robustesa**: gestionar fitxers mal formats o amb columnes desordenades
- **Gestió dinàmica d'alumnes**: la llista d'alumnes es pot actualitzar sense tocar el codi

---

## Stack tecnològic

**Decisió: Python + Streamlit** — app web accessible per xarxa local o Oracle Cloud VM (ARM A1, tier gratuït).

Dependències (`requirements.txt`):
- `streamlit>=1.32.0`
- `pandas>=2.0.0` / `openpyxl>=3.1.0`
- `fpdf2>=2.7.0` — exportació a PDF (fases posteriors)

### Comandes

```bash
pip install -r requirements.txt
streamlit run app.py
# Obre http://localhost:8501
# Per accés des d'altres equips de la xarxa: http://<IP_maquina>:8501
```

---

## Estat del desenvolupament

### ✅ Fase 1 — Completada

**Esquelet, autenticació i zona d'entregues.**

Fitxers creats i funcionals:

```
app.py                          # Router principal (session_state: role/user/grup/page/tasca_sel)
requirements.txt
data/
  alumnes.json                  # 22 alumnes ADG32 + 1 alumne de prova (camp "prova": true)
  config.json                   # Professors ADG21/ADG32 (password_hash SHA-256, buit = primer accés)
  tasques/                      # Creat dinàmicament quan el professor crea la primera tasca
    <num_tasca>/
      <grup>/
        config.json             # Configuració de la tasca (dates, mode_facturacio, activa)
        entregues/
          <expedient>/
            metadata.json       # Registre de cada llistat pujat (data, fora_termini, tipus)
            <fitxers>.xlsx      # Nomenclatura: 02.03-5796-01_COMANDES_COMPRES.xlsx
modules/
  auth.py                       # SHA-256, login professor, configuració inicial de contrasenya
  alumnes_data.py               # CRUD sobre data/alumnes.json
  tasques_data.py               # Gestió de tasques (crear, llistar, obertes/tancades)
  validacio.py                  # Pas 1: detecció automàtica del tipus + 5 validacions
  fitxers.py                    # Guardar xlsx amb nomenclatura correcta + metadata.json
views/
  inici.py                      # Selecció alumne / professor
  alumne/
    identificacio.py            # Grup → nom de la llista → confirmació correu
    portal.py                   # Tasques obertes amb graella d'estat per codi (01–08)
    lliurament.py               # Pujada múltiple + validació immediata + botó "Guardar vàlids"
  professor/
    login.py                    # Login + first-time setup de contrasenya
    tauler.py                   # Resum d'entregues per tasca activa (dataframe)
    tasques.py                  # Crear tasques, activar/desactivar
```

**Decisions de disseny preses a la Fase 1:**
- Autenticació alumne: selecció de nom + confirmació de correu (sense OAuth).
- Autenticació professor: contrasenya local (SHA-256). Si `password_hash` és buit al `config.json`, es mostra el formulari de configuració inicial.
- Detecció automàtica del tipus de llistat: compara capçaleres del xlsx contra `CAPCALERES_REQUERIDES` al mòdul `validacio.py`. En cas de coincidència parcial, indica quines columnes manquen.
- Fitxers de dades de referència (compres/vendes reals): **no implementats encara** — Fase 2.
- Les dades de referència són **per alumne** (cada empresa té productes i preus diferents).

---

### 🔲 Fase 2 — Pendent

**Gestió del professor: pujada de dades de referència.**

- Pantalla `views/professor/referencia.py`: el professor descarrega una plantilla xlsx amb tots els alumnes del grup, l'omple i la puja.
- Plantilla té dos fulls: **COMPRES** i **VENDES** (veure estructura de camps al CLAUDE.md).
- Mòdul `modules/referencia_data.py`: parseig i emmagatzematge de les dades de referència per tasca i alumne.
- Camp `R_DATA_ENTREGA_TASCA` l'omple l'app automàticament (data de pujada del llistat 03).
- Camp `R_EMPRESA_C` / `R_EMPRESA_V` l'omple l'app des d'`alumnes.json`.
- Pantalla `views/professor/seguiment.py`: taula detallada d'entregues (substituirà la del tauler).

---

### 🔲 Fase 3 — Pendent

**Motor de correcció automàtica.**

- `modules/correccio_compres.py` — llistats 01, 02, 03
- `modules/correccio_vendes.py` — llistats 04, 05, 06
- `modules/correccio_magatzem.py` — llistats 07, 08
- `views/professor/correccio.py` — llançar correcció + gestió de casos ambigus (la correcció s'atura i espera decisió del professor)
- Resultat: `data/tasques/<num>/<grup>/correccions/resultats.json`

---

### 🔲 Fase 4 — Pendent

**Resultats i exportació.**

- `modules/informe.py` — generació d'informes per alumne i resum de grup
- `views/professor/resultats.py` — vista de notes, errors, ajust manual
- Exportació: resum en xlsx, informes individuals en PDF

---

### 🔲 Fase 5 — Pendent

**Gestió d'alumnes i desplegament a Oracle Cloud.**

- `views/professor/alumnes_gestio.py` — CRUD d'alumnes sobre `data/alumnes.json`
- Instruccions de desplegament a Oracle Cloud VM (ARM A1)

---

## Estructura de `data/alumnes.json`

```json
[
  {
    "expedient": "5796",
    "nom": "SACARES MORAGUES, NADAL",
    "correu": "5796.nsacares@cifpjoantaix.cat",
    "grup": "ADG32",
    "rao_social": "ADG32 5796 NSACARES SL",
    "cif": "B00214783",
    "actiu": true,
    "prova": false
  }
]
```

---

## Errors coneguts i regles apreses

*(Actualitzar cada vegada que Claude cometi un error recurrent)*

- [ ] Afegir aquí errors detectats durant el desenvolupament
