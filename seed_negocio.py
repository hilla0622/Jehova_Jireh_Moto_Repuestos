"""Carga integral repetible. Sin --apply verifica y revierte; nunca borra operaciones.

Los datos son generados para la presentación del proyecto; no acreditan operaciones,
identidades, transferencias ni presentaciones oficiales. La procedencia se conserva
en las tablas técnicas cargas_negocio y carga_negocio_registros, fuera de los textos
comerciales. El respaldo completo debe existir antes de aplicar sobre la base local.
"""
import argparse
import ast
import calendar
from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path
import random
import re

from catalogo_carga_negocio import PRODUCTOS, NOMBRES, APELLIDOS, BARRIOS, TALLERES, PROVEEDORES
from calculos_rrhh import calcular_nomina_empleado
import fiscal_service as fiscal

ROOT = Path(__file__).resolve().parent
VERSION = 'NEGOCIO-2024-2026-V1'
CENT = Decimal('.01')
PARAMETROS = {'INSS_LABORAL': 7, 'INSS_PATRONAL': 21.5, 'INATEC_PATRONAL': 2,
              'VACACIONES_MES': 2.5, 'AGUINALDO_PROV': 100 / 12}


def dinero(n):
    return Decimal(str(n)).quantize(CENT, rounding=ROUND_HALF_UP)


def dias(inicio, fin):
    while inicio <= fin:
        yield inicio
        inicio += timedelta(days=1)


def meses(inicio, fin):
    for anio in range(inicio.year, fin.year + 1):
        for mes in range(1, 13):
            primero = date(anio, mes, 1)
            ultimo = date(anio, mes, calendar.monthrange(anio, mes)[1])
            if ultimo >= inicio and primero <= fin:
                yield primero, min(ultimo, fin), ultimo <= fin


def jornada_comercial(dia):
    return dia.weekday() != 6 and (dia.month, dia.day) not in ((1, 1), (12, 25), (9, 14), (9, 15))


