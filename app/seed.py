"""Script de inicialización de datos.

1. Datos base: catálogo de interaction_types y usuario admin.
2. Datos de demostración (Fase 8): 30 clientes realistas con interacciones
   históricas, deals en las 5 etapas del pipeline, tareas (pendientes, vencidas y
   completadas), análisis predictivos y tags, para que dashboard, pipeline,
   filtros y "Mis tareas" tengan datos en la demo.

Es idempotente: se puede ejecutar varias veces sin duplicar datos. Cada cliente
de demo se identifica por su email; si ya existe, se omite junto con todo su
historial. No llama a Gemini: los análisis predictivos son datos de ejemplo.

Uso local:      python -m app.seed
Uso en Docker:  docker compose exec app python -m app.seed
"""

import random
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from sqlmodel import Session, select

from app.core.config import settings
from app.core.database import engine, init_db
from app.core.security import hash_password
from app.models import (
    ChurnRisk,
    Customer,
    CustomerInsight,
    CustomerTag,
    Deal,
    DealStage,
    Interaction,
    InteractionType,
    TagSource,
    Task,
    TaskPriority,
    TaskStatus,
    User,
    UserRole,
)

INTERACTION_TYPES = ["Llamada", "Correo", "Reunión", "Ticket"]

# --- Datos base ---------------------------------------------------------------


def seed_interaction_types(session: Session) -> None:
    for name in INTERACTION_TYPES:
        existing = session.exec(
            select(InteractionType).where(InteractionType.name == name)
        ).first()
        if not existing:
            session.add(InteractionType(name=name))
    session.commit()


def seed_admin_user(session: Session) -> None:
    existing = session.exec(
        select(User).where(User.email == settings.admin_email)
    ).first()
    if existing:
        return

    admin = User(
        full_name=settings.admin_full_name,
        email=settings.admin_email,
        hashed_password=hash_password(settings.admin_password),
        role=UserRole.ADMIN,
    )
    session.add(admin)
    session.commit()


# --- Datos de demostración ----------------------------------------------------

# (contacto, empresa, dominio, sector → tag manual, perfil)
DEMO_CUSTOMERS = [
    ("Mariana Ortega", "Logística Andina S.A.", "logisticaandina.com", "logística", "champion"),
    ("Javier Rojas", "Grupo Ferretero del Sur", "ferreterodelsur.com", "retail", "active"),
    ("Lucía Benítez", "Clínica Santa Elena", "clinicasantaelena.com", "salud", "champion"),
    ("Andrés Castillo", "Constructora Altamira", "altamira.com.ar", "construcción", "active"),
    ("Valentina Morales", "Café Montaña Verde", "montanaverde.com", "gastronomía", "new_lead"),
    ("Diego Herrera", "TransCargo Express", "transcargo.com", "logística", "at_risk"),
    ("Camila Navarro", "Farmacias Bienestar", "farmaciasbienestar.com", "salud", "active"),
    ("Sebastián Vargas", "Agroexportadora El Valle", "agroelvalle.com", "agro", "champion"),
    ("Daniela Fuentes", "Colegio San Ignacio", "sanignacio.edu.ar", "educación", "new_lead"),
    ("Martín Ríos", "Hotel Costa Azul", "hotelcostaazul.com", "turismo", "at_risk"),
    ("Paula Méndez", "Estudio Jurídico Méndez & Asociados", "estudiomendez.com", "servicios", "dormant"),
    ("Tomás Aguilar", "Panificadora La Espiga", "laespiga.com", "gastronomía", "new_lead"),
    ("Florencia Paz", "Textiles del Norte", "textilesdelnorte.com", "industria", "active"),
    ("Ricardo Salinas", "Distribuidora Pacífico", "distpacifico.com", "retail", "champion"),
    ("Gabriela Cruz", "Inmobiliaria Horizonte", "horizonteprop.com", "servicios", "active"),
    ("Nicolás Peña", "Talleres Mecánicos Peña", "tallerespena.com", "servicios", "dormant"),
    ("Sofía Romero", "Óptica Visión Clara", "visionclara.com", "salud", "new_lead"),
    ("Emilio Torres", "Minera Cerro Alto", "cerroalto.com", "industria", "active"),
    ("Carolina Ibarra", "Instituto Superior del Litoral", "isdellitoral.edu.ar", "educación", "champion"),
    ("Federico Luna", "Restaurantes Sabor Criollo", "saborcriollo.com", "gastronomía", "at_risk"),
    ("Isabel Domínguez", "Laboratorio BioAnálisis", "bioanalisis.com", "salud", "active"),
    ("Gonzalo Medina", "Seguros Previsión", "segurosprevision.com", "servicios", "at_risk"),
    ("Natalia Campos", "Editorial Páginas Abiertas", "paginasabiertas.com", "servicios", "new_lead"),
    ("Hernán Ruiz", "Frigorífico La Pampa", "frigolapampa.com", "agro", "champion"),
    ("Verónica Salas", "Centro Odontológico Sonrisa", "odontosonrisa.com", "salud", "dormant"),
    ("Joaquín Molina", "Energía Solar Andes", "solarandes.com", "industria", "active"),
    ("Renata Silva", "Moda Urbana Boutique", "modaurbana.com", "retail", "at_risk"),
    ("Pablo Guzmán", "Viñedos Santa Rosa", "vinedossantarosa.com", "agro", "new_lead"),
    ("Elena Cabrera", "Consultora Nexo Digital", "nexodigital.com", "servicios", "cold"),
    ("Mateo Figueroa", "Gimnasio Fuerza Total", "fuerzatotal.com", "servicios", "cold"),
]

