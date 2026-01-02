# -*- coding: utf-8 -*-

from odoo import models, api


class SaleLiquidationReport(models.AbstractModel):
    _name = 'report.sale_purchase_link_extended.report_sale_liquidation'
    _description = 'Reporte de Liquidación de Ventas'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Prepara los valores para el reporte de liquidación"""
        docs = self.env['sale.order'].browse(docids)
        
        return {
            'doc_ids': docids,
            'doc_model': 'sale.order',
            'docs': docs,
            'data': data,
        }
