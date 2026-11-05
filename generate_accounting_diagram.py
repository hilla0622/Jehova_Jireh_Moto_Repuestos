import subprocess
from PIL import Image

def generate_adjusted_diagram():
    boundary_x = 180
    boundary_y = 30
    boundary_w = 1060
    boundary_h = 1660

    actor_contador_x = 45
    actor_contador_y = 820
    actor_contador_w = 55
    actor_contador_h = 105

    actor_gerente_x = 1310
    actor_gerente_y = 880
    actor_gerente_w = 55
    actor_gerente_h = 105

    # Primary Use Cases:
    # (id, name, y, h, w, x, is_cont, is_ger)
    primary = [
        # Seguridad
        ("cu_login", "Iniciar Sesión", 75, 44, 270, 230, True, False),

        # Catálogo y Saldos
        ("cu_cat", "Gestionar Catálogo de Cuentas\nContables", 135, 46, 280, 230, True, False),
        ("cu_saldos", "Registrar Saldos Iniciales\nContables", 195, 46, 280, 230, True, False),

        # Asientos y Libros
        ("cu_asientos", "Registrar Asientos Manuales y\nGastos Operativos", 255, 46, 280, 230, True, False),
        ("cu_asientos_auto", "Generar Asientos Automáticos por\nIntegración (Ventas, Compras, Nómina)", 315, 48, 295, 230, True, False),
        ("cu_correc_clasif", "Corregir Errores de Clasificación\nen Operaciones", 375, 46, 290, 230, True, False),
        ("cu_diario", "Consultar Libro Diario General", 435, 44, 280, 230, True, True),
        ("cu_mayor", "Consultar Libro Mayor", 495, 44, 280, 230, True, True),

        # Conciliación y Flujo de Efectivo
        ("cu_conciliacion", "Realizar Conciliación Bancaria y\nDepuración de Partidas", 555, 46, 290, 230, True, False),
        ("cu_etiquetas_flujo", "Configurar Etiquetas de Flujo\nen Cuentas Contables", 615, 46, 290, 230, True, False),
        ("cu_clasif_flujo", "Clasificar Transacciones Complejas\ny Ajustes de Efectivo", 675, 46, 290, 230, True, False),
        ("cu_ajustes_nomet", "Registrar Ajustes por Partidas\nque No Implican Efectivo", 735, 46, 290, 230, True, False),

        # Estados Financieros
        ("cu_comp", "Generar Balance de Comprobación", 795, 44, 280, 230, True, True),
        ("cu_er", "Elaborar Estado de Resultados\n(Pérdidas y Ganancias)", 855, 46, 280, 230, True, True),
        ("cu_bg", "Elaborar Balance General\n(Situación Financiera)", 935, 46, 280, 230, True, True),
        ("cu_flujo", "Elaborar Estado de Flujo de Efectivo", 1000, 44, 280, 230, True, True),

        # Gestión Tributaria / IR con identificadores RF58 - RF68
        ("cu_info_trib", "Registrar Información Tributaria\ndel Negocio (RF58)", 1070, 46, 295, 230, True, False),
        ("cu_reglas_trib", "Administrar Reglas Tributarias\n(RF59)", 1130, 46, 295, 230, True, False),
        ("cu_datos_fiscales", "Registrar Datos Fiscales y\nDocumentos de Respaldo (RF60)", 1190, 46, 295, 230, True, False),
        ("cu_anticipos_cred", "Registrar Anticipos, Retenciones\ny Créditos Fiscales (RF61)", 1250, 46, 295, 230, True, False),
        ("cu_ajustes_fisc", "Registrar Ajustes Fiscales de\nConciliación (RF65)", 1310, 46, 295, 230, True, False),
        ("cu_prep_ir", "Preparar Formulario de Declaración\nAnual del IR (RF62)", 1370, 48, 295, 230, True, False),
        ("cu_rev_ir", "Revisar y Aprobar Declaración\nAnual Preparada (RF66)", 1445, 46, 295, 230, True, False),
        ("cu_export_ir", "Exportar e Imprimir Declaración\nAnual del IR (PDF / Excel) (RF67)", 1515, 48, 300, 230, True, True),
        ("cu_hist_trib", "Consultar historial y registrar\npresentación y pagos (RF68)", 1580, 48, 305, 230, True, True),
    ]

    # Secondary Use Cases:
    # (id, name, y, h, w, x, targets, rtype)
    # Note: targets can be list or single id
    secondary = [
        ("cu_auth", "Autenticar Usuario", 75, 44, 210, 580, ["cu_login"], "include"),
        ("cu_cuadre", "Validar Cuadre Estricto\nDebe = Haber", 255, 46, 220, 580, ["cu_asientos"], "include"),
        ("cu_cuadre_efectivo", "Verificar y Cuadrar Saldo\nFinal de Efectivo", 1000, 44, 230, 580, ["cu_flujo"], "include"),
        ("cu_export_eeff", "Exportar e Imprimir Estados\nFinancieros (PDF / Excel)", 885, 52, 235, 600, ["cu_comp", "cu_er", "cu_bg", "cu_flujo"], "extend"),

        # Includes tributarios:
        ("cu_calc_ir", "Calcular Preliminarmente IR\ny Saldo Resultante (RF64)", 1350, 46, 240, 600, ["cu_prep_ir"], "include"),
        ("cu_valida_trib", "Realizar Validación Preventiva\nde la Declaración (RF63)", 1410, 46, 240, 600, ["cu_prep_ir", "cu_rev_ir"], "include"),
    ]

    all_cases = {}
    for item in primary:
        cid, name, y, h, w, x, is_c, is_g = item
        all_cases[cid] = {"name": name, "x": x, "y": y, "w": w, "h": h, "type": "primary", "is_c": is_c, "is_g": is_g}
    for item in secondary:
        cid, name, y, h, w, x, tgts, rtype = item
        all_cases[cid] = {"name": name, "x": x, "y": y, "w": w, "h": h, "type": rtype, "tgts": tgts}

    # -------------------------------------------------------------
    # 1. GENERATE DRAW.IO XML
    # -------------------------------------------------------------
    drawio = []
    drawio.append('<mxfile host="app.diagrams.net" modified="2026-10-15T20:10:00.000Z" agent="Antigravity" version="21.6.8" type="device">')
    drawio.append('  <diagram id="CU_Contabilidad_JJ" name="Casos de Uso - Módulo Contabilidad y Estados Financieros">')
    drawio.append('    <mxGraphModel dx="1800" dy="1800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1550" pageHeight="1760" math="0" shadow="0">')
    drawio.append('      <root>')
    drawio.append('        <mxCell id="0" />')
    drawio.append('        <mxCell id="1" parent="0" />')

    # Boundary
    drawio.append(f'        <mxCell id="sys_boundary" value="" style="shape=rect;html=1;whiteSpace=wrap;align=center;verticalAlign=bottom;strokeColor=#104E8B;strokeWidth=2.5;fillColor=#FFFFFF;dashed=0;" vertex="1" parent="1">')
    drawio.append(f'          <mxGeometry x="{boundary_x}" y="{boundary_y}" width="{boundary_w}" height="{boundary_h}" as="geometry" />')
    drawio.append('        </mxCell>')

    # Title
    drawio.append('        <mxCell id="title_header" value="Módulo: Elaboración de Estados Financieros, Contabilidad y Gestión Tributaria" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontFamily=Helvetica;fontSize=15;fontStyle=1;fontColor=#003366;" vertex="1" parent="1">')
    drawio.append(f'          <mxGeometry x="{boundary_x + 25}" y="{boundary_y + 12}" width="750" height="30" as="geometry" />')
    drawio.append('        </mxCell>')

    # Footer
    drawio.append('        <mxCell id="footer_text" value="Aplicación Web Administrativa para la Gestión de Ventas, Inventario y Procesos Operativos de Jehová Jireh Masatepe Moto Repuestos" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontFamily=Helvetica;fontSize=11.5;fontStyle=1;fontColor=#003366;" vertex="1" parent="1">')
    drawio.append(f'          <mxGeometry x="{boundary_x + 25}" y="{boundary_y + boundary_h - 28}" width="950" height="25" as="geometry" />')
    drawio.append('        </mxCell>')

    # Actor Contador
    drawio.append(f'        <mxCell id="actor_contador" value="CONTADOR&#xa;(EXTERNO)" style="shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;fontFamily=Helvetica;fontSize=11;fontStyle=1;fontColor=#000000;strokeColor=#0891B2;strokeWidth=2;fillColor=#06B6D4;" vertex="1" parent="1">')
    drawio.append(f'          <mxGeometry x="{actor_contador_x}" y="{actor_contador_y}" width="{actor_contador_w}" height="{actor_contador_h}" as="geometry" />')
    drawio.append('        </mxCell>')

    # Actor Gerente
    drawio.append(f'        <mxCell id="actor_gerente" value="GERENTE ADMINISTRATIVO&#xa;Y FINANCIERO" style="shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;fontFamily=Helvetica;fontSize=10.5;fontStyle=1;fontColor=#000000;strokeColor=#A0522D;strokeWidth=2;fillColor=#FF8C00;" vertex="1" parent="1">')
    drawio.append(f'          <mxGeometry x="{actor_gerente_x}" y="{actor_gerente_y}" width="{actor_gerente_w}" height="{actor_gerente_h}" as="geometry" />')
    drawio.append('        </mxCell>')

    # Primary use cases
    for item in primary:
        cid, name, y, h, w, x, is_c, is_g = item
        clean_name = name.replace("\n", "&#xa;")
        drawio.append(f'        <mxCell id="{cid}" value="{clean_name}" style="shape=ellipse;html=1;whiteSpace=wrap;align=center;verticalAlign=middle;fontFamily=Helvetica;fontSize=10.5;fontStyle=1;fillColor=#CFE2F3;strokeColor=#4A709C;strokeWidth=1.5;fontColor=#0B2545;" vertex="1" parent="1">')
        drawio.append(f'          <mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry" />')
        drawio.append('        </mxCell>')

    # Secondary use cases
    for item in secondary:
        cid, name, y, h, w, x, tgts, rtype = item
        clean_name = name.replace("\n", "&#xa;")
        if rtype == "include":
            style = "shape=ellipse;html=1;whiteSpace=wrap;align=center;verticalAlign=middle;fontFamily=Helvetica;fontSize=10;fillColor=#E1D5E7;strokeColor=#9673A6;strokeWidth=1.5;fontColor=#4A154B;"
        else:
            style = "shape=ellipse;html=1;whiteSpace=wrap;align=center;verticalAlign=middle;fontFamily=Helvetica;fontSize=10;fillColor=#FFE6CC;strokeColor=#D79B00;strokeWidth=1.5;fontColor=#7F4B00;"
        drawio.append(f'        <mxCell id="{cid}" value="{clean_name}" style="{style}" vertex="1" parent="1">')
        drawio.append(f'          <mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry" />')
        drawio.append('        </mxCell>')

    # Relationships <<include>> and <<extend>>
    rel_idx = 1
    for item in secondary:
        cid, name, y, h, w, x, tgts, rtype = item
        if rtype == "include":
            for t in tgts:
                drawio.append(f'        <mxCell id="rel_{rel_idx}" value="&amp;lt;&amp;lt;include&amp;gt;&amp;gt;" style="html=1;verticalAlign=bottom;labelBackgroundColor=none;endArrow=open;endFill=0;dashed=1;fontFamily=Helvetica;fontSize=9.5;fontStyle=2;fontColor=#0000FF;strokeColor=#0000FF;strokeWidth=1.5;" edge="1" parent="1" source="{t}" target="{cid}">')
                drawio.append('          <mxGeometry relative="1" as="geometry" />')
                drawio.append('        </mxCell>')
                rel_idx += 1
        elif rtype == "extend":
            for t in tgts:
                drawio.append(f'        <mxCell id="rel_{rel_idx}" value="&amp;lt;&amp;lt;extend&amp;gt;&amp;gt;" style="html=1;verticalAlign=bottom;labelBackgroundColor=none;endArrow=open;endFill=0;dashed=1;fontFamily=Helvetica;fontSize=9.5;fontStyle=2;fontColor=#D79B00;strokeColor=#D79B00;strokeWidth=1.5;" edge="1" parent="1" source="{cid}" target="{t}">')
                drawio.append('          <mxGeometry relative="1" as="geometry" />')
                drawio.append('        </mxCell>')
                rel_idx += 1

    # Associations for Contador
    cont_idx = 1
    for item in primary:
        cid, name, y, h, w, x, is_c, is_g = item
        if is_c:
            drawio.append(f'        <mxCell id="assoc_cont_{cont_idx}" style="endArrow=none;html=1;rounded=0;strokeColor=#0891B2;strokeWidth=1.5;fontFamily=Helvetica;" edge="1" parent="1" source="actor_contador" target="{cid}">')
            drawio.append('          <mxGeometry relative="1" as="geometry" />')
            drawio.append('        </mxCell>')
            cont_idx += 1

    # Associations for Gerente
    ger_idx = 1
    for item in primary:
        cid, name, y, h, w, x, is_c, is_g = item
        if is_g:
            drawio.append(f'        <mxCell id="assoc_ger_{ger_idx}" style="endArrow=none;html=1;rounded=0;strokeColor=#A0522D;strokeWidth=1.5;fontFamily=Helvetica;" edge="1" parent="1" source="actor_gerente" target="{cid}">')
            drawio.append('          <mxGeometry relative="1" as="geometry" />')
            drawio.append('        </mxCell>')
            ger_idx += 1

    # Connect Gerente to cu_export_eeff
    drawio.append(f'        <mxCell id="assoc_ger_ext_1" style="endArrow=none;html=1;rounded=0;strokeColor=#A0522D;strokeWidth=1.5;fontFamily=Helvetica;" edge="1" parent="1" source="actor_gerente" target="cu_export_eeff">')
    drawio.append('          <mxGeometry relative="1" as="geometry" />')
    drawio.append('        </mxCell>')

    drawio.append('      </root>')
    drawio.append('    </mxGraphModel>')
    drawio.append('  </diagram>')
    drawio.append('</mxfile>')

    with open(r"c:\Users\arana\Downloads\Jehova_Jireh_Moto_Repuestos\diagrama_casos_de_uso_estados_financieros.drawio", "w", encoding="utf-8") as f:
        f.write("\n".join(drawio))

    # -------------------------------------------------------------
    # 2. GENERATE HIGH QUALITY SVG / HTML
    # -------------------------------------------------------------
    svg_w = 1540
    svg_h = 1750

    html_content = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{
    margin: 0;
    padding: 20px;
    background: #ffffff;
    font-family: Arial, Helvetica, sans-serif;
    display: flex;
    justify-content: center;
  }}
  svg {{
    background: #ffffff;
  }}
