# Sistema de Monitoreo de Altura de Ríos 🌊

Este proyecto surge ante la dificultad de acceder a datos históricos y estructurados sobre los niveles de los ríos desde portales oficiales, los cuales suelen estar limitados a consultas visuales en tiempo real o formatos no estandarizados.

La solución funciona como un **recolector, procesador y expositor centralizado** de información hidrométrica. Automatiza la captura de datos desde múltiples fuentes oficiales y los transforma en una infraestructura ordenada, persistente y fácil de consumir mediante una **API RESTful**, un **Dashboard público** y un **Panel de Administración**.

---

## 🏗️ Diseño Arquitectónico

El sistema se basa en una **arquitectura distribuida de microservicios independientes**, orquestada mediante **Docker** y **Docker Compose**. Esta estructura desacoplada permite que el Ingestador (*Scraper*), el Servidor de Datos (*API*), la Base de Datos y los Frontends (*Dashboard* y *Panel de Admin*) operen como piezas autónomas.

```
                    ┌─────────────────────────┐
                    │    Fuentes Oficiales    │
                    │ (PNA, INA, CARU, GCHU)  │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │ Ingestador de Datos     │
                    │   (Python / Scraper)    │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │   Base de Datos PostgreSQL│
                    │ (Estaciones, Mediciones,│
                    │   Ceros, Errores Log)   │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │     API RESTful         │
                    │ (FastAPI + Rate Limit)  │
                    └──────┬────────────┬─────┘
                           │            │
             ┌─────────────┘            └─────────────┐
             ▼                                        ▼
┌─────────────────────────┐              ┌─────────────────────────┐
│   Dashboard Público     │              │ Panel de Administración │
│ (React + Vite + Nginx)  │              │ (React + Vite + Nginx)  │
└─────────────────────────┘              └─────────────────────────┘
```

### Componentes Principales:
1. **Ingestador de Datos (Scraper Daemon):** Servicio distribuido en Python que extrae periódicamente información de múltiples fuentes hidrológicas oficiales mediante estrategias modulares.
2. **API RESTful (FastAPI):** Proveedor centralizado de datos (*Single Source of Truth*) con soporte para paginación, filtros temporales, límites de tasa (*rate limiting*) y conversión dinámica de datums altimétricos.
3. **Base de Datos Relacional (PostgreSQL 15):** Motor de persistencia para estaciones, mediciones históricas, ceros de escala/datums y registro de errores de ingesta.
4. **Dashboard de Visualización (React + TypeScript + Vite):** Interfaz web pública para explorar estaciones, visualizar curvas históricas de altura, consultar niveles de alerta/evacuación y filtrar por datums.
5. **Panel de Administración (React + TypeScript + Vite):** Interfaz web administrativa para la gestión de estaciones, ceros de escala (*gauge points*), tipos de datum y equivalencias de nivel.

---

## 📡 Fuentes de Datos Integradas

El scraper integra actualmente **cuatro fuentes oficiales** de datos hidrométricos y **una fuente de precipitación modelada**, procesadas de forma concurrente o configurable:

| Fuente | Descripción | Método de Extracción | Configuración Env |
|---|---|---|---|
| **Prefectura Naval Argentina (PNA)** | Mediciones de altura de ríos y puertos argentinos. | Web Scraping HTML (Incremental y Backfill) | `PREFECTURA_INTERVAL` |
| **Instituto Nacional del Agua (INA)** | Series de tiempo hidrométricas oficiales (API `alerta.ina.gob.ar/a5`). | API REST JSON | `INA_ENABLED`, `INA_INTERVAL` |
| **Comisión Administradora del Río Uruguay (CARU)** | Mediciones de estaciones a lo largo del Río Uruguay. | Web Scraping / API Web | `CARU_ENABLED`, `CARU_INTERVAL` |
| **Municipalidad de Gualeguaychú** | Monitoreo del nivel del Río Gualeguaychú en la cuenca local. | Web Scraping | `MUNICIPALIDAD_GCHU_ENABLED`, `MUNICIPALIDAD_GCHU_INTERVAL` |
| **Open-Meteo** | Precipitación horaria modelada para las estaciones habilitadas (mm). | API REST JSON (Incremental y Backfill) | `OPEN_METEO_ENABLED`, `OPEN_METEO_INTERVAL` |

