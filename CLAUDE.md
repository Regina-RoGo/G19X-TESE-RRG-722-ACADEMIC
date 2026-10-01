# CRM Inteligente — Contexto del proyecto (MVP + Roadmap Extendido)

Este archivo es la fuente de verdad del alcance para este repo. Antes de proponer o generar código, respeta estrictamente estas reglas. Si algo que se te pide contradice este documento, avisa en vez de implementarlo directamente.

## Qué es este proyecto

Plataforma de CRM con inteligencia artificial, desarrollada por **una sola persona**. Las Fases 1–4 (semanas 1–4) construyeron el **MVP** con un único caso de uso de IA (resumen ejecutivo comercial) — completado y validado.

**Ampliación de alcance autorizada:** tras el éxito del MVP, se aprobó convertirlo en una plataforma completa mediante el **Roadmap Extendido (Fases 5 a 8)**, descrito más abajo. La ampliación **mantiene la arquitectura limpia existente** (monolito FastAPI por capas Router → Service → Repository, SSR con Jinja2 + HTMX, PostgreSQL, Docker Compose) — no se reescribe ni se reestructura lo ya construido, se extiende.

## Reglas duras (no negociables sin avisar explícitamente)

- El alcance válido es: MVP (Fases 1–4, ya cerrado) + Roadmap Extendido (Fases 5–8). NO agregar tablas, pantallas, endpoints o dependencias fuera de lo descrito en este documento "solo para que se vea más completo".
- Trabajar **una fase a la vez**: no adelantar funcionalidades de una fase posterior mientras la actual no esté funcionando de punta a punta.
- Sigue fuera de alcance (incluso en el Roadmap Extendido): RAG, agentes autónomos, microservicios, automatizaciones/workflows (ej. envío automático de correos, reglas disparadas por eventos), SPA/frameworks de frontend con build, y `audit_log`/`roles` normalizada.
- Todas las funcionalidades de IA usan **Gemini** con el mismo patrón ya probado en `app/services/ai_service.py`: salida estructurada (`response_schema`), timeout configurable, un reintento, error controlado que nunca rompe la app, y resultado persistido en PostgreSQL (no se recalcula en cada request).
- Si una funcionalidad parece razonable pero no está aquí, primero pregunta si pertenece al roadmap — no la implementes por iniciativa propia.

## Stack tecnológico

**Backend**
- FastAPI (Python), arquitectura por capas: Router → Service → Repository.
- PostgreSQL como base de datos.
- Autenticación con JWT (login real: endpoint que valida credenciales y emite el token).
- RBAC con dos roles: `admin` y `comercial`.
- Integración con Google Gemini API (Free Tier) vía `google-genai` — un caso de uso en el MVP, ampliado en Fases 5–6 (ver Roadmap Extendido).
- Docker Compose para levantar backend + PostgreSQL con un solo comando.
- Documentación automática vía Swagger/OpenAPI.

**Frontend**
- FastAPI + Jinja2 (server-side rendering) — el mismo servicio backend renderiza las páginas, sin build por separado, sin configurar CORS ni levantar un segundo servidor.
- TailwindCSS vía CDN + DaisyUI (componentes de UI ya bonitos por defecto: cards, botones, tablas, forms) — se ve presentable sin invertir tiempo en diseño.
- HTMX para las interacciones que necesitan sentirse dinámicas (enviar el formulario de interacción, generar el resumen IA) sin recargar toda la página y sin necesidad de escribir una SPA.
- Sesión vía cookie con el JWT (el propio backend la setea al hacer login), en vez de manejar el token manualmente en JS.
- **Chart.js vía CDN** (a partir de la Fase 7) para los gráficos del dashboard ejecutivo — los datos se inyectan desde el servidor (JSON en el template o endpoint de fragmento), sin build ni framework adicional.
- **Toasts/indicadores de UX** (Fase 7) con componentes DaisyUI (`toast`, `alert`, `loading`) disparados por HTMX (`HX-Trigger` desde el backend) — sin librerías JS extra.
- Esta combinación es la más simple de integrar (un solo servicio, cero configuración de build), y sigue permitiendo una interfaz moderna y consistente.

## Modelo de datos del MVP (5 tablas — no agregar más sin confirmar)

| Tabla | Propósito |
|---|---|
| `users` | Usuarios del sistema, credenciales y rol (enum: admin / comercial) |
| `customers` | Datos base de cada cliente |
| `interactions` | Historial de interacciones con un cliente |
| `interaction_types` | Catálogo de tipos de interacción (llamada, correo, reunión, ticket) — usado como dropdown en el frontend |
| `ai_summaries` | Resúmenes ejecutivos generados por IA, asociados a un cliente |

Relaciones: `users` 1→N `interactions` (quién la registró) · `customers` 1→N `interactions` · `interaction_types` 1→N `interactions` · `customers` 1→N `ai_summaries`.

Tablas que el MVP dejó para fases posteriores: `opportunities` → se incorpora en la Fase 5 como `deals`; `customer_segments` → Fase 6 como tags de segmentación; `follow_up_tasks` → Fase 6 como `tasks`. Siguen fuera de alcance: `roles` normalizada, `audit_log`, `alerts`. El modelo de datos extendido está en la sección **Roadmap Extendido**.

## Pantallas del frontend del MVP (4 — no agregar más sin confirmar)

1. **Login** — autenticación contra el backend.
2. **Home / panel simple** — landing tras login con 2–3 métricas básicas (total de clientes, interacciones recientes).
3. **Lista de clientes** — consulta y búsqueda simple.
4. **Detalle de cliente** — una sola vista con: datos del cliente, historial de interacciones, formulario para registrar interacción, y sección para generar/ver el resumen ejecutivo IA.