</style>
</head>
<body>
<svg width="{svg_w}" height="{svg_h}" viewBox="0 0 {svg_w} {svg_h}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <!-- Marcador flecha azul para <<include>> -->
    <marker id="arrow-blue" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 8 5 L 0 9" fill="none" stroke="#0033CC" stroke-width="1.6" />
    </marker>
    <!-- Marcador flecha naranja para <<extend>> -->
    <marker id="arrow-orange" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 8 5 L 0 9" fill="none" stroke="#D79B00" stroke-width="1.6" />
    </marker>
  </defs>

  <!-- Límite del Sistema (Marco Azul) -->
  <rect x="{boundary_x}" y="{boundary_y}" width="{boundary_w}" height="{boundary_h}" fill="#FFFFFF" stroke="#104E8B" stroke-width="2.5" />

  <!-- Título Superior -->
  <text x="{boundary_x + 25}" y="{boundary_y + 30}" font-size="16" font-weight="bold" fill="#003366">Módulo: Elaboración de Estados Financieros, Contabilidad y Gestión Tributaria</text>

  <!-- Pie de Página -->
  <text x="{boundary_x + 25}" y="{boundary_y + boundary_h - 15}" font-size="11.5" font-weight="bold" fill="#003366">Aplicación Web Administrativa para la Gestión de Ventas, Inventario y Procesos Operativos de Jehová Jireh Masatepe Moto Repuestos</text>

  <!-- ==================== LÍNEAS DE ASOCIACIÓN CONTADOR ==================== -->
  <g stroke="#0891B2" stroke-width="1.5">
