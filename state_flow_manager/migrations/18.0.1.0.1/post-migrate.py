"""
Migración: Renombrar 'domain_fail_message' a 'pre_condition_fail_message'

El campo 'domain_fail_message' se aplicaba tanto para fallos de 'pre_condition_domain'
como de 'pre_condition_filter_code'. El nuevo nombre refleja mejor su propósito.
"""

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Migra los datos del campo 'domain_fail_message' a 'pre_condition_fail_message'.
    """
    _logger.info("Iniciando migración de 'domain_fail_message' a 'pre_condition_fail_message'")

    # Verificar si existen ambas columnas (en caso de que sea una ejecución parcial)
    cr.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'state_flow_transition'
        AND column_name IN ('domain_fail_message', 'pre_condition_fail_message')
    """)

    existing_columns = {row[0] for row in cr.fetchall()}

    # Si la columna antigua existe
    if 'domain_fail_message' in existing_columns:
        _logger.info("Encontrada columna 'domain_fail_message', iniciando migración de datos")

        # Si la columna nueva ya existe (mejor por seguridad)
        if 'pre_condition_fail_message' in existing_columns:
            # Copiar datos solo donde pre_condition_fail_message es NULL
            cr.execute("""
                UPDATE state_flow_transition
                SET pre_condition_fail_message = domain_fail_message
                WHERE pre_condition_fail_message IS NULL
                AND domain_fail_message IS NOT NULL
            """)
            _logger.info(f"Migrados {cr.rowcount} registros de 'domain_fail_message' a 'pre_condition_fail_message'")
        else:
            # La columna nueva no existe aún (será creada por Odoo al aplicar el modelo)
            # Aquí no hacemos nada, Odoo manejará la creación de la nueva columna
            _logger.info("Columna 'pre_condition_fail_message' no existe aún, será creada por Odoo")
            # De todas formas, preparamos un rename si es posible
            try:
                cr.execute("""
                    ALTER TABLE state_flow_transition
                    RENAME COLUMN domain_fail_message TO pre_condition_fail_message
                """)
                _logger.info("Renombrada columna 'domain_fail_message' a 'pre_condition_fail_message'")
            except Exception as e:
                _logger.warning(f"No se pudo renombrar directamente: {e}. Odoo lo hará al actualizar el modelo")

    _logger.info("Migración completada")