## Caso de uso de IA del MVP

(En el MVP fue el único; el Roadmap Extendido agrega sugerencias de venta en la Fase 5 y analítica predictiva en la Fase 6.)

**Resumen Ejecutivo Comercial**: toma el historial de interacciones de un cliente, arma un prompt estructurado, lo envía a Gemini y guarda/muestra el resultado en la ficha del cliente. Debe manejar el caso de que el servicio externo falle o tarde (timeout configurable, error controlado — no debe romper la app).

## Requisitos funcionales clave (con criterios de aceptación resumidos)

- **Login (RF-01):** credenciales válidas → JWT; inválidas → error claro sin filtrar info sensible.
- **Clientes (RF-03):** CRUD básico, cambios visibles de inmediato en el frontend.
- **Interacciones (RF-04):** registrar y consultar, con tipo seleccionado del catálogo.
- **Resumen IA (RF-05):** generar bajo demanda desde el frontend, guardar asociado al cliente.
- **RBAC (RF-06):** solo `admin` puede modificar/eliminar recursos restringidos.
- **Frontend (RF-07):** todas las vistas muestran datos reales de PostgreSQL, nunca mock data.

## Cronograma de referencia (4 semanas, 1 dev)

1. Modelo de datos + scaffolding backend/frontend + Docker Compose.
2. Login + RBAC + CRUD de clientes + integración frontend-backend básica.
3. CRUD de interacciones + integración con Gemini + vista de detalle de cliente completa.
4. Pruebas end-to-end, manejo de errores, pulido visual, documentación, preparación de demo.

Continuación (Roadmap Extendido): Fase 5 Pipeline de ventas · Fase 6 Analítica predictiva + Tareas · Fase 7 Dashboard ejecutivo visual · Fase 8 Seed masivo, Swagger y polish. Detalle en la sección **Roadmap Extendido**.

## Decisiones ya cerradas (no reabrir sin razón fuerte)

Para no perder tiempo re-decidiendo, estos puntos quedan definidos así para todo el proyecto (MVP y Roadmap Extendido):

- **Frontend:** FastAPI + Jinja2 + Tailwind/DaisyUI + HTMX (ver stack arriba), más Chart.js vía CDN desde la Fase 7. No evaluar otras opciones a menos que algo bloquee el avance.
- **Modelo de datos:** las 5 tablas del MVP + las tablas del Roadmap Extendido (ver abajo). Si durante el desarrollo aparece una necesidad real de una tabla más, agregarla está bien — pero no agregar "por si acaso".
- **Migraciones:** se sigue sin Alembic. Las tablas nuevas las crea `SQLModel.metadata.create_all`; las columnas nuevas en tablas existentes van como `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` idempotente en `init_db()` (`app/core/database.py`), igual que se hizo con `ai_summaries.sentiment`.
- **Timeout de Gemini:** 25 segundos (subido desde 15 en la Semana 4), con un reintento automático. Si en la práctica no alcanza, ajustarlo directamente en el código sin necesidad de discutirlo antes.
- **Casos de uso de IA:** Resumen Ejecutivo Comercial (MVP, cerrado) + Sugerencias de venta (Fase 5) + Analítica predictiva: churn, lead scoring y tags (Fase 6). Siempre generados **bajo demanda** por el usuario (botón), nunca en jobs de fondo, para respetar el Free Tier.

Si en algún punto algo de esto genuinamente no funciona (por ejemplo, HTMX se queda corto para una interacción específica), está bien resolverlo sobre la marcha con el criterio más simple posible — no es necesario detenerse a pedir validación externa.

## Cómo trabajar en este repo

- Avanza por fases siguiendo el cronograma de referencia; no saltes a construir el frontend antes de tener el backend mínimo probado, ni implementes IA antes de tener interacciones persistidas.
- Si vas a instalar una librería nueva que no está en el stack definido arriba, dilo antes de hacerlo y explica por qué.
- Prioriza que cada fase quede *funcionando de punta a punta* (aunque sea mínimo) antes de añadir la siguiente.
- Cada módulo nuevo respeta las capas existentes: `app/models/` → `app/schemas/` → `app/repositories/` → `app/services/` → `app/routers/` (API JSON en `/api/...`, fragmentos HTMX y páginas en `pages.py` o un router de páginas por módulo si `pages.py` crece demasiado). La lógica se escribe una vez en el service y la reutilizan tanto la API JSON como los fragmentos HTMX.
- RBAC en módulos nuevos: lectura para ambos roles; eliminar/reasignar recursos restringido a `admin`, salvo que la fase indique otra cosa.

## Roadmap Extendido (Fases 5–8) — autorizado tras el éxito del MVP

### Fase 5 — Pipeline de Ventas y Oportunidades (Deals / Leads)

- **Modelo:** tabla `deals` (`id`, `title`, `value` NUMERIC(12,2), `stage`, `probability` 0–100, `customer_id` FK, `created_at`, `updated_at`). Etapa como enum `DealStage` guardado como VARCHAR (no ENUM nativo de Postgres): `PROSPECT` → `CONTACTED` → `PROPOSAL_SENT` → `CLOSED_WON` / `CLOSED_LOST` — sin tabla de etapas configurable.
- **Backend:** CRUD de deals + endpoint para mover de etapa (`PATCH /api/deals/{id}/stage`).
- **Frontend (nueva pantalla):** **Pipeline** — tablero Kanban con una columna por etapa; mover un deal entre etapas vía HTMX (drag & drop con SortableJS vía CDN o, si se prefiere cero JS extra, un selector de etapa por tarjeta — decidir al iniciar la fase). Los deals del cliente también se listan en su ficha de detalle.
- **IA — Sugerencias de venta:** botón en el deal (o en la ficha del cliente) que envía a Gemini el historial de interacciones + estado del deal y devuelve próximos pasos / estrategia de cierre recomendada (salida estructurada, persistida para no regenerar en cada visita).
- **Nuevas relaciones:** `customers` 1→N `deals`.

