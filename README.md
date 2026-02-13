# Api altura Río Uruguay 🌊

Este proyecto nace con la necesidad de transformar los datos públicos de la **Prefectura Naval Argentina** sobre la altura del Río Uruguay en una fuente de información estructurada, accesible y persistente a través de una API moderna.

Actualmente, los datos de los niveles del río solo están disponibles para consulta visual en un portal web. El objetivo de este sistema es automatizar la captura de esos datos, almacenarlos y ofrecer una interfaz programable para su consulta.

---

## 🚀 La Idea

El sistema se basa en una arquitectura desacoplada compuesta por dos pilares fundamentales:

### 1. El Ingestador (Scraper/Feeder)
Es el encargado de la "fuerza bruta". Su función es conectarse periódicamente a las fuentes oficiales, extraer la información técnica de los puertos (altura, estado, coordenadas y tendencia) y alimentar nuestra base de datos.
* **Misión:** Garantizar que los datos estén actualizados y generar un historial que la fuente original no ofrece.
* **Filosofía:** Resiliencia ante cambios en la fuente externa y normalización de datos.

### 2. El Servidor de Datos (API)
Es la cara visible del proyecto. Provee una interfaz RESTful para que otros desarrolladores o aplicaciones puedan consultar el estado del río de forma eficiente.
* **Misión:** Entregar respuestas rápidas en formato JSON, permitir filtros por puerto y consultas de rangos históricos.
* **Filosofía:** Simplicidad, tipado fuerte y documentación automática.



---

## 🛠 Visión Técnica

Más allá de la funcionalidad, este proyecto es un laboratorio para aplicar mejores prácticas de ingeniería de software y cultura DevOps, incluyendo:

* **Contenerización:** Todo el ecosistema (API, Scraper y Base de Datos) correrá de forma orquestada con Docker.
* **Automatización:** Uso de pipelines (GitHub Actions) para la ejecución programada del scraper y tests automáticos.
* **Infraestructura como Código:** Configuración de entornos reproducible y consistente.

---