'''
    ac_cx = actor_contador_x + 27
    ac_cy = actor_contador_y + 40

    for item in primary:
        cid, name, y, h, w, x, is_c, is_g = item
        if is_c:
            target_x = x
            target_y = y + h / 2
            if cid == "cu_login":
                html_content += f'    <polyline points="{ac_cx},{actor_contador_y} {ac_cx},{target_y} {target_x},{target_y}" fill="none" />\n'
            else:
                html_content += f'    <line x1="{actor_contador_x + actor_contador_w}" y1="{ac_cy}" x2="{target_x}" y2="{target_y}" />\n'

    html_content += '''  </g>

  <!-- ==================== LÍNEAS DE ASOCIACIÓN GERENTE ==================== -->
  <g stroke="#A0522D" stroke-width="1.5">
'''
    ag_cx = actor_gerente_x
    ag_cy = actor_gerente_y + 40

    # Gerente connects to:
    # Contabilidad: cu_diario, cu_mayor, cu_comp, cu_er, cu_bg, cu_flujo, cu_export_eeff
    # Tributaria: cu_export_ir, cu_hist_trib (NO aprueba ni modifica datos fiscales)

    # 1. Diario & Mayor
    html_content += f'    <line x1="{ag_cx}" y1="{ag_cy}" x2="{all_cases["cu_diario"]["x"] + all_cases["cu_diario"]["w"]}" y2="{all_cases["cu_diario"]["y"] + all_cases["cu_diario"]["h"]/2}" />\n'
    html_content += f'    <line x1="{ag_cx}" y1="{ag_cy}" x2="{all_cases["cu_mayor"]["x"] + all_cases["cu_mayor"]["w"]}" y2="{all_cases["cu_mayor"]["y"] + all_cases["cu_mayor"]["h"]/2}" />\n'

    # 2. Balance de Comprobación & Estado de Resultados
    html_content += f'    <line x1="{ag_cx}" y1="{ag_cy}" x2="{all_cases["cu_comp"]["x"] + all_cases["cu_comp"]["w"]}" y2="{all_cases["cu_comp"]["y"] + all_cases["cu_comp"]["h"]/2}" />\n'
    html_content += f'    <line x1="{ag_cx}" y1="{ag_cy}" x2="{all_cases["cu_er"]["x"] + all_cases["cu_er"]["w"]}" y2="{all_cases["cu_er"]["y"] + all_cases["cu_er"]["h"]/2}" />\n'

    # 3. Exportar EEFF
    html_content += f'    <line x1="{ag_cx}" y1="{ag_cy}" x2="{all_cases["cu_export_eeff"]["x"] + all_cases["cu_export_eeff"]["w"]}" y2="{all_cases["cu_export_eeff"]["y"] + all_cases["cu_export_eeff"]["h"]/2}" />\n'

    # 4. Balance General & Flujo de Efectivo
    html_content += f'    <line x1="{ag_cx}" y1="{ag_cy}" x2="{all_cases["cu_bg"]["x"] + all_cases["cu_bg"]["w"]}" y2="{all_cases["cu_bg"]["y"] + all_cases["cu_bg"]["h"]/2}" />\n'
    html_content += f'    <line x1="{ag_cx}" y1="{ag_cy}" x2="{all_cases["cu_flujo"]["x"] + all_cases["cu_flujo"]["w"]}" y2="{all_cases["cu_flujo"]["y"] + all_cases["cu_flujo"]["h"]/2}" />\n'

    # 5. Exportar IR (RF67)
    html_content += f'    <line x1="{ag_cx}" y1="{ag_cy}" x2="{all_cases["cu_export_ir"]["x"] + all_cases["cu_export_ir"]["w"]}" y2="{all_cases["cu_export_ir"]["y"] + all_cases["cu_export_ir"]["h"]/2}" />\n'

    # 6. Historial y registro de pagos (RF68)
    html_content += f'    <line x1="{ag_cx}" y1="{ag_cy}" x2="{all_cases["cu_hist_trib"]["x"] + all_cases["cu_hist_trib"]["w"]}" y2="{all_cases["cu_hist_trib"]["y"] + all_cases["cu_hist_trib"]["h"]/2}" />\n'

    html_content += '''  </g>

  <!-- ==================== RELACIONES <<include>> Y <<extend>> ==================== -->