### Fase 6 — Analítica Predictiva con IA + Tareas de Seguimiento

- **IA — Analítica predictiva por cliente** (una sola llamada estructurada a Gemini, igual que resumen+sentimiento): **riesgo de churn/abandono** (nivel + justificación), **lead scoring** (0–100 + justificación) y **tags de segmentación** sugeridos. Esto reemplaza la exclusión de "detección de churn" del MVP; el badge de sentimiento de la Semana 4 se mantiene como está (es tono de interacción, distinto del churn).
- **Modelo:** resultados persistidos con fecha de cálculo (tabla `customer_insights` o columnas en `ai_summaries` — decidir al iniciar la fase, preferir lo más simple); tags en `customer_tags` (cliente ↔ tag, con origen `IA` o `manual`).
- **Tareas (Tasks):** tabla `tasks` (título, descripción, `customer_id` FK, `deal_id` FK opcional, `assigned_to` FK a `users`, fecha de vencimiento, estado pendiente/completada). Crear y completar vía HTMX desde la ficha del cliente, más una vista "Mis tareas" (pendientes/vencidas del usuario autenticado).
- **Filtros:** la lista de clientes permite filtrar por tag y por nivel de riesgo.

### Fase 7 — Dashboard Ejecutivo Visual + UX

- **Chart.js vía CDN** en el Dashboard (`/`): pipeline por etapa (monto y cantidad), deals ganados vs. perdidos, distribución de clientes por riesgo de churn / lead score / tags, actividad de interacciones en el tiempo. Datos reales agregados en `dashboard_service` (nunca mock).
- **UX Indicators / Toasts:** notificaciones toast (DaisyUI) al crear/editar/eliminar/mover recursos, disparadas vía `HX-Trigger` desde el backend; indicadores de carga consistentes en todas las acciones HTMX; estados vacíos cuidados.

### Fase 8 — Seed Masivo, Swagger Docs y Polish Final

- **Seed data masivo** en `app/seed.py` (idempotente, como el actual): 30+ clientes realistas, interacciones variadas por cliente, deals repartidos en todas las etapas, algunas tareas — para que dashboard, pipeline y analítica se vean con datos en la demo. Sin llamar a Gemini desde el seed.
- **Swagger/OpenAPI:** tags por módulo, descripciones, ejemplos en los schemas y respuestas de error documentadas en todos los endpoints `/api/...`.
- **Polish final:** revisión end-to-end de todos los flujos en navegador, consistencia visual, manejo de errores y actualización de documentación.

### Modelo de datos extendido (resumen)

MVP (5): `users`, `customers`, `interactions`, `interaction_types`, `ai_summaries`.
Roadmap Extendido: `deals` (F5) · `sales_suggestions` (F5) · `customer_insights` o equivalente (F6) · `customer_tags` (F6) · `tasks` (F6).

### Pantallas extendidas (resumen)

MVP (4): Login, Dashboard, Lista de clientes, Detalle de cliente.
Roadmap Extendido: **Pipeline** (F5, tablero Kanban) · **Mis tareas** (F6). El Dashboard (F7) y el Detalle de cliente (F5–F6) se amplían, no se duplican.

## Progreso

### Semana 1 — Completada ✅

- **Scaffolding backend**: FastAPI con arquitectura por capas (`app/routers`, `app/services`, `app/repositories`, `app/models`, `app/core`), demostrada de punta a punta con el flujo `/api/health` (Router → Service → Repository → PostgreSQL).
- **Modelo de datos**: las 5 tablas del MVP creadas vía SQLModel (`app/models/`) con sus PKs, FKs y relaciones — `users`, `customers`, `interactions`, `interaction_types`, `ai_summaries`. Verificadas en PostgreSQL con `\dt`.
- **Frontend scaffolding**: Jinja2 + Tailwind/DaisyUI (CDN) + HTMX conectados (`app/templates/`), con un ejemplo funcional (`/fragments/health-check`).
- **Docker Compose**: `docker compose up --build -d` levanta `db` (Postgres 16, healthcheck) y `app` (FastAPI con reload) sin errores.
- **Seed de datos**: `app/seed.py` ejecutado y verificado — puebla `interaction_types` (Llamada, Correo, Reunión, Ticket) y crea el usuario admin base. Confirmado idempotente (corrido dos veces, sin duplicados: 4 tipos, 1 usuario).
- **Hashing de contraseñas**: `app/core/security.py` (bcrypt vía passlib) listo para el login de la Semana 2.
- Pendiente explícito para la Semana 2 (no iniciado): login real con JWT, RBAC, CRUD de clientes.

### Semana 2 — Completada ✅

