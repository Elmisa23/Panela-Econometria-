import numpy as np
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.stattools import adfuller, kpss
import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd
from scipy.stats import jarque_bera
from statsmodels.stats.diagnostic import het_arch

# 1. Localizar la base dentro del proyecto.
carpeta_proyecto = Path(__file__).resolve().parent
archivo = carpeta_proyecto / "Datos" / "Base_panela_Corabastos_2015_2025.csv"

# 2. Leer el archivo CSV.
datos = pd.read_csv(archivo)

# 3. Convertir las fechas: día/mes/año, como aparecen en tu archivo.
datos["fecha"] = pd.to_datetime(
    datos["fecha"],
    format="%d/%m/%Y"
)

# 4. Ordenar del mes más antiguo al más reciente.
datos = datos.sort_values("fecha").reset_index(drop=True)
if (datos["fecha"].duplicated().any() or datos["precio_cop_kg"].isna().any()
        or len(datos) != 132 or datos["fecha"].iloc[0] != pd.Timestamp("2015-01-01")
        or datos["fecha"].iloc[-1] != pd.Timestamp("2025-12-01")):
    raise ValueError("La base no cumple el período y la frecuencia esperados.")

# 5. Mostrar los datos principales.
print("\nPrimeras cinco observaciones:")
print(datos[["fecha", "precio_cop_kg"]].head())

print("\nCantidad de observaciones:", len(datos))
print("Primera fecha:", datos["fecha"].min().strftime("%d/%m/%Y"))
print("Última fecha:", datos["fecha"].max().strftime("%d/%m/%Y"))

print("\nValores faltantes:")
print(datos[["fecha", "precio_cop_kg"]].isna().sum())

print("\nFechas duplicadas:", datos["fecha"].duplicated().sum())

# 6. Crear una carpeta para guardar los resultados.
carpeta_resultados = carpeta_proyecto / "resultados"
carpeta_resultados.mkdir(exist_ok=True)

# Auditoría de los valores registrados en el CSV; no modifica la procedencia.
procedencia = datos.assign(anio=datos["fecha"].dt.year)
auditoria = (procedencia.groupby(["archivo_fuente", "hoja_fuente"], dropna=False)
             .agg(observaciones=("fecha", "size"),
                  anios=("anio", lambda x: ", ".join(map(str, sorted(x.unique())))))
             .reset_index())
auditoria.to_csv(carpeta_resultados / "00_trazabilidad_csv.csv", index=False,
                 encoding="utf-8-sig")

# 7. Dibujar el precio mensual.
fig, ax = plt.subplots(figsize=(10, 5))

ax.plot(
    datos["fecha"],
    datos["precio_cop_kg"],
    color="saddlebrown",
    linewidth=1.8
)

ax.set_title(
    "Precio mayorista de la panela cuadrada morena\n"
    "Corabastos, Bogotá | 2015–2025"
)
ax.set_xlabel("Año")
ax.set_ylabel("Precio promedio mensual (COP/kg)")
ax.grid(alpha=0.3)

fig.tight_layout()

