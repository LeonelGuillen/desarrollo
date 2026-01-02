# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class LinkPurchaseWizard(models.TransientModel):
    _name = 'link.purchase.wizard'
    _description = 'Wizard para Vincular Órdenes de Compra Existentes'

    sale_order_id = fields.Many2one(
        'sale.order', 
        string='Orden de Venta',
        required=True,
        readonly=True
    )
    
    # ========== FILTROS DE BÚSQUEDA ==========
    partner_id = fields.Many2one(
        'res.partner',
        string='Proveedor',
        domain="[('supplier_rank', '>', 0)]",
        help='Filtrar compras por proveedor'
    )
    
    date_from = fields.Date(
        string='Fecha Desde',
        help='Buscar compras desde esta fecha'
    )
    
    date_to = fields.Date(
        string='Fecha Hasta',
        help='Buscar compras hasta esta fecha'
    )
    
    origin_filter = fields.Char(
        string='Referencia',
        help='Buscar por número de orden o referencia'
    )
    
    state_filter = fields.Selection([
        ('draft', 'Borrador'),
        ('sent', 'Enviada'),
        ('to approve', 'Por Aprobar'),
        ('purchase', 'Orden de Compra'),
        ('done', 'Bloqueada'),
    ], string='Estado', default='purchase')
    
    # ========== CAMPOS PARA MOSTRAR RESULTADOS ==========
    available_purchase_ids = fields.Many2many(
        'purchase.order',
        'link_purchase_wizard_available_rel',
        'wizard_id',
        'purchase_id',
        string='Compras Disponibles',
        compute='_compute_available_purchases',
        help='Órdenes de compra que coinciden con los filtros'
    )
    
    selected_purchase_ids = fields.Many2many(
        'purchase.order',
        'link_purchase_wizard_selected_rel',
        'wizard_id',
        'purchase_id',
        string='Compras Seleccionadas',
        help='Órdenes de compra a vincular con esta venta'
    )
    
    available_count = fields.Integer(
        string='Cantidad Disponible',
        compute='_compute_available_purchases'
    )
    
    x_copy_vehicle_data = fields.Boolean(
        string='Copiar datos de vehículo a las compras',
        default=True,
        help='Si se marca, los datos de placa/marca/año/VIN se copiarán a las órdenes de compra seleccionadas'
    )
    
    # ========== INFORMACIÓN DE LA VENTA ==========
    sale_vehicle_info = fields.Html(
        string='Información del Vehículo',
        compute='_compute_sale_vehicle_info'
    )
    
    @api.depends('sale_order_id')
    def _compute_sale_vehicle_info(self):
        """Muestra los datos del vehículo de la venta"""
        for wizard in self:
            if not wizard.sale_order_id:
                wizard.sale_vehicle_info = '<p><em>No hay venta seleccionada</em></p>'
                continue
            
            sale = wizard.sale_order_id
            html = '<div class="alert alert-info">'
            html += f'<p><strong>Orden de Venta:</strong> {sale.name}</p>'
            
            if sale.x_placa or sale.x_marca or sale.x_anio or sale.x_vin:
                html += '<p><strong>Datos del Vehículo:</strong></p>'
                html += '<ul class="mb-0">'
                if sale.x_placa:
                    html += f'<li><strong>Placa:</strong> {sale.x_placa}</li>'
                if sale.x_marca:
                    html += f'<li><strong>Marca:</strong> {sale.x_marca}</li>'
                if sale.x_anio:
                    html += f'<li><strong>Año:</strong> {sale.x_anio}</li>'
                if sale.x_vin:
                    html += f'<li><strong>VIN:</strong> {sale.x_vin}</li>'
                html += '</ul>'
            else:
                html += '<p><em>Esta venta no tiene datos de vehículo</em></p>'
            
            html += '</div>'
            wizard.sale_vehicle_info = html
    
    @api.depends('partner_id', 'date_from', 'date_to', 'origin_filter', 'state_filter')
    def _compute_available_purchases(self):
        """
        🎯 Busca compras disponibles según los filtros
        
        Excluye:
        - Compras ya vinculadas a esta venta
        - Compras canceladas (opcional según state_filter)
        """
        for wizard in self:
            domain = [
                ('x_sale_order_id', '=', False),  # Solo compras sin venta asociada
            ]
            
            # Aplicar filtros
            if wizard.partner_id:
                domain.append(('partner_id', '=', wizard.partner_id.id))
            
            if wizard.date_from:
                domain.append(('date_order', '>=', wizard.date_from))
            
            if wizard.date_to:
                domain.append(('date_order', '<=', wizard.date_to))
            
            if wizard.origin_filter:
                domain.append(
                    '|', 
                    ('name', 'ilike', wizard.origin_filter),
                    ('partner_ref', 'ilike', wizard.origin_filter)
                )
            
            if wizard.state_filter:
                domain.append(('state', '=', wizard.state_filter))
            
            # Buscar compras
            purchases = self.env['purchase.order'].search(domain, order='date_order desc')
            
            wizard.available_purchase_ids = purchases
            wizard.available_count = len(purchases)
    
    # ========== ACCIONES ==========
    
    def action_refresh_search(self):
        """Refresca la búsqueda con los filtros actuales"""
        self.ensure_one()
        # El campo computado se recalculará automáticamente
        return {
            'type': 'ir.actions.do_nothing',
        }
    
    def action_select_all(self):
        """Selecciona todas las compras disponibles"""
        self.ensure_one()
        self.selected_purchase_ids = [(6, 0, self.available_purchase_ids.ids)]
        return {
            'type': 'ir.actions.do_nothing',
        }
    
    def action_deselect_all(self):
        """Deselecciona todas las compras"""
        self.ensure_one()
        self.selected_purchase_ids = [(5, 0, 0)]
        return {
            'type': 'ir.actions.do_nothing',
        }
    
    def action_link_purchases(self):
        """
        🎯 Vincula las compras seleccionadas a la venta
        
        Proceso:
        1. Actualiza x_sale_order_id en cada compra
        2. Opcionalmente copia datos de vehículo
        3. Agrega mensaje en chatter de la venta
        4. Recalcula campos computados
        """
        self.ensure_one()
        
        if not self.selected_purchase_ids:
            raise UserError(_('Debe seleccionar al menos una orden de compra para vincular.'))
        
        sale = self.sale_order_id
        linked_count = 0
        
        for po in self.selected_purchase_ids:
            # Preparar valores
            vals = {
                'x_sale_order_id': sale.id,
            }
            
            # Copiar datos de vehículo si está marcado
            if self.x_copy_vehicle_data:
                if sale.x_placa:
                    vals['x_placa'] = sale.x_placa
                if sale.x_marca:
                    vals['x_marca'] = sale.x_marca
                if sale.x_anio:
                    vals['x_anio'] = sale.x_anio
                if sale.x_vin:
                    vals['x_vin'] = sale.x_vin
            
            # Actualizar compra
            po.write(vals)
            linked_count += 1
        
        # Mensaje en chatter
        sale.message_post(
            body=_(
                '<p><strong>✅ Órdenes de Compra Vinculadas Manualmente</strong></p>'
                '<p>Se vincularon <strong>%s</strong> órdenes de compra existentes:</p>'
                '<ul>%s</ul>'
            ) % (
                linked_count,
                ''.join([f'<li>{po.name} - {po.partner_id.name}</li>' for po in self.selected_purchase_ids])
            )
        )
        
        # Forzar recálculo de todos los campos relacionados
        sale._compute_purchase_order_count()
        sale._compute_liquidation_data()
        sale._compute_purchase_statistics()
        sale._compute_purchase_orders_summary()
        sale._compute_products_control_summary()
        
        # Mostrar notificación
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Vinculación Exitosa'),
                'message': _(f'Se vincularon {linked_count} órdenes de compra a {sale.name}'),
                'type': 'success',
                'sticky': False,
                'next': {
                    'type': 'ir.actions.act_window_close'
                }
            }
        }
