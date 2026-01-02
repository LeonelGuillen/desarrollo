# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # ========== MÉTODO CRÍTICO: Transferir datos a factura de proveedor ==========
    def _prepare_invoice(self):
        """Override para incluir datos de vehículo en la factura de proveedor"""
        invoice_vals = super()._prepare_invoice()
        
        invoice_vals.update({
            'x_placa': self.x_placa,
            'x_marca': self.x_marca,
            'x_anio': self.x_anio,
            'x_vin': self.x_vin,
        })
        
        return invoice_vals

    # ========== CAMPOS DE VINCULACIÓN CON VENTA ==========
    x_sale_order_id = fields.Many2one(
        'sale.order',
        string='Orden de Venta Asociada',
        tracking=True,
        copy=False,
        help='Orden de venta que originó esta orden de compra'
    )
    
    x_sale_order_name = fields.Char(
        string='Número de Venta',
        related='x_sale_order_id.name',
        store=True,
        readonly=True
    )

    # ========== CAMPOS DE VEHÍCULO ==========
    x_placa = fields.Char(
        string='Placa',
        help='Número de placa del vehículo',
        tracking=True,
        copy=False
    )
    
    x_marca = fields.Char(
        string='Marca',
        help='Marca del vehículo',
        tracking=True,
        copy=False
    )
    
    x_anio = fields.Char(
        string='Año',
        help='Año del vehículo',
        tracking=True,
        copy=False
    )
    
    x_vin = fields.Char(
        string='Número de VIN',
        help='Número de identificación del vehículo',
        tracking=True,
        copy=False
    )

    # ========== AUTO-CONVERSIÓN A MAYÚSCULAS ==========
    @api.onchange('x_placa', 'x_marca', 'x_anio', 'x_vin')
    def _onchange_vehicle_fields(self):
        """Convierte campos de vehículo a MAYÚSCULAS en tiempo real"""
        if self.x_placa:
            self.x_placa = self.x_placa.upper()
        if self.x_marca:
            self.x_marca = self.x_marca.upper()
        if self.x_anio:
            self.x_anio = self.x_anio.upper()
        if self.x_vin:
            self.x_vin = self.x_vin.upper()

    def write(self, vals):
        """Asegurar mayúsculas al guardar"""
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
        """Asegurar mayúsculas al crear"""
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

    # ========== ACCIÓN: Ver orden de venta ==========
    def action_view_sale_order(self):
        """Abre la orden de venta asociada"""
        self.ensure_one()
        
        if not self.x_sale_order_id:
            return {'type': 'ir.actions.act_window_close'}
        
        return {
            'name': 'Orden de Venta',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': self.x_sale_order_id.id,
            'target': 'current',
        }


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    x_sale_line_id = fields.Many2one(
        'sale.order.line',
        string='Línea de Venta Asociada',
        copy=False,
        help='Línea de venta que originó esta línea de compra',
        ondelete='set null'
    )
    
    x_sale_order_id = fields.Many2one(
        'sale.order',
        related='x_sale_line_id.order_id',
        string='Orden de Venta',
        store=True,
        readonly=True
    )