# 8. Guardar la gráfica y mostrarla.
fig.savefig(
    carpeta_resultados / "01_precio_original.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close(fig)

# 9. Prueba ADF sobre el precio original.
precio = datos["precio_cop_kg"].astype(float)

for especificacion, nombre in [
    ("c", "Con constante"),
    ("ct", "Con constante y tendencia")
]:
    resultado = adfuller(
        precio,
        regression=especificacion,
        maxlag=12,
        autolag="AIC",
        result_object=False
    )

    print(f"\nADF: {nombre}")
    print(f"Estadístico: {resultado[0]:.4f}")
    print(f"Valor p: {resultado[1]:.4f}")
    print(f"Rezagos utilizados: {resultado[2]}")
    print(f"Observaciones utilizadas: {resultado[3]}")

    # 10. Prueba KPSS sobre el precio original.
for especificacion, nombre in [
    ("c", "Con constante"),
    ("ct", "Con constante y tendencia")
]:
    resultado_kpss = kpss(
        precio,
        regression=especificacion,
        nlags="auto",
        result_object=False
    )

    print(f"\nKPSS: {nombre}")
    print(f"Estadístico: {resultado_kpss[0]:.4f}")
    print(f"Valor p reportado: {resultado_kpss[1]:.4f}")
    print(f"Rezagos utilizados: {resultado_kpss[2]}")
    print(f"Valor crítico al 5%: {resultado_kpss[3]['5%']:.4f}")

    # 11. Calcular la primera diferencia del precio.
datos["diferencia_precio"] = datos["precio_cop_kg"].diff()

# El primer mes no tiene un mes anterior para comparar.
datos_diferencia = datos.dropna(subset=["diferencia_precio"])

print("\nPrimeras cinco diferencias:")
print(
    datos_diferencia[
        ["fecha", "precio_cop_kg", "diferencia_precio"]
    ].head()
)

print("\nCantidad de diferencias:", len(datos_diferencia))

# 12. Graficar los cambios mensuales del precio.
fig, ax = plt.subplots(figsize=(10, 5))

ax.plot(
    datos_diferencia["fecha"],
    datos_diferencia["diferencia_precio"],
    color="steelblue",
    linewidth=1.5
)

ax.axhline(
    y=0,
    color="black",
    linestyle="--",
    linewidth=1
)

ax.set_title(
    "Cambio mensual del precio de la panela cuadrada morena\n"
    "Corabastos, Bogotá | Primera diferencia"
)
ax.set_xlabel("Año")
ax.set_ylabel("Cambio respecto al mes anterior (COP/kg)")
ax.grid(alpha=0.3)

fig.tight_layout()

fig.savefig(
    carpeta_resultados / "02_primera_diferencia.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close(fig)

# 13. Evaluar la primera diferencia con ADF y KPSS.
cambios = datos_diferencia["diferencia_precio"].astype(float)

adf_cambios = adfuller(
    cambios,
    regression="c",
    maxlag=12,
    autolag="AIC",
    result_object=False
)

kpss_cambios = kpss(
    cambios,
    regression="c",
    nlags="auto",
    result_object=False
)

# Guardar también las pruebas de identificación y recordar que KPSS limita
# sus valores p a los extremos de la tabla disponible.
filas_estacionariedad = []
for etiqueta, serie, especificaciones in [
    ("niveles", precio, ["c", "ct"]), ("primera diferencia", cambios, ["c"])
]:
    for especificacion in especificaciones:
        adf = adfuller(serie, regression=especificacion, maxlag=12, autolag="AIC")
        kp = kpss(serie, regression=especificacion, nlags="auto")
        filas_estacionariedad.append({"serie": etiqueta, "deterministicos": especificacion,
            "ADF_estadistico": adf[0], "ADF_p": adf[1], "ADF_rezagos": adf[2],
            "KPSS_estadistico": kp[0], "KPSS_p_acotado": kp[1], "KPSS_rezagos": kp[2]})
pd.DataFrame(filas_estacionariedad).to_csv(
    carpeta_resultados / "03_pruebas_estacionariedad.csv", index=False, encoding="utf-8-sig")

print("\n--- PRUEBAS SOBRE LA PRIMERA DIFERENCIA ---")
print("Cantidad de cambios mensuales:", len(cambios))

print("\nADF: Primera diferencia, con constante")
print(f"Estadístico: {adf_cambios[0]:.4f}")
print(f"Valor p: {adf_cambios[1]:.6f}")
print(f"Rezagos utilizados: {adf_cambios[2]}")
print(f"Valor crítico al 5%: {adf_cambios[4]['5%']:.4f}")

print("\nKPSS: Primera diferencia, con constante")
print(f"Estadístico: {kpss_cambios[0]:.4f}")
print(f"Valor p reportado: {kpss_cambios[1]:.4f}")
print(f"Rezagos utilizados: {kpss_cambios[2]}")
print(f"Valor crítico al 5%: {kpss_cambios[3]['5%']:.4f}")

# 14. ACF y PACF de la primera diferencia.
fig, ejes = plt.subplots(2, 1, figsize=(11, 8))

plot_acf(
    cambios,
    lags=24,
    alpha=0.05,
    zero=False,
    ax=ejes[0]
)

plot_pacf(
    cambios,
    lags=24,
    alpha=0.05,
    zero=False,
    method="ywm",
    ax=ejes[1]
)

ejes[0].set_title("ACF de la primera diferencia del precio")
ejes[1].set_title("PACF de la primera diferencia del precio")

for eje in ejes:
    eje.set_xlabel("Rezago (meses)")
    eje.set_ylabel("Correlación")
    eje.set_xticks(range(1, 25))
    eje.grid(alpha=0.3)

fig.tight_layout()

fig.savefig(
    carpeta_resultados / "03_acf_pacf_diferencia.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close(fig)

# 15. Preparar el precio con un índice mensual.
serie_precio = (
    datos.set_index("fecha")["precio_cop_kg"]
    .astype(float)
    .asfreq("MS")
)

if serie_precio.isna().any():
    raise ValueError("Hay meses sin precio. Revisa la base antes de continuar.")

# Modelos propuestos a partir de ACF y PACF.
candidatos = {
    "ARIMA(1,1,0)": (1, 1, 0),
    "ARIMA(0,1,1)": (0, 1, 1),
    "ARIMA(1,1,1)": (1, 1, 1),
    "ARIMA AR(1,5), d=1": ([1, 5], 1, 0)
}

modelos_ajustados = {}
filas_comparacion = []
resumenes = []

# 16. Estimar los candidatos con deriva.
for nombre, orden in candidatos.items():
    print(f"\nEstimando: {nombre}")

    modelo = ARIMA(
        serie_precio,
        order=orden,
        trend="t",
        enforce_stationarity=True,
        enforce_invertibility=True
    )

    ajuste = modelo.fit()

    modelos_ajustados[nombre] = ajuste

    filas_comparacion.append({
        "Modelo": nombre,
        "AIC": ajuste.aic,
        "BIC": ajuste.bic,
        "Convergio": ajuste.mle_retvals.get("converged", False)
    })

    resumenes.append(
        f"\n{'=' * 60}\n{nombre}\n{ajuste.summary().as_text()}"
    )

# 17. Mostrar y guardar la comparación.
comparacion = pd.DataFrame(filas_comparacion)
comparacion = comparacion.sort_values("AIC").reset_index(drop=True)

print("\n--- COMPARACION INICIAL: MODELOS CON DERIVA ---")
print(comparacion.round(3).to_string(index=False))

comparacion.to_csv(
    carpeta_resultados / "04_comparacion_modelos.csv",
    index=False,
    encoding="utf-8-sig"
)

(carpeta_resultados / "05_resumenes_modelos.txt").write_text(
    "\n".join(resumenes),
    encoding="utf-8"
)

# 18. Estimar la alternativa sin deriva.
ajuste_sin_deriva = ARIMA(
    serie_precio,
    order=([1, 5], 1, 0),
    trend="n",
    enforce_stationarity=True,
    enforce_invertibility=True
).fit()

modelos_ajustados["AR(1,5), d=1, sin deriva"] = ajuste_sin_deriva

versiones = {
    "Con deriva": modelos_ajustados["ARIMA AR(1,5), d=1"],
    "Sin deriva": ajuste_sin_deriva
}

filas_revision = []

# 19. Comparar ajuste y autocorrelación de residuos.
for nombre, ajuste in versiones.items():
    # Excluir los errores iniciales afectados por la inicialización.
    inicio = max(
        ajuste.loglikelihood_burn,
        ajuste.filter_results.nobs_diffuse
    )

    residuos = ajuste.resid.iloc[inicio:].dropna()

    ljung_box = acorr_ljungbox(
        residuos,
        lags=[6, 12, 24],
        model_df=2,
        return_df=True
    )

    filas_revision.append({
        "Version": nombre,
        "AIC": ajuste.aic,
        "BIC": ajuste.bic,
        "Convergio": ajuste.mle_retvals.get("converged", False),
        "p_LB6": ljung_box.loc[6, "lb_pvalue"],
        "p_LB12": ljung_box.loc[12, "lb_pvalue"],
        "p_LB24": ljung_box.loc[24, "lb_pvalue"]
    })

revision = pd.DataFrame(filas_revision)

print("\n--- REVISION DEL MODELO CON REZAGOS 1 Y 5 ---")
print(revision.round(4).to_string(index=False))

revision.to_csv(
    carpeta_resultados / "06_revision_deriva_residuos.csv",
    index=False,
    encoding="utf-8-sig"
)

(carpeta_resultados / "07_modelo_sin_deriva.txt").write_text(
    ajuste_sin_deriva.summary().as_text(),
    encoding="utf-8"
)

# 20. Graficar residuos del candidato sin deriva.
inicio = max(
    ajuste_sin_deriva.loglikelihood_burn,
    ajuste_sin_deriva.filter_results.nobs_diffuse
)

residuos_candidato = (
    ajuste_sin_deriva.resid.iloc[inicio:].dropna()
)

fig, ejes = plt.subplots(2, 1, figsize=(11, 8))

ejes[0].plot(
    residuos_candidato.index,
    residuos_candidato,
    color="steelblue",
    linewidth=1.2
)
ejes[0].axhline(0, color="black", linestyle="--")
ejes[0].set_title("Residuos del modelo ARIMA con AR(1,5), sin deriva")
ejes[0].set_xlabel("Año")
ejes[0].set_ylabel("Error de predicción (COP/kg)")
ejes[0].grid(alpha=0.3)

plot_acf(
    residuos_candidato,
    lags=24,
    zero=False,
    alpha=0.05,
    ax=ejes[1]
)
ejes[1].set_title("ACF de los residuos")
ejes[1].set_xlabel("Rezago (meses)")
ejes[1].set_ylabel("Correlación")
ejes[1].set_xticks(range(1, 25))
ejes[1].grid(alpha=0.3)

fig.tight_layout()
fig.savefig(
    carpeta_resultados / "08_diagnostico_residuos_v2.png",
    dpi=300,
    bbox_inches="tight"
)
plt.close(fig)

# 21. Explorar una alternativa con tendencia lineal.
tiempo = np.arange(len(serie_precio))

pendiente, intercepto = np.polyfit(
    tiempo,
    serie_precio.to_numpy(),
    deg=1
)

tendencia_lineal = intercepto + pendiente * tiempo
precio_sin_tendencia = serie_precio - tendencia_lineal

# 22. Graficar las desviaciones respecto a la tendencia.
fig, ejes = plt.subplots(3, 1, figsize=(11, 11))

ejes[0].plot(
    precio_sin_tendencia.index,
    precio_sin_tendencia,
    color="saddlebrown"
)
ejes[0].axhline(0, color="black", linestyle="--")
ejes[0].set_title("Precio menos su tendencia lineal")
ejes[0].set_xlabel("Año")
ejes[0].set_ylabel("Desviación (COP/kg)")

plot_acf(
    precio_sin_tendencia,
    lags=24,
    zero=False,
    ax=ejes[1]
)
ejes[1].set_title("ACF del precio sin tendencia lineal")

plot_pacf(
    precio_sin_tendencia,
    lags=24,
    zero=False,
    method="ywm",
    ax=ejes[2]
)
ejes[2].set_title("PACF del precio sin tendencia lineal")

for eje in ejes[1:]:
    eje.set_xlabel("Rezago (meses)")
    eje.set_xticks(range(1, 25))

for eje in ejes:
    eje.grid(alpha=0.3)

fig.tight_layout()
fig.savefig(
    carpeta_resultados / "09_alternativa_tendencia.png",
    dpi=300,
    bbox_inches="tight"
)
plt.close(fig)

# 23. Alternativa en niveles: AR(2) con constante y tendencia.
ajuste_niveles = ARIMA(
    serie_precio,
    order=(2, 0, 0),
    trend="ct",
    enforce_stationarity=True
).fit()

modelos_ajustados["AR(2) con tendencia"] = ajuste_niveles

print("\n--- AR(2) CON CONSTANTE Y TENDENCIA ---")
print(ajuste_niveles.summary())
print(
    "\nConvergio:",
    ajuste_niveles.mle_retvals.get("converged", False)
)

# Revisar autocorrelación de los residuos.
inicio_niveles = max(
    ajuste_niveles.loglikelihood_burn,
    ajuste_niveles.filter_results.nobs_diffuse
)

residuos_niveles = (
    ajuste_niveles.resid.iloc[inicio_niveles:].dropna()
)

lb_niveles = acorr_ljungbox(
    residuos_niveles,
    lags=[6, 12, 24],
    model_df=2,
    return_df=True
)

print("\nLjung-Box del modelo en niveles:")
print(lb_niveles.round(4))

# Comprobar las raíces del componente AR.
modulos_raices = np.abs(ajuste_niveles.arroots)

print("\nModulos de las raices AR:")
print(modulos_raices.round(4))

# Guardar el resumen y los diagnósticos.
texto_niveles = (
    ajuste_niveles.summary().as_text()
    + "\n\nConvergio: "
    + str(ajuste_niveles.mle_retvals.get("converged", False))
    + "\n\nLjung-Box:\n"
    + lb_niveles.to_string()
    + "\n\nModulos de las raices AR:\n"
    + str(modulos_raices)
)

(carpeta_resultados / "10_modelo_niveles.txt").write_text(
    texto_niveles,
    encoding="utf-8"
)

# 24. Reproducir el fallo y probar el reinicio ya propuesto. La escala en
# miles de pesos también reduce problemas de acondicionamiento numérico.
def ajustar_126(serie, modo):
    escala = 1000 if modo == "reinicio_escalado" else 1
    y = serie / escala
    modelo = ARIMA(y, order=([1, 2, 6], 0, 0), trend="ct",
                   enforce_stationarity=True, enforce_invertibility=True)
    if modo == "original":
        return modelo.fit(method_kwargs={"maxiter": 1000}), escala
    base = ARIMA(y, order=(2, 0, 0), trend="ct",
                 enforce_stationarity=True).fit(method_kwargs={"maxiter": 1000})
    iniciales = base.params.to_dict()
    iniciales["ar.L6"] = 0.0
    return modelo.fit(start_params=[iniciales[n] for n in modelo.param_names],
                      method_kwargs={"maxiter": 1000}), escala


def valido(ajuste):
    return bool(ajuste.mle_retvals.get("converged", False)
                and np.isfinite(ajuste.llf) and ajuste.llf != 0
                and np.all(np.isfinite(ajuste.params))
                and np.all(np.isfinite(ajuste.bse)) and np.all(ajuste.bse > 0)
                and np.all(np.abs(ajuste.arroots) > 1))


intentos = []
ajuste_126 = None
for modo in ["original", "reinicio", "reinicio_escalado"]:
    try:
        ajuste, escala = ajustar_126(serie_precio, modo)
        correcto = valido(ajuste)
        intentos.append(f"\n{modo}, escala={escala}, válido={correcto}\n"
                        f"convergencia={ajuste.mle_retvals}\n"
                        f"raíces AR={np.abs(ajuste.arroots)}\n"
                        + ajuste.summary().as_text())
        if correcto:
            ajuste_126, escala_126 = ajuste, escala
            break
    except Exception as error:
        intentos.append(f"\n{modo}: error {type(error).__name__}: {error}")
(carpeta_resultados / "11_modelo_niveles_126.txt").write_text(
    "\n".join(intentos), encoding="utf-8")

# 25. Diagnósticos: Ljung–Box ajusta los grados de libertad por parámetros
# AR/MA; ARCH contrasta dependencia de errores al cuadrado, no toda posible
# inestabilidad de varianza. Jarque–Bera no demuestra independencia.
def diagnosticar(nombre, ajuste, grados, escala=1):
    inicio = max(ajuste.loglikelihood_burn, ajuste.filter_results.nobs_diffuse)
    residuos = ajuste.resid.iloc[inicio:].dropna() * escala
    lb = acorr_ljungbox(residuos, lags=[6, 12, 24], model_df=grados)
    jb = jarque_bera(residuos)
    arch = het_arch(residuos, nlags=6, ddof=grados)
    tabla = pd.DataFrame({"coeficiente": ajuste.params, "error_estandar": ajuste.bse,
                          "p_valor": ajuste.pvalues})
    texto = (f"{nombre}\nVálido: {valido(ajuste)}\n"
             f"Convergencia: {ajuste.mle_retvals}\n"
             f"Raíces AR, módulos: {np.abs(ajuste.arroots)}\n"
             f"Coeficientes en escala del ajuste (factor {escala}):\n{tabla}\n"
             f"Ljung-Box:\n{lb}\nJarque-Bera: estadístico={jb.statistic}, p={jb.pvalue}\n"
             f"ARCH LM (6 rezagos): estadístico={arch[0]}, p={arch[1]}\n"
             f"Desviación estándar primera/segunda mitad: "
             f"{residuos.iloc[:len(residuos)//2].std():.3f} / "
             f"{residuos.iloc[len(residuos)//2:].std():.3f} COP/kg\n")
    fig, axes = plt.subplots(3, 1, figsize=(11, 9))
    axes[0].plot(residuos.index, residuos); axes[0].axhline(0, color="black")
    axes[0].set_title(nombre + ": residuos (COP/kg)")
    axes[1].plot(residuos.index, residuos.rolling(12).std())
    axes[1].set_title("Desviación estándar móvil de 12 meses")
    plot_acf(residuos, lags=24, zero=False, ax=axes[2])
    fig.tight_layout(); fig.savefig(carpeta_resultados / ("12_" + nombre + ".png"), dpi=180)
    plt.close(fig)
    return texto, lb


diagnosticos = []
texto, lb_principal = diagnosticar("integrado", ajuste_sin_deriva, 2)
diagnosticos.append(texto)
texto, lb_ar2 = diagnosticar("niveles_ar2", ajuste_niveles, 2)
diagnosticos.append(texto)
if ajuste_126 is not None:
    texto, lb_126 = diagnosticar("niveles_ar126", ajuste_126, 3, escala_126)
    diagnosticos.append(texto)
else:
    diagnosticos.append("AR(1,2,6): ningún intento produjo una estimación válida.\n")
(carpeta_resultados / "12_diagnosticos_finales.txt").write_text(
    "\n".join(diagnosticos), encoding="utf-8")

# 26. Comparación retrospectiva de un paso cuando ambos candidatos superan
# el filtro de autocorrelación. Ventana expansiva: 2022–2025; cada ajuste
# utiliza únicamente observaciones anteriores al mes pronosticado.
adecuado_126 = ajuste_126 is not None and (lb_126.lb_pvalue > 0.05).all()
filas = []
if adecuado_126:
    for i in range(84, len(serie_precio)):
        entrenamiento = serie_precio.iloc[:i]
        a = ARIMA(entrenamiento, order=([1, 5], 1, 0), trend="n").fit()
        b, factor = ajustar_126(entrenamiento, "reinicio_escalado")
        if not valido(a) or not valido(b):
            raise RuntimeError(f"Ajuste retrospectivo inválido en {serie_precio.index[i]}")
        filas.append({"fecha": serie_precio.index[i], "observado": serie_precio.iloc[i],
                      "integrado": float(a.forecast().iloc[0]),
                      "niveles": float(b.forecast().iloc[0]) * factor,
                      "ingenuo": entrenamiento.iloc[-1]})
    retrospectiva = pd.DataFrame(filas)
    retrospectiva.to_csv(carpeta_resultados / "13_pronosticos_retrospectivos.csv", index=False)
    metricas = []
    for nombre in ["integrado", "niveles", "ingenuo"]:
        error = retrospectiva[nombre] - retrospectiva.observado
        metricas.append({"modelo": nombre, "MAE": np.mean(np.abs(error)),
                         "RMSE": np.sqrt(np.mean(error**2))})
    pd.DataFrame(metricas).to_csv(carpeta_resultados / "13_metricas_retrospectivas.csv", index=False)

# La elección se documenta explícitamente tras evaluar los resultados.
pronostico = ajuste_sin_deriva.get_forecast(steps=10)
intervalos = pronostico.conf_int(alpha=0.05)
salida = pd.DataFrame({"fecha": pronostico.predicted_mean.index,
                       "pronostico_cop_kg": pronostico.predicted_mean.to_numpy(),
                       "limite_inferior_95": intervalos.iloc[:, 0].to_numpy(),
                       "limite_superior_95": intervalos.iloc[:, 1].to_numpy()})
salida.to_csv(carpeta_resultados / "14_pronostico_10_meses.csv", index=False, encoding="utf-8-sig")
fig, ax = plt.subplots(figsize=(11, 5))
ax.plot(serie_precio.index, serie_precio, label="Precio observado")
ax.plot(salida.fecha, salida.pronostico_cop_kg, label="Pronóstico", color="darkorange")
ax.fill_between(salida.fecha, salida.limite_inferior_95, salida.limite_superior_95,
                color="orange", alpha=.25, label="Intervalo de predicción 95 %")
ax.set(title="Precio de panela y pronóstico a 10 meses\n"
             "Pronósticos enero–octubre de 2026 con información hasta diciembre de 2025",
       ylabel="COP/kg", xlabel="Fecha")
ax.grid(alpha=.3); ax.legend(); fig.tight_layout()
fig.savefig(carpeta_resultados / "14_pronostico_10_meses.png", dpi=200); plt.close(fig)
print("\nDiagnósticos y pronósticos guardados en resultados.")


