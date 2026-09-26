USE jehova_jireh_db;
GO

DECLARE @UsuarioID INT = 1;
DECLARE @AsientoID INT;

-- ==============================================================================
-- ASIENTO 1: Saldos Iniciales y Aportaciones (01 de Agosto de 2026)
-- ==============================================================================
INSERT INTO asientos_contables (fecha, concepto, modulo_origen, usuario_id)
VALUES ('2026-08-01', 'Apertura de saldos iniciales de balance', 'CONTABILIDAD', @UsuarioID);
SET @AsientoID = SCOPE_IDENTITY();

-- DEBE (Total 565,000)
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 420000.00, 0.00 FROM cuentas_contables WHERE codigo = '1.1.04'; -- Inventario
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 90000.00, 0.00 FROM cuentas_contables WHERE codigo = '1.2.01'; -- Mobiliario
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 55000.00, 0.00 FROM cuentas_contables WHERE codigo = '1.2.02'; -- Cómputo

-- HABER (Total 565,000)
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 0.00, 250000.00 FROM cuentas_contables WHERE codigo = '3.1.01'; -- Capital
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 0.00, 250000.00 FROM cuentas_contables WHERE codigo = '2.1.01'; -- Proveedores
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 0.00, 60000.00 FROM cuentas_contables WHERE codigo = '2.1.02'; -- Doc por pagar
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 0.00, 5000.00 FROM cuentas_contables WHERE codigo = '3.1.02'; -- Utilidades ac (parcial)


-- ==============================================================================
-- ASIENTO 2: Registro de Ventas y Costos Operativos (15 de Agosto de 2026)
-- ==============================================================================
INSERT INTO asientos_contables (fecha, concepto, modulo_origen, usuario_id)
VALUES ('2026-08-15', 'Registro de ingresos por ventas y servicios de la quincena', 'VENTAS', @UsuarioID);
SET @AsientoID = SCOPE_IDENTITY();

-- DEBE (Total 1,030,000)
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 650000.00, 0.00 FROM cuentas_contables WHERE codigo = '5.1.01'; -- Costo ventas
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 185000.00, 0.00 FROM cuentas_contables WHERE codigo = '1.1.02'; -- Bancos
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 60000.00, 0.00 FROM cuentas_contables WHERE codigo = '1.1.03'; -- Clientes
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 45000.00, 0.00 FROM cuentas_contables WHERE codigo = '1.1.01'; -- Caja
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 18000.00, 0.00 FROM cuentas_contables WHERE codigo = '1.1.05'; -- IVA acred
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 70000.00, 0.00 FROM cuentas_contables WHERE codigo = '6.1.01'; -- Sueldos
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 2000.00, 0.00 FROM cuentas_contables WHERE codigo = '6.1.04'; -- Agua (parcial)

-- HABER (Total 1,030,000)
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 0.00, 950000.00 FROM cuentas_contables WHERE codigo = '4.1.01'; -- Ventas rep
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 0.00, 80000.00 FROM cuentas_contables WHERE codigo = '4.1.02'; -- Ingresos taller


-- ==============================================================================
-- ASIENTO 3: Registro de Gastos y Ajustes de Fin de Mes (31 de Agosto de 2026)
-- ==============================================================================
INSERT INTO asientos_contables (fecha, concepto, modulo_origen, usuario_id)
VALUES ('2026-08-31', 'Provisión de gastos operativos, depreciación y cierres', 'CONTABILIDAD', @UsuarioID);
SET @AsientoID = SCOPE_IDENTITY();

-- DEBE (Total 103,000)
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 30000.00, 0.00 FROM cuentas_contables WHERE codigo = '6.1.02'; -- Alquiler
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 12000.00, 0.00 FROM cuentas_contables WHERE codigo = '6.1.03'; -- Energía
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 5000.00, 0.00 FROM cuentas_contables WHERE codigo = '6.1.05'; -- Internet
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 10000.00, 0.00 FROM cuentas_contables WHERE codigo = '6.1.06'; -- Publicidad
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 8000.00, 0.00 FROM cuentas_contables WHERE codigo = '6.1.07'; -- Mant
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 3000.00, 0.00 FROM cuentas_contables WHERE codigo = '6.1.08'; -- Papeleria
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 12000.00, 0.00 FROM cuentas_contables WHERE codigo = '6.1.09'; -- Depreciacion gasto
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 22000.00, 0.00 FROM cuentas_contables WHERE codigo = '6.1.10'; -- Comisiones
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 1000.00, 0.00 FROM cuentas_contables WHERE codigo = '6.1.04'; -- Agua (resto)

-- HABER (Total 103,000)
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 0.00, 12000.00 FROM cuentas_contables WHERE codigo = '1.2.03'; -- Depre ac
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 0.00, 22000.00 FROM cuentas_contables WHERE codigo = '2.1.03'; -- IVA por pagar
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 0.00, 18000.00 FROM cuentas_contables WHERE codigo = '2.1.04'; -- Sueldos pagar
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 0.00, 5000.00 FROM cuentas_contables WHERE codigo = '2.1.05'; -- Serv por pagar
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 0.00, 46000.00 FROM cuentas_contables WHERE codigo = '3.1.02'; -- Utilidades ac (resto)

GO
PRINT 'Saldos iniciales registrados exitosamente (divididos en múltiples fechas).';
