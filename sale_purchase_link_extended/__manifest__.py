# -*- coding: utf-8 -*-
{
    'name': 'Sale Purchase Link Extended',
    'version': '18.0.1.0.0',
    'category': 'Sales/Purchase',
    'summary': '''
        Vinculación avanzada entre Órdenes de Venta, Compra y Facturas con:
        - Proveedor genérico automático
        - Copia de información de vehículo (Ventas → Compras → Facturas)
        - Fecha límite a 10 días hábiles
        - Control detallado de productos
        - Liquidación de caso completa
        - Búsqueda y filtros en facturas por vehículo
    ''',
    'description': '''
        Sale Purchase Link Extended
        ============================
        
        Funcionalidades Principales:
        -----------------------------
        1. **Proveedor Genérico Automático**
           - Crea/usa automáticamente un proveedor genérico para productos sin proveedor
           - No bloquea el proceso de creación de OC
        
        2. **Información de Vehículo**
           - Copia placa, marca, año y VIN de ventas a compras
           - Transferencia automática a facturas
           - Conversión automática a mayúsculas
           - Campos de búsqueda y agrupación
           - Disponible en Ventas, Compras y Facturas
        
        3. **Vinculación Bidireccional**
           - Órdenes de compra vinculadas a orden de venta
           - Líneas de compra vinculadas a líneas de venta
           - Facturas vinculadas a orden de venta
           - Trazabilidad completa en todo el flujo
        
        4. **Fecha Límite Inteligente**
           - Cálculo automático a 10 días hábiles (Lunes-Viernes)
           - Desde la fecha de confirmación de la OC
           - Alertas visuales por vencimiento
        
        5. **Control de Productos**
           - Estado de compra por producto (Sin Pedir/Parcial/Completo)
           - Cantidades vendidas vs compradas
           - Cantidades pendientes
           - Vista en líneas de venta
        
        6. **Liquidación Detallada**
           - Resumen HTML de todas las OC relacionadas con montos
           - Control visual de productos vendidos vs comprados
           - Estadísticas de compra y venta
           - Margen de utilidad
           - Exportación a Excel y PDF
        
        7. **Integración con Facturas (NUEVO)**
           - Campos de vehículo en facturas de cliente
           - Transferencia automática desde orden de venta
           - Búsqueda rápida por placa/marca/VIN
           - Filtros: "Con Vehículo Asociado", "Sin Vehículo"
           - Agrupación por placa o marca
           - Campo relacionado: Orden de Venta (computado)
           - Compatible con Odoo Studio para campos relacionados
        
        Wizard de Creación:
        -------------------
        - Resumen previo de productos a comprar
        - Opción de agrupar por proveedor
        - Asignación automática a proveedor genérico
        - Notificaciones en chatter
        
        Navegación:
        -----------
        - Botones inteligentes en OV y OC
        - Filtros predefinidos
        - Agrupación por placa, marca, proveedor
        - Búsqueda en facturas por datos de vehículo
        
        Casos de Uso:
        -------------
        - Talleres mecánicos: Historial completo de servicios por vehículo
        - Concesionarios: Seguimiento de vehículos vendidos
        - Flotillas: Control de gastos de mantenimiento por vehículo
        - Distribuidores de repuestos: Trazabilidad Venta → Compra → Factura
        
        Validado contra Odoo 18 oficial
    ''',
    'author': 'LEO GUILLEN',
    'website': 'https://odoo.leoguillen.com',
    'license': 'LGPL-3',
    'depends': [
        'sale_management',
        'purchase',
        'stock',
        'account',  # Agregado para integración con facturas
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizards/create_purchase_wizard_views.xml',
        'views/sale_order_views.xml',
        'views/purchase_order_views.xml',
        'views/account_move_views.xml',  # Agregado para vistas de facturas
        'reports/sale_liquidation_report.xml',
    ],
    'demo': [],
    'images': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'post_init_hook': None,
}