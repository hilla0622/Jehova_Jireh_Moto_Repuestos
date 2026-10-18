"""Carga académica pequeña y repetible. Sin --apply, valida y revierte la transacción.

No altera salarios, saldos de vacaciones, parámetros, nóminas ni pagos existentes.
Requiere la migración de control RRHH y reportlab para los adjuntos de muestra.
"""
import argparse
import json
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

from app import get_db_connection

MARK = '[DEMO-RRHH-2026]'
AUTHOR = 'Demo académica'
RRHH_APPROVER = 'Lic. María Elena Calero'
ROOT = Path(__file__).resolve().parent
TABLES = ('empleados', 'solicitudes_empleo', 'contratos_laborales',
          'expediente_empleado', 'historial_laboral', 'jornadas_laborales',
          'asistencia_laboral', 'horas_extras', 'movimientos_laborales',
          'nomina', 'detalle_nomina', 'liquidaciones_laborales', 'pagos_nomina',
          'higiene_riesgos', 'higiene_riesgo_seguimientos', 'higiene_incidentes',
          'higiene_epp', 'higiene_capacitaciones', 'higiene_inspecciones',
          'parametros_laborales', 'calendario_obligaciones', 'rrhh_archivos')


def profile(employee):
    folder = ROOT / 'output' / 'pdf'
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f'ficha_demo_rrhh_{employee["id"]}.pdf'
    styles = getSampleStyleSheet()
    styles['Title'].textColor = colors.HexColor('#17445c')
    parts = [Paragraph('Jehová Jireh Moto Repuestos', styles['Title']),
             Paragraph('Ficha de inducción - expediente académico', styles['Heading2']),
             Paragraph('MUESTRA ACADÉMICA. Datos de demostración, sin validez oficial.', styles['Normal']),
             Spacer(1, 22)]
    fields = [('Trabajador', employee['nombre_completo']), ('Cargo', employee['cargo']),
              ('Fecha de la actividad', '17/10/2026'), ('Lugar', 'Tienda principal, Masatepe'),
              ('Responsable de la demostración', 'Administración'),
              ('Contenido', 'Atención al cliente, ubicación de repuestos, orden de estanterías, '
               'uso de equipo de protección y comunicación de incidentes.'),
              ('Duración', '1 hora, de 14:00 a 15:00'),
              ('Observaciones', 'Ejemplo para presentar el expediente digital. No certifica '
               'una capacitación real ni contiene firmas o sellos oficiales.')]
    for label, value in fields:
        parts += [Paragraph(f'<b>{label}:</b> {escape(str(value))}', styles['BodyText']), Spacer(1, 12)]
    SimpleDocTemplate(str(path), title='Ficha académica de RRHH',
                      author='Demostración académica', rightMargin=54, leftMargin=54).build(parts)
    return path


