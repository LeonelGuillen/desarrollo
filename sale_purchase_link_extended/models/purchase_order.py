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

    # ========== 🆕 MEJORA #2: CAMPO EDITABLE PARA VINCULACIÓN MANUAL ==========
    x_sale_order_id = fields.Many2one(
        'sale.order',
        string='Orden de Venta Asociada',
        tracking=True,
        copy=False,
        # ⚠️ CAMBIO CRÍTICO: Sin readonly para permitir edición manual
        help='Orden de venta que originó esta orden de compra. Puede editarse manualmente para vincular compras existentes.'
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

    # ========== 🆕 MEJORA #2: AUTO-ACTUALIZACIÓN AL VINCULAR VENTA ==========
    @api.onchange('x_sale_order_id')
    def _onchange_sale_order_id(self):
        """
        🎯 Al seleccionar una venta, sugerir datos del vehículo automáticamente
        
        UX: Si el usuario selecciona una venta manualmente, le sugiere los datos
        del vehículo para que no los tenga que copiar a mano.
        """
        if self.x_sale_order_id:
            # Solo sugerir si los campos están vacíos (no sobrescribir datos existentes)
            if not self.x_placa and self.x_sale_order_id.x_placa:
                self.x_placa = self.x_sale_order_id.x_placa
            if not self.x_marca and self.x_sale_order_id.x_marca:
                self.x_marca = self.x_sale_order_id.x_marca
            if not self.x_anio and self.x_sale_order_id.x_anio:
                self.x_anio = self.x_sale_order_id.x_anio
            if not self.x_vin and self.x_sale_order_id.x_vin:
                self.x_vin = self.x_sale_order_id.x_vin
    
    def write(self, vals):
        """
        🎯 Override write para:
        1. Asegurar mayúsculas en campos de vehículo
        2. Actualizar relaciones cuando se vincula/desvincula una venta
        
        ⚠️ SEGURO: Protección contra recursión y errores
        """
        # 1. Asegurar mayúsculas
        if 'x_placa' in vals and vals['x_placa']:
            vals['x_placa'] = vals['x_placa'].upper()
        if 'x_marca' in vals and vals['x_marca']:
            vals['x_marca'] = vals['x_marca'].upper()
        if 'x_anio' in vals and vals['x_anio']:
            vals['x_anio'] = vals['x_anio'].upper()
        if 'x_vin' in vals and vals['x_vin']:
            vals['x_vin'] = vals['x_vin'].upper()
        
        result = super().write(vals)
        
        # 2. Actualizar relaciones si se cambió la venta asociada
        # ⚠️ PROTECCIÓN: Solo si realmente cambió y no es parte de un cálculo en curso
        if 'x_sale_order_id' in vals and not self.env.context.get('skip_sale_update'):
            for po in self:
                if po.x_sale_order_id:
                    try:
                        # Usar with_context para evitar loops infinitos
                        sale = po.x_sale_order_id.with_context(skip_sale_update=True)
                        
                        # Invalidar cache para forzar recálculo
                        sale.invalidate_recordset(['purchase_order_count', 'total_purchase_amount'])
                        
                        # Mensaje en chatter para auditoría (solo si no es creación)
                        if not self.env.context.get('tracking_disable'):
                            sale.message_post(
                                body=f'<p>✅ Orden de Compra <strong>{po.name}</strong> vinculada manualmente.</p>'
                            )
                    except Exception as e:
                        # Log del error pero no bloquear la operación
                        import logging
                        _logger = logging.getLogger(__name__)
                        _logger.warning(f'Error actualizando venta desde compra {po.name}: {str(e)}')
        
        return result

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
        
        orders = super().create(vals_list)
        
        # Actualizar relaciones en ventas asociadas al crear
        for po in orders:
            if po.x_sale_order_id:
                po.x_sale_order_id._compute_purchase_order_count()
                po.x_sale_order_id._compute_liquidation_data()
        
        return orders

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