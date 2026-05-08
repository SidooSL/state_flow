"""
Migración: Agregar campos de filtro Python para post-conditions.

Se agregan 'post_transition_filter_code' y 'post_transition_filter_fail_message'
para permitir validaciones adicionales después de la transición, similar a las
precondiciones.
"""

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Migración sin cambios de datos. Las nuevas columnas serán creadas por Odoo.
    """
    _logger.info("Migración 18.0.1.0.2: Agregados campos de filtro para post-conditions")