### Precipitación con Open-Meteo

La serie de precipitación se asocia a **estaciones existentes** y se habilita por estación desde el Panel de Administración (columna *Precipitación*), siempre que la estación tenga coordenadas. No se crean estaciones nuevas a partir de esta fuente.

* **Granularidad y unidad:** valores horarios en milímetros (mm), correspondientes a la hora precedente.
* **Zona horaria:** `America/Argentina/Cordoba`; los timestamps se almacenan como *naive* local, igual que el resto de las mediciones.
* **Modo incremental:** consulta los últimos `OPEN_METEO_PAST_DAYS` días (máximo 92) contra la API de pronóstico.
* **Modo backfill:** reconstruye el histórico en bloques de `OPEN_METEO_BACKFILL_CHUNK_DAYS` días contra la API de archivo (`models=era5`), con una demora de `OPEN_METEO_ARCHIVE_DELAY_DAYS` días para dar tiempo a la consolidación del reanálisis.
* **Límite gratuito:** 10.000 llamadas/día. El scraper agrupa hasta `OPEN_METEO_MAX_POINTS_PER_REQUEST` coordenadas por request y estima el consumo antes del backfill; si supera `OPEN_METEO_DAILY_CALL_BUDGET`, registra una advertencia.
* **Atribución:** datos de [Open-Meteo](https://open-meteo.com/) bajo licencia [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

> **Limitación:** la precipitación de Open-Meteo es un dato **modelado en grilla**, no una observación in-situ. Puede diferir de los registros pluviométricos locales, especialmente en eventos convectivos. Además, el empalme entre la API de archivo (ERA5) y la de pronóstico puede presentar una discontinuidad menor en el borde temporal.

---

## 📐 Conversión de Datums y Ceros de Escala

El sistema soporta la gestión y conversión entre distintos sistemas de referencia altimétrica (**Datums** / **Ceros de Escala**):

* **Cero Local:** Nivel relativo de la regla de la estación hidrométrica.
* **IGN (Instituto Geográfico Nacional):** Nivel del mar oficial de la red altimétrica argentina.
* **Wharton:** Referencial altimétrico utilizado en cuencas específicas.

A través del servicio de conversión (`common/datum_service.py`) y endpoints de la API (`?datum=IGN` o `?datum=WHARTON`), las lecturas pueden convertirse dinámicamente según la diferencia de cota (*offset*) asignada al punto de escala.

---

## 💻 Aplicaciones y Frontends

### 1. Dashboard Público (`/dashboard`)
* **Ubicación:** `http://localhost:3000` (contenedor `rio_dashboard`)
* **Características:**
  * Mapa interactivamente vinculado e indicadores de estaciones.
  * Gráficos interactivos de evolución histórica de alturas.
  * Indicadores visuales de **Alerta** y **Evacuación** en tiempo real.
  * Selector de rango de fechas y filtro dinámico por Cero de Escala / Datum (Local, IGN, Wharton).
  * Diseño responsivo para dispositivos móviles y escritorio.

### 2. Panel de Administración (`/admin`)
* **Ubicación:** `http://localhost:3001` (contenedor `rio_admin`)
* **Características:**
  * CRUD de Estaciones hidrométricas (modificación de nombres, ríos, fuentes, coordenadas y umbrales de alerta).
  * Gestión de Puntos de Escala (*Gauge Points*).
  * Gestión de Tipos de Referencia (*Reference Zero Types*).
  * Configuración de Offsets y equivalencias altimétricas entre la escala local y los datums oficiales.

---

## 🛠️ Aspectos Técnicos y Buenas Prácticas

* **Strategy Pattern (Scrapers):** Cada fuente oficial (`Prefectura`, `INA`, `CARU`, `MunicipalidadGchu`) implementa una estrategia modular derivada de `ScraperStrategy`. Esto permite:
  * Intercambiar modos de ejecución (*Incremental* vs *Backfill* histórico).
  * Habilitar o deshabilitar fuentes independientemente vía variables de entorno.
  * Agregar nuevas fuentes hidrológicas sin alterar el motor principal del ingestador.
* **Repository Pattern:** Desacoplamiento total entre la lógica de dominio/servicios y las consultas ORM (SQLAlchemy), utilizado tanto en la API como en el Scraper.
* **Manejo y Seguimiento de Errores (Error Tracking):** Captura persistente de fallos de ingesta en la tabla `scraper_errors` (fallos HTTP, timeouts, errores de parseo), facilitando métricas de estado de los scrapers.
* **Rate Limiting:** Control de frecuencia en la API RESTful mediante `slowapi` (`RATE_LIMIT_DEFAULT=60/minute`).
* **Tipado Fuerte y Validación:** Integración de **Pydantic v2** para schemas API y **SQLAlchemy Mapped Types** para persistencia con tipado seguro.

---

## 🚀 Guía de Inicio Rápido

### Requisitos Previos
* Docker y Docker Compose instalados.
* Archivo `.env` configurado a partir de `.env.example`.

### Configuración del Entorno (`.env`)
Copia el archivo de ejemplo y ajusta los parámetros según tus necesidades:

```bash
cp .env.example .env
```

### Despliegue con Docker Compose
Para levantar la infraestructura completa (Base de Datos, API, Scraper, Dashboard y Admin Panel):

```bash
docker compose up -d
```

Los servicios estarán disponibles en:
* **API REST & Swagger Docs:** `http://localhost:8000/docs`
* **Dashboard Público:** `http://localhost:3000`
* **Panel de Administración:** `http://localhost:3001`
* **PostgreSQL:** `localhost:5432`

---

## ⚙️ Modos de Ejecución del Scraper

Por defecto, el ingestador corre en **modo continuo/incremental**, ejecutando las fuentes activadas según sus intervalos (`SCRAPER_TICK=60`).

### Ejecución de Backfill (Histórico)
Para reconstruir datos históricos (por ejemplo, los últimos 30 días en INA o Prefectura):

```bash
docker compose run --rm -e SCRAPER_MODE=backfill -e BACKFILL_DAYS=30 scraper
```

El mismo comando aplica a Open-Meteo para las estaciones con precipitación habilitada. Para históricos largos, tené en cuenta el presupuesto diario de llamadas (`OPEN_METEO_DAILY_CALL_BUDGET`).

### Habilitar / Deshabilitar Fuentes
Puedes activar o desactivar fuentes específicas modificando las variables de entorno en tu `.env`:

```env
INA_ENABLED=true
CARU_ENABLED=true
MUNICIPALIDAD_GCHU_ENABLED=true
```

---

## 🧪 Ejecución de Tests

El proyecto cuenta con suites de pruebas unitarias e integración con **Pytest**:

```bash
# Tests de la API REST
docker exec rio_api pytest

# Tests del Scraper
docker exec rio_scraper pytest
```

---

## 📖 Referencia de la API REST

Accede a la documentación interactiva (Swagger UI / OpenAPI) en `http://localhost:8000/docs`.

### Endpoints Principales:
* `GET /stations`: Listado paginado de estaciones hidrométricas.
* `GET /stations/{station_id}`: Detalle de una estación específica.
* `GET /measurements/{station_id}`: Historial de mediciones de una estación (admite `?datum=IGN` o `?datum=WHARTON`, paginación y rango de fechas).
* `GET /measurements/latest/{station_id}`: Última lectura registrada para una estación.
* `GET /precipitation/{station_id}`: Historial de precipitación horaria de una estación (paginación y rango de fechas).
* `GET /precipitation/latest/{station_id}`: Última precipitación registrada para una estación.
* `GET /precipitation/latest/bulk`: Última precipitación de todas las estaciones visibles con la serie habilitada.
* `GET /alerts`: Estaciones en nivel de alerta.
* `GET /alerts/evacuation`: Estaciones en nivel de evacuación.
* `GET /datums`: Listado de tipos de referencia altimétrica (IGN, Wharton, etc.).
* `GET /datums/station/{station_id}`: Punto de escala y offsets asociados a una estación.