# Historial por perfil: (días atrás, tipo, nota). {contact}/{company} se completan por cliente.
INTERACTION_SCRIPTS = {
    "champion": [
        (85, "Reunión", "Reunión de kickoff con {contact} ({company}): se definieron objetivos del trimestre y responsables por área."),
        (60, "Correo", "Envío del informe mensual de uso; {contact} respondió conforme y pidió agregar un tablero por sucursal."),
        (34, "Llamada", "Seguimiento trimestral: el equipo de {company} reporta ahorro de tiempo en la operación. Interés en ampliar licencias."),
        (12, "Reunión", "Presentación de la propuesta de ampliación a gerencia. Buena recepción; piden escalonar el pago en dos cuotas."),
        (3, "Correo", "{contact} confirma que la ampliación entra en el presupuesto del próximo mes y solicita el contrato actualizado."),
    ],
    "active": [
        (40, "Llamada", "Primer contacto con {contact}: {company} evalúa reemplazar su planilla de seguimiento comercial."),
        (28, "Reunión", "Demo del sistema para el equipo de {company}. Preguntas sobre la integración con su facturación."),
        (15, "Correo", "Envío de la propuesta económica y del cronograma de implementación en tres etapas."),
        (6, "Llamada", "{contact} comenta que compras está comparando con otro proveedor; pide mejorar el plazo de pago."),
    ],
    "new_lead": [
        (9, "Correo", "{contact} completó el formulario web solicitando información de precios para {company}."),
        (4, "Llamada", "Llamada de calificación: equipo comercial de 8 personas; buscan ordenar el seguimiento de clientes antes de fin de año."),
    ],
    "at_risk": [
        (70, "Reunión", "Revisión de servicio con {company}: conformes en general, piden mejorar los tiempos de respuesta de soporte."),
        (38, "Ticket", "Ticket: errores al exportar reportes desde la sucursal principal. {contact} indica que afecta el cierre mensual."),
        (21, "Ticket", "Segundo reclamo por demoras en la resolución del ticket anterior. Tono molesto."),
        (8, "Llamada", "{contact} menciona que están evaluando alternativas si no se resuelve antes de la renovación."),
    ],
    "dormant": [
        (150, "Reunión", "Reunión de presentación con {contact}; interés moderado, sin presupuesto asignado este año."),
        (110, "Correo", "Envío de material comercial y lista de precios actualizada."),
        (82, "Llamada", "Intento de seguimiento: {contact} no disponible, se dejó mensaje en recepción."),
    ],
    "cold": [],
}