- **Auth JWT (RF-01)**: `POST /api/auth/login` (`app/routers/auth.py`) valida credenciales contra `users` (`app/services/auth_service.py`, `app/repositories/user_repository.py`) y setea el JWT en una cookie **HttpOnly** (`app/core/security.py`: `create_access_token`/`decode_access_token` vía `python-jose`). Credenciales inválidas → error genérico sin filtrar info sensible. Probado con curl y en navegador.
- **RBAC (RF-06)**: `app/core/dependencies.py` — `get_current_user` (cualquier rol autenticado, lee la cookie) y `require_role`/`require_admin` (solo `admin`). Verificado con un usuario `comercial` de prueba: puede listar clientes pero recibe `403` al crear/editar/eliminar.
- **CRUD de clientes (RF-03)**: capas completas — `app/repositories/customer_repository.py` (crear, obtener por id, listar, buscar por nombre/email), `app/services/customer_service.py` (lógica + 404 controlado), `app/routers/customers.py` (`GET`/`POST`/`PUT`/`DELETE /api/customers`, lectura abierta a cualquier rol autenticado, escritura restringida a `admin`). Esquemas de entrada/salida en `app/schemas/customer.py`. Probado end-to-end contra PostgreSQL real (crear, listar, buscar, actualizar, borrar, 404, RBAC).
- **Frontend conectado (RF-07)**: pantallas **Login** (`/login`) y **Lista de clientes** (`/customers`) en Jinja2 + TailwindCSS/DaisyUI (CDN) + HTMX (`app/templates/login.html`, `app/templates/customers.html` + partial `customers_table.html`, `app/routers/pages.py`). Login envía el form por HTMX al endpoint de auth y redirige al panel de clientes; errores de credenciales se muestran inline sin recargar. Lista de clientes muestra datos reales de Postgres (nunca mock) con buscador dinámico (`?q=`) que filtra por nombre/email vía HTMX sin recargar la página. Rutas de página protegidas: sin sesión válida, redirigen a `/login` (`get_current_user_optional` en `app/core/dependencies.py`).
- **Verificado visualmente en navegador** (Chrome real): carga de `/login` con estilo DaisyUI, error de credenciales inválidas inline, login exitoso con redirect a `/customers`, tabla con datos reales, búsqueda dinámica por nombre y por email, sin errores de consola.

### Semana 3 — Completada ✅

- **CRUD de interacciones (RF-04)**: capas completas — `app/schemas/interaction.py`, `app/repositories/interaction_repository.py` (crear, listar historial por cliente), `app/services/interaction_service.py` (valida que el cliente y el tipo de interacción existan, asigna automáticamente al usuario autenticado como autor), `app/routers/interactions.py` (`GET`/`POST /api/customers/{id}/interactions`, protegidos con `get_current_user`, abiertos a ambos roles — RF-04 no restringe por rol). Registrado en `main.py`. Probado end-to-end contra PostgreSQL real: creación con autor correcto, listado, 404 por cliente inexistente, 404 por tipo de interacción inválido, 401 sin autenticación.
- **Resumen IA (RF-05)**: librería **`google-genai==2.24.0`** (SDK oficial actual de Google, sucesor de `google-generativeai`) agregada a `requirements.txt`. `app/services/ai_service.py` arma el prompt estructurado (puntos clave, estado/sentimiento, siguientes pasos) a partir del historial real de interacciones del cliente, llama a Gemini (`client.models.generate_content`, modelo `gemini-3.6-flash` — `gemini-2.5-flash` fue retirado y la propia API indicó el reemplazo) con timeout configurable vía `GEMINI_TIMEOUT_SECONDS` (`HttpOptions(timeout=...)` en milisegundos) y un reintento automático ante timeout/error de API (`httpx.TimeoutException`, `httpx.ConnectError`, `google.genai.errors.APIError`), sin romper la app (error controlado `AIServiceError`). Persistencia vía `app/repositories/ai_summary_repository.py` (incluye `get_latest_by_customer` para mostrar el último resumen generado); schema de salida en `app/schemas/ai_summary.py`. Endpoint `POST /api/customers/{id}/summarize` en `app/routers/customers.py` (protegido con `get_current_user`, cualquier rol) ejecuta el análisis, guarda en `ai_summaries` y retorna el resumen; `400` si el cliente no tiene interacciones (error de validación, no de Gemini), `502` si Gemini falla tras el reintento. **Probado contra la API real de Gemini** con las interacciones registradas: resumen generado y persistido correctamente; timeout/reintento verificado forzando un deadline insuficiente (falla controlada, sin crash).
- **Vista de detalle de cliente (frontend)**: `GET /customers/{id}` (`app/routers/pages.py` → `app/templates/customer_detail.html`) muestra en una sola pantalla los datos del cliente, la tarjeta de **Resumen Ejecutivo (IA)** y el historial de interacciones + formulario para registrar una nueva, tal como define la Pantalla 4 del MVP. Todo carga con datos reales de PostgreSQL (customer_service, interaction_service, `interaction_type_repository.get_all` para el dropdown de tipos, `ai_summary_repository.get_latest_by_customer` para precargar el último resumen si existe).
  - **Nueva interacción vía HTMX**: el formulario postea a `POST /fragments/customers/{id}/interactions` (nuevo endpoint en `pages.py`, reutiliza `interaction_service.create_interaction`) y re-renderiza el partial `partials/interactions_list.html`, insertando la interacción al tope del historial sin recargar la página; el formulario se limpia solo tras un envío exitoso.
  - **Resumen IA vía HTMX**: el botón "Generar Resumen" postea a `POST /fragments/customers/{id}/summarize` (nuevo endpoint en `pages.py`, reutiliza `ai_service.generate_summary` — la misma lógica que expone la API JSON) y swapea el resultado en `partials/ai_summary_result.html`; muestra un spinner (`hx-indicator` + `loading loading-spinner` de DaisyUI) y deshabilita el botón (`hx-disabled-elt`) mientras Gemini responde. Errores controlados (cliente sin interacciones, falla de Gemini) se renderizan como una alerta inline (`alert-error`) sin romper la vista, en vez de propagar el status HTTP de error al swap de HTMX.
  - La lista de clientes (`partials/customers_table.html`) ahora enlaza cada fila a su vista de detalle.
  - **Verificado en navegador (Chrome real) de punta a punta**: login → lista de clientes → detalle de "Acme Corp" (con resumen previo ya cargado desde la Semana 3 anterior) → registro de una nueva interacción (aparece al instante en el historial, sin reload) → generación de un nuevo resumen que refleja ambas interacciones (spinner visible durante la llamada, botón deshabilitado, resultado swapeado correctamente) → verificado también el caso sin interacciones ("Gamma Retail": placeholder inicial correcto y alerta de error inline al intentar generar resumen sin datos). Sin errores en consola (solo el warning esperado de Tailwind CDN, ya presente desde la Semana 1).