'''

    for item in secondary:
        cid, name, y, h, w, x, tgts, rtype = item
        if rtype == "include":
            for t in tgts:
                src = all_cases[t]
                sx = src["x"] + src["w"]
                sy = src["y"] + src["h"] / 2
                tx = x
                ty = y + h / 2
                mid_x = (sx + tx) / 2
                mid_y = (sy + ty) / 2
                html_content += f'''  <g stroke="#0033CC" stroke-width="1.5" stroke-dasharray="5,4">
    <line x1="{sx}" y1="{sy}" x2="{tx}" y2="{ty}" marker-end="url(#arrow-blue)" />
  </g>
  <rect x="{mid_x - 36}" y="{mid_y - 8}" width="72" height="16" fill="#FFFFFF" rx="3" />
  <text x="{mid_x}" y="{mid_y + 4}" font-size="10" font-style="italic" fill="#0033CC" text-anchor="middle">&lt;&lt;include&gt;&gt;</text>
'''
        elif rtype == "extend":
            for t in tgts:
                dest = all_cases[t]
                sx = x
                sy = y + h / 2
                tx = dest["x"] + dest["w"]
                ty = dest["y"] + dest["h"] / 2
                mid_x = (sx + tx) / 2
                mid_y = (sy + ty) / 2
                html_content += f'''  <g stroke="#D79B00" stroke-width="1.5" stroke-dasharray="5,4">
    <line x1="{sx}" y1="{sy}" x2="{tx}" y2="{ty}" marker-end="url(#arrow-orange)" />
  </g>
  <rect x="{mid_x - 34}" y="{mid_y - 7}" width="68" height="15" fill="#FFFFFF" rx="3" />
  <text x="{mid_x}" y="{mid_y + 4}" font-size="9.5" font-style="italic" fill="#D79B00" text-anchor="middle">&lt;&lt;extend&gt;&gt;</text>
