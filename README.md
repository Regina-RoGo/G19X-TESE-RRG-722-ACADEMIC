# Desarrollo de una Plataforma Inteligente de CRM con Inteligencia Artificial 

**Alumno:** Regina Rodríguez Gómez · **Matrícula:** G19X-TESE-RRG-722-ACADEMIC
**Institución:** Tecnológico de Estudios Superiores de Ecatepec

## Qué hace

Plataforma web de gestión de relaciones con clientes (CRM) que integra Inteligencia Artificial Generativa (Google Gemini) para asistir al equipo comercial. Centraliza clientes, interacciones, oportunidades en un tablero Kanban y tareas de seguimiento, proporcionando resúmenes ejecutivos, análisis de sentimiento, lead scoring y riesgo de churn bajo demanda.

## Qué necesitas instalado

- Docker Desktop (con Docker Compose v2+)
- Python 3.12 (opcional, solo para ejecutar scripts fuera de contenedor)

## Base de datos

1. La base de datos PostgreSQL 16 se crea y configura automáticamente dentro de Docker.
2. Para cargar el catálogo inicial y el usuario administrador de prueba, ejecuta:
   ```bash
   docker compose exec app python -m app.seed
   ```

## Configuración

Copia `.env.example` a `.env` y llena los valores (los reales están en
«Accesos de prueba», en Mis documentos, llamado "Este es el .env").

## Cómo instalarlo y ejecutarlo

docker compose up --build -d

Se abre en http://localhost:8000

## Usuario de prueba

Administrador: admin@crm.local 
Comercial: comercial@crm.local 
(contraseñas en "«Accesos de prueba») 

## Lo que todavía no funciona

La pantalla para dar de alta/crear nuevos usuarios directamente desde la interfaz web (se gestionan vía backend/script). 

## Avisos generales:

Toda documentación se encuentra ya cargada en la plataforma TODOAcademy en documentación técnica para mayor comodidad y seguridad. 

Este proyecto integra Google Gemini API para potenciar el análisis comercial predictivo y generativo:

Resumen Ejecutivo: Síntesis automática del perfil del cliente e historial de interacciones.
Sugerencias de Venta: Recomendaciones accionables para el equipo comercial.
Lead Scoring & Churn: Calificación automática de probabilidad de cierre y riesgo de cancelación (escala 0-100).

(Asimismo, se utilizaron herramientas de IA conversacional como asistentes de codificación -Claude Code- para la aceleración en la maquetación de plantillas, estructuración de esquemas y refactorización del código).