# Deals por perfil: (título, etapa, rango de monto, días desde el alta, días desde la última actualización).
DEAL_SCRIPTS = {
    "champion": [
        ("Licencias anuales 2026", DealStage.CLOSED_WON, (18000, 42000), 80, 55),
        ("Ampliación a sucursales", DealStage.PROPOSAL_SENT, (9000, 22000), 14, 3),
    ],
    "active": [
        ("Implementación CRM comercial", None, (8000, 26000), 38, 6),  # etapa alternada
    ],
    "new_lead": [
        ("Plan inicial para equipo de ventas", DealStage.PROSPECT, (3000, 9000), 8, 4),
    ],
    "at_risk": [
        ("Módulo de reportes avanzados", DealStage.CLOSED_LOST, (5000, 12000), 65, 20),
        ("Renovación de contrato anual", DealStage.CONTACTED, (10000, 24000), 30, 8),
    ],
    "dormant": [
        ("Propuesta de digitalización", DealStage.CLOSED_LOST, (4000, 11000), 140, 80),
    ],
    "cold": [],
}

STAGE_PROBABILITY_RANGE = {
    DealStage.PROSPECT: (10, 20),
    DealStage.CONTACTED: (25, 40),
    DealStage.PROPOSAL_SENT: (55, 75),
    DealStage.CLOSED_WON: (100, 100),
    DealStage.CLOSED_LOST: (0, 0),
}

# Tareas por perfil: (título, prioridad, vencimiento en días desde hoy, estado, vinculada a deal abierto).
TASK_SCRIPTS = {
    "champion": [
        ("Enviar contrato actualizado de ampliación a {contact}", TaskPriority.HIGH, 3, TaskStatus.PENDING, True),
        ("Preparar informe trimestral de uso", TaskPriority.MEDIUM, -10, TaskStatus.DONE, False),
    ],
    "active": [
        ("Llamar a {contact} para negociar condiciones de pago", TaskPriority.HIGH, 2, TaskStatus.PENDING, True),
        ("Enviar caso de éxito del rubro", TaskPriority.MEDIUM, -4, TaskStatus.PENDING, True),
    ],
    "new_lead": [
        ("Agendar demo con {contact}", TaskPriority.MEDIUM, 5, TaskStatus.PENDING, True),
    ],
    "at_risk": [
        ("Escalar ticket de exportación a soporte técnico", TaskPriority.HIGH, -3, TaskStatus.PENDING, False),
        ("Reunión de retención con {contact}", TaskPriority.HIGH, 2, TaskStatus.PENDING, True),
        ("Responder reclamo formal", TaskPriority.MEDIUM, -15, TaskStatus.DONE, False),
    ],
    "dormant": [
        ("Retomar contacto con {contact}", TaskPriority.MEDIUM, -20, TaskStatus.PENDING, False),
    ],
    "cold": [
        ("Enviar presentación institucional a {contact}", TaskPriority.LOW, 7, TaskStatus.PENDING, False),
    ],
}