def main(apply=False):
    conn = get_db_connection()
    conn.autocommit = False
    cur = conn.cursor()
    counts = Counter()
    manifest = {'marca': MARK, 'inserciones': [], 'campos_completados': []}

    def rows(sql, params=()):
        cur.execute(sql, params)
        names = [x[0] for x in cur.description]
        return [dict(zip(names, r)) for r in cur.fetchall()]

    def insert(table, values, where, params):
        cur.execute(f'SELECT id FROM {table} WITH (UPDLOCK, HOLDLOCK) WHERE {where}', params)
        found = cur.fetchone()
        if found:
            return int(found[0])
        columns = ','.join(f'[{key}]' for key in values)
        placeholders = ','.join('?' for _ in values)
        cur.execute(f'INSERT INTO {table} ({columns}) OUTPUT INSERTED.id VALUES ({placeholders})', tuple(values.values()))
        identity = int(cur.fetchone()[0])
        counts[table] += 1
        manifest['inserciones'].append({'tabla': table, 'id': identity})
        return identity

    try:
        employees = rows('SELECT * FROM empleados WHERE activo=1 ORDER BY id')
        if len(employees) != 5:
            raise ValueError('Esta carga está preparada para los cinco empleados revisados; revise el escenario antes de aplicarla.')
        before = {table: rows(f'SELECT COUNT(*) AS n FROM {table}')[0]['n'] for table in TABLES}
        shifts = {r['id']: r for r in rows('SELECT * FROM jornadas_laborales')}
        for index, employee in enumerate(employees):
            eid = employee['id']
            shift_id = 2 if employee['cargo'] == 'Bodeguero' else 3 if employee['cargo'] == 'Contador' else 1
            shift = shifts[shift_id]
            defaults = dict(direccion=f'Masatepe, zona urbana. Dirección de muestra {index + 1}.',
                            fecha_nacimiento=f'{1990 + index}-04-15',
                            contacto_emergencia=f'Familiar de muestra {index + 1}',
                            telefono_emergencia=f'0000-010{index}',
                            jornada_id=shift_id, jornada_asignada=shift['nombre'])
            missing = {k: v for k, v in defaults.items() if employee[k] is None or employee[k] == ''}
            if missing:
                manifest['campos_completados'].append({'empleado_id': eid, 'anteriores': {k: employee[k] for k in missing}})
                clause = ','.join(f'[{k}]=?' for k in missing)
                note = (employee['observaciones'] or '') + ' ' + MARK + ' Dirección, nacimiento y contacto complementarios ficticios.'
                cur.execute(f'UPDATE empleados SET {clause}, observaciones=? WHERE id=?', (*missing.values(), note.strip(), eid))
                counts['fichas_completadas'] += 1
                if 'jornada_id' in missing:
                    insert('historial_laboral', dict(empleado_id=eid, fecha_vigencia='2026-10-15',
                           tipo_modificacion='Asignación de jornada', campo_afectado='jornada_id',
                           valor_anterior='Sin asignar', valor_nuevo=str(shift_id),
                           motivo=MARK + ' Asignación inicial para demostración.', usuario_responsable=AUTHOR),
                           'empleado_id=? AND motivo=?', (eid, MARK + ' Asignación inicial para demostración.'))
            insert('contratos_laborales', dict(numero_contrato=f'DEMO-CTR-2026-{eid:03}',
                   empleado_id=eid, tipo_contratacion='Tiempo Indeterminado', cargo=employee['cargo'],
                   jornada_laboral=shift['nombre'], salario_mensual=employee['salario_base'],
                   fecha_inicio=employee['fecha_ingreso'], lugar_trabajo='Masatepe - Tienda principal',
                   forma_pago='Mensual', estado='Vigente', observaciones=MARK + ' Contrato académico; no documento firmado.'),
                   'empleado_id=?', (eid,))
            path = profile(employee)
            exp_id = insert('expediente_empleado', dict(empleado_id=eid, tipo_documento='Constancia de inducción',
                            nombre_archivo=path.name, usuario_responsable=AUTHOR,
                            observaciones=MARK + ' Ficha descargable de muestra; sin validez oficial.'),
                            'empleado_id=? AND nombre_archivo=?', (eid, path.name))
            insert('rrhh_archivos', dict(clase='EXPEDIENTE', referencia_id=exp_id,
                   nombre_archivo=path.name, mime='application/pdf', contenido=path.read_bytes(), registrado_por=AUTHOR),
                   'clase=? AND referencia_id=?', ('EXPEDIENTE', exp_id))
            for day in (15, 16, 17):
                date = f'2026-10-{day}'
                # No registrar presencia durante una ausencia ya registrada.
                if rows('SELECT id FROM movimientos_laborales WHERE empleado_id=? AND ? BETWEEN fecha_inicio AND fecha_fin', (eid, date)):
                    continue
                entry, departure = shift['hora_entrada'], shift['hora_salida']
                overtime = (eid == employees[1]['id'] and day == 15) or (eid == employees[0]['id'] and day == 16)
                if overtime:
                    h, m = map(int, departure[:5].split(':'))
                    departure = f'{h + 1:02}:{m:02}'
                insert('asistencia_laboral', dict(empleado_id=eid, fecha=date, hora_entrada=entry,
                       hora_salida=departure, estado='Completa', minutos_tardanza=0,
                       observaciones=MARK + (' Incluye una hora extra de recepción de mercadería.' if overtime else ' Jornada ordinaria.')),
                       'empleado_id=? AND fecha=?', (eid, date))
                if overtime:
                    rate = rows("SELECT valor FROM parametros_laborales WHERE codigo='HORAS_EXTRAS_RECARGO'")
                    rate = Decimal(str(rate[0]['valor'])) if rate else Decimal(100)
                    hourly = (employee['salario_base'] / Decimal(240)).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
                    total = (hourly * (1 + rate / 100)).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
                    insert('horas_extras', dict(empleado_id=eid, fecha=date, cantidad_horas=1,
                           motivo=MARK + ' Recepción y orden de un pedido de repuestos.', valor_hora_ordinaria=hourly,
                           recargo_porcentaje=rate, monto_total=total, estado='Aprobada', autorizado_por=RRHH_APPROVER),
                           'empleado_id=? AND fecha=? AND motivo LIKE ?', (eid, date, MARK.replace('[', '[[]') + '%'))
        warehouse = next(e for e in employees if e['cargo'] == 'Bodeguero')
        insert('higiene_incidentes', dict(codigo_incidente='DEMO-INC-2026-001', fecha='2026-10-15T10:20:00',
               area='Bodega', empleado_id=warehouse['id'], tipo_suceso='Incidente',
               descripcion=MARK + ' Caja vacía en pasillo detectada antes de provocar una caída; sin lesiones.',
               posibles_causas='Embalajes pendientes de retirar después de recibir mercadería.',
               medidas_correctivas='Retirar cajas y reservar una zona de desembalaje.', dias_incapacidad=0,
               estado_seguimiento='Cerrado', registrado_por=AUTHOR), 'codigo_incidente=?', ('DEMO-INC-2026-001',))
        for equipment in ('Guantes de protección mecánica', 'Gafas de seguridad'):
            insert('higiene_epp', dict(empleado_id=warehouse['id'], tipo_equipo=equipment,
                   fecha_entrega='2026-10-15', cantidad=1, estado_equipo='Nuevo', fecha_reposicion_sugerida='2027-04-15',
                   entregado_por=AUTHOR, observaciones=MARK + ' Revisar desgaste antes de cada uso.', area='Bodega'),
                   'empleado_id=? AND tipo_equipo=? AND observaciones LIKE ?', (warehouse['id'], equipment, MARK.replace('[', '[[]') + '%'))
        insert('higiene_capacitaciones', dict(nombre_capacitacion='Inducción de orden y seguridad - demo',
               fecha='2026-10-17', duracion_horas=1, facilitador='Administración (demostración)',
               temas_tratados='Orden de estanterías, EPP, atención y reporte de incidentes.',
               asistentes_conteo=5, observaciones=MARK + ' De 14:00 a 15:00; actividad académica ficticia.'),
               'nombre_capacitacion=?', ('Inducción de orden y seguridad - demo',))
        insert('higiene_inspecciones', dict(fecha_inspeccion='2026-10-17T09:00:00', inspector=AUTHOR,
               pasillos_despejados=1, estanterias_seguras=1, repuestos_ordenados=1, extintores_adecuados=1,
               salidas_emergencia_libres=1, area_caja_segura=1, puntos_aprobados=6, total_puntos=6,
               porcentaje_cumplimiento=100, observaciones=MARK + ' Revisión de muestra posterior al orden del pasillo.',
               acciones_correctivas='Mantener zona de desembalaje y revisión al cierre.', estado='Aprobada'),
               'observaciones LIKE ?', (MARK.replace('[', '[[]') + '%',))
        risk = rows('SELECT TOP 1 * FROM higiene_riesgos ORDER BY id')[0]
        insert('higiene_riesgo_seguimientos', dict(riesgo_id=risk['id'], fecha_revision='2026-10-17',
               observaciones=MARK + ' Ejemplo de seguimiento: recordar uso de carrito y ayuda para cargas voluminosas.',
               estado=risk['estado'], registrado_por=AUTHOR), 'riesgo_id=? AND observaciones LIKE ?', (risk['id'], MARK.replace('[', '[[]') + '%'))
        after = {table: rows(f'SELECT COUNT(*) AS n FROM {table}')[0]['n'] for table in TABLES}
        for table in ('empleados', 'nomina', 'detalle_nomina', 'pagos_nomina', 'movimientos_laborales', 'parametros_laborales'):
            assert before[table] == after[table], f'Se alteró el volumen protegido: {table}'
        assert all(after.values()), 'Queda alguna sección sin datos.'
        if apply:
            conn.commit()
            # Conservar el manifiesto de la primera aplicación si se vuelve a ejecutar.
            if manifest['inserciones'] or manifest['campos_completados']:
                output = ROOT / 'output' / 'rrhh_demo_manifest.json'
                output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
        else:
            conn.rollback()
        print(json.dumps({'aplicado': apply, 'cambios': dict(counts), 'totales': after}, ensure_ascii=False, indent=2))
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Confirmar inserciones; por defecto se revierte.')
    main(parser.parse_args().apply)
