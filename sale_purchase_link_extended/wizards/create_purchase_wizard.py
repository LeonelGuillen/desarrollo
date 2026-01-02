# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class CreatePurchaseWizard(models.TransientModel):
    _name = 'create.purchase.wizard'
    _description = 'Wizard para Crear Ordenes de Compra'

    sale_order_id = fields.Many2one(
        'sale.order', 
        string='Orden de Venta',
        required=True
    )
    
    group_by_vendor = fields.Boolean(
        string='Agrupar por Proveedor',
        default=True,
        help='Si se marca, se creará una orden de compra por cada proveedor'
    )
    
    x_purchase_only_missing = fields.Boolean(
        string='Comprar solo cantidades faltantes',
        default=True,
        help='Si se marca, solo se crearán líneas de compra para la cantidad que aún no se ha pedido.\n'
             'Si se desmarca, se crearán líneas por el total de la venta, ignorando compras previas.'
    )
    
    x_has_purchased_lines = fields.Boolean(
        string='Tiene líneas ya compradas',
        compute='_compute_vendor_info'
    )
    
    products_control_summary = fields.Html(
        string='Control de Productos',
        related='sale_order_id.products_control_summary',
        readonly=True
    )
    
    has_products_without_vendor = fields.Boolean(
        string='Tiene productos sin proveedor',
        compute='_compute_vendor_info'
    )
    
    products_without_vendor_count = fields.Integer(
        string='Cantidad sin proveedor',
        compute='_compute_vendor_info'
    )
    
    products_without_vendor_list = fields.Text(
        string='Productos sin proveedor',
        compute='_compute_vendor_info'
    )
    
    @api.depends('sale_order_id')
    def _compute_vendor_info(self):
        """Calcula información sobre productos sin proveedor y productos ya comprados"""
        for wizard in self:
            products_no_vendor = []
            has_purchased = False
            if wizard.sale_order_id:
                # Usamos los campos computados de la OV que ya existen
                for line in wizard.sale_order_id.order_line:
                    if not line.product_id.seller_ids:
                        products_no_vendor.append(line.product_id.name)
                    
                    # Verificamos el campo computado 'x_qty_purchased' de la línea de venta
                    if line.x_qty_purchased > 0:
                        has_purchased = True
            
            wizard.has_products_without_vendor = bool(products_no_vendor)
            wizard.products_without_vendor_count = len(products_no_vendor)
            wizard.products_without_vendor_list = '\n'.join(products_no_vendor) if products_no_vendor else ''
            wizard.x_has_purchased_lines = has_purchased
    
    def _get_or_create_generic_vendor(self):
        """Obtiene o crea el proveedor genérico"""
        # (Sin cambios en este método)
        generic_vendor = self.env['res.partner'].search([
            ('name', '=', 'PROVEEDOR GENERICO'),
            ('supplier_rank', '>', 0)
        ], limit=1)
        
        if not generic_vendor:
            generic_vendor = self.env['res.partner'].create({
                'name': 'PROVEEDOR GENERICO',
                'supplier_rank': 1,
                'company_type': 'company',
                'email': 'generico@proveedor.com',
                'phone': '0000-0000',
                'comment': 'Proveedor genérico creado automáticamente para productos sin proveedor asignado',
            })
            _logger.info('Proveedor genérico creado: ID %s', generic_vendor.id)
        
        return generic_vendor
    
    def action_create_purchase_orders(self):
        """Crea las órdenes de compra con la lógica de "solo faltantes"""
        self.ensure_one()
        
        sale_order = self.sale_order_id
        if not sale_order.order_line:
            raise UserError(_('La orden de venta no tiene líneas.'))
        
        generic_vendor = self._get_or_create_generic_vendor()
        
        purchase_orders = self.env['purchase.order']
        lines_by_vendor = {}
        
        # (Toda la lógica de agrupación de líneas no cambia)
        for line in sale_order.order_line:
            qty_sold = line.product_uom_qty
            qty_to_purchase = qty_sold

            if self.x_purchase_only_missing:
                qty_to_purchase = line.x_qty_pending_purchase
                if qty_to_purchase < 0:
                    qty_to_purchase = 0.0
            
            if qty_to_purchase <= 0:
                _logger.info(
                    'Línea %s omitida (Cant. a comprar = 0, x_purchase_only_missing=%s)',
                    line.product_id.name, self.x_purchase_only_missing
                )
                continue 
            
            vendor = False
            price = line.price_unit
            
            if line.product_id.seller_ids:
                vendor = line.product_id.seller_ids[0].partner_id
                price = line.product_id.seller_ids[0].price
            else:
                vendor = generic_vendor
            
            if self.group_by_vendor:
                if vendor not in lines_by_vendor:
                    lines_by_vendor[vendor] = []
                lines_by_vendor[vendor].append({
                    'line': line, 
                    'price': price,
                    'qty_to_purchase': qty_to_purchase
                })
            else:
                if 'all' not in lines_by_vendor:
                    lines_by_vendor['all'] = []
                lines_by_vendor['all'].append({
                    'line': line,
                    'price': price,
                    'vendor': vendor,
                    'qty_to_purchase': qty_to_purchase
                })
        
        if not lines_by_vendor:
            raise UserError(_(
                'No se crearon órdenes de compra. Todos los productos'
                ' ya están comprados o las cantidades a comprar son cero.'
            ))
            
        # (Toda la lógica de creación de POs no cambia)
        for vendor_key, lines_data in lines_by_vendor.items():
            if vendor_key == 'all':
                vendor = lines_data[0]['vendor']
            else:
                vendor = vendor_key
            
            po_vals = {
                'partner_id': vendor.id,
                'x_sale_order_id': sale_order.id,
                'x_placa': sale_order.x_placa,
                'x_marca': sale_order.x_marca,
                'x_anio': sale_order.x_anio,
                'x_vin': sale_order.x_vin,
                'order_line': [],
            }
            
            for line_data in lines_data:
                line = line_data['line']
                price = line_data['price']
                qty = line_data['qty_to_purchase']
                
                po_line_vals = {
                    'product_id': line.product_id.id,
                    'name': line.product_id.name,
                    'product_qty': qty,
                    'price_unit': price,
                    'product_uom': line.product_id.uom_po_id.id,
                    'date_planned': fields.Datetime.now(),
                    'x_sale_line_id': line.id,
                }
                po_vals['order_line'].append((0, 0, po_line_vals))
            
            purchase_order = self.env['purchase.order'].create(po_vals)
            purchase_orders |= purchase_order
        
        # (La lógica de message_post no cambia)
        generic_lines = sum(1 for v, lines in lines_by_vendor.items() 
                          for ld in lines 
                          if not ld['line'].product_id.seller_ids)
        
        if generic_lines > 0:
            sale_order.message_post(
                body=_(
                    '<p><strong>ℹ️ Órdenes de Compra Creadas</strong></p>'
                    '<p>Se asignaron <strong>%s productos</strong> al '
                    '<strong>PROVEEDOR GENERICO</strong> porque no tenían proveedor configurado.</p>'
                    '<p><em>Puede cambiar el proveedor editando las órdenes de compra creadas.</em></p>'
                ) % generic_lines
            )
        
        
        # --- INICIO DE LA SOLUCIÓN AL ERROR ---
        # Corrección para el Error #4: Estructura de acción incorrecta 
        # Leemos la acción base para obtener un dict completo y consistente.
        action = self.env.ref('purchase.purchase_form_action').read()[0]
        
        # 2. Modificar la acción base según el caso
        if len(purchase_orders) == 1:
            # Caso 1: Una sola orden. Mostrar formulario.
            # (Lección #4: res_id debe ir con view_mode: 'form') [cite: 122]
            action['views'] = [(self.env.ref('purchase.purchase_order_form').id, 'form')]
            action['res_id'] = purchase_orders.id
            action['view_mode'] = 'form'
            action['name'] = _('Orden de Compra Creada')
        else:
            # Caso 2: Múltiples órdenes. Mostrar lista.
            # (Lección #4: domain debe ir con view_mode: 'tree,form' y sin res_id) [cite: 123]
            action['domain'] = [('id', 'in', purchase_orders.ids)]
            action['view_mode'] = 'tree,form'
            action['name'] = _('Ordenes de Compra Creadas')
            if 'res_id' in action:
                del action['res_id']
        
        # 3. Retornar la acción COMPLETA y CONSISTENTE
        return action
        # --- FIN DE LA SOLUCIÓN ---