- Semana 3 cierra las 4 pantallas y los 5 RF clave (RF-01, RF-03 a RF-07) definidos para el MVP. Pendiente para la Semana 4 (no iniciado): pruebas end-to-end adicionales, manejo de errores más pulido, home/panel con métricas básicas (Pantalla 2, aún no construida — sigue siendo el placeholder de scaffolding en `index.html`), pulido visual y preparación de demo.

### Semana 4 — Completada ✅

- **Dashboard de métricas (Pantalla 2, RF-07)**: `GET /` (`app/routers/pages.py`) ahora requiere sesión (redirige a `/login` igual que el resto de las vistas, ya no es un placeholder abierto) y renderiza `index.html` con datos reales de PostgreSQL vía `app/services/dashboard_service.py`: total de clientes, total de interacciones y total de resúmenes IA generados (`count()` agregado a `customer_repository`, `interaction_repository` y `ai_summary_repository`), más las 5 interacciones y 5 clientes más recientes (`get_recent()` en los mismos repositorios) para las tarjetas de "Actividad reciente" y "Clientes recientes" (cada una linkea directo al detalle del cliente).
- **Navegación (RF-07)**: `base.html` agrega el link "Dashboard" junto a "Clientes" en el navbar, con estado activo (`btn-active`) resuelto por `request.url.path`, para que el flujo Dashboard ↔ Lista de clientes ↔ Detalle sea consistente.
- **Bonus — Sentiment Analysis (extensión del único caso de uso de IA, no uno nuevo)**: el mismo prompt/llamada de "Resumen Ejecutivo Comercial" ahora le pide a Gemini clasificar también el sentimiento general del cliente. Se evaluó explícitamente con el usuario el riesgo de que esto se solape con "detección de churn" (excluida del MVP) y se resolvió usando las etiquetas **POSITIVO / NEUTRAL / NEGATIVO** (en vez de "EN RIESGO") para dejar claro que es tono de la interacción, no un scoring de abandono.
  - `app/models/ai_summary.py`: enum `Sentiment` (POSITIVO/NEUTRAL/NEGATIVO) y columna `sentiment` (string) en `ai_summaries`.
  - `app/core/database.py`: como el MVP no usa Alembic, `init_db()` aplica un `ALTER TABLE ai_summaries ADD COLUMN IF NOT EXISTS sentiment ...` idempotente en cada arranque, para no perder los resúmenes ya guardados al agregar la columna.
  - `app/services/ai_service.py`: en vez de parsear texto libre, usa `response_schema` de Gemini (salida JSON estructurada) con un modelo Pydantic `{resumen, sentimiento}` — más confiable que un regex sobre markdown. Sigue siendo una única llamada a Gemini, con el mismo timeout/reintento controlado.
  - `app/schemas/ai_summary.py` expone `sentiment` también en el endpoint JSON (`POST /api/customers/{id}/summarize`).
  - `partials/ai_summary_result.html` muestra un badge de color junto al resumen en la ficha del cliente (verde=POSITIVO, amarillo=NEUTRAL, rojo=NEGATIVO).
  - **Ajuste de timeout**: `GEMINI_TIMEOUT_SECONDS` subió de 15 a 25 (en `.env`, `.env.example` y el default en `config.py`) porque el modelo `gemini-3.6-flash` está tardando ~14s en el free tier y estaba pegado al límite anterior; cambio permitido directamente por la decisión ya cerrada sobre el timeout de Gemini. Verificado con la API real: falla controlada ante 503/504 de Gemini (alert-error inline, sin romper la app) y generación exitosa end-to-end con el badge correcto persistido en Postgres.
- **Bonus — Exportación de clientes a CSV**: `GET /customers/export/csv` (`app/routers/pages.py`, protegido igual que el resto de las páginas — redirige a `/login` sin sesión, sin restricción de rol porque no es más permisivo que la lista de clientes ya visible a ambos roles) arma el CSV (ID, Nombre, Email, Teléfono, Fecha de Registro) vía `customer_service.export_customers_csv` usando el módulo `csv` de la librería estándar (sin dependencias nuevas) y lo devuelve como descarga (`Content-Disposition: attachment`, con BOM UTF-8 para que Excel muestre bien los acentos). Botón "Exportar a CSV" (DaisyUI `btn btn-outline btn-sm`) agregado en la cabecera de `customers.html`, junto al buscador.
- Ambos bonus se confirmaron con el usuario antes de implementarse por ser adiciones no listadas explícitamente en este documento (un endpoint nuevo y una extensión del caso de uso de IA), siguiendo la regla de "avisar en vez de implementar directamente" cuando algo no está cubierto por el alcance original.

### Fase 5 — Pipeline de Ventas y Oportunidades — Completada ✅

