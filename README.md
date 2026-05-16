# Sistema de Monitoreo de Altura de Ríos 🌊

Este proyecto surge ante la dificultad de acceder a datos históricos y estructurados sobre los niveles de los ríos desde portales oficiales, que suelen estar limitados a consultas visuales en tiempo real.

La solución funciona como un recolector y expositor centralizado de información, automatizando la captura de datos desde múltiples fuentes oficiales y transformándolos en una infraestructura ordenada, persistente y fácil de consumir para aplicaciones externas, análisis estadísticos o sistemas de alerta.

---


## 🏗️ Diseño Arquitectónico

El sistema se basa en una **arquitectura distribuida de servicios independientes y desacoplados**, orquestada mediante **Docker**. Esta decisión permite que el Ingestador (Scraper) y el Servidor (API) operen como piezas autónomas, facilitando el mantenimiento y la escalabilidad de cada componente.

Asimismo, el proyecto adopta un modelo **Cliente-Servidor**. Al exponer una API RESTful centralizada, el sistema actúa como un proveedor único de datos estructurados (*Single Source of Truth*), permitiendo que diversos clientes (como aplicaciones móviles, dashboards o herramientas de análisis) consuman la información de forma independiente.

### Componentes Core:
1.  **Ingestador de Datos (Scraper):** Módulo basado en Python que extrae información de múltiples fuentes hidrológicas oficiales (ver [Fuentes de Datos](#-fuentes-de-datos)).
2.  **API RESTful:** Desarrollada con **FastAPI**, proporciona una interfaz de alto rendimiento para consultas de datos en tiempo real e históricos.
3.  **Base de Datos Relacional:** PostgreSQL como motor de persistencia, asegurando integridad referencial y eficiencia en consultas geoespaciales y temporales.

---

## 📡 Fuentes de Datos

El scraper integra actualmente dos fuentes oficiales de datos hidrométricos:

### 🔹 Prefectura Naval Argentina
Extrae mediciones de altura publicadas en el portal web de la Prefectura Naval. Opera mediante scraping HTML y soporta dos modos de ejecución: incremental y backfill histórico.

### 🔹 INA (Instituto Nacional del Agua)
Consume la API REST pública del INA (`alerta.ina.gob.ar/a5`) para obtener series de altura hidrométrica (variable `2`). Esta fuente puede habilitarse o deshabilitarse de forma independiente mediante la variable de entorno `INA_ENABLED`.

---

## 🛠️ Aspectos Técnicos y Buenas Prácticas

El proyecto implementa estándares de desarrollo para garantizar la calidad y mantenibilidad del código:

### 🔹 Patrones de Diseño
*   **Repository Pattern:** Desacoplamiento total entre la lógica de negocio y las operaciones de acceso a datos (ORM), facilitando el testing y la mantenibilidad.
*   **Strategy Pattern (Scraper):** Se optó por este patrón para la lógica de captura de datos por las siguientes razones:
    *   **Versatilidad:** Permite intercambiar dinámicamente entre diferentes modos de ejecución (lectura incremental en tiempo real vs. reconstrucción histórica de datos o *backfilling*).
    *   **Extensibilidad:** Facilita la incorporación de nuevas fuentes de datos o métodos de extracción sin modificar el flujo principal del scraper.
    *   **Mantenibilidad:** Aisla la lógica específica de parseo y navegación de la lógica de orquestación y persistencia.
*   **Tipado Fuerte y Validación:** Uso de **Pydantic** para esquemas de datos y **SQLAlchemy Mapped Types** para una integración tipo-segura (type-safe) con la base de datos.
*   **Composición de Objetos:** Uso de objetos compuestos (e.g., `Coordinates`) en el modelo de dominio para una mejor organización semántica.

### 🔹 DevOps y Automatización (CI/CD)
*   **Contenerización:** Uso de **Docker y Docker Compose** para orquestar servicios con configuraciones de entorno aisladas y repetibles.
*   **Pipeline de Integración Continua:** Configuración de **GitHub Actions** para ejecución automática de tests en cada Pull Request.
*   **Testing Culture:** Suite de tests unitarios e integración utilizando **Pytest**, garantizando la confiabilidad del sistema ante refactorizaciones.

---

## 🚀 Guía de Inicio Rápido

### Requisitos Previos
*   Docker y Docker Compose instalados.
*   Archivo `.env` configurado (ver `.env.example`).

### Despliegue con Docker
```bash
docker compose up -d
```

### Ejecutar los Tests
```bash
# Tests de la API
docker exec rio_api pytest

# Tests del Scraper
docker exec rio_scraper pytest
```

### Ejecución del Scraper
Por defecto, el scraper se ejecuta en **modo incremental cada 12 horas** (`SCRAPER_INTERVAL=43200`), procesando ambas fuentes (Prefectura e INA) en cada ciclo.

#### Modo Backfill (Histórico)
Si se desea reconstruir el historial de mediciones (por ejemplo, los últimos 30 días), se puede ejecutar el scraper con la variable de entorno `SCRAPER_MODE=backfill`:

```bash
docker compose run --rm -e SCRAPER_MODE=backfill -e BACKFILL_DAYS=30 scraper
```

Esto ejecutará el backfill en ambas fuentes simultáneamente.

#### Habilitar/Deshabilitar la fuente INA
La integración con INA está **habilitada por defecto**. Para desactivarla:

```bash
# En el archivo .env
INA_ENABLED=false
```

---

## 📖 Documentación de la API

Accede a la documentación interactiva (Swagger UI) en:
`http://localhost:8000/docs`

### Endpoints Principales:
*   `GET /stations`: Listado de estaciones con soporte para paginación y ordenamiento.
*   `GET /measurements/{station_id}`: Historial de mediciones con filtros de fecha.
*   `GET /alerts`: Estaciones que superan niveles de alerta o evacuación en tiempo real.