# Análisis predictivo de ejemplo por perfil (sin Gemini).
INSIGHT_SCRIPTS = {
    "champion": {
        "lead_score": (80, 92),
        "churn": [ChurnRisk.BAJO],
        "lead_justification": "Relación activa con contacto frecuente, un deal ganado y una ampliación en negociación con presupuesto confirmado.",
        "churn_justification": "Sin reclamos registrados; el contacto expresa conformidad con el servicio y planea ampliar.",
        "tags": ["alto valor", "cliente fidelizado", "potencial upsell"],
        "tasks": [
            ("Proponer capacitación para las nuevas sucursales", TaskPriority.MEDIUM, 10),
            ("Solicitar testimonio para caso de éxito", TaskPriority.LOW, 20),
        ],
    },
    "active": {
        "lead_score": (60, 78),
        "churn": [ChurnRisk.BAJO, ChurnRisk.MEDIO],
        "lead_justification": "Evaluación avanzada: demo realizada y propuesta enviada; la decisión depende de las condiciones de pago.",
        "churn_justification": "Interacciones recientes y frecuentes, aunque compras compara con otro proveedor.",
        "tags": ["en negociación", "sensible a precio"],
        "tasks": [
            ("Preparar alternativa de pago en cuotas", TaskPriority.HIGH, 3),
            ("Llamar a {contact} para negociar condiciones de pago", TaskPriority.HIGH, 2),
        ],
    },
    "new_lead": {
        "lead_score": (40, 58),
        "churn": [ChurnRisk.BAJO],
        "lead_justification": "Lead entrante con necesidad concreta y plazo definido, todavía sin demo ni propuesta.",
        "churn_justification": "Relación reciente y con interés activo; no hay señales de abandono.",
        "tags": ["lead entrante", "pyme"],
        "tasks": [
            ("Enviar material comparativo de planes", TaskPriority.MEDIUM, 4),
        ],
    },
    "at_risk": {
        "lead_score": (18, 35),
        "churn": [ChurnRisk.ALTO],
        "lead_justification": "Potencial bajo en el corto plazo: la renovación está en duda y ya se perdió una oportunidad.",
        "churn_justification": "Dos tickets con resolución insatisfactoria y mención explícita de evaluar alternativas antes de la renovación.",
        "tags": ["riesgo de renovación", "soporte crítico"],
        "tasks": [
            ("Ofrecer sesión técnica dedicada para resolver los reportes", TaskPriority.HIGH, 1),
            ("Reunión de retención con {contact}", TaskPriority.HIGH, 2),
        ],
    },
    "dormant": {
        "lead_score": (22, 40),
        "churn": [ChurnRisk.MEDIO, ChurnRisk.ALTO],
        "lead_justification": "Interés inicial sin presupuesto asignado y sin respuesta en los últimos intentos de contacto.",
        "churn_justification": "Más de 80 días sin contacto efectivo; el silencio prolongado indica riesgo de perder la relación.",
        "tags": ["inactivo", "sin presupuesto"],
        "tasks": [
            ("Enviar novedades del producto para reactivar el interés", TaskPriority.LOW, 7),
        ],
    },
}


def _demo_email(contact: str, domain: str) -> str:
    first, last = contact.lower().split(" ", 1)
    clean = str.maketrans("áéíóúñ", "aeioun")
    return f"{first[0]}{last.split()[0]}@{domain}".translate(clean)


def _ago(now: datetime, rng: random.Random, days: int) -> datetime:
    """Fecha `days` atrás en horario laboral, con hora aleatoria."""
    moment = (now - timedelta(days=days)).replace(
        hour=rng.randint(9, 18), minute=rng.choice([0, 15, 30, 45]), second=0, microsecond=0
    )
    return min(moment, now)  # "hoy" nunca queda en el futuro


