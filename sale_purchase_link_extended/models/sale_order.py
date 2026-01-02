# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # ========== MÉTODO PARA TRANSFERIR DATOS A FACTURA ==========
    def _prepare_invoice(self):
        """Override para incluir datos de vehículo en la factura"""
        invoice_vals = super()._prepare_invoice()
        
        # Transferir datos de vehículo a la factura
        invoice_vals.update({
            'x_placa': self.x_placa,
            'x_marca': self.x_marca,
            'x_anio': self.x_anio,
            'x_vin': self.x_vin,
        })
        
        return invoice_vals

    # ========== CAMPOS DE INFORMACIÓN DEL VEHÍCULO ==========
    x_placa = fields.Char(
        string='Placa',
        help='Número de placa del vehículo',
        tracking=True
    )
    
    x_marca = fields.Char(
        string='Marca',
        help='Marca del vehículo',
        tracking=True
    )
    
    x_anio = fields.Char(
        string='Año',
        help='Año del vehículo',
        tracking=True
    )
    
    x_vin = fields.Char(
        string='Número de VIN',
        help='Número de identificación del vehículo',
        tracking=True
    )

    # ========== CAMPOS DE RELACIÓN CON COMPRAS ==========
    purchase_order_ids = fields.One2many(
        'purchase.order',
        'x_sale_order_id',
        string='Órdenes de Compra Relacionadas',
        help='Órdenes de compra generadas desde esta orden de venta'
    )
    
    purchase_order_count = fields.Integer(
        string='# de Órdenes de Compra',
        compute='_compute_purchase_order_count',
        store=False
    )
    
    # ========== MEJORA #5: CONTROL DE PRODUCTOS PEDIDOS/NO PEDIDOS ==========
    purchase_lines_in_process = fields.Integer(
        string='Líneas en Proceso',
        compute='_compute_purchase_statistics',
        store=False,
        help='Número de líneas de compra confirmadas'
    )
    
    pending_to_purchase = fields.Integer(
        string='Pendientes por Comprar',
        compute='_compute_purchase_statistics',
        store=False,
        help='Número de líneas de venta sin línea de compra asociada'
    )
    
    products_purchased_qty = fields.Float(
        string='Cantidad Total Comprada',
        compute='_compute_purchase_statistics',
        store=False,
        help='Cantidad total de productos ya pedidos en compras'
    )
    
    products_pending_qty = fields.Float(
        string='Cantidad Total Pendiente',
        compute='_compute_purchase_statistics',
        store=False,
        help='Cantidad total de productos aún no pedidos'
    )

    # ========== MEJORA #6: LIQUIDACIÓN DETALLADA ==========
    
    total_invoiced_amount = fields.Monetary(
        string='Total Facturado (Bruto)',
        compute='_compute_liquidation_data',
        store=False,
        help='Total de las facturas (out_invoice) confirmadas relacionadas con esta OV'
    )
    
    total_credit_note_amount = fields.Monetary(
        string='Total Notas de Crédito',
        compute='_compute_liquidation_data',
        store=False,
        help='Total de las notas de crédito (out_refund) confirmadas'
    )
    
    total_net_invoiced_amount = fields.Monetary(
        string='Total Facturado (Neto)',
        compute='_compute_liquidation_data',
        store=False,
        help='Total facturado menos notas de crédito (Ingreso Real)'
    )
    
    total_purchase_amount = fields.Monetary(
        string='Total de Compras',
        compute='_compute_liquidation_data',
        store=False,
        help='Total de las compras confirmadas'
    )
    
    sale_completion_percentage = fields.Float(
        string='Porcentaje de Utilidad (Neto)',
        compute='_compute_liquidation_data',
        store=False,
        help='Porcentaje de ganancia neta sobre el ingreso neto.\n'
             'Fórmula: (Ganancia Neta / Ingreso Neto)'
    )
    
    profit_margin = fields.Monetary(
        string='Margen de Utilidad (Neto)',
        compute='_compute_liquidation_data',
        store=False,
        help='Diferencia entre ventas facturadas netas y compras realizadas'
    )
    
    purchase_orders_summary = fields.Html(
        string='Resumen de Órdenes de Compra',
        compute='_compute_purchase_orders_summary',
        help='Detalle de todas las órdenes de compra relacionadas con montos'
    )
    
    products_control_summary = fields.Html(
        string='Control de Productos',
        compute='_compute_products_control_summary',
        help='Control detallado de productos vendidos vs comprados'
    )

    # ========== MÉTODOS DE ESCRITURA CON MAYÚSCULAS ==========
    @api.onchange('x_placa', 'x_marca', 'x_anio', 'x_vin')
    def _onchange_vehicle_fields(self):
        """Convierte los campos de vehículo a mayúsculas"""
        if self.x_placa:
            self.x_placa = self.x_placa.upper()
        if self.x_marca:
            self.x_marca = self.x_marca.upper()
        if self.x_anio:
            self.x_anio = self.x_anio.upper()
        if self.x_vin:
            self.x_vin = self.x_vin.upper()

    def write(self, vals):
        """Override write para asegurar mayúsculas"""
        if 'x_placa' in vals and vals['x_placa']:
            vals['x_placa'] = vals['x_placa'].upper()
        if 'x_marca' in vals and vals['x_marca']:
            vals['x_marca'] = vals['x_marca'].upper()
        if 'x_anio' in vals and vals['x_anio']:
            vals['x_anio'] = vals['x_anio'].upper()
        if 'x_vin' in vals and vals['x_vin']:
            vals['x_vin'] = vals['x_vin'].upper()
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        """Override create para asegurar mayúsculas"""
        for vals in vals_list:
            if 'x_placa' in vals and vals['x_placa']:
                vals['x_placa'] = vals['x_placa'].upper()
            if 'x_marca' in vals and vals['x_marca']:
                vals['x_marca'] = vals['x_marca'].upper()
            if 'x_anio' in vals and vals['x_anio']:
                vals['x_anio'] = vals['x_anio'].upper()
            if 'x_vin' in vals and vals['x_vin']:
                vals['x_vin'] = vals['x_vin'].upper()
        return super().create(vals_list)

    # ========== CAMPOS COMPUTADOS BÁSICOS ==========
    @api.depends('purchase_order_ids')
    def _compute_purchase_order_count(self):
        """Calcula el número de órdenes de compra asociadas"""
        for order in self:
            order.purchase_order_count = len(order.purchase_order_ids)

    # ========== MEJORA #5: ESTADÍSTICAS DE PRODUCTOS ==========
    @api.depends('order_line.x_purchase_status')
    def _compute_purchase_statistics(self):
        """Calcula las estadísticas detalladas de compras vs ventas"""
        for order in self:
            # Líneas en proceso (OC confirmadas)
            lines_in_process = 0
            for po in order.purchase_order_ids:
                if po.state in ['purchase', 'done']:
                    lines_in_process += len(po.order_line)
            order.purchase_lines_in_process = lines_in_process
            
            # Productos pendientes y comprados
            pending_lines = 0
            total_qty_purchased = 0.0
            total_qty_pending = 0.0
            
            for line in order.order_line:
                qty_purchased = line.x_qty_purchased
                qty_pending = line.x_qty_pending_purchase
                
                total_qty_purchased += qty_purchased
                
                if qty_pending > 0:
                    pending_lines += 1
                    total_qty_pending += qty_pending
            
            order.pending_to_purchase = pending_lines
            order.products_purchased_qty = total_qty_purchased
            order.products_pending_qty = total_qty_pending

    # ========== MEJORA #6: LIQUIDACIÓN DETALLADA ==========
    @api.depends('invoice_ids', 'invoice_ids.state', 'invoice_ids.move_type', 'invoice_ids.amount_total',
                 'purchase_order_ids', 'purchase_order_ids.state', 
                 'purchase_order_ids.amount_total', 'amount_total')
    def _compute_liquidation_data(self):
        """Calcula los datos de liquidación, incluyendo notas de crédito y margen %"""
        for order in self:
            posted_moves = order.invoice_ids.filtered(lambda inv: inv.state == 'posted')
            
            invoiced_gross = sum(posted_moves.filtered(
                lambda inv: inv.move_type == 'out_invoice'
            ).mapped('amount_total'))
            order.total_invoiced_amount = invoiced_gross
            
            credit_notes_total = sum(posted_moves.filtered(
                lambda inv: inv.move_type == 'out_refund'
            ).mapped('amount_total'))
            order.total_credit_note_amount = credit_notes_total
            
            net_invoiced = invoiced_gross - credit_notes_total
            order.total_net_invoiced_amount = net_invoiced
            
            purchased = sum(order.purchase_order_ids.filtered(
                lambda po: po.state in ['purchase', 'done']
            ).mapped('amount_total'))
            order.total_purchase_amount = purchased
            
            profit = net_invoiced - purchased
            order.profit_margin = profit
            
            if net_invoiced > 0:
                order.sale_completion_percentage = profit / net_invoiced
            else:
                order.sale_completion_percentage = 0.0

    @api.depends('purchase_order_ids', 'purchase_order_ids.state', 
                 'purchase_order_ids.amount_total')
    def _compute_purchase_orders_summary(self):
        """Genera resumen HTML de órdenes de compra"""
        for order in self:
            if not order.purchase_order_ids:
                order.purchase_orders_summary = '<p><em>No hay órdenes de compra relacionadas</em></p>'
                continue
            
            html = '<table class="table table-sm table-striped">'
            html += '<thead><tr>'
            html += '<th>Orden de Compra</th>'
            html += '<th>Proveedor</th>'
            html += '<th>Estado</th>'
            html += '<th>Fecha</th>'
            html += '<th class="text-end">Monto</th>'
            html += '</tr></thead><tbody>'
            
            total = 0.0
            for po in order.purchase_order_ids:
                state_class = {
                    'draft': 'secondary',
                    'sent': 'info',
                    'to approve': 'warning',
                    'purchase': 'success',
                    'done': 'primary',
                    'cancel': 'danger'
                }.get(po.state, 'secondary')
                state_label = dict(po._fields['state'].selection).get(po.state, po.state)
                html += f'<tr>'
                html += f'<td><strong>{po.name}</strong></td>'
                html += f'<td>{po.partner_id.name}</td>'
                html += f'<td><span class="badge badge-{state_class}">{state_label}</span></td>'
                html += f'<td>{po.date_order.strftime("%d/%m/%Y") if po.date_order else "-"}</td>'
                html += f'<td class="text-end"><strong>{order.currency_id.symbol} {po.amount_total:,.2f}</strong></td>'
                html += f'</tr>'
                if po.state in ['purchase', 'done']:
                    total += po.amount_total
            
            html += '</tbody><tfoot><tr class="table-active">'
            html += '<td colspan="4" class="text-end"><strong>Total Compras Confirmadas:</strong></td>'
            html += f'<td class="text-end"><strong>{order.currency_id.symbol} {total:,.2f}</strong></td>'
            html += '</tr></tfoot></table>'
            order.purchase_orders_summary = html

    @api.depends('order_line.x_purchase_status')
    def _compute_products_control_summary(self):
        """Genera resumen HTML de control de productos"""
        for order in self:
            if not order.order_line:
                order.products_control_summary = '<p><em>No hay líneas de venta</em></p>'
                continue
            
            html = '<table class="table table-sm table-bordered">'
            html += '<thead class="table-light"><tr>'
            html += '<th>Producto</th>'
            html += '<th class="text-center">Cant. Vendida</th>'
            html += '<th class="text-center">Cant. Comprada</th>'
            html += '<th class="text-center">Cant. Pendiente</th>'
            html += '<th class="text-center">Estado</th>'
            html += '</tr></thead><tbody>'
            
            for line in order.order_line:
                qty_sold = line.product_uom_qty
                qty_purchased = line.x_qty_purchased 
                qty_pending = line.x_qty_pending_purchase
                
                if line.x_purchase_status == 'purchased':
                    status = '<span class="badge badge-success">✓ Completo</span>'
                    row_class = 'table-success'
                elif line.x_purchase_status == 'partial':
                    status = '<span class="badge badge-warning">⚠ Parcial</span>'
                    row_class = 'table-warning'
                else:
                    status = '<span class="badge badge-danger">✗ Sin Pedir</span>'
                    row_class = 'table-danger'
                
                html += f'<tr class="{row_class}">'
                html += f'<td><strong>{line.product_id.display_name}</strong></td>'
                html += f'<td class="text-center">{qty_sold:.2f}</td>'
                html += f'<td class="text-center">{qty_purchased:.2f}</td>'
                html += f'<td class="text-center">{max(0, qty_pending):.2f}</td>'
                html += f'<td class="text-center">{status}</td>'
                html += f'</tr>'
            
            html += '</tbody></table>'
            order.products_control_summary = html

    # ========== ACCIONES Y BOTONES ==========
    def action_view_purchase_orders(self):
        """Abre la vista de órdenes de compra relacionadas"""
        self.ensure_one()
        action = self.env.ref('purchase.purchase_form_action').read()[0]
        
        if len(self.purchase_order_ids) > 1:
            action['domain'] = [('id', 'in', self.purchase_order_ids.ids)]
            action['view_mode'] = 'tree,form'
            if 'res_id' in action:
                del action['res_id']
        elif len(self.purchase_order_ids) == 1:
            form_view = self.env.ref('purchase.purchase_order_form').id
            action['views'] = [(form_view, 'form')]
            action['res_id'] = self.purchase_order_ids.id
            action['view_mode'] = 'form' 
        else:
            action = {'type': 'ir.actions.act_window_close'}
        
        if action.get('type') != 'ir.actions.act_window_close':
            action['context'] = {
                'default_x_sale_order_id': self.id,
                'default_x_placa': self.x_placa,
                'default_x_marca': self.x_marca,
                'default_x_anio': self.x_anio,
                'default_x_vin': self.x_vin,
            }
        return action

    def action_create_purchase_orders(self):
        """Abre el wizard para crear órdenes de compra"""
        self.ensure_one()
        if not self.order_line:
            raise UserError(_('No hay líneas en la orden de venta para crear órdenes de compra.'))
        return {
            'name': _('Crear Órdenes de Compra'),
            'type': 'ir.actions.act_window',
            'res_model': 'create.purchase.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_order_id': self.id,
            }
        }

    def action_export_liquidation_excel(self):
        """Exporta la liquidación a Excel"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/export/liquidation/{self.id}/excel',
            'target': 'new',
        }

    def action_export_liquidation_pdf(self):
        """Exporta la liquidación a PDF"""
        return self.env.ref(
            'sale_purchase_link_extended.action_report_sale_liquidation'
        ).report_action(self)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    x_purchase_line_ids = fields.One2many(
        'purchase.order.line',
        'x_sale_line_id',
        string='Líneas de Compra Relacionadas',
        help='Líneas de compra generadas desde esta línea de venta'
    )
    
    x_qty_purchased = fields.Float(
        string='Cantidad Comprada',
        compute='_compute_qty_purchased',
        store=False,
        help='Cantidad total comprada para esta línea'
    )
    
    x_qty_pending_purchase = fields.Float(
        string='Cantidad Pendiente',
        compute='_compute_qty_purchased',
        store=False,
        help='Cantidad pendiente por comprar'
    )
    
    x_purchase_status = fields.Selection([
        ('not_purchased', 'Sin Pedir'),
        ('partial', 'Parcial'),
        ('purchased', 'Completo')
    ], string='Estado de Compra', compute='_compute_qty_purchased', store=False)

    @api.depends('x_purchase_line_ids.product_qty', 'x_purchase_line_ids.order_id.state', 'product_uom_qty')
    def _compute_qty_purchased(self):
        """Calcula la cantidad comprada y pendiente"""
        for line in self:
            purchased_lines = line.x_purchase_line_ids.filtered(
                lambda l: l.order_id.state != 'cancel'
            )
            qty_purchased = sum(purchased_lines.mapped('product_qty'))
            
            line.x_qty_purchased = qty_purchased
            line.x_qty_pending_purchase = line.product_uom_qty - qty_purchased
            
            if qty_purchased <= 0:
                line.x_purchase_status = 'not_purchased'
            elif qty_purchased < line.product_uom_qty:
                line.x_purchase_status = 'partial'
            else:
                line.x_purchase_status = 'purchased'