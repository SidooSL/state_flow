from odoo import models, fields

class ResPartner(models.Model):
    _inherit = ['res.partner', 'state.flow.mixin']
    _name = 'res.partner'

    