'''

    html_content += '''
  <!-- ==================== ÓVALOS CASOS DE USO PRIMARIOS (Celeste) ==================== -->
'''
    for item in primary:
        cid, name, y, h, w, x, is_c, is_g = item
        rx = w / 2
        ry = h / 2
        lines = name.split("\n")
        html_content += f'  <g transform="translate({x}, {y})">\n'
        html_content += f'    <ellipse cx="{rx}" cy="{ry}" rx="{rx}" ry="{ry}" fill="#CFE2F3" stroke="#4A709C" stroke-width="1.5" />\n'
        if len(lines) == 1:
            html_content += f'    <text x="{rx}" y="{ry + 4}" font-size="10.5" font-weight="bold" fill="#0B2545" text-anchor="middle">{lines[0]}</text>\n'
        elif len(lines) == 2:
            html_content += f'    <text x="{rx}" y="{ry - 3}" font-size="10.5" font-weight="bold" fill="#0B2545" text-anchor="middle">{lines[0]}</text>\n'
            html_content += f'    <text x="{rx}" y="{ry + 11}" font-size="10.5" font-weight="bold" fill="#0B2545" text-anchor="middle">{lines[1]}</text>\n'
        html_content += '  </g>\n'

    html_content += '''
  <!-- ==================== ÓVALOS CASOS DE USO SECUNDARIOS (Morado / Naranja) ==================== -->
