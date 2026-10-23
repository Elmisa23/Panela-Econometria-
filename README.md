# Precio mensual de la panela en Corabastos

Análisis Box–Jenkins del precio mensual de panela cuadrada morena en Bogotá, Corabastos, enero de 2015 a diciembre de 2025: 132 observaciones, denominadas COP/kg en el CSV. El archivo registra la fuente, hoja y fila de cada dato; `resultados/00_trazabilidad_csv.csv` reúne las nueve referencias de archivo y 66 combinaciones de archivo y hoja. Los nueve Excel disponibles están en `Datos/original`.

La verificación `resultados/15_verificacion_fuentes.csv` compara fecha, producto, mercado y precio con la fila numerada en Excel: los cuatro campos coinciden en las 132 observaciones. La hoja de 2019–2022 está registrada en el CSV con minúsculas y guion (por ejemplo, `ene-19`), mientras el Excel usa mayúscula y espacio (`Ene 19`). Los nombres locales del archivo 2015–2017 y del archivo de 2023 también difieren de los registrados; se usaron las correspondencias documentadas en `verificar_fuentes.py`, sin cambiar el CSV. Estas coincidencias de contenido apoyan las correspondencias, aunque no prueban que sean copias idénticas a los archivos nombrados originalmente.

En 84 registros de 2019–2025 el encabezado indica precio por kilogramo; los otros 48 registros de 2015–2018 tienen el encabezado «Precio» sin unidad explícita. La moneda COP tampoco aparece explícita en los encabezados revisados. Por ello, la tabla marca 84 coincidencias de campos y denominador, ninguna discrepancia numérica y 48 registros no completamente comprobables por unidad. Las notas y encabezados recopilados están en `resultados/15_notas_fuentes.txt`.