def _seed_customer(
    session: Session,
    rng: random.Random,
    now: datetime,
    index: int,
    row: tuple,
    users: List[User],
    types: Dict[str, InteractionType],
) -> None:
    contact, company, domain, sector, profile = row
    fmt = {"contact": contact.split()[0], "company": company}
    # Pequeño desfase por cliente para que la actividad no caiga toda el mismo día.
    jitter = rng.randint(-2, 2)
    script = INTERACTION_SCRIPTS[profile]
    oldest = (script[0][0] if script else 10) + jitter + rng.randint(5, 30)

    customer = Customer(
        name=contact,
        company=company,
        email=_demo_email(contact, domain),
        phone=f"+54 9 11 {rng.randint(4000, 6999)}-{rng.randint(1000, 9999)}",
        created_at=_ago(now, rng, max(oldest, 1)),
    )
    session.add(customer)
    session.flush()

    for offset, (days, type_name, note) in enumerate(script):
        session.add(
            Interaction(
                notes=note.format(**fmt),
                occurred_at=_ago(now, rng, max(days + jitter, 0)),
                customer_id=customer.id,
                interaction_type_id=types[type_name].id,
                user_id=users[(index + offset) % len(users)].id,
            )
        )

    open_deal: Optional[Deal] = None
    won_value = Decimal("0")
    for title, stage, (low, high), created_days, updated_days in DEAL_SCRIPTS[profile]:
        if stage is None:  # "active": alterna entre propuesta enviada y contactado
            stage = DealStage.PROPOSAL_SENT if index % 2 == 0 else DealStage.CONTACTED
        value = Decimal(rng.randrange(low, high, 500))
        deal = Deal(
            title=title,
            value=value,
            stage=stage,
            probability=rng.randint(*STAGE_PROBABILITY_RANGE[stage]),
            customer_id=customer.id,
            created_at=_ago(now, rng, max(created_days + jitter, 1)),
        )
        deal.updated_at = max(deal.created_at, _ago(now, rng, max(updated_days + jitter, 0)))
        session.add(deal)
        session.flush()
        if stage == DealStage.CLOSED_WON:
            won_value += value
        if stage not in (DealStage.CLOSED_WON, DealStage.CLOSED_LOST) and open_deal is None:
            open_deal = deal

    today = now.date()
    for offset, (title, priority, due_days, status, link_deal) in enumerate(TASK_SCRIPTS[profile]):
        session.add(
            Task(
                title=title.format(**fmt),
                priority=priority,
                due_date=today + timedelta(days=due_days),
                status=status,
                customer_id=customer.id,
                deal_id=open_deal.id if link_deal and open_deal else None,
                assigned_to=users[(index + offset) % len(users)].id,
                created_at=_ago(now, rng, max(abs(due_days) + 5, 6)),
            )
        )

    insight_script = INSIGHT_SCRIPTS.get(profile)
    if insight_script:
        generated_at = _ago(now, rng, rng.randint(1, 5))
        session.add(
            CustomerInsight(
                customer_id=customer.id,
                lead_score=rng.randint(*insight_script["lead_score"]),
                lead_score_justification=insight_script["lead_justification"],
                # Determinístico por cliente: en "active", los deals en Contactado (índice impar) quedan en MEDIO.
                churn_risk=insight_script["churn"][index % len(insight_script["churn"])],
                churn_justification=insight_script["churn_justification"],
                suggested_tags=insight_script["tags"],
                suggested_tasks=[
                    {
                        "title": title.format(**fmt),
                        "priority": priority.value,
                        "due_date": (generated_at.date() + timedelta(days=days)).isoformat(),
                    }
                    for title, priority, days in insight_script["tasks"]
                ],
                generated_at=generated_at,
            )
        )
        # Se aplican algunos tags sugeridos por IA; el resto queda disponible en la ficha.
        for tag_name in insight_script["tags"][: rng.randint(1, 2)]:
            session.add(CustomerTag(customer_id=customer.id, name=tag_name, source=TagSource.IA))

    session.add(CustomerTag(customer_id=customer.id, name=sector, source=TagSource.MANUAL))


def seed_demo_data(session: Session) -> Dict[str, int]:
    users = list(session.exec(select(User).order_by(User.id)).all())
    types = {t.name: t for t in session.exec(select(InteractionType)).all()}
    rng = random.Random(2026)  # contenido reproducible entre ejecuciones
    now = datetime.utcnow()

    created = skipped = 0
    for index, row in enumerate(DEMO_CUSTOMERS):
        email = _demo_email(row[0], row[2])
        if session.exec(select(Customer).where(Customer.email == email)).first():
            skipped += 1
            continue
        _seed_customer(session, rng, now, index, row, users, types)
        session.commit()  # un commit por cliente: o queda completo o no queda
        created += 1
    return {"created": created, "skipped": skipped}


def run_seed() -> None:
    init_db()
    with Session(engine) as session:
        seed_interaction_types(session)
        seed_admin_user(session)
        result = seed_demo_data(session)
    print(
        "Seed completado: interaction_types y usuario admin listos; "
        f"clientes de demo creados: {result['created']}, ya existentes: {result['skipped']}."
    )


if __name__ == "__main__":
    run_seed()