- **Parte 1 (modelo + repositorio) ✅**: `app/models/deal.py` (entidad `Deal` + enum `DealStage`, `updated_at` con `onupdate`), relación `Customer.deals` ↔ `Deal.customer`, registrado en `app/models/__init__.py`. `app/repositories/deal_repository.py`: `create`, `get_by_id`, `get_all(stage=None)` (filtro por etapa), `get_by_customer`, `count`, `update`, `delete`. La tabla la crea `create_all` en `init_db()` (idempotente, solo crea lo que falta). Verificado en Docker: tabla `deals` creada con índices en `stage` y `customer_id` y FK a `customers`; datos existentes intactos (conteos iguales antes/después); smoke test del repositorio (crear, filtrar por etapa, actualizar con cambio de `updated_at`, relación en ambos sentidos, borrar) OK; sin errores en logs.
- **Parte 2 (API) ✅**: `app/schemas/deal.py` (`DealCreate`, `DealUpdate` parcial, `DealStageUpdate`, `DealRead`; validación `probability` 0–100, `value` ≥ 0, etapa del enum). `app/services/deal_service.py`: valida que el cliente exista (404), regla de etapas cerradas (`CLOSED_WON` fija `probability=100`, `CLOSED_LOST` fija `0`, se aplica en crear/editar/mover), `updated_at` explícito en cada cambio. `app/routers/deals.py` (registrado en `main.py`): `GET /api/deals` (filtros `?stage=` y `?customer_id=`), `GET/PATCH/DELETE /api/deals/{id}`, `POST /api/deals`, `PATCH /api/deals/{id}/stage`. RBAC: leer, crear, editar y mover etapa → ambos roles (los comerciales operan su pipeline); eliminar → solo `admin`.
- **Borrado protegido de clientes**: `customer_service.delete_customer` devuelve **409** con mensaje claro (ej. "tiene registros asociados: 1 deal, 2 interacciones, 4 resúmenes IA") si el cliente tiene deals, interacciones o resúmenes IA (`count_by_customer` en los tres repositorios); también captura `IntegrityError` → 409 ante carreras. Antes terminaba en 500 por la FK.
- Verificado end-to-end contra la API real (script curl con admin + usuario `comercial` temporal): 401 sin sesión, 201 crear, 404 cliente/deal inexistente, 422 etapa/probabilidad/valor inválidos, filtros por etapa, PATCH parcial, cambios de etapa con probabilidad automática, 409 al borrar cliente con actividad, 204 al borrar cliente sin actividad, 403 comercial borrando deal, 204 admin. Datos de prueba limpiados; Swagger lista los 6 endpoints y 5 schemas de deals; sin errores en logs.
- **Parte 3 (Pipeline Kanban + UI) ✅**: nueva pantalla `GET /pipeline` (`pipeline.html` + partial `partials/pipeline_board.html`) con 5 columnas (Prospecto, Contactado, Propuesta Enviada, Ganado, Perdido — `deal_service.STAGE_LABELS`), contador y monto total por columna (`deal_service.get_pipeline`; `deal_repository.get_all` precarga el cliente con `selectinload` para evitar N+1). Link "Pipeline" en el navbar (`base.html`, que ahora tiene un `{% block scripts %}`).
  - **Drag & drop**: **SortableJS 1.15.2 (CDN jsdelivr)** con `forceFallback: true` (eventos de puntero en vez de DnD nativo: consistente entre navegadores y touch). Al soltar en otra columna, `htmx.ajax("PATCH", "/api/deals/{id}/stage")` envía `{"stage": ...}` como JSON gracias a la extensión oficial **`json-enc` de HTMX 1.9.12** (misma versión que htmx), y luego recarga el tablero desde `GET /fragments/pipeline/board` para reflejar contadores/totales/probabilidad reales. Ante error (404, 401, red) muestra una alerta inline y el tablero se resincroniza (la tarjeta vuelve a su lugar real).
  - **Crear deal desde el tablero**: modal DaisyUI (`<dialog>`) con cliente, título, monto, probabilidad y etapa → `POST /fragments/deals` (reusa `deal_service.create_deal`), re-renderiza el tablero y cierra el modal.
  - **Deals en la ficha del cliente** (`customer_detail.html`): tarjeta "Deals" (partial `partials/customer_deals_list.html`: título, monto, badge de etapa por color, probabilidad, fecha) + formulario "Nuevo deal" → `POST /fragments/customers/{id}/deals`.
  - Errores de validación/cliente inexistente en ambos formularios: el endpoint responde con `HX-Retarget`/`HX-Reswap` hacia la alerta del formulario (`partials/form_error.html`) en vez de reemplazar el tablero/lista. Macros compartidas en `partials/_deal_macros.html` (badge de etapa + campos del formulario); filtro Jinja `money` y global `stage_labels` en `pages.py`.
  - **Verificado en Chrome real** con usuario `comercial` temporal: crear deal desde el modal, drag & drop Prospecto→Ganado (probabilidad pasa a 100 % tras la recarga) y Ganado→Contactado (request confirmado: `PATCH /api/deals/{id}/stage`, `Content-Type: application/json`, body `{"stage":"CONTACTED"}`), error controlado al mover un deal borrado ("Deal no encontrado" + resync), crear deal desde la ficha del cliente (aparece en la tabla y en el Pipeline). Consola sin errores (solo el warning conocido de Tailwind CDN); logs de Docker sin errores. Datos de prueba eliminados.
  - Nota: el drag de la herramienta de automatización (un solo movimiento instantáneo) no dispara Sortable; se verificó con eventos de puntero graduales simulados en la página, que recorren el mismo flujo que un mouse real.