class Carga:
    def __init__(self, conn, inicio, fin):
        self.conn, self.cur = conn, conn.cursor()
        self.inicio, self.fin = inicio, fin
        self.rng = random.Random(20261102)
        self.conteos, self.registros, self.cambios = Counter(), [], []
        self.productos, self.clientes, self.proveedores = [], [], []
        self.eventos, self.saldos = defaultdict(list), defaultdict(lambda: Decimal(0))
        self.secuencia = Counter()
        self.cur.execute('SET DATEFORMAT ymd; SET XACT_ABORT ON; SET NOCOUNT ON;')
        self.cur.execute('''IF OBJECT_ID('cargas_negocio','U') IS NULL CREATE TABLE cargas_negocio (
            id INT IDENTITY PRIMARY KEY, version VARCHAR(70) NOT NULL UNIQUE,
            fecha_inicio DATE NOT NULL, fecha_fin DATE NOT NULL, resumen NVARCHAR(MAX),
            creado_en DATETIME2 DEFAULT SYSUTCDATETIME());
            IF OBJECT_ID('carga_negocio_registros','U') IS NULL BEGIN
              CREATE TABLE carga_negocio_registros (carga_id INT NOT NULL REFERENCES cargas_negocio(id),
                tabla VARCHAR(100) NOT NULL, registro_id INT NOT NULL,
                PRIMARY KEY(carga_id,tabla,registro_id));
              CREATE INDEX IX_carga_registro ON carga_negocio_registros(tabla,registro_id);
            END;
            IF OBJECT_ID('carga_negocio_cambios','U') IS NULL CREATE TABLE carga_negocio_cambios (
              id INT IDENTITY PRIMARY KEY, carga_id INT NOT NULL REFERENCES cargas_negocio(id),
              tabla VARCHAR(100) NOT NULL, registro_id INT NOT NULL, campo VARCHAR(100) NOT NULL,
              antes NVARCHAR(MAX), despues NVARCHAR(MAX));''')
        self.cur.execute("DECLARE @r INT; EXEC @r=sp_getapplock @Resource='carga_integral_negocio', @LockMode='Exclusive', @LockOwner='Transaction', @LockTimeout=5000; IF @r<0 THROW 50001,'Hay otra carga en ejecución',1;")
        self.cur.execute('SELECT id,resumen,fecha_inicio,fecha_fin FROM cargas_negocio WHERE version=?', VERSION)
        self.existente = self.cur.fetchone()
        if self.existente:
            if self.existente[2] != inicio or self.existente[3] != fin:
                raise ValueError('La versión ya existe con otro período; no se insertarán duplicados.')
            return
        self.cur.execute('INSERT INTO cargas_negocio(version,fecha_inicio,fecha_fin) OUTPUT inserted.id VALUES(?,?,?)', VERSION, inicio, fin)
        self.cid = self.cur.fetchone()[0]
        self.cur.execute('SELECT codigo,id FROM cuentas_contables')
        self.cuentas = dict(self.cur.fetchall())
        self.cur.execute('SELECT id FROM usuarios ORDER BY id')
        self.usuarios = [r[0] for r in self.cur.fetchall()]
        self.uid = self.usuarios[0]
        self.cur.execute('''SELECT u.id FROM usuarios u JOIN roles r ON r.id=u.rol_id
            WHERE r.nombre IN ('Vendedor','Administrador') ORDER BY u.id''')
        self.vendedores = [r[0] for r in self.cur.fetchall()]

    def insertar(self, tabla, **valores):
        columnas = ','.join('[' + c + ']' for c in valores)
        self.cur.execute(f'INSERT INTO [{tabla}] ({columnas}) OUTPUT inserted.id VALUES ({",".join("?" for _ in valores)})', tuple(valores.values()))
        rid = int(self.cur.fetchone()[0])
        self.registros.append((self.cid, tabla, rid))
        self.conteos[tabla] += 1
        return rid

    def cambiar(self, tabla, rid, campo, antes, despues):
        if antes == despues:
            return
        self.cur.execute(f'UPDATE [{tabla}] SET [{campo}]=? WHERE id=?', despues, rid)
        self.cambios.append((self.cid, tabla, rid, campo,
                             None if antes is None else str(antes),
                             None if despues is None else str(despues)))

    def codigo(self, prefijo, dia):
        clave = f'{prefijo}-{dia:%Y%m%d}'
        self.secuencia[clave] += 1
        return f'{clave}-{self.secuencia[clave]:04d}'

    def asiento(self, dia, concepto, lineas, modulo, referencia=None, usuario=None):
        lineas = [(c, dinero(d), dinero(h)) for c, d, h in lineas if d or h]
        if sum(d for _, d, _ in lineas) != sum(h for _, _, h in lineas):
            raise ValueError('Asiento no balanceado: ' + concepto)
        aid = self.insertar('asientos_contables', fecha=dia, concepto=concepto[:255],
            modulo_origen=modulo, referencia_id=referencia, usuario_id=usuario or self.uid,
            created_at=datetime.combine(dia, time(12)))
        for codigo, debe, haber in lineas:
            self.insertar('movimientos_contables', asiento_id=aid, cuenta_id=self.cuentas[codigo], debe=debe, haber=haber)
            self.saldos[codigo] += debe - haber
        return aid

    def mover(self, p, cantidad, tipo, momento, referencia, motivo):
        antes = p['stock']
        despues = antes + cantidad
        if despues < 0:
            raise ValueError('Salida sin existencias: ' + p['sku'])
        self.insertar('movimientos_inventario', fecha=momento, producto_id=p['id'],
            tipo_movimiento=tipo, cantidad=abs(cantidad), stock_anterior=antes,
            stock_posterior=despues, referencia_origen=referencia[:100], motivo=motivo,
            usuario_id=self.uid, created_at=momento)
        p['stock'] = despues

    def catalogos(self):
        self.cur.execute('SELECT nombre,id FROM categorias')
        cats = dict(self.cur.fetchall())
        for i, fila in enumerate(PRODUCTOS):
            sku, nombre, categoria, marca, modelo, costo, precio, rotacion = fila
            if categoria not in cats:
                cats[categoria] = self.insertar('categorias', nombre=categoria,
                    descripcion=f'Repuestos y suministros de {categoria.lower()}', created_at=self.inicio)
            self.cur.execute('SELECT id FROM productos WHERE codigo_sku=?', sku)
            if self.cur.fetchone():
                raise ValueError('SKU existente; revise la carga antes de reutilizar: ' + sku)
            pid = self.insertar('productos', codigo_sku=sku, codigo_barras=f'2902601{i:06d}',
                nombre=nombre, descripcion=f'{nombre}. Verificar modelo y medida antes de instalar.',
                marca=marca, modelo_compatible=modelo, categoria_id=cats[categoria],
                ubicacion_estante=f'{chr(65+i//12)}-{1+i%12:02d}', costo=dinero(costo),
                precio_venta=dinero(precio), stock_actual=0, stock_minimo=3 if rotacion<5 else 8,
                activo=True, created_at=self.inicio, updated_at=self.fin)
            self.productos.append(dict(id=pid,sku=sku,nombre=nombre,costo=dinero(costo),
                precio=dinero(precio),peso=rotacion,stock=0,minimo=3 if rotacion<5 else 8))
        nombres = set()
        for i in range(190):
            while True:
                nombre = f'{self.rng.choice(NOMBRES)} {self.rng.choice(APELLIDOS)} {self.rng.choice(APELLIDOS)}'
                if nombre not in nombres:
                    nombres.add(nombre); break
            tipo = self.rng.choices(['General','Frecuente','Mayorista'],[60,34,6])[0]
            cliente = dict(nombre_completo=nombre,telefono=f'+505 {self.rng.randint(8100,8899)}-{self.rng.randint(1000,9999)}',
                email=None,direccion=self.rng.choice(BARRIOS),tipo_cliente=tipo,created_at=self.inicio)
            cliente['id'] = self.insertar('clientes',**cliente)
            self.clientes.append(cliente)
        for nombre, contacto in TALLERES:
            cliente = dict(nombre_completo=f'{nombre} - {contacto}',telefono=f'+505 {self.rng.randint(8200,8799)}-{self.rng.randint(1000,9999)}',
                direccion=self.rng.choice(BARRIOS),tipo_cliente='Taller',created_at=self.inicio)
            cliente['id'] = self.insertar('clientes', **cliente)
            self.clientes.append(cliente)
        for nombre, contacto, ciudad in PROVEEDORES:
            pid = self.insertar('proveedores', nombre_empresa=nombre,contacto_nombre=contacto,
                telefono=f'+505 22{self.rng.randint(10,99)}-{self.rng.randint(1000,9999)}',
                direccion=f'Zona comercial, {ciudad}',activo=True,created_at=self.inicio,updated_at=self.fin)
            self.proveedores.append(pid)
        self.asiento(self.inicio,'Aporte para capital de trabajo y abastecimiento',
            [('1.1.02',480000,0),('1.1.01',12000,0),('3.1.01',0,492000)],'CAPITAL')
        self.asiento(self.inicio,'Adquisición de estanterías y equipo para atención de mostrador',
            [('1.2.01',42000,0),('1.2.02',24000,0),('1.1.02',0,66000)],'ACTIVOS')

    def comprar(self, dia, items, credito=False, pendiente=False, momento=None):
        momento=momento or datetime.combine(dia,time(7,15))
        codigo = self.codigo('COM',dia)
        total = sum(p['costo'] * cantidad for p,cantidad in items)
        cid = self.insertar('compras',codigo_compra=codigo,numero_factura_proveedor=self.codigo('FAC',dia),
            proveedor_id=self.rng.choice(self.proveedores),usuario_id=self.uid,fecha_compra=dia,
            total=total,forma_pago='Crédito' if credito else 'Transferencia',
            estado='Pendiente' if pendiente else 'Completada',
            observaciones='Reposición de repuestos de mayor rotación' if not pendiente else 'Entrega programada por el proveedor',created_at=dia)
        for p,cantidad in items:
            self.insertar('detalle_compras',compra_id=cid,producto_id=p['id'],cantidad=cantidad,
                costo_unitario=p['costo'],subtotal=p['costo']*cantidad)
            if not pendiente:
                self.mover(p,cantidad,'ENTRADA_COMPRA',momento,codigo,'Recepción de mercadería del proveedor')
        if pendiente:
            return
        self.insertar('recepciones_compra',compra_id=cid,fechaRecepcion=momento,estado='Completada')
        self.asiento(dia,f'Compra de repuestos {codigo}',[('1.1.04',total,0),('2.1.01' if credito else '1.1.02',0,total)],'COMPRAS',cid)
        if credito:
            self.eventos[dia+timedelta(days=self.rng.choice([15,21,30]))].append(('pagar_compra',cid,total,codigo))

    def venta(self, dia, turno, numero, web=False):
        momento=datetime.combine(dia,time(8))+timedelta(minutes=numero*17+self.rng.randint(0,9))
        cliente = self.rng.choice(self.clientes)
        cantidad_lineas = self.rng.choices([1,2,3,4,5],[38,33,19,8,2])[0]
        seleccion = []
        while len(seleccion)<cantidad_lineas:
            p = self.rng.choices(self.productos,weights=[p['peso'] for p in self.productos])[0]
            if p not in seleccion: seleccion.append(p)
        lineas = []
        mayorista = cliente['tipo_cliente'] in ('Taller','Mayorista')
        for p in seleccion:
            cantidad = self.rng.choices([1,2,3,4,6],[60,24,9,5,2])[0] if mayorista else self.rng.choices([1,2,3],[84,14,2])[0]
            if p['stock']<cantidad:
                self.comprar(dia,[(p,self.rng.randint(18,42)+cantidad)],credito=self.rng.random()<.22,momento=momento-timedelta(seconds=30))
            factor = Decimal('.92') if dia.year==2024 else Decimal('.96') if dia.year==2025 else Decimal('1')
            if mayorista:factor*=Decimal('.94')
            elif self.rng.random()<.07:factor*=Decimal('.97')
            precio = dinero(p['precio']*factor)
            lineas.append((p,cantidad,precio,precio*cantidad))
        total = sum(l[3] for l in lineas)
        costo = sum(l[0]['costo']*l[1] for l in lineas)
        metodo = self.rng.choices(['Efectivo','Transferencia','Tarjeta','Crédito'],[56,26,13,5])[0]
        if web:metodo=self.rng.choice(['Transferencia','Tarjeta'])
        codigo = self.codigo('WEB' if web else 'VEN',dia)
        if web:
            rid=self.insertar('pedidos_web',codigo=codigo,cliente_id=cliente['id'],fecha=momento,
                subtotal=total,total=total,formaEntrega='Retiro en Tienda',
                metodo=metodo,estado='Completado',nombre_cliente=cliente['nombre_completo'],
                telefono=cliente['telefono'],direccion_entrega='Retiro en Tienda (Sucursal Masatepe)')
            tabla,modulo,origen='pedidos_web','PEDIDOS_WEB','PEDIDO_WEB'
            carrito=self.insertar('carritos',cliente_id=cliente['id'],subtotal=total,estado='Completado')
        else:
            rid=self.insertar('ventas',codigo_venta=codigo,cliente_id=cliente['id'],usuario_id=turno['usuario'],
                fecha_venta=dia,subtotal=total,descuento=0,total=total,forma_pago=metodo,
                estado='Completada',sesion_caja_id=turno['id'],notas='Entrega de repuestos en mostrador',created_at=momento)
            tabla,modulo,origen='ventas','VENTAS','VENTA_POS'
        for p,cantidad,precio,subtotal in lineas:
            if web:
                valores=dict(producto_id=p['id'],cantidad=cantidad,precioUnitario=precio,subtotal=subtotal)
                self.insertar('detalle_pedidos_web',pedido_id=rid,**valores)
                self.insertar('detalle_carritos',carrito_id=carrito,**valores)
            else:
                self.insertar('detalle_ventas',venta_id=rid,producto_id=p['id'],cantidad=cantidad,
                    precio_unitario=precio,costo_historico=p['costo'],subtotal=subtotal)
            self.mover(p,-cantidad,'SALIDA_VENTA',momento,codigo,'Despacho de repuestos por pedido web' if web else 'Entrega de repuestos por venta de mostrador')
        debe='1.1.03' if metodo=='Crédito' else '1.1.01' if metodo=='Efectivo' else '1.1.02'
        self.asiento(dia,f'{"Pedido" if web else "Venta"} {codigo}',[(debe,total,0),('4.1.01',0,total),
            ('5.1.01',costo,0),('1.1.04',0,costo)],modulo,rid,turno['usuario'])
        ids=dict(venta_id=None if web else rid,pedido_web_id=rid if web else None,origen=origen)
        if metodo!='Crédito':
            self.insertar('pagos',**ids,metodo=metodo,monto=total,referencia=f'Cobro {codigo}',fecha=momento)
        else:
            self.eventos[dia+timedelta(days=self.rng.choice([10,15,21,30]))].append(('cobrar',rid,total,codigo))
        self.insertar('comprobantes',**ids,numero=f'TICK-{codigo}',fechaEmision=momento,total=total)
        if metodo=='Efectivo':turno['efectivo']+=total
        if not web and metodo!='Crédito' and self.rng.random()<.017:
            p,cantidad,precio,_=self.rng.choice(lineas)
            self.eventos[dia+timedelta(days=self.rng.randint(1,6))].append(('devolver',rid,p,precio,codigo))

    def procesar_eventos(self,dia):
        for evento in self.eventos.pop(dia,[]):
            tipo=evento[0]
            if tipo=='pagar_compra':
                _,cid,total,codigo=evento
                self.asiento(dia,f'Pago a proveedor por {codigo}',[('2.1.01',total,0),('1.1.02',0,total)],'PAGO_PROVEEDOR',cid)
            elif tipo=='cobrar':
                _,vid,total,codigo=evento
                self.insertar('pagos',venta_id=vid,origen='VENTA_POS',metodo='Transferencia',monto=total,
                    referencia=f'Abono de cuenta {codigo}',fecha=datetime.combine(dia,time(10,30)))
                self.asiento(dia,f'Cobro de cuenta por {codigo}',[('1.1.02',total,0),('1.1.03',0,total)],'COBRO_CLIENTE',vid)
            elif tipo=='devolver':
                _,vid,p,precio,codigo=evento
                cod=self.codigo('DEV',dia)
                motivo=self.rng.choice(['Medida incompatible con el modelo de motocicleta','Cambio de referencia solicitado por el cliente','Compra duplicada; empaque sin abrir'])
                did=self.insertar('devoluciones',venta_id=vid,codigo_devolucion=cod,fecha=datetime.combine(dia,time(7)),
                    motivo=motivo,total_devuelto=precio,usuario_id=self.uid)
                self.insertar('detalle_devoluciones',devolucion_id=did,producto_id=p['id'],cantidad=1,precio_unitario=precio,subtotal=precio)
                self.mover(p,1,'DEVOLUCION_CLIENTE',datetime.combine(dia,time(7)),cod,'Reintegro de producto revisado en buen estado')
                self.asiento(dia,f'Devolución {cod} de {codigo}',[('4.1.01',precio,0),('1.1.02',0,precio),
                    ('1.1.04',p['costo'],0),('5.1.01',0,p['costo'])],'DEVOLUCION',did)

    def operaciones(self):
        self.comprar(self.inicio,[(p,self.rng.randint(16,38)) for p in self.productos])
        for dia in dias(self.inicio,self.fin):
            self.procesar_eventos(dia)
            if jornada_comercial(dia):
                if dia.weekday()==0:
                    items=[(p,self.rng.randint(15,40)) for p in self.productos if p['stock']<p['minimo']+self.rng.randint(2,9)]
                    if items:self.comprar(dia,items,credito=self.rng.random()<.3)
                uid=self.rng.choice(self.vendedores)
                apertura=self.saldos['1.1.01']
                sid=self.insertar('sesiones_caja',usuario_id=uid,fecha_apertura=datetime.combine(dia,time(7,45)),
                    monto_inicial=apertura,estado='Cerrada',observaciones='Apertura y arqueo de caja de mostrador')
                turno=dict(id=sid,usuario=uid,efectivo=Decimal(0))
                estacional=[.82,.89,1.02,1.08,1.01,.93,.98,1.08,.91,1.11,1.15,1.35][dia.month-1]
                quincena=1.25 if dia.day in (14,15,16,29,30) else 1
                cantidad=max(2,min(29,round(self.rng.lognormvariate(2.22,.42)*estacional*quincena*(1+.1*(dia.year-2024)))))
                if dia==self.fin:cantidad=max(2,cantidad//2)
                for numero in range(cantidad):self.venta(dia,turno,numero,web=self.rng.random()<.09)
                final=apertura+turno['efectivo']
                self.cur.execute('UPDATE sesiones_caja SET fecha_cierre=?,monto_final_esperado=?,monto_final_real=?,diferencia=0 WHERE id=?',
                    datetime.combine(dia,time(12 if dia==self.fin else 17,30)),final,final,sid)
                if self.saldos['1.1.01']>18000:
                    deposito=self.saldos['1.1.01']-Decimal(self.rng.randrange(6000,10001,500))
                    self.asiento(dia,'Depósito de recaudación de caja en cuenta bancaria',
                        [('1.1.02',deposito,0),('1.1.01',0,deposito)],'TESORERIA',sid)
            if dia.day==calendar.monthrange(dia.year,dia.month)[1]:self.cierre_mensual(dia)
            if dia.day==1:print(f'Procesando {dia:%Y-%m}: {self.conteos["ventas"]} ventas de mostrador',flush=True)
        for p in self.productos:self.cur.execute('UPDATE productos SET stock_actual=? WHERE id=?',p['stock'],p['id'])
        # Pedidos abiertos y una reposición aún sin recibir, sin afectar existencias ni ventas.
        for i in range(7):
            cliente=self.rng.choice(self.clientes);p=self.rng.choice(self.productos);q=self.rng.randint(1,3)
            rid=self.insertar('pedidos_web',codigo=self.codigo('WEB',self.fin),cliente_id=cliente['id'],
                fecha=datetime.combine(self.fin,time(10,i*5)),subtotal=p['precio']*q,total=p['precio']*q,
                formaEntrega='Retiro en Tienda',metodo='Transferencia',estado='Pendiente',nombre_cliente=cliente['nombre_completo'],
                telefono=cliente['telefono'],direccion_entrega='Retiro en Tienda (Sucursal Masatepe)')
            self.insertar('detalle_pedidos_web',pedido_id=rid,producto_id=p['id'],cantidad=q,precioUnitario=p['precio'],subtotal=p['precio']*q)
        self.comprar(self.fin,[(p,self.rng.randint(10,24)) for p in self.rng.sample(self.productos,6)],pendiente=True)

    def cierre_mensual(self,dia):
        for codigo,concepto,base in [('6.1.02','Alquiler del local',8500),('6.1.03','Energía eléctrica',1900),
              ('6.1.04','Servicio de agua',350),('6.1.05','Internet y telefonía',1150),
              ('6.1.06','Publicidad y promoción',1200),('6.1.07','Mantenimiento del local',650),
              ('6.1.08','Papelería y material de empaque',550),('6.1.10','Comisiones bancarias',210)]:
            importe=dinero(base if codigo in ('6.1.02','6.1.05') else base*self.rng.uniform(.7,1.4))
            self.asiento(dia,f'{concepto} {dia:%m/%Y}',[(codigo,importe,0),('1.1.02',0,importe)],'GASTOS')
        self.asiento(dia,f'Depreciación de estanterías y equipo {dia:%m/%Y}',[('6.1.09',750,0),('1.2.03',0,750)],'DEPRECIACION')
        self.nomina(dia)
        # Anticipo registrado como acreditamiento interno; no crea presentación oficial.
        self.cur.execute('''SELECT COALESCE(SUM(m.haber-m.debe),0) FROM movimientos_contables m
            JOIN asientos_contables a ON a.id=m.asiento_id WHERE m.cuenta_id=? AND YEAR(a.fecha)=? AND MONTH(a.fecha)=?''',
            self.cuentas['4.1.01'],dia.year,dia.month)
        base=self.cur.fetchone()[0];importe=dinero(max(0,base)*Decimal('.01'))
        if importe:
            ref=f'ANT-{dia:%Y%m}-02'
            rid=self.insertar('acreditamientos_tributarios',tipo='ANTICIPO_PAGADO',concepto=f'Anticipo de IR del período {dia:%m/%Y}',
                ejercicio_fiscal=dia.year,periodo_mes=dia.month,fecha=dia,numero_referencia=ref,
                monto_base=base,porcentaje_aplicado=1,importe_total=importe,importe_aplicado=0,estado='Registrado',usuario_id=self.uid,created_at=dia)
            self.asiento(dia,f'Anticipo de IR {ref}',[('1.1.06',importe,0),('1.1.02',0,importe)],'TRIBUTARIO',rid)

    def nomina(self,dia, *, pagar=True, generar_extras=True):
        self.cur.execute('SELECT id FROM nomina WHERE periodo_anio=? AND periodo_mes=?',dia.year,dia.month)
        row=self.cur.fetchone()
        nid=row[0] if row else self.insertar('nomina',periodo_anio=dia.year,periodo_mes=dia.month,
            fecha_generacion=datetime.combine(dia,time(11)),estado='CERRADA')
        self.cur.execute('SELECT empleado_id FROM detalle_nomina WHERE nomina_id=?',nid)
        existentes={r[0] for r in self.cur.fetchall()}
        for e in self.empleados:
            ini=max(e['fecha_ingreso'],date(dia.year,dia.month,1))
            fin=min(e.get('fecha_baja') or dia,dia)
            if ini>fin or e['id'] in existentes:continue
            completos=ini.day==1 and fin==dia
            dias_pagados=30 if completos else min(30,(fin-ini).days+1)
            salario=dinero(e['salario_base']*Decimal(dias_pagados)/30)
            extras=Decimal(0)
            if generar_extras and self.rng.random()<.37:
                cantidad=self.rng.choice([1,2,2,3,4])
                valor_hora=dinero(e['salario_base']/240)
                extras=dinero(valor_hora*cantidad*2)
                fecha_extra=fin
                while fecha_extra.weekday()==6:fecha_extra-=timedelta(days=1)
                self.insertar('horas_extras',empleado_id=e['id'],fecha=fecha_extra,
                    cantidad_horas=cantidad,valor_hora_ordinaria=valor_hora,recargo_porcentaje=100,monto_total=extras,
                    motivo=self.rng.choice(['Recepción de mercadería fuera de horario','Inventario físico de estanterías','Atención de pedidos de talleres']),
                    estado='Pagada',autorizado_por='Gilda Pérez',nomina_id=nid,created_at=fin)
            calc={k:dinero(v) for k,v in calcular_nomina_empleado(float(salario),float(extras),parametros=PARAMETROS).items()}
            acumulado=dinero(max(0,(ini-e['fecha_ingreso']).days)*Decimal(30)/365)
            vacaciones_mes=dinero(Decimal(dias_pagados)/12)
            detalle=self.insertar('detalle_nomina',nomina_id=nid,empleado_id=e['id'],salario_base=salario,
                inss_laboral=calc['inss_laboral'],ir=calc['ir_retencion'],neto_pagar=calc['salario_neto'],
                ingresos_extra=extras,inss_patronal=calc['inss_patronal'],inatec_patronal=calc['inatec_patronal'],
                provision_vacaciones=calc['provision_vacaciones'],provision_aguinaldo=calc['provision_aguinaldo'],
                dias_trabajados=dias_pagados,vac_acumulada=acumulado,vac_mes=vacaciones_mes,
                vac_saldo_final=acumulado+vacaciones_mes,historico_salario=e['salario_base'],
                historico_nombre=e['nombre_completo'],historico_identificacion=e.get('identificacion'),
                historico_cargo=e['cargo'],historico_ingreso=e['fecha_ingreso'])
            self.insertar('colilla_pago',detalle_nomina_id=detalle,periodo=f'{dia:%m/%Y}',netoRecibir=calc['salario_neto'])
            prov=calc['provision_vacaciones']+calc['provision_aguinaldo']
            self.asiento(dia,f'Nómina {dia:%m/%Y} - {e["nombre_completo"]}',[
                ('6.1.01',calc['salario_bruto'],0),('6.1.11',calc['inss_patronal']+calc['inatec_patronal'],0),
                ('6.1.12',prov,0),('2.1.06',0,calc['inss_laboral']+calc['inss_patronal']),
                ('2.1.07',0,calc['ir_retencion']),('2.1.08',0,prov),('2.1.10',0,calc['inatec_patronal']),
                ('2.1.04',0,calc['salario_neto'])],'RRHH',nid)
            if not pagar:
                continue
            prefijo_trf=f'TRF-BAC-{fin.year}-'
            self.cur.execute('''SELECT ISNULL(MAX(TRY_CONVERT(INT,RIGHT(numero_referencia,4))),0)+1
                FROM pagos_nomina WHERE numero_referencia LIKE ? AND LEN(numero_referencia)=?''',
                prefijo_trf+'%',len(prefijo_trf)+4)
            referencia_trf=f'{prefijo_trf}{self.cur.fetchone()[0]:04d}'
            pago=self.insertar('pagos_nomina',nomina_id=nid,empleado_id=e['id'],monto_pagado=calc['salario_neto'],
                fecha_pago=datetime.combine(fin,time(11,30)),metodo_pago='Transferencia Bancaria',
                numero_referencia=referencia_trf,estado='Confirmado',registrado_por='Gilda Pérez',
                cuenta_id=self.cuentas['1.1.02'],observaciones=f'Abono de salario neto de {dia:%m/%Y}')
            aid=self.asiento(fin,f'Pago de salario {dia:%m/%Y} - {e["nombre_completo"]}',[
                ('2.1.04',calc['salario_neto'],0),('1.1.02',0,calc['salario_neto'])],'RRHH_PAGO',pago)
            self.cur.execute('UPDATE pagos_nomina SET asiento_id=? WHERE id=?',aid,pago)
            self.asiento(dia,f'Entero de deducciones y aportes {dia:%m/%Y} - {e["nombre_completo"]}',[
                ('2.1.06',calc['inss_laboral']+calc['inss_patronal'],0),('2.1.07',calc['ir_retencion'],0),
                ('2.1.10',calc['inatec_patronal'],0),('1.1.02',0,calc['inss_laboral']+calc['inss_patronal']+calc['ir_retencion']+calc['inatec_patronal'])],'RRHH_APORTES',detalle)
        self.cur.execute('''SELECT SUM(salario_base+ingresos_extra),SUM(inss_laboral+ir+otras_deducciones),
            SUM(neto_pagar),SUM(inss_patronal),SUM(inatec_patronal),SUM(provision_vacaciones),SUM(provision_aguinaldo)
            FROM detalle_nomina WHERE nomina_id=?''',nid)
        valores=self.cur.fetchone()
        campos=['total_ingresos','total_deducciones','total_neto','inss_patronal_total',
                'inatec_patronal_total','provision_vac_total','provision_agui_total']
        self.cur.execute('SELECT '+','.join(campos)+' FROM nomina WHERE id=?',nid)
        previos=self.cur.fetchone()
        for campo,antes,despues in zip(campos,previos,valores):self.cambiar('nomina',nid,campo,antes,despues or 0)

    def personal(self):
        jid=self.insertar('jornadas_laborales',nombre='Mostrador y bodega',hora_entrada='08:00',hora_salida='17:00',
            minutos_descanso=60,dias_laborables='Lunes a sábado',dia_descanso='Domingo',horas_semanales=44,activo=True,created_at=self.inicio)
        for nombre,cargo,salario,ingreso,baja in [
            ('Luis Alberto Duarte Solís','Vendedor de Mostrador',11500,date(2024,1,2),None),
            ('Rosa Elena Navarro Méndez','Cajero de tienda',9800,date(2024,3,4),None),
            ('Óscar David Espinoza Rivas','Auxiliar de bodega',9200,date(2025,2,3),None),
            ('Marvin José Bermúdez López','Auxiliar de bodega',8800,date(2024,1,8),date(2024,11,30)),
        ]:
            self.cur.execute('SELECT id FROM cargos WHERE nombre_cargo=?',cargo)
            row=self.cur.fetchone()
            cargo_id=row[0] if row else self.insertar('cargos',nombre_cargo=cargo,descripcion=f'Atención de tareas de {cargo.lower()}',
                salario_base_sugerido=salario,activo=True,area='Operaciones',responsabilidades='Atención al cliente y cuidado de herramientas y repuestos')
            self.insertar('empleados',nombre_completo=nombre,identificacion=f'EMP-{ingreso.year}-{len(self.registros):05d}',
                cargo=cargo,cargo_id=cargo_id,salario_base=salario,fecha_ingreso=ingreso,activo=baja is None,
                telefono=f'+505 {self.rng.randint(8200,8899)}-{self.rng.randint(1000,9999)}',
                direccion=self.rng.choice(BARRIOS),contacto_emergencia=self.rng.choice(NOMBRES)+' '+self.rng.choice(APELLIDOS),
                jornada_id=jid,jornada_asignada='Mostrador y bodega',fecha_baja=baja,motivo_baja='Renuncia voluntaria' if baja else None,
                inss_estado='Inactivo' if baja else 'Activo',created_at=ingreso)
        self.cur.execute('''SELECT id,nombre_completo,identificacion,cargo,salario_base,fecha_ingreso,fecha_baja,activo
            FROM empleados WHERE activo=1 OR identificacion LIKE 'EMP-%' ORDER BY id''')
        campos=[c[0] for c in self.cur.description]
        self.empleados=[dict(zip(campos,r)) for r in self.cur.fetchall()]
        self.cur.execute('SELECT empleado_id FROM contratos_laborales')
        con_contrato={r[0] for r in self.cur.fetchall()}
        for e in self.empleados:
            if e['id'] not in con_contrato:
                self.insertar('contratos_laborales',numero_contrato=f'CTR-{e["fecha_ingreso"]:%Y}-{e["id"]:04d}',
                    empleado_id=e['id'],cargo=e['cargo'],tipo_contratacion='Tiempo Indeterminado',lugar_trabajo='Tienda principal, Masatepe',
                    jornada_laboral='Diurna, lunes a sábado',salario_mensual=e['salario_base'],forma_pago='Mensual',
                    fecha_inicio=e['fecha_ingreso'],fecha_fin=e['fecha_baja'],estado='Finalizado' if e['fecha_baja'] else 'Vigente',
                    observaciones='Funciones de atención y apoyo a la operación de la tienda',created_at=e['fecha_ingreso'])
            # Se registra información del expediente; no se inventan adjuntos o firmas.
            self.insertar('historial_laboral',empleado_id=e['id'],fecha_vigencia=e['fecha_ingreso'],tipo_modificacion='Ingreso',
                campo_afectado='cargo',valor_nuevo=e['cargo'],motivo='Inicio de labores en la tienda',usuario_responsable='Gilda Pérez',created_at=e['fecha_ingreso'])
        self.cur.execute('SELECT empleado_id,fecha FROM asistencia_laboral')
        asistencias={(r[0],r[1]) for r in self.cur.fetchall()}
        permisos={}
        for e in self.empleados:
            for primero,fin,_ in meses(max(self.inicio,e['fecha_ingreso']),min(self.fin,e['fecha_baja'] or self.fin)):
                if self.rng.random()<.22:
                    dia=primero+timedelta(days=self.rng.randint(5,20))
                    if dia>fin or dia<e['fecha_ingreso'] or not jornada_comercial(dia):continue
                    self.insertar('movimientos_laborales',empleado_id=e['id'],tipo='PERMISO_CON_GOCE',fecha_inicio=dia,
                        fecha_fin=dia,dias_tomados=1,observacion=self.rng.choice(['Consulta médica programada','Diligencia familiar autorizada']),
                        estado='Aprobado',aprobado_por='Gilda Pérez',created_at=dia)
                    permisos[e['id'],dia]='Permiso'
            for anio in (2024,2025,2026):
                vac=date(anio,7,6)+timedelta(days=e['id']%12)
                if vac>self.fin or (vac-e['fecha_ingreso']).days<180 or (e['fecha_baja'] and vac>e['fecha_baja']):continue
                fin=vac+timedelta(days=5)
                if fin>self.fin:continue
                self.insertar('movimientos_laborales',empleado_id=e['id'],tipo='VACACIONES',fecha_inicio=vac,fecha_fin=fin,
                    dias_tomados=6,observacion='Descanso anual coordinado con el responsable de tienda',estado='Aprobado',
                    aprobado_por='Gilda Pérez',created_at=vac-timedelta(days=14))
                self.insertar('vacaciones',empleado_id=e['id'],fechaInicio=vac,fechaFin=fin,dias=6,estado='Aprobada')
                for dia in dias(vac,fin):permisos[e['id'],dia]='Vacaciones'
            for dia in dias(max(self.inicio,e['fecha_ingreso']),min(self.fin,e['fecha_baja'] or self.fin)):
                if not jornada_comercial(dia) or (e['id'],dia) in asistencias:continue
                estado=permisos.get((e['id'],dia),'Presente')
                demora=self.rng.randint(3,19) if estado=='Presente' and self.rng.random()<.045 else 0
                self.insertar('asistencia_laboral',empleado_id=e['id'],fecha=dia,
                    hora_entrada=time(8,demora) if estado=='Presente' else None,
                    hora_salida=time(12 if dia.weekday()==5 or dia==self.fin else 17) if estado=='Presente' else None,
                    estado='Tardanza' if demora else estado,minutos_tardanza=demora,
                    observaciones='Registro de jornada' if estado=='Presente' else 'Ausencia autorizada',created_at=dia)
        for i in range(18):
            dia=date(2025+i//10,1+i%10,5+i%16)
            nombre=f'{NOMBRES[i]} {APELLIDOS[(i+5)%len(APELLIDOS)]} {APELLIDOS[(i+9)%len(APELLIDOS)]}'
            self.insertar('solicitudes_empleo',codigo_solicitud=f'SOL-{dia.year}-R{i+1:03d}',nombres_apellidos=nombre,
                telefono=f'+505 {self.rng.randint(8200,8899)}-{self.rng.randint(1000,9999)}',direccion=BARRIOS[i%len(BARRIOS)],
                puesto_solicitado=self.rng.choice(['Vendedor de mostrador','Auxiliar de bodega','Mecánico de motocicletas']),
                formacion_academica=self.rng.choice(['Bachiller en ciencias y letras','Técnico en mecánica de motocicletas','Técnico en administración']),
                experiencia_laboral=f'{1+i%5} años en atención de mostrador y repuestos',disponibilidad='Inmediata',
                salario_pretendido=self.rng.randrange(8500,13001,500),estado=self.rng.choice(['Recibida','En revisión','Entrevista','Descartada']),
                observaciones='Evaluación de experiencia y disponibilidad de horario',fecha_registro=dia)
        for primero,fin,completo in meses(self.inicio,self.fin):
            if not completo:continue
            for nombre,institucion in [('Pago de cotizaciones','INSS'),('Aporte para capacitación','INATEC'),('Revisión de retenciones mensuales','DGI')]:
                vence=fin+timedelta(days=5 if institucion=='DGI' else 10)
                self.insertar('calendario_obligaciones',nombre_obligacion=f'{nombre} {primero:%m/%Y}',institucion=institucion,
                    periodo='Mensual',fecha_vencimiento=vence,responsable='Contabilidad',estado='Pendiente' if vence>self.fin else 'Cumplida',
                    fecha_cumplimiento=fin if vence<=self.fin else None,observaciones='Seguimiento del calendario de obligaciones')
        self.seguridad()

    def seguridad(self):
        temas=[('Manipulación manual de cargas','Bodega','Moderado','Utilizar carretilla y distribuir el peso en estanterías bajas'),
            ('Derrame de lubricantes','Bodega','Moderado','Conservar envases cerrados y limpiar derrames de inmediato'),
            ('Caída de objetos','Almacén','Moderado','Asegurar estanterías y respetar capacidad de carga'),
            ('Fatiga por postura','Mostrador','Bajo','Alternar posición de pie y sentado; realizar pausas activas'),
            ('Contacto con herramientas','Taller','Moderado','Usar guantes y protección ocular al intervenir piezas')]
        for i,(tipo,area,nivel,medida) in enumerate(temas):
            rid=self.insertar('higiene_riesgos',area=area,tipo_riesgo=tipo,descripcion=f'Exposición a {tipo.lower()} durante la operación de tienda',
                nivel_riesgo=nivel,medidas_preventivas=medida,responsable_seguimiento='Roberto Silva',estado='En seguimiento',
                fecha_registro=self.inicio,fecha_revision=date(2026,10,20))
            for anio in (2024,2025,2026):
                self.insertar('higiene_riesgo_seguimientos',riesgo_id=rid,fecha_revision=date(anio,10,10+i),
                    observaciones='Se revisaron las medidas preventivas y se reforzó el orden del área.',estado='En seguimiento',registrado_por='Roberto Silva')
        for e in self.empleados:
            for anio in range(max(self.inicio.year,e['fecha_ingreso'].year),self.fin.year+1):
                entrega=max(e['fecha_ingreso'],date(anio,2,8))
                if entrega>self.fin or (e['fecha_baja'] and entrega>e['fecha_baja']):continue
                for equipo in (['Guantes de protección mecánica','Gafas de seguridad'] if 'Mecánico' in e['cargo'] else ['Calzado de seguridad']):
                    self.insertar('higiene_epp',empleado_id=e['id'],tipo_equipo=equipo,fecha_entrega=entrega,cantidad=1,
                        estado_equipo='Bueno',fecha_reposicion_sugerida=entrega+timedelta(days=365),entregado_por='Roberto Silva',
                        area='Taller' if 'Mecánico' in e['cargo'] else 'Tienda',observaciones='Entrega y revisión del equipo asignado')
        for primero,fin,completo in meses(self.inicio,self.fin):
            if not completo:continue
            puntos=self.rng.choices([5,6],[25,75])[0]
            self.insertar('higiene_inspecciones',fecha_inspeccion=datetime.combine(fin,time(10)),inspector='Roberto Silva',
                pasillos_despejados=True,estanterias_seguras=True,repuestos_ordenados=puntos==6,extintores_adecuados=True,
                salidas_emergencia_libres=True,area_caja_segura=True,puntos_aprobados=puntos,total_puntos=6,
                porcentaje_cumplimiento=dinero(puntos/6*100),observaciones='Revisión del orden, almacenamiento y equipo de emergencia',
                acciones_correctivas='Reubicar cajas en el pasillo de repuestos' if puntos<6 else 'Mantener las condiciones verificadas',
                estado='Pendiente' if puntos<6 else 'Completada')
            if primero.month in (3,6,9,12):
                self.insertar('higiene_capacitaciones',nombre_capacitacion=self.rng.choice(['Orden y limpieza de bodega','Uso de extintores','Atención segura en mostrador','Manipulación de baterías y lubricantes']),
                    fecha=fin,duracion_horas=self.rng.choice([1,1.5,2]),facilitador='Roberto Silva',
                    temas_tratados='Identificación de riesgos y aplicación de medidas preventivas',
                    asistentes_conteo=sum(e['fecha_ingreso']<=fin and (not e['fecha_baja'] or e['fecha_baja']>=fin) for e in self.empleados),
                    observaciones='Sesión interna con el equipo de trabajo',created_at=fin)
        for i,dia in enumerate([date(2024,5,16),date(2024,10,8),date(2025,4,22),date(2025,11,5),date(2026,6,11)]):
            disponibles=[e for e in self.empleados if e['fecha_ingreso']<=dia and (not e['fecha_baja'] or e['fecha_baja']>=dia)]
            self.insertar('higiene_incidentes',codigo_incidente=f'INC-{dia:%Y%m%d}',fecha=datetime.combine(dia,time(10,15)),
                area='Bodega',empleado_id=self.rng.choice(disponibles)['id'],tipo_suceso='Incidente sin lesión',
                descripcion=self.rng.choice(['Caída de caja vacía al reorganizar estantería','Derrame menor de aceite contenido durante recepción','Tropiezo con material de empaque sin caída']),
                posibles_causas='Material fuera de su ubicación asignada',medidas_correctivas='Ordenar el área y revisar la rutina de recepción',
                dias_incapacidad=0,estado_seguimiento='Cerrado',registrado_por='Roberto Silva')

    def finalizar(self):
        print('Normalizando textos y comprobando contrapartidas anteriores...',flush=True)
        self.normalizar_textos()
        self.corregir_contrapartidas()
        self.asegurar_liquidez()
        print('Preparando cortes de flujo de efectivo y borradores fiscales...',flush=True)
        self.finanzas()
        self.declaraciones()
        self.normalizar_textos()
        print('Registrando trazabilidad y verificando integridad de todas las áreas...',flush=True)
        self.cur.executemany('INSERT INTO carga_negocio_registros(carga_id,tabla,registro_id) VALUES(?,?,?)',self.registros)
        if self.cambios:self.cur.executemany('INSERT INTO carga_negocio_cambios(carga_id,tabla,registro_id,campo,antes,despues) VALUES(?,?,?,?,?,?)',self.cambios)
        comprobaciones=self.verificar()
        return dict(insertados=dict(self.conteos),normalizaciones=len(self.cambios),inicio=str(self.inicio),fin=str(self.fin),
                    comprobaciones=comprobaciones,contrapartidas=self.contrapartidas,financiacion=self.financiacion)

    def asegurar_liquidez(self, aporte_confirmado=None):
        self.cur.execute('''SELECT a.fecha,SUM(m.debe-m.haber) FROM asientos_contables a
            JOIN movimientos_contables m ON m.asiento_id=a.id WHERE m.cuenta_id=? AND a.fecha<=?
            GROUP BY a.fecha ORDER BY a.fecha''',self.cuentas['1.1.02'],self.fin)
        saldo=Decimal(0);minimo=None
        for _,valor in self.cur.fetchall():saldo+=valor;minimo=saldo if minimo is None else min(minimo,saldo)
        minimo=minimo if minimo is not None else Decimal(0)
        aporte=max(Decimal(0),((Decimal(20000)-minimo)/50000).to_integral_value(rounding='ROUND_CEILING')*50000)
        if aporte_confirmado is not None and aporte!=aporte_confirmado:
            raise ValueError('La necesidad de capital cambió; no se aplicará un importe diferente del autorizado.')
        if aporte:
            self.asiento(self.inicio,'Aporte adicional del propietario para capital de trabajo',
                [('1.1.02',aporte,0),('3.1.01',0,aporte)],'CAPITAL')
        self.financiacion=dict(aporte_adicional=str(aporte),minimo_bancario_posterior=str(minimo+aporte),
            criterio='Capital inicial necesario para mantener reserva de operación sin sobregiros no contratados')

    def normalizar_textos(self):
        self.cur.execute('''SELECT t.name,c.name FROM sys.tables t JOIN sys.columns c ON c.object_id=t.object_id
            JOIN sys.types ty ON ty.user_type_id=c.user_type_id WHERE ty.name IN ('varchar','nvarchar')
            AND EXISTS(SELECT 1 FROM sys.columns x WHERE x.object_id=t.object_id AND x.name='id')''')
        campos=list(self.cur.fetchall())
        for tabla,campo in campos:
            if tabla in ('usuarios','sesiones','cargas_negocio','carga_negocio_registros','carga_negocio_cambios','flujo_eventos'):
                continue
            if any(k in campo.lower() for k in ('password','archivo','adjunto','url','comprobante','curriculum')):continue
            self.cur.execute(f'''SELECT id,[{campo}] FROM [{tabla}] WHERE [{campo}] LIKE '%DEMO%'
                OR [{campo}] LIKE '%demostraci%' OR [{campo}] LIKE '%fictici%' OR [{campo}] LIKE '%simulaci%' ''')
            for rid,antes in list(self.cur.fetchall()):
                nuevo=antes
                if nuevo=='Datos de demostración':nuevo='Barrio San José, Masatepe'
                elif nuevo in ('Demo académica','Demo académica RRHH','Demo académica de RRHH'):nuevo='Administración'
                else:
                    nuevo=re.sub(r'\[DEMO[^\]]*\]\s*','',nuevo,flags=re.I)
                    nuevo=nuevo.replace('DEMO_FISCAL','CONTABILIDAD')
                    nuevo=re.sub(r'\bDEMO\b','REG',nuevo,flags=re.I)
                    nuevo=re.sub(r'\s*[-—]?\s*muestra sin validez oficial\.?','',nuevo,flags=re.I)
                    nuevo=re.sub(r'\bdemostración\b','control interno',nuevo,flags=re.I)
                    nuevo=re.sub(r'\bsimulación\b','cálculo',nuevo,flags=re.I)
                    nuevo=re.sub(r'\bfictici[oa]s?\b\s*','',nuevo,flags=re.I)
                    nuevo=nuevo.replace('Auxiliar de control interno','Auxiliar de ventas').strip()
                if nuevo!=antes:self.cambiar(tabla,rid,campo,antes,nuevo)

    def corregir_contrapartidas(self):
        self.contrapartidas=[]
        self.cur.execute('''SELECT a.id,a.modulo_origen,a.referencia_id,SUM(m.debe-m.haber)
            FROM asientos_contables a JOIN movimientos_contables m ON m.asiento_id=a.id
            GROUP BY a.id,a.modulo_origen,a.referencia_id HAVING ABS(SUM(m.debe-m.haber))>.01''')
        for aid,modulo,ref,diferencia in list(self.cur.fetchall()):
            self.cur.execute('''SELECT c.codigo,m.debe,m.haber FROM movimientos_contables m
                JOIN cuentas_contables c ON c.id=m.cuenta_id WHERE asiento_id=? ORDER BY m.id''',aid)
            lineas=[tuple(r) for r in self.cur.fetchall()]
            # El respaldo existente prueba salario bruto y neto, no su reparto tributario.
            if modulo not in ('RRHH','RRHH_ANULACION') or len(lineas)!=2 or {r[0] for r in lineas}!={'6.1.01','2.1.04'}:
                self.contrapartidas.append(dict(asiento=aid,corregido=False,diferencia=str(diferencia)));continue
            codigo='2.1.09'
            if codigo not in self.cuentas:
                self.cuentas[codigo]=self.insertar('cuentas_contables',codigo=codigo,nombre='Deducciones de nómina por conciliar',
                    clasificacion='Pasivo corriente',naturaleza='Acreedora',descripcion='Retenciones pendientes de distribución según el soporte de nómina',activo=True)
            self.insertar('movimientos_contables',asiento_id=aid,cuenta_id=self.cuentas[codigo],
                debe=-diferencia if diferencia<0 else 0,haber=diferencia if diferencia>0 else 0)
            self.contrapartidas.append(dict(asiento=aid,corregido=True,importe=str(diferencia),cuenta=codigo,
                respaldo='Diferencia entre bruto y neto de las dos partidas existentes; distribución de deducciones pendiente'))

    def migrar_finanzas(self):
        # Reutilizar solamente los SQL literales de las migraciones existentes en esta transacción.
        for archivo,funcion in [('migrar_modulo_flujo_efectivo.py','ejecutar'),('migrar_flujo_v2.py','execute')]:
            arbol=ast.parse((ROOT/archivo).read_text(encoding='utf-8-sig'))
            llamadas=[]
            for nodo in ast.walk(arbol):
                if not isinstance(nodo,ast.Call):continue
                if funcion=='ejecutar' and isinstance(nodo.func,ast.Name) and nodo.func.id==funcion and len(nodo.args)>=3:
                    sql=nodo.args[2]
                elif funcion=='execute' and isinstance(nodo.func,ast.Attribute) and nodo.func.attr==funcion and nodo.args:
                    sql=nodo.args[0]
                else:continue
                if isinstance(sql,ast.Constant) and isinstance(sql.value,str):llamadas.append((nodo.lineno,sql.value))
            for _,sql in sorted(llamadas):self.cur.execute(sql)

    def finanzas(self):
        self.migrar_finanzas()
        self.cur.execute("UPDATE cuentas_contables SET flujo_categoria='Operacion',es_efectivo_equivalente=0 WHERE codigo='2.1.09'")
        from routes_flujo_efectivo import generar
        from flujo_service import serializable
        for anio in range(self.inicio.year,self.fin.year+1):
            fin=min(date(anio,12,31),self.fin)
            reporte=generar(self.cur,dict(start=f'{anio}-01-01',end=fin.isoformat(),metodo='Directo'))
            if not reporte['puede_guardar']:
                raise ValueError('Flujo no verificable: '+json.dumps(serializable(reporte.get('pendientes_clasificacion')),ensure_ascii=False))
            rid=self.insertar('estados_flujo_efectivo',ejercicio_fiscal=anio,periodo_tipo='Anual',fecha_inicio=date(anio,1,1),fecha_fin=fin,
                metodo='Directo',saldo_inicial_efectivo=dinero(reporte['saldo_inicial']),flujo_neto_operacion=dinero(reporte['flujo_neto_operacion']),
                flujo_neto_inversion=dinero(reporte['flujo_neto_inversion']),flujo_neto_financiamiento=dinero(reporte['flujo_neto_financiamiento']),
                variacion_neta_efectivo=dinero(reporte['variacion_neta_efectivo']),saldo_final_calculado=dinero(reporte['saldo_final_calculado']),
                saldo_final_balance_general=dinero(reporte['saldo_final_balance']),diferencia_cuadratura=0,esta_cuadrado=True,
                estado='Borrador',observaciones='Corte anual preparado para revisión contable',usuario_elaboro_id=self.uid)
            for actividad,clave in [('Operacion','actividades_operacion'),('Inversion','actividades_inversion'),('Financiamiento','actividades_financiamiento')]:
                for orden,linea in enumerate(reporte[clave],1):
                    self.insertar('estado_flujo_efectivo_detalle',flujo_id=rid,actividad=actividad,concepto=linea['concepto'][:255],
                        tipo_movimiento=linea['tipo'],importe=dinero(linea['importe']),orden_presentacion=orden)
            self.insertar('flujo_eventos',tipo='corte',clave=str(rid),contenido=json.dumps(serializable(reporte),ensure_ascii=False),
                motivo='Corte anual recalculado y verificado contra el mayor',usuario_id=self.uid)
        # Conciliaciones como borradores internos: no se inventa un extracto emitido por un banco.
        for mes in (7,8,9,10):
            fin=date(2026,mes,calendar.monthrange(2026,mes)[1])
            self.cur.execute('''SELECT COALESCE(SUM(m.debe-m.haber),0) FROM movimientos_contables m
                JOIN asientos_contables a ON a.id=m.asiento_id WHERE m.cuenta_id=? AND a.fecha<=?''',self.cuentas['1.1.02'],fin)
            saldo=self.cur.fetchone()[0]
            self.insertar('conciliaciones_bancarias',cuenta_id=self.cuentas['1.1.02'],anio=2026,mes=mes,fecha_corte=fin,
                saldo_segun_libros=saldo,saldo_segun_banco=0,diferencia=saldo,estado='Borrador',
                observaciones='Saldo de libros disponible; pendiente de adjuntar y cotejar extracto bancario',usuario_id=self.uid)

    def declaraciones(self):
        for anio in range(self.inicio.year,self.fin.year+1):
            sim=fiscal.preparar_declaracion_desde_contabilidad(self.cur,{'anio':anio})
            if not sim['balance']['balance_cuadrado']:raise ValueError(f'Balance descuadrado del ejercicio {anio}')
            rid=fiscal.guardar_declaracion_completa(self.cur,sim,self.uid,es_aprobada=False)
            self.registros.append((self.cid,'declaraciones_ir',rid));self.conteos['declaraciones_ir']+=1
            self.cur.execute('SELECT id FROM declaracion_renglones_detalle WHERE declaracion_id=?',rid)
            for row in self.cur.fetchall():self.registros.append((self.cid,'declaracion_renglones_detalle',row[0]));self.conteos['declaracion_renglones_detalle']+=1
            self.cur.execute('SELECT id FROM declaracion_validaciones WHERE declaracion_id=?',rid)
            for row in self.cur.fetchall():self.registros.append((self.cid,'declaracion_validaciones',row[0]));self.conteos['declaracion_validaciones']+=1

    def verificar(self):
        def sin_filas(nombre,sql):
            self.cur.execute(sql,self.cid)
            resultado=self.cur.fetchone()
            if resultado:raise ValueError(nombre+': '+str(tuple(resultado)))
        sin_filas('Venta sin cuadre de detalle','''SELECT v.id FROM ventas v JOIN carga_negocio_registros r ON r.tabla='ventas' AND r.registro_id=v.id
            LEFT JOIN detalle_ventas d ON d.venta_id=v.id WHERE r.carga_id=? GROUP BY v.id,v.total,v.descuento HAVING ABS(v.total+v.descuento-SUM(d.subtotal))>.01''')
        sin_filas('Compra sin cuadre de detalle','''SELECT c.id FROM compras c JOIN carga_negocio_registros r ON r.tabla='compras' AND r.registro_id=c.id
            LEFT JOIN detalle_compras d ON d.compra_id=c.id WHERE r.carga_id=? GROUP BY c.id,c.total HAVING ABS(c.total-SUM(d.subtotal))>.01''')
        sin_filas('Venta sin respaldo de cobro','''SELECT v.id FROM ventas v JOIN carga_negocio_registros r ON r.tabla='ventas' AND r.registro_id=v.id
            LEFT JOIN (SELECT venta_id,SUM(monto) monto FROM pagos GROUP BY venta_id) p ON p.venta_id=v.id
            WHERE r.carga_id=? AND ((v.forma_pago<>'Crédito' AND ABS(v.total-COALESCE(p.monto,0))>.01) OR COALESCE(p.monto,0)>v.total)''')
        sin_filas('Pedido completado sin respaldo','''SELECT w.id FROM pedidos_web w JOIN carga_negocio_registros r ON r.tabla='pedidos_web' AND r.registro_id=w.id
            LEFT JOIN (SELECT pedido_id,SUM(subtotal) total FROM detalle_pedidos_web GROUP BY pedido_id) d ON d.pedido_id=w.id
            LEFT JOIN (SELECT pedido_web_id,SUM(monto) total FROM pagos GROUP BY pedido_web_id) p ON p.pedido_web_id=w.id
            WHERE r.carga_id=? AND (ABS(w.total-COALESCE(d.total,0))>.01 OR (w.estado='Completado' AND ABS(w.total-COALESCE(p.total,0))>.01))''')
        sin_filas('Inventario con salto de existencias','''SELECT id FROM (SELECT m.id,m.stock_anterior,m.stock_posterior,m.cantidad,m.tipo_movimiento,
            COALESCE(LAG(m.stock_posterior) OVER(PARTITION BY m.producto_id ORDER BY m.fecha,m.id),0) previo
            FROM movimientos_inventario m JOIN carga_negocio_registros r ON r.tabla='movimientos_inventario' AND r.registro_id=m.id WHERE r.carga_id=?) x
            WHERE stock_anterior<>previo OR stock_posterior<0 OR stock_posterior<>stock_anterior+CASE WHEN tipo_movimiento IN ('ENTRADA_COMPRA','DEVOLUCION_CLIENTE','AJUSTE_ENTRADA') THEN cantidad ELSE -cantidad END''')
        sin_filas('Stock final no coincide','''SELECT p.id FROM productos p JOIN carga_negocio_registros r ON r.tabla='productos' AND r.registro_id=p.id
            OUTER APPLY (SELECT TOP 1 stock_posterior FROM movimientos_inventario WHERE producto_id=p.id ORDER BY fecha DESC,id DESC) k
            WHERE r.carga_id=? AND p.stock_actual<>k.stock_posterior''')
        sin_filas('Asiento nuevo no balanceado','''SELECT a.id FROM asientos_contables a JOIN carga_negocio_registros r ON r.tabla='asientos_contables' AND r.registro_id=a.id
            JOIN movimientos_contables m ON m.asiento_id=a.id WHERE r.carga_id=? GROUP BY a.id HAVING ABS(SUM(m.debe-m.haber))>.01''')
        sin_filas('Pago de nómina nuevo no coincide','''SELECT d.id FROM detalle_nomina d JOIN carga_negocio_registros r ON r.tabla='detalle_nomina' AND r.registro_id=d.id
            LEFT JOIN (SELECT nomina_id,empleado_id,SUM(monto_pagado) monto FROM pagos_nomina WHERE estado='Confirmado' GROUP BY nomina_id,empleado_id) p
            ON p.nomina_id=d.nomina_id AND p.empleado_id=d.empleado_id WHERE r.carga_id=? AND ABS(d.neto_pagar-COALESCE(p.monto,0))>.01''')
        sin_filas('Arqueo de caja no coincide','''SELECT s.id FROM sesiones_caja s JOIN carga_negocio_registros r ON r.tabla='sesiones_caja' AND r.registro_id=s.id
            LEFT JOIN (SELECT sesion_caja_id,SUM(total) total FROM ventas WHERE forma_pago='Efectivo' AND estado='Completada' GROUP BY sesion_caja_id) v ON v.sesion_caja_id=s.id
            WHERE r.carga_id=? AND ABS(s.monto_final_real-s.monto_inicial-COALESCE(v.total,0))>.01''')
        sin_filas('Ingreso contado dos veces','''SELECT p.id FROM pagos p JOIN carga_negocio_registros r ON r.tabla='pagos' AND r.registro_id=p.id
            WHERE r.carga_id=? AND p.venta_id IS NOT NULL AND p.pedido_web_id IS NOT NULL''')
        self.cur.execute('''SELECT CONVERT(char(7),v.fecha_venta,126),COUNT(*),SUM(v.total),COUNT(DISTINCT v.total)
            FROM ventas v JOIN carga_negocio_registros r ON r.tabla='ventas' AND r.registro_id=v.id AND r.carga_id=?
            GROUP BY CONVERT(char(7),v.fecha_venta,126) ORDER BY 1''',self.cid)
        mensual=[dict(periodo=r[0],ventas=r[1],importe=str(r[2]),importes_distintos=r[3]) for r in self.cur.fetchall()]
        if len({m['importe'] for m in mensual})<len(mensual)//2:raise ValueError('Serie mensual insuficientemente variada')
        self.cur.execute('''SELECT SUM(p.stock_actual*p.costo) FROM productos p JOIN carga_negocio_registros r
            ON r.tabla='productos' AND r.registro_id=p.id WHERE r.carga_id=?''',self.cid)
        valor_stock=self.cur.fetchone()[0]
        if valor_stock!=self.saldos['1.1.04']:raise ValueError('Inventario físico no coincide con el mayor de la carga')
        self.cur.execute('DBCC CHECKCONSTRAINTS WITH ALL_CONSTRAINTS')
        if self.cur.description and self.cur.fetchone():raise ValueError('Hay restricciones de integridad incumplidas')
        return dict(ventas_detalles=True,compras_detalles=True,cobros=True,web_sin_duplicados=True,kardex=True,
            inventario_valorado=str(valor_stock),nomina_y_pagos=True,asientos=True,cajas=True,integridad=True,variacion_mensual=mensual)


def main():
    from app import get_db_connection
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--apply',action='store_true')
    p.add_argument('--inicio',default='2024-01-01');p.add_argument('--fin',default=fiscal.fecha_hoy_nicaragua())
    args=p.parse_args();inicio=date.fromisoformat(args.inicio);fin=date.fromisoformat(args.fin)
    if fin>date.fromisoformat(fiscal.fecha_hoy_nicaragua()) or inicio>fin:raise ValueError('Período inválido o futuro.')
    if args.apply:
        archivo=ROOT/'output'/'carga_negocio'/'respaldo.json'
        if not archivo.exists() or not json.loads(archivo.read_text(encoding='utf-8')).get('verificado'):
            raise ValueError('Se requiere un respaldo completo verificado antes de aplicar la carga.')
    conn=get_db_connection();conn.autocommit=False
    try:
        carga=Carga(conn,inicio,fin)
        if carga.existente:
            print(json.dumps(dict(ya_aplicada=True,resumen=json.loads(carga.existente[1])),ensure_ascii=False,indent=2));conn.rollback();return
        carga.catalogos();carga.personal();carga.operaciones()
        resumen=carga.finalizar()
        carga.cur.execute('UPDATE cargas_negocio SET resumen=? WHERE id=?',json.dumps(resumen,ensure_ascii=False),carga.cid)
        if args.apply:conn.commit()
        else:conn.rollback()
        resumen['aplicado']=args.apply
        folder=ROOT/'output'/'carga_negocio';folder.mkdir(exist_ok=True,parents=True)
        (folder/('resultado.json' if args.apply else 'verificacion.json')).write_text(json.dumps(resumen,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
        print(json.dumps(resumen,ensure_ascii=False,indent=2,default=str))
    except Exception:
        conn.rollback();raise
    finally:conn.close()


if __name__=='__main__':main()
