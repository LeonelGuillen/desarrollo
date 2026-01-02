# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    # ==============================================================================================
    #                                  CAMPOS RELACIONALES (EL MOTOR)
    # ==============================================================================================
    # Estos campos buscan la Venta o Compra origen. Son la base para traer la placa.
    
    x_sale_order_id = fields.Many2one(
        'sale.order',
        string='Orden de Venta Origen',
        compute='_compute_source_orders',
        store=True,
        copy=False,
        help='Venta vinculada. Se busca automáticamente por líneas de factura o documento origen.'
    )
    
    x_purchase_order_id = fields.Many2one(
        'purchase.order',
        string='Orden de Compra Origen',
        compute='_compute_source_orders',
        store=True,
        copy=False,
        help='Compra vinculada. Se busca automáticamente por líneas de factura o documento origen.'
    )

    # ==============================================================================================
    #                                  CAMPOS DE VEHÍCULO (COMPUTADOS Y EDITABLES)
    # ==============================================================================================
    # Cambiamos a compute + store + readonly=False para llenar datos antiguos automáticamente
    
    x_placa = fields.Char(
        string='Placa',
        compute='_compute_vehicle_fields',  # <--- MAGIA: Se calcula solo
        store=True,                         # <--- Se guarda en BD (para búsquedas rápidas)
        readonly=False,                     # <--- PERMITE EDICIÓN MANUAL
        tracking=True,
        help='Placa del vehículo. Se trae de la venta/compra, pero puede editarse manualmente.'
    )
    
    x_marca = fields.Char(
        string='Marca',
        compute='_compute_vehicle_fields',
        store=True,
        readonly=False,
        tracking=True
    )
    
    x_anio = fields.Char(
        string='Año',
        compute='_compute_vehicle_fields',
        store=True,
        readonly=False,
        tracking=True
    )
    
    x_vin = fields.Char(
        string='Número de VIN',
        compute='_compute_vehicle_fields',
        store=True,
        readonly=False,
        tracking=True
    )

    # ==============================================================================================
    #                                  LÓGICA DE CÓMPUTO ROBUSTA
    # ==============================================================================================

    @api.depends('invoice_line_ids.sale_line_ids', 'invoice_line_ids.purchase_line_id', 'invoice_origin')
    def _compute_source_orders(self):
        """
        VALIDACIÓN DE ORIGEN:
        Busca profundamente cuál es el documento padre (Venta o Compra).
        Prioriza la vinculación real de líneas (más exacta) sobre el texto de 'invoice_origin'.
        """
        for move in self:
            sale_order = False
            purchase_order = False

            # 1. Búsqueda exacta por líneas (Line Matching)
            # Esto arregla casos donde 'invoice_origin' está sucio o vacío
            for line in move.invoice_line_ids:
                if not sale_order and line.sale_line_ids:
                    sale_order = line.sale_line_ids[0].order_id
                if not purchase_order and line.purchase_line_id:
                    purchase_order = line.purchase_line_id.order_id
                
                if sale_order and purchase_order:
                    break  # Ya encontramos ambos, dejar de buscar

            # 2. Fallback: Búsqueda por nombre de origen (Text Matching)
            # Para facturas muy antiguas migradas sin líneas vinculadas
            if not sale_order and move.invoice_origin:
                sale_order = self.env['sale.order'].search([('name', '=', move.invoice_origin)], limit=1)
            
            if not purchase_order and move.invoice_origin:
                purchase_order = self.env['purchase.order'].search([('name', '=', move.invoice_origin)], limit=1)

            move.x_sale_order_id = sale_order
            move.x_purchase_order_id = purchase_order

    @api.depends('x_sale_order_id', 'x_purchase_order_id')
    def _compute_vehicle_fields(self):
        """
        RECUPERACIÓN DE DATOS (AUTO-FILL):
        Si detecta una Venta o Compra vinculada, se trae los datos del vehículo.
        Al ser store=True, esto se ejecutará una vez y guardará el dato en la BD.
        """
        for move in self:
            # Prioridad: Venta > Compra
            source = move.x_sale_order_id or move.x_purchase_order_id
            
            if source:
                # Si encontramos origen, sugerimos sus datos
                # (Solo si el campo en la factura no tiene un valor manual diferente ya guardado,
                #  aunque en el primer cómputo masivo, llenará todo lo que coincida).
                move.x_placa = source.x_placa or move.x_placa
                move.x_marca = source.x_marca or move.x_marca
                move.x_anio = source.x_anio or move.x_anio
                move.x_vin = source.x_vin or move.x_vin
            else:
                # Si no hay origen, mantenemos lo que tenga (o vacío)
                # IMPORTANTE: No borrar datos si el usuario los puso a mano y luego borró el origen
                move.x_placa = move.x_placa
                move.x_marca = move.x_marca
                move.x_anio = move.x_anio
                move.x_vin = move.x_vin

    # ==============================================================================================
    #                                  VALIDACIONES DE FORMATO
    # ==============================================================================================

    @api.onchange('x_placa', 'x_marca', 'x_anio', 'x_vin')
    def _onchange_upper_vehicle(self):
        """UX: Convierte a mayúsculas mientras el usuario escribe"""
        if self.x_placa: self.x_placa = self.x_placa.upper()
        if self.x_marca: self.x_marca = self.x_marca.upper()
        if self.x_anio: self.x_anio = self.x_anio.upper()
        if self.x_vin: self.x_vin = self.x_vin.upper()

    def write(self, vals):
        """BACKEND: Asegura mayúsculas al guardar, incluso si viene de integraciones"""
        for field in ['x_placa', 'x_marca', 'x_anio', 'x_vin']:
            if field in vals and vals[field]:
                vals[field] = vals[field].upper()
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        """BACKEND: Asegura mayúsculas al crear"""
        for vals in vals_list:
            for field in ['x_placa', 'x_marca', 'x_anio', 'x_vin']:
                if vals.get(field):
                    vals[field] = vals[field].upper()
        return super().create(vals_list)