# Sale Purchase Link Extended

## Descripción

Módulo personalizado para Odoo 18 Enterprise que extiende la funcionalidad del módulo de Ventas para automatizar la creación, vinculación y seguimiento de Órdenes de Compra (OC) basadas en las líneas de una Orden de Venta (OV).

## Características Principales

### 1. Gestión de Activos/Vehículos
- **Campos adicionales en Orden de Venta y Compra:**
  - Placa
  - Marca
  - Año
  - Número de VIN
- **Conversión automática a mayúsculas** para todos estos campos

### 2. Creación y Vinculación de Compras
- **Botón inteligente** "Crear/Ver Compras Relacionadas" en OV
- **Wizard de creación** que permite:
  - Seleccionar qué líneas comprar
  - Agrupar por proveedor
  - Asignar proveedores manualmente
- **Relación Uno (OV) a Muchos (OC)**
- **Vinculación a nivel de línea** entre líneas de venta y compra

### 3. Seguimiento y Control
El botón inteligente muestra:
- Número de OCs asociadas
- Líneas en trámite de compra
- Pendientes por comprar

### 4. Pestaña de Liquidación de Caso
Proporciona un análisis completo con:
- **Listado de compras** con estado y montos
- **Total facturado** vs **Total de compras**
- **Porcentaje de venta completado**
- **Margen de utilidad** calculado automáticamente
- **Exportación** a Excel y PDF

## Instalación

1. Copiar el módulo a la carpeta de addons de Odoo
2. Actualizar lista de aplicaciones
3. Buscar "Sale Purchase Link Extended"
4. Instalar el módulo

## Dependencias

- `sale_management`
- `purchase`
- `stock`
- `account`

## Uso

### Crear Órdenes de Compra desde una Venta

1. Abrir una Orden de Venta confirmada
2. Hacer clic en el botón "Crear Compra" (botón inteligente)
3. En el wizard:
   - Seleccionar las líneas a comprar
   - Asignar proveedores si es necesario
   - Elegir si agrupar por proveedor
4. Hacer clic en "Crear Órdenes de Compra"

### Ver Estadísticas de Liquidación

1. Abrir una Orden de Venta
2. Ir a la pestaña "Liquidación de Caso"
3. Revisar:
   - Compras asociadas
   - Montos facturados
   - Margen de utilidad
4. Exportar a Excel o PDF si es necesario

## Configuración

### Campos de Vehículo
Los campos de Placa, Marca, Año y VIN se pueden llenar en:
- **Orden de Venta:** Se copian automáticamente a las OCs generadas
- **Orden de Compra:** Se pueden editar manualmente

### Proveedores
El wizard de creación de compras usa el primer proveedor configurado en el producto. Si no hay proveedor configurado, se debe asignar manualmente en el wizard.

## Permisos

- **Vendedores:** Pueden crear y ver órdenes de compra desde ventas
- **Gerentes de Ventas:** Acceso completo a todas las funcionalidades

## Características Técnicas

### Modelos Extendidos
- `sale.order` - Orden de Venta
- `sale.order.line` - Línea de Orden de Venta
- `purchase.order` - Orden de Compra
- `purchase.order.line` - Línea de Orden de Compra

### Modelos Nuevos
- `create.purchase.wizard` - Wizard de creación de compras
- `create.purchase.wizard.line` - Líneas del wizard

### Campos Computados
- `purchase_order_count` - Número de OCs asociadas
- `purchase_lines_in_process` - Líneas en trámite
- `pending_to_purchase` - Pendientes por comprar
- `total_invoiced_amount` - Total facturado
- `total_purchase_amount` - Total de compras
- `sale_completion_percentage` - % de venta completado
- `profit_margin` - Margen de utilidad

## Reportes

### Reporte de Liquidación de Caso (PDF)
Incluye:
- Información del vehículo
- Resumen financiero
- Lista de órdenes de compra
- Estadísticas

## Soporte

Para soporte o consultas sobre el módulo, contactar a [tu equipo de soporte]

## Licencia

LGPL-3

## Autor

[Tu Empresa]

## Versión

18.0.1.0.0

## Fecha

2025