- **Parte 4 (reapertura + Sugerencias de venta IA) ✅**:
  - **Probabilidad al reabrir**: un deal `CLOSED_WON`/`CLOSED_LOST` que vuelve a una etapa abierta toma la probabilidad base de esa etapa (`OPEN_STAGE_DEFAULT_PROBABILITY` en `deal_service`: Prospecto 10 %, Contactado 30 %, Propuesta Enviada 60 %). Aplica tanto al drag & drop (`PATCH /stage`) como al `PATCH /api/deals/{id}`; si ese PATCH trae `probability` explícita, se respeta. Movimientos entre etapas abiertas conservan la probabilidad.
  - **IA — Sugerencias de venta** (segundo caso de uso de IA, autorizado en el Roadmap): `ai_service.generate_sales_suggestions` arma un prompt con el historial de interacciones + deals activos (y los cerrados como contexto histórico) y pide a Gemini salida estructurada `{proximos_pasos: [str], estrategia_cierre: str}` (3–5 pasos priorizados + párrafo de estrategia con riesgos/objeciones). `_call_gemini` se generalizó (prompt, system instruction, `response_schema`, descripción de la tarea) y lo comparten el resumen ejecutivo y las sugerencias: mismo modelo, timeout `GEMINI_TIMEOUT_SECONDS` (25 s), 1 reintento, `AIServiceError` controlado. `400` si el cliente no tiene interacciones.
  - **Persistencia**: nueva tabla `sales_suggestions` (`app/models/sales_suggestion.py`: `next_steps` JSON, `closing_strategy`, `generated_at`, `customer_id` FK) + `app/repositories/sales_suggestion_repository.py` (`create`, `get_latest_by_customer`, `count_by_customer`) + `app/schemas/sales_suggestion.py`. El borrado protegido de clientes (409) también cuenta las sugerencias.
  - **Endpoints**: `POST /api/customers/{id}/sales-suggestions` (JSON, 201; 502 si Gemini falla tras el reintento) y `POST /fragments/customers/{id}/sales-suggestions` (HTMX; errores como alerta inline en `partials/sales_suggestion_result.html`).
  - **UI**: tarjeta "Sugerencias de venta (IA)" en `/customers/{id}` con botón "Obtener sugerencias de venta" (spinner + botón deshabilitado durante la llamada), muestra la última sugerencia guardada al cargar la ficha.
  - **Verificado**: reglas de probabilidad al reabrir (todas las combinaciones) vía API; generación real con Gemini (~9.5 s, 4 pasos + estrategia que cita los deals activos y el ganado, persistida en BD); falla real de Gemini (503 "high demand" en ambos intentos) → 502 controlado sin romper la app; en Chrome: sugerencia precargada, generación nueva con spinner/botón deshabilitado y swap HTMX, alerta inline para cliente sin interacciones, consola sin errores; logs de Docker sin tracebacks. Datos de prueba eliminados.
### Fase 6 — Analítica Predictiva con IA + Tareas — Completada ✅

- **Parte 1 (backend) ✅**:
  - **Modelos**: `customer_insights` (`app/models/customer_insight.py`: `lead_score` 0–100 + `lead_score_justification`, `churn_risk` enum `ChurnRisk` BAJO/MEDIO/ALTO como VARCHAR + `churn_justification`, `suggested_tags` JSON, `suggested_tasks` JSON `[{title, priority, due_date}]`, `generated_at`, `customer_id` FK) — se eligió tabla propia en vez de columnas en `ai_summaries`. `tasks` (`app/models/task.py`: `title`, `description`, `status` PENDING/DONE, `priority` LOW/MEDIUM/HIGH, `due_date`, `created_at`, `customer_id` FK, `deal_id` FK opcional con `ON DELETE SET NULL`, `assigned_to` FK a `users`).
  - **IA — Analítica predictiva**: `ai_service.generate_insights` envía perfil + interacciones + deals + tareas pendientes (para no repetirlas) en una sola llamada estructurada (`_call_gemini`, mismo timeout/reintento/`AIServiceError`). Lead score y días de vencimiento se acotan en el servidor; tags normalizados (minúsculas, sin duplicados, máx. 5); máx. 3 tareas sugeridas. Las tareas sugeridas **no se crean solas** (evita automatización): quedan en el insight para que el usuario decida.
  - **API**: `GET`/`POST /api/customers/{id}/insights` (último análisis / generar; 400 sin interacciones, 404 sin análisis previo, 502 si Gemini falla tras el reintento). `/api/tasks` (`app/routers/tasks.py`): `GET` con filtros `customer_id`, `assigned_to`, `status`, `mine`, `overdue`; `POST`; `GET`/`PATCH`/`DELETE /{id}`. RBAC: crear/editar/completar → ambos roles (por defecto se asigna al usuario autenticado); asignar/reasignar a otro usuario y eliminar → solo `admin`. Valida cliente, deal (debe pertenecer al cliente → 422) y usuario asignado. El borrado protegido de clientes (409) también cuenta insights y tareas.
  - **Verificado** (script contra la API real + Gemini real, 38/38 checks): tablas/índices/FKs en Postgres, RBAC, validaciones, filtros `mine`/`overdue`, borrar deal deja la tarea con `deal_id` NULL, insight real persistido (~12 s), timeout forzado → `AIServiceError` tras 2 intentos. Logs sin errores; datos de prueba eliminados.