El organismo publicador es el Departamento Administrativo Nacional de Estadística (DANE), Sistema de Información de Precios y Abastecimiento del Sector Agropecuario (SIPSA), componente de precios mayoristas. La [página oficial del boletín mensual](https://www.dane.gov.co/index.php/estadisticas-por-tema/agropecuario/sistema-de-informacion-de-precios-sipsa/mayoristas-boletin-mensual-1) ofrece las series históricas. El [geovisor oficial del DANE](https://geoportal.dane.gov.co/geovisores/territorio/precios-mayoristas-sipsa/) indica que los precios semanales y mensuales se expresan en pesos por kilogramo o por unidad. Esto complementa los encabezados, pero esa indicación general no identifica por sí sola el denominador de cada uno de los 48 registros antiguos; su unidad específica queda pendiente de comprobación.

La base se construyó extrayendo y concatenando valores mensuales publicados para panela cuadrada morena en Bogotá, Corabastos. No calculamos los promedios mensuales ni reconstruimos su fórmula. Los encabezados de 2021–2025 dicen «Precio promedio por kilogramo»; en los anteriores se lee «Precio» o «Precio por kilogramo». Las hojas revisadas no explican el procedimiento exacto de agregación. No se infiere causalidad ni se ajustan precios por inflación.

Las siguientes correspondencias vinculan los archivos locales con las descargas de la página oficial; se basan en período, nombres y contenido auditado. No se ha comprobado que cada copia local sea idéntica byte por byte a la descarga oficial actual.

| Período | Archivo local en `Datos/original` | Descarga oficial DANE |
|---|---|---|
| 2015–2017 | `series-historicas-precios-mayoristas_2015_2017.xlsx` | [Serie 2013–2017](https://www.dane.gov.co/files/investigaciones/agropecuario/sipsa/series-historicas/series-historicas-precios-mayoristas.xlsx) |
| 2018 | `series-historicas-precios-mayoristas-2018.xlsx` | [Serie 2018](https://www.dane.gov.co/files/investigaciones/agropecuario/sipsa/series-historicas/series-historicas-precios-mayoristas-2018.xlsx) |
| 2019 | `series-historicas-precios-mayoristas-2019.xlsx` | [Serie 2019](https://www.dane.gov.co/files/investigaciones/agropecuario/sipsa/series-historicas/series-historicas-precios-mayoristas-2019.xlsx) |
| 2020 | `series-historicas-precios-mayoristas-2020.xlsx` | [Serie 2020](https://www.dane.gov.co/files/investigaciones/agropecuario/sipsa/series-historicas/series-historicas-precios-mayoristas-2020.xlsx) |
| 2021 | `series-historicas-precios-mayoristas-2021.xlsx` | [Serie 2021](https://www.dane.gov.co/files/investigaciones/agropecuario/sipsa/series-historicas/series-historicas-precios-mayoristas-2021.xlsx) |
| 2022 | `series-historicas-precios-mayoristas-2022.xlsx` | [Serie 2022](https://www.dane.gov.co/files/investigaciones/agropecuario/sipsa/series-historicas/series-historicas-precios-mayoristas-2022.xlsx) |
| 2023 | `anex-SIPSA-SerieHistoricaMayorista-2023.xlsx` | [Serie 2023](https://www.dane.gov.co/files/operaciones/SIPSA/anex-SIPSA-SerieHistoricaMayorista-Dic2023.xlsx) |
| 2024 | `anex-SIPSA-SerieHistoricaMayorista-2024.xlsx` | [Serie 2024](https://www.dane.gov.co/files/operaciones/SIPSA/anex-SIPSA-SerieHistoricaMayorista-2024.xlsx) |
| 2025 | `anex-SIPSA-SerieHistoricaMayorista-2025.xlsx` | [Serie 2025](https://www.dane.gov.co/files/operaciones/SIPSA/anex-SIPSA-SerieHistoricaMayorista-2025.xlsx) |

## Ejecución

Desde la carpeta del proyecto, con Python y las dependencias de `requirements.txt` instaladas:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe analisis.py
```

El script utiliza rutas relativas al archivo, guarda tablas, resúmenes y gráficas en `resultados` y cierra las figuras sin abrir ventanas. Los archivos históricos adicionales en esa carpeta se conservan; `11_modelo_niveles_126.txt` documenta los intentos actuales. Las versiones registradas corresponden al entorno con que se ejecutó el análisis, Python 3.14.

## Decisiones y resultados

ADF y KPSS tienen hipótesis nulas distintas: en niveles ambos rechazan sus respectivas nulas, mientras en primera diferencia ADF rechaza raíz unitaria y KPSS no rechaza estacionariedad. Los valores p de KPSS pueden estar acotados por su tabla. La ACF y la PACF motivaron manualmente AR y MA de primer orden y AR en los rezagos 1 y 5; no se realizó una búsqueda automática. Entre las versiones integradas con y sin deriva se usaron ajuste, parsimonia y diagnósticos; sus AIC son comparables entre sí. No se comparan directamente AIC entre órdenes de integración distintos.

Se elige **ARIMA([1,5],1,0) sin deriva** entre los candidatos evaluados, con 132 meses, coeficientes AR estimados 0,237 y 0,249. Convergió, sus raíces AR tienen módulo superior a uno y Ljung–Box con dos grados de libertad por parámetros dinámicos da p=0,351, 0,501 y 0,724 en 6, 12 y 24 meses. Esto no demuestra independencia. Jarque–Bera rechaza normalidad (p aproximadamente 5,6 × 10⁻²³); hay errores extremos. ARCH LM de seis rezagos no rechaza la ausencia de efectos ARCH (p=0,579), pero no prueba varianza constante: la desviación estándar de residuos pasa aproximadamente de 176 a 202 COP/kg entre mitades. Los coeficientes y diagnósticos completos están en `12_diagnosticos_finales.txt` y las gráficas correspondientes.

La alternativa AR(2) con constante y tendencia conserva autocorrelación residual (Ljung–Box p=0,0093 en 6). La alternativa AR(1,2,6) originalmente entrega log-verosimilitud cero y errores estándar inválidos pese a indicar convergencia. Reiniciar desde AR(2) en pesos no lo corrige; estimar en miles de pesos y reiniciar sí produce convergencia, raíces y errores estándar válidos sin retirar restricciones. Sin embargo, el modelo corregido aún rechaza ausencia de autocorrelación en 6 y 12 (p=0,0070 y 0,0343). Sus coeficientes, incluyendo AR(2) no significativo, y diagnósticos se guardan en `11_modelo_niveles_126.txt` y `12_diagnosticos_finales.txt`. Entre estos candidatos finales revisados, se eligió el modelo integrado; los diagnósticos completos de los demás modelos iniciales no se evaluaron, por lo que no se afirma que sean inadecuados. **No se realizó una evaluación predictiva retrospectiva frente al pronóstico ingenuo.** El código contempla una comparación condicional con orígenes mensuales expansivos de 2022–2025, un paso y una referencia ingenua, pero no se activó con los resultados obtenidos. Como la selección ya exploró toda la serie, tal comparación no sería completamente independiente.

El pronóstico de enero a octubre de 2026 y sus intervalos están en `14_pronostico_10_meses.csv` y la gráfica correspondiente. Los intervalos del modelo suponen especificación y parámetros estimados adecuados, errores futuros aproximadamente normales y varianza estable; son intervalos condicionales que no incorporan toda la incertidumbre de estimación ni cambios estructurales. La no normalidad y los valores extremos pueden deteriorar su cobertura; 95 % es nominal, no una garantía de cobertura exacta. No se eliminaron observaciones.

Para el póster faltan citar la fuente, precisar la unidad de los registros de 2015–2018, seleccionar las gráficas y resumir metodología, resultados y limitaciones; los pronósticos son una proyección histórica y deben contrastarse con observaciones posteriores si se dispone de ellas.