'''
    for item in secondary:
        cid, name, y, h, w, x, tgts, rtype = item
        rx = w / 2
        ry = h / 2
        lines = name.split("\n")
        if rtype == "include":
            fill = "#E1D5E7"
            stroke = "#9673A6"
            fcolor = "#4A154B"
        else:
            fill = "#FFE6CC"
            stroke = "#D79B00"
            fcolor = "#7F4B00"

        html_content += f'  <g transform="translate({x}, {y})">\n'
        html_content += f'    <ellipse cx="{rx}" cy="{ry}" rx="{rx}" ry="{ry}" fill="{fill}" stroke="{stroke}" stroke-width="1.5" />\n'
        if len(lines) == 1:
            html_content += f'    <text x="{rx}" y="{ry + 4}" font-size="10" font-weight="bold" fill="{fcolor}" text-anchor="middle">{lines[0]}</text>\n'
        elif len(lines) == 2:
            html_content += f'    <text x="{rx}" y="{ry - 3}" font-size="10" font-weight="bold" fill="{fcolor}" text-anchor="middle">{lines[0]}</text>\n'
            html_content += f'    <text x="{rx}" y="{ry + 10}" font-size="10" font-weight="bold" fill="{fcolor}" text-anchor="middle">{lines[1]}</text>\n'
        html_content += '  </g>\n'

    # Stick Figures for Actors
    def draw_actor(ax, ay, color, label_lines):
        cx = ax + 27
        s = f'''  <!-- Actor -->
  <g stroke="{color}" stroke-width="2.5" fill="none">
    <circle cx="{cx}" cy="{ay + 18}" r="14" fill="{color}" />
    <line x1="{cx}" y1="{ay + 32}" x2="{cx}" y2="{ay + 72}" />
    <line x1="{cx - 22}" y1="{ay + 46}" x2="{cx + 22}" y2="{ay + 46}" />
    <line x1="{cx}" y1="{ay + 72}" x2="{cx - 18}" y2="{ay + 105}" />
    <line x1="{cx}" y1="{ay + 72}" x2="{cx + 18}" y2="{ay + 105}" />
  </g>