- **Parte 2 (tags + UI HTMX) ✅**:
  - **`customer_tags`** (`app/models/customer_tag.py`: `name` normalizado —minúsculas, espacios simples, máx. 40—, `source` `TagSource` IA/MANUAL, único por `(customer_id, name)`) + `customer_tag_repository` + `customer_tag_service` (`normalize_tag_name` compartido con `ai_service`). API: `GET`/`POST /api/customers/{id}/tags` (409 duplicado, 422 vacío) y `DELETE /api/customers/{id}/tags/{tag_id}` (solo `admin`). Los tags no bloquean el borrado del cliente: se eliminan con él.
  - **Filtros de clientes**: `GET /api/customers?tag=&churn=` y en `/customers` (selects de tag y churn + buscador, combinables, vía HTMX). El churn considera solo el **análisis más reciente** de cada cliente (`customer_insight_repository.latest_ids_subquery`, max id por cliente). La tabla muestra lead score, badge de churn y tags.
  - **Ficha del cliente**: tarjeta **"Analítica IA & Insights"** (lead score radial, badge de churn, justificaciones, botón "Generar Insights" con spinner) + tags (aplicados con marca IA, sugeridos por IA aplicables con un clic, alta manual, quitar solo admin). Tarjeta **"Tareas de seguimiento"**: formulario manual (prioridad, vencimiento, deal abierto, "Asignar a" solo para admin), tareas sugeridas por IA convertibles en un clic (quedan marcadas "✓ Creada" si ya existe una tarea con el mismo título) y lista con checkbox PENDING ↔ DONE. Generar insights refresca tags y tareas out-of-band (`hx-swap-oob`).
  - **"Mis tareas"** (`GET /tasks`, link en el navbar): filtros estado (Pendientes/Vencidas/Completadas/Todas), prioridad y asignado (a mí / todos / usuario), vencidas en rojo, cambio de estado vía HTMX devolviendo solo la fila.
  - **Estructura**: `templates` y `form_error` se movieron a `app/core/templating.py`; nuevos routers de páginas `app/routers/insight_pages.py` (fragmentos de la ficha) y `app/routers/task_pages.py` ("Mis tareas") para no seguir creciendo `pages.py`. Macros en `partials/_insight_macros.html`.
  - **Verificado**: script contra la API real + Gemini real (50/50 checks: tags, RBAC, filtros, fragmentos, OOB, errores inline) y regresión de la Parte 1; en Chrome real con usuario `comercial` temporal: filtros de churn/tag/búsqueda, generación de insights (un 503 real de Gemini se mostró como alerta inline sin romper la ficha; el reintento generó el análisis), aplicar tag IA, tag manual, sugerencia → tarea en un clic, completar tareas desde la ficha y desde "Mis tareas". Se corrigió un `htmx:syntax:error` en el `hx-trigger` de `/customers`; consola final solo con el warning conocido de Tailwind CDN. Datos de prueba eliminados.
### Fase 7 — Dashboard Ejecutivo Visual + Toasts — Completada ✅

- **Dashboard (`GET /` + `GET /fragments/dashboard`)**: `dashboard_service.get_dashboard_data` arma todo con agregaciones SQL reales (`deal_repository.stage_summary` — cantidad, monto y monto ponderado por etapa en un solo `GROUP BY`; `customer_repository.count_active`/`churn_distribution`; `interaction_repository.count_by_day`; `task_repository.count_pending`). Partial `partials/dashboard_content.html`:
  - **KPIs**: Ingresos (monto `CLOSED_WON`), Pipeline abierto (monto + ponderado por probabilidad), Clientes activos (interacción en 30 días o deal abierto, sobre el total), Conversión (ganados / cerrados; "—" sin cerrados), Tareas pendientes (+ vencidas, link a "Mis tareas").
  - **Pipeline por etapa**: las 5 etapas con badge, cantidad, monto y barra proporcional.
  - **Actividad reciente**: interacciones + deals (nuevo/actualizado, con etapa y monto) en una sola línea de tiempo (8 eventos), cada uno linkea a la ficha.
  - **Chart.js 4.4.1 (CDN)**: interacciones por día (30 días, barras) y clientes por riesgo de churn (último análisis de cada cliente, colores de estado + etiquetas). Datos inyectados como JSON (`<script type="application/json">`); los gráficos se recrean en `htmx:afterSettle`.
  - **Reactivo**: refresco HTMX cada 60 s solo con la pestaña visible, al volver a la pestaña y con el botón "Actualizar". Estados vacíos para cada sección.
  - **Responsivo**: KPIs en 2 columnas en móvil / 5 en escritorio; navbar con menú desplegable (hamburguesa) bajo `md`.
- **Toasts (`partials/_toast.html`, incluido en `base.html`)**: helper `toast(response, message, level)` en `app/core/templating.py` setea `HX-Trigger: {"showToast": {...}}` (JSON con `ensure_ascii` para headers latin-1); el JS los pinta como `alert` DaisyUI (success/error/warning/info, auto-cierre, clic para cerrar, `textContent` contra XSS). `form_error` emite además un toast de advertencia; `ai_error` clasifica fallos de IA (validación → warning, `AIServiceError` de Gemini → error). Un handler global de `htmx:responseError`/`htmx:sendError` convierte cualquier 4xx/5xx/caída de red en toast (401 → sesión expirada, 403, 422, `detail` del JSON). Barra de progreso global mientras haya requests HTMX.
  - Integrado en: interacciones, tags (aplicar/quitar/duplicado), deals (crear desde Pipeline y ficha; mover etapa — el `PATCH /api/deals/{id}/stage` agrega el header solo si viene de HTMX, warning al pasar a Perdido), tareas (crear, completar/reabrir, error) y Gemini (resumen, sugerencias, insights). El Pipeline reemplazó su alerta inline de error por el toast.
- **Verificado**: curl de todos los endpoints con `HX-Trigger`; en Chrome real: KPIs y ponderado correctos con deals de prueba en las 5 etapas, refresco reactivo (interacción creada por API aparece tras "Actualizar" y clientes activos sube), toasts de mover etapa (éxito, warning Perdido, 404), resumen real de Gemini, tag, tag duplicado, interacción, tarea creada y completada; fallo de Gemini mockeado → toast `error`; layout sin overflow a 360/768/1024 px. Consola solo con el warning conocido de Tailwind CDN; logs sin errores. Datos de prueba eliminados.
### Fase 8 — Seed Masivo, Swagger Docs y Polish Final — Pendiente ⏳
