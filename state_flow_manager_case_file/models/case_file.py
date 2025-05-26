from odoo import models, fields

class CaseFile(models.Model):
    _name = 'case.file'
    _description = 'Case File (Expediente)'
    _inherit = [
        'state.flow.mixin',
        'mail.thread', 
        'mail.activity.mixin'
    ]
    # For attachments, inheriting mail.thread is usually sufficient as it provides the message_attachment_ids field.
    # If you need a direct 'ir.attachment' field on the model itself, you could add:
    # attachment_ids = fields.Many2many('ir.attachment', string='Attachments')

    name = fields.Char(string='Case Title', required=True, tracking=True)
    reference_number = fields.Char(string='Reference', copy=False, readonly=True, default=lambda self: self.env['ir.sequence'].next_by_code('case.file') or 'New')
    description = fields.Text(string='Detailed Description')
    responsible_user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user, tracking=True)
    active = fields.Boolean(default=True)

    # state.flow.mixin fields (process_id, current_state_id, etc.) are inherited.
    # mail.thread fields (message_ids, message_follower_ids, etc.) are inherited.
    # mail.activity.mixin fields (activity_ids, etc.) are inherited. 