'''
        for idx, line in enumerate(label_lines):
            ly = ay + 120 + (idx * 13)
            s += f'  <text x="{cx}" y="{ly}" font-size="10.5" font-weight="bold" fill="#000000" text-anchor="middle">{line}</text>\n'
        return s

    html_content += draw_actor(actor_contador_x, actor_contador_y, "#0891B2", ["CONTADOR", "(EXTERNO)"])
    html_content += draw_actor(actor_gerente_x, actor_gerente_y, "#FF8C00", ["GERENTE ADMINISTRATIVO", "Y FINANCIERO"])

    html_content += '''
</svg>
</body>
</html>
'''

    with open(r"c:\Users\arana\Downloads\Jehova_Jireh_Moto_Repuestos\diagrama_contabilidad_preview.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    png_out = r"c:\Users\arana\Downloads\Jehova_Jireh_Moto_Repuestos\diagrama_casos_de_uso_estados_financieros.png"
    html_url = "file:///c:/Users/arana/Downloads/Jehova_Jireh_Moto_Repuestos/diagrama_contabilidad_preview.html"

    cmd = [
        chrome_path,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--force-device-scale-factor=1.5",
        f"--window-size={svg_w + 60},{svg_h + 60}",
        f"--screenshot={png_out}",
        html_url
    ]
    subprocess.run(cmd, capture_output=True, text=True)
    print("PNG updated successfully!")

generate_adjusted_diagram()
