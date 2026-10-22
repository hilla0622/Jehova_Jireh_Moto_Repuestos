# UNIDAD V: INGENIERÍA WEB BASADA EN UML (METODOLOGÍA UWE)
## APLICACIÓN WEB ADMINISTRATIVA — JEHOVÁ JIREH MASATEPE MOTO REPUESTOS
**Universidad Nacional de Ingeniería (UNI) — DACTIC**  
**Asignatura:** Ingeniería de Software I | **Docente:** Msc. Juan Francisco Gómez Flores  

---

## 5.2 MODELOS DE DISEÑO UWE APLICADOS A LOS MÓDULOS DEL SISTEMA

La metodología **UWE (UML-based Web Engineering)** propone un proceso de diseño sistemático y dirigido por modelos para aplicaciones hipermedia y web transaccionales. A diferencia de las metodologías de software de escritorio clásicas, UWE separa de forma explícita:
1. **La información del dominio** (Modelo Lógico-Conceptual y de Contenido).
2. **El espacio navegable del usuario** (Modelo de Navegación).
3. **La arquitectura visual de las interfaces** (Modelo de Presentación).
4. **La lógica transaccional de negocio** (Modelo de Procesos).

A continuación se documentan en estricto orden los tres apartados requeridos por módulo:
- **5.2.1 Modelo Lógico-Conceptual** (8 módulos).
- **5.2.2 Modelo de Navegación** (8 módulos, con estereotipos UWE: `«navigationClass»`, `«menu»`, `«index»`, `«query»`, `«processNode»`).
- **5.2.3 Modelo de Presentación** (8 módulos, con estereotipos UWE: `«presentationClass»`, `«presentationGroup»`, `«form»`, `«textInput»`, `«button»`, `«selection»`, `«anchor»`).

---

# 5.2.1 MODELO LÓGICO-CONCEPTUAL

El Modelo Lógico-Conceptual captura la estructura esencial de la información empresarial de **Jehová Jireh Moto Repuestos** de forma independiente de la interfaz web y de la tecnología de implementación, estableciendo clases del dominio, atributos semánticos, cardinalidades y asociaciones.

---

### 5.2.1.1 Gestión de Productos e Inventario
Describe el catálogo de repuestos, su clasificación taxonómica, control físico en bodega y la trazabilidad de entradas, salidas y ajustes de mercadería.

```mermaid
classDiagram
    class Categoria {
        +Integer id
        +String nombre
        +String descripcion
        +Boolean activo
    }
    class Producto {
        +String codigoSku
        +String nombre
        +String marca
        +String modeloCompatible
        +String ubicacionEstante
        +Decimal costo
        +Decimal precioVenta
        +Integer stockActual
        +Integer stockMinimo
        +Boolean activo
    }
    class MovimientoInventario {
        +DateTime fecha
        +String tipoMovimiento
        +Integer cantidad
        +Integer stockAnterior
        +Integer stockPosterior
        +String referenciaOrigen
        +String motivo
    }
    class AjusteInventario {
        +DateTime fecha
        +String tipoAjuste
        +Integer cantidad
        +String motivo
        +Decimal costoImpacto
    }
    class Usuario {
        +String username
        +String nombreCompleto
        +String rol
    }

    Categoria "1" --> "0..*" Producto : clasifica
    Producto "1" --> "0..*" MovimientoInventario : registra_historial
    Producto "1" --> "0..*" AjusteInventario : recibe_ajustes
    Usuario "1" --> "0..*" MovimientoInventario : autoriza
    Usuario "1" --> "0..*" AjusteInventario : ejecuta
    AjusteInventario "0..1" ..> "1" MovimientoInventario : origina
```

---

### 5.2.1.2 Gestión de Ventas y Caja (Punto de Venta)
Representa la relación entre el turno operativo de caja, la cabecera de la factura de venta, las partidas individuales de repuestos comercializados con su costo histórico, los métodos de cobranza y el tratamiento de devoluciones de clientes.

```mermaid
classDiagram
    class SesionCaja {
        +DateTime fechaApertura
        +DateTime fechaCierre
        +Decimal montoInicial
        +Decimal saldoEsperado
        +Decimal saldoReal
        +Decimal diferencia
        +String estado
    }
    class Venta {
        +String codigoVenta
        +DateTime fechaVenta
        +Decimal subtotal
        +Decimal descuento
        +Decimal total
        +String formaPago
        +String canalVenta
        +String estado
        +String nombreClienteInvitado
    }
    class DetalleVenta {
        +Integer cantidad
        +Decimal precioUnitario
        +Decimal costoHistorico
        +Decimal subtotal
    }
    class Cliente {
        +String nombreCompleto
        +String identificacion
        +String telefono
        +String correo
        +String direccion
        +String tipoCliente
    }
    class Pago {
        +String metodo
        +Decimal monto
        +String referencia
        +DateTime fecha
        +String origen
    }
    class Comprobante {
        +String numero
        +DateTime fechaEmision
        +Decimal total
        +String tipo
    }
    class Devolucion {
        +String codigoDevolucion
        +DateTime fecha
        +String motivo
        +Decimal totalDevuelto
        +String estado
    }
    class DetalleDevolucion {
        +Integer cantidad
        +Decimal precioUnitario
        +Decimal subtotal
    }
    class Producto {
        +String codigoSku
        +String nombre
        +Decimal precioVenta
    }

    SesionCaja "0..1" --> "0..*" Venta : contiene
    Cliente "0..1" --> "0..*" Venta : realiza
    Venta "1" *-- "1..*" DetalleVenta : compone
    Producto "1" <-- "0..*" DetalleVenta : referencia
    Venta "1" --> "1..*" Pago : liquida_con
    Venta "1" --> "0..1" Comprobante : genera
    Venta "1" --> "0..*" Devolucion : origina
    Devolucion "1" *-- "1..*" DetalleDevolucion : detalla
    Producto "1" <-- "0..*" DetalleDevolucion : reintegra
```

---

### 5.2.1.3 Gestión de Compras y Proveedores
Modela el reabastecimiento de repuestos, contratos con casas comerciales proveedoras, recepción física en bodega e impacto en los costos de adquisición.

```mermaid
classDiagram
    class Proveedor {
        +String nombreEmpresa
        +String contactoNombre
        +String identificacionFiscal
        +String telefono
        +String email
        +String direccion
        +Boolean activo
    }
    class Compra {
        +String codigoCompra
        +String facturaProveedor
        +DateTime fechaCompra
        +Decimal total
        +String formaPago
        +String estado
        +String observaciones
    }
    class DetalleCompra {
        +Integer cantidad
        +Decimal costoUnitario
        +Decimal subtotal
    }
    class RecepcionCompra {
        +DateTime fechaRecepcion
        +String estado
        +String observaciones
    }
    class Producto {
        +String codigoSku
        +String nombre
        +Decimal costo
        +Integer stockActual
    }
    class MovimientoInventario {
        +DateTime fecha
        +String tipoMovimiento
        +Integer cantidad
    }

    Proveedor "1" --> "0..*" Compra : suministra
    Compra "1" *-- "1..*" DetalleCompra : contiene
    Producto "1" <-- "0..*" DetalleCompra : adquiere
    Compra "1" --> "0..*" RecepcionCompra : formaliza
    RecepcionCompra "1" ..> "1..*" MovimientoInventario : desencadena_entrada
    Producto "1" <-- "0..*" MovimientoInventario : incrementa_stock
```

---

### 5.2.1.4 Elaboración de Estados Financieros y Contabilidad
Modela la contabilidad por partida doble, catálogo de cuentas normalizado, asientos contables, conciliación bancaria mensual, estado de flujo de efectivo por actividades (operación, inversión, financiamiento) y módulo fiscal DGI.

```mermaid
classDiagram
    class CuentaContable {
        +String codigo
        +String nombre
        +String clasificacion
        +String naturaleza
        +String flujoCategoria
        +Boolean ajusteNoMonetario
    }
    class AsientoContable {
        +DateTime fecha
        +String concepto
        +String moduloOrigen
        +Integer referenciaId
    }
    class MovimientoContable {
        +Decimal debe
        +Decimal haber
    }
    class ConciliacionBancaria {
        +Integer anio
        +Integer mes
        +DateTime fechaCorte
        +Decimal saldoSegunLibros
        +Decimal saldoSegunBanco
        +Decimal diferencia
        +String estado
    }
    class PartidaConciliacion {
        +String tipoPartida
        +DateTime fecha
        +String documentoReferencia
        +Decimal monto
        +String efectoEnSaldo
    }
    class EstadoFlujoEfectivo {
        +Integer ejercicioFiscal
        +DateTime fechaInicio
        +DateTime fechaFin
        +String metodo
        +Decimal flujoOperacion
        +Decimal flujoInversion
        +Decimal flujoFinanciamiento
        +Decimal saldoFinal
    }
    class DeclaracionIR {
        +Integer ejercicioFiscal
        +Integer version
        +Decimal impuestoDeterminado
        +Decimal totalAcreditamientos
        +Decimal saldoAPagar
        +String estado
    }

    AsientoContable "1" *-- "2..*" MovimientoContable : equilibra
    CuentaContable "1" <-- "0..*" MovimientoContable : imputa_a
    ConciliacionBancaria "1" *-- "0..*" PartidaConciliacion : concilia_con
    CuentaContable "1" <-- "0..*" ConciliacionBancaria : audita_cuenta
    CuentaContable "1" ..> "0..*" EstadoFlujoEfectivo : nutre_actividades
    AsientoContable "0..*" ..> "1" DeclaracionIR : sustenta_fiscalmente
```

---

### 5.2.1.5 Estadística, Reportes y Análisis
Estructura el motor analítico del negocio que desacopla los filtros de consulta, los KPIs de desempeño, la rotación de existencias ABC (inversión vs consumo) y las medidas estadísticas descriptivas.

```mermaid
classDiagram
    class FiltroReporte {
        +Date fechaInicio
        +Date fechaFin
        +String rangoPreset
        +Integer mes
        +Integer anio
        +String canal
        +String criterioABC
    }
    class ReporteEstadistico {
        +DateTime fechaGeneracion
        +String nombreNegocio
        +String periodoTexto
    }
    class IndicadoresComerciales {
        +Decimal ventasNetas
        +Integer unidadesVendidas
        +Integer transacciones
        +Decimal ticketPromedio
        +Decimal costoVentas
        +Decimal utilidadBruta
        +Decimal margenBrutoPorcentaje
        +Decimal promedioDiarioVentas
    }
    class MedidasDescriptivas {
        +Integer n
        +Decimal media
        +Decimal mediana
        +Decimal minimo
        +Decimal maximo
        +Decimal rango
        +Decimal varianza
        +Decimal desviacionEstandar
        +Decimal coeficienteVariacion
    }
    class ComparacionPeriodos {
        +String indicador
        +Decimal valorBase
        +Decimal valorComparado
        +Decimal variacionAbsoluta
        +Decimal variacionPorcentual
    }
    class ResultadoCategoria {
        +String categoria
        +Integer unidades
        +Decimal totalVentas
        +Decimal utilidad
        +Decimal margenPorcentaje
    }
    class RotacionABCProducto {
        +String codigoSku
        +String nombre
        +String claseABC
        +Decimal valorInmovilizado
        +Decimal rotacionMonetaria
        +Boolean esHuesoSinVentas
    }

    FiltroReporte "1" --> "1" ReporteEstadistico : parametriza
    ReporteEstadistico "1" *-- "1" IndicadoresComerciales : consolida
    ReporteEstadistico "1" *-- "1" MedidasDescriptivas : computa
    ReporteEstadistico "1" *-- "0..*" ComparacionPeriodos : evalua
    ReporteEstadistico "1" *-- "0..*" ResultadoCategoria : clasifica_por_linea
    ReporteEstadistico "1" *-- "0..*" RotacionABCProducto : segmenta_pareto
```

---

### 5.2.1.6 Gestión de Recursos Humanos y Nómina
Representa la administración de colaboradores, contratos bajo legislación nicaragüense (Código del Trabajo Ley 185), control de asistencia, cálculo quincenal de nómina con INSS laboral/patronal, IR según tarifa progresiva DGI e higiene y seguridad laboral (Ley 618).

```mermaid
classDiagram
    class Empleado {
        +String nombres
        +String apellidos
        +String identificacionCedula
        +Decimal salarioBase
        +DateTime fechaIngreso
        +String numeroINSS
        +String telefono
        +Boolean activo
    }
    class Cargo {
        +String nombreCargo
        +String area
        +Decimal salarioBaseSugerido
    }
    class JornadaLaboral {
        +String nombre
        +Time horaEntrada
        +Time horaSalida
        +Integer horasSemanales
    }
    class ContratoLaboral {
        +String numeroContrato
        +String tipoContratacion
        +DateTime fechaInicio
        +Decimal salarioMensual
        +String estado
    }
    class AsistenciaLaboral {
        +Date fecha
        +Time horaEntrada
        +Time horaSalida
        +String estado
        +Integer minutosTardanza
    }
    class HoraExtra {
        +Date fecha
        +Decimal cantidadHoras
        +Decimal recargoPorcentaje
        +Decimal montoTotal
    }
    class Nomina {
        +Integer periodoMes
        +Integer periodoAnio
        +DateTime fechaGeneracion
        +Decimal totalIngresos
        +Decimal totalDeducciones
        +Decimal totalNeto
        +Decimal inssPatronalTotal
    }
    class DetalleNomina {
        +Decimal salarioBase
        +Decimal ingresosExtras
        +Decimal inssLaboral
        +Decimal irLaboral
        +Decimal netoPagar
    }
    class ColillaPago {
        +String numeroColilla
        +DateTime fechaEmision
        +Decimal montoNeto
    }
    class InspeccionHigiene {
        +DateTime fechaInspeccion
        +String inspector
        +Integer puntosAprobados
        +Decimal porcentajeCumplimiento
    }

    Cargo "1" --> "0..*" Empleado : asigna
    JornadaLaboral "1" --> "0..*" Empleado : rige
    Empleado "1" --> "0..*" ContratoLaboral : suscribe
    Empleado "1" --> "0..*" AsistenciaLaboral : registra
    Empleado "1" --> "0..*" HoraExtra : acumula
    Nomina "1" *-- "1..*" DetalleNomina : contiene
    Empleado "1" <-- "1" DetalleNomina : corresponde_a
    DetalleNomina "1" --> "0..1" ColillaPago : formaliza
    Empleado "0..*" ..> "0..*" InspeccionHigiene : amparado_por
```

---

### 5.2.1.7 Portal Web y Catálogo Público (Comercio Electrónico)
Modela la navegación externa de clientes, catálogo público con precios comerciales, carrito de compras persistente, colocación de pedidos web y métodos de entrega (retiro en tienda Masatepe o envío).

```mermaid
classDiagram
    class ClienteWeb {
        +String nombreCompleto
        +String email
        +String telefono
        +String direccionEnvio
        +String departamento
    }
    class Carrito {
        +DateTime fechaCreacion
        +Decimal subtotal
        +String estado
    }
    class DetalleCarrito {
        +Integer cantidad
        +Decimal precioUnitario
        +Decimal subtotal
    }
    class PedidoWeb {
        +String codigoPedido
        +DateTime fechaPedido
        +Decimal total
        +String formaEntrega
        +String metodoPago
        +String estado
    }
    class DetallePedidoWeb {
        +Integer cantidad
        +Decimal precioUnitario
        +Decimal subtotal
    }
    class Producto {
        +String codigoSku
        +String nombre
        +Decimal precioVenta
        +Integer stockActual
    }

    ClienteWeb "1" --> "0..*" Carrito : prepara
    Carrito "1" *-- "0..*" DetalleCarrito : incluye
    Producto "1" <-- "0..*" DetalleCarrito : referencia
    ClienteWeb "1" --> "0..*" PedidoWeb : formaliza
    PedidoWeb "1" *-- "1..*" DetallePedidoWeb : desglosa
    Producto "1" <-- "0..*" DetallePedidoWeb : reserva
```

---

### 5.2.1.8 Gestión de Usuarios y Seguridad
Modela el control de acceso basado en roles (RBAC), credenciales de autenticación, sesiones y auditoría de operadores dentro del sistema.

```mermaid
classDiagram
    class Rol {
        +String nombre
        +String descripcion
        +Integer nivelJerarquia
    }
    class Permiso {
        +String codigo
        +String modulo
        +String accion
    }
    class Usuario {
        +String username
        +String contrasenaHash
        +String nombreCompleto
        +String email
        +Boolean activo
        +DateTime ultimoAcceso
    }
    class SesionAcceso {
        +DateTime fechaInicio
        +DateTime fechaFin
        +String direccionIp
        +String estado
    }

    Rol "1" --> "0..*" Usuario : agrupa
    Rol "1" --> "1..*" Permiso : concede
    Usuario "1" --> "0..*" SesionAcceso : inicia
```

---

# 5.2.2 MODELO DE NAVEGACIÓN

El Modelo de Navegación en UWE describe el hiperespacio y los recorridos disponibles para los usuarios en la aplicación web. Emplea los siguientes estereotipos normativos:
- `«navigationClass»`: Nodo o página de destino navegable.
- `«menu»`: Agrupador contextual de accesos y opciones de navegación.
- `«index»`: Lista o catálogo de enlaces que apuntan a instancias de una clase navegable.
- `«query»`: Formulario de consulta, búsqueda o filtrado de información.
- `«processNode»`: Nodo que desencadena la ejecución de un proceso de negocio transaccional.
- `«navigationLink»`: Enlace dirigido entre nodos navegables.

---

### 5.2.2.1 Navegación de Productos e Inventario
Recorrido para consultar el catálogo de repuestos, aplicar filtros por categoría o texto, revisar existencias y ejecutar operaciones de ajuste y consulta del Kardex.

```mermaid
flowchart TD
    Dashboard["«navigationClass»<br/><b>PanelPrincipal</b>"]
    MenuInv["«menu»<br/><b>MenuInventario</b>"]
    QueryProd["«query»<br/><b>FiltroProductos</b><br/>(Buscar SKU, Categoría)"]
    IndexProd["«index»<br/><b>TablaInventario</b><br/>(Lista Repuestos)"]
    FichaProd["«navigationClass»<br/><b>FichaProducto</b><br/>(Detalle Repuesto)"]
    ProcRegProd["«processNode»<br/><b>RegistrarProducto</b>"]
    ProcAjuste["«processNode»<br/><b>RegistrarAjusteStock</b>"]
    KardexView["«navigationClass»<br/><b>HistorialKardex</b>"]

    Dashboard -->|Selecciona Inventario| MenuInv
    MenuInv --> QueryProd
    QueryProd -->|Aplica filtro| IndexProd
    IndexProd -->|Ver detalle| FichaProd
    MenuInv -->|Clic Nuevo Repuesto| ProcRegProd
    FichaProd -->|Ajustar existencias| ProcAjuste
    FichaProd -->|Ver movimientos| KardexView
    ProcRegProd -->|Éxito| IndexProd
    ProcAjuste -->|Actualiza| FichaProd
```

---

### 5.2.2.2 Navegación de Ventas y Caja (Punto de Venta)
Recorrido del cajero/vendedor desde la apertura de turno, selección ágil de repuestos, cálculo de totales, liquidación y emisión del comprobante.

```mermaid
flowchart TD
    MenuVentas["«menu»<br/><b>MenuVentasPOS</b>"]
    ProcApertura["«processNode»<br/><b>AperturaTurnoCaja</b>"]
    TerminalPOS["«navigationClass»<br/><b>TerminalPOS</b><br/>(Pantalla de Venta)"]
    QueryRepuesto["«query»<br/><b>BuscarRepuestoPOS</b>"]
    IndexCatalogo["«index»<br/><b>CatalogoRapidoPOS</b>"]
    ProcRegistrarVenta["«processNode»<br/><b>RegistrarVentaYCobro</b>"]
    ComprobanteTicket["«navigationClass»<br/><b>TicketFacturaVenta</b>"]
    IndexVentasHist["«index»<br/><b>HistorialVentasDia</b>"]
    ProcDevolucion["«processNode»<br/><b>RegistrarDevolucion</b>"]
    ProcCierreCaja["«processNode»<br/><b>CierreArqueoCaja</b>"]

    MenuVentas -->|Verifica turno| ProcApertura
    ProcApertura -->|Caja Abierta| TerminalPOS
    TerminalPOS --> QueryRepuesto
    QueryRepuesto --> IndexCatalogo
    IndexCatalogo -->|Agrega al carrito| TerminalPOS
    TerminalPOS -->|Confirmar Cobro| ProcRegistrarVenta
    ProcRegistrarVenta -->|Genera Comprobante| ComprobanteTicket
    MenuVentas -->|Ver ventas| IndexVentasHist
    IndexVentasHist -->|Solicitar anulación| ProcDevolucion
    TerminalPOS -->|Fin de jornada| ProcCierreCaja
```

---

### 5.2.2.3 Navegación de Compras y Proveedores
Rutas para registrar órdenes de compra de repuestos a proveedores mayoristas, recepcionar mercadería y verificar el ingreso en bodega.

```mermaid
flowchart TD
    MenuCompras["«menu»<br/><b>MenuComprasProveedores</b>"]
    IndexProveedores["«index»<br/><b>ListaProveedores</b>"]
    ProcNuevoProv["«processNode»<br/><b>RegistrarProveedor</b>"]
    FormOrdenCompra["«navigationClass»<br/><b>NuevaOrdenCompra</b>"]
    QueryRepuestosCompra["«query»<br/><b>BuscarRepuestosCompra</b>"]
    ProcRegistrarCompra["«processNode»<br/><b>GuardarCompraRecepcion</b>"]
    IndexHistorialCompras["«index»<br/><b>HistorialCompras</b>"]
    DetalleCompraView["«navigationClass»<br/><b>DetalleFacturaCompra</b>"]

    MenuCompras -->|Proveedores| IndexProveedores
    IndexProveedores -->|Agregar| ProcNuevoProv
    MenuCompras -->|Nueva Compra| FormOrdenCompra
    FormOrdenCompra --> QueryRepuestosCompra
    QueryRepuestosCompra -->|Carga líneas| FormOrdenCompra
    FormOrdenCompra -->|Confirmar Recepción| ProcRegistrarCompra
    ProcRegistrarCompra --> IndexHistorialCompras
    IndexHistorialCompras -->|Consultar| DetalleCompraView
```

---

### 5.2.2.4 Navegación de Estados Financieros y Contabilidad
Estructura de navegación para contabilidad formal, consulta de libros, balance, resultados, conciliación bancaria y flujo de efectivo.

```mermaid
flowchart TD
    MenuFinanzas["«menu»<br/><b>MenuEstadosFinancieros</b>"]
    IndexCuentas["«index»<br/><b>CatalogoCuentas</b>"]
    ProcAsiento["«processNode»<br/><b>RegistrarAsientoContable</b>"]
    NavLibroDiario["«navigationClass»<br/><b>LibroDiarioMayor</b>"]
    NavBalance["«navigationClass»<br/><b>BalanceGeneral</b>"]
    NavResultados["«navigationClass»<br/><b>EstadoResultados</b>"]
    NavFlujo["«navigationClass»<br/><b>FlujoEfectivoDirecto</b>"]
    NavConciliacion["«navigationClass»<br/><b>ConciliacionBancaria</b>"]
    NavFiscalDGI["«navigationClass»<br/><b>DeclaracionFiscalDGI</b>"]

    MenuFinanzas --> IndexCuentas
    MenuFinanzas -->|Nuevo Asiento| ProcAsiento
    ProcAsiento --> NavLibroDiario
    MenuFinanzas --> NavBalance
    MenuFinanzas --> NavResultados
    MenuFinanzas --> NavFlujo
    MenuFinanzas --> NavConciliacion
    MenuFinanzas --> NavFiscalDGI
```

---

### 5.2.2.5 Navegación de Estadística, Reportes y Análisis
Recorrido navegable del módulo analítico, gobernado por la barra de filtrado temporal dinámico y las 7 sub-pestañas de visualización gerencial.

```mermaid
flowchart TD
    MenuReportes["«menu»<br/><b>MenuReportesEstadisticas</b>"]
    BarraFiltros["«query»<br/><b>FiltroTemporalDinamico</b><br/>(Hoy, 7D, Mes, Año, Comparar)"]
    SubMenu7Tabs["«menu»<br/><b>SubmenuAnalisis7Pestanas</b>"]
    TabResumen["«navigationClass»<br/><b>PestanaResumenKPIs</b>"]
    TabVentas["«navigationClass»<br/><b>PestanaTendenciaVentas</b>"]
    TabRentabilidad["«navigationClass»<br/><b>PestanaRentabilidadLineas</b>"]
    TabABC["«navigationClass»<br/><b>PestanaRotacionABC</b>"]
    TabDevoluciones["«navigationClass»<br/><b>PestanaDevoluciones</b>"]
    TabEstadisticas["«navigationClass»<br/><b>PestanaMedidasDescriptivas</b>"]
    ModalInforme["«navigationClass»<br/><b>ModalInformeEjecutivo</b>"]
    ProcExportExcel["«processNode»<br/><b>ExportarLibroExcelXLSX</b>"]

    MenuReportes --> BarraFiltros
    BarraFiltros -->|Aplica criterios| SubMenu7Tabs
    SubMenu7Tabs --> TabResumen
    SubMenu7Tabs --> TabVentas
    SubMenu7Tabs --> TabRentabilidad
    SubMenu7Tabs --> TabABC
    SubMenu7Tabs --> TabDevoluciones
    SubMenu7Tabs --> TabEstadisticas
    SubMenu7Tabs -->|Generar Informe| ModalInforme
    SubMenu7Tabs -->|Descargar Excel| ProcExportExcel
    ModalInforme -->|Imprimir / Guardar| ModalInforme
```

---

### 5.2.2.6 Navegación de Recursos Humanos y Nómina
Navegación para el control de personal, expediente laboral, registro de horas extras/asistencias, formulación de nóminas y colillas de pago.

```mermaid
flowchart TD
    MenuRRHH["«menu»<br/><b>MenuRecursosHumanos</b>"]
    IndexEmpleados["«index»<br/><b>DirectorioColaboradores</b>"]
    ProcNuevoEmpleado["«processNode»<br/><b>RegistrarContratoEmpleado</b>"]
    ExpedienteView["«navigationClass»<br/><b>ExpedienteLaboralIndividual</b>"]
    NavAsistencia["«navigationClass»<br/><b>ControlAsistenciasHorasExtras</b>"]
    ProcGenerarNomina["«processNode»<br/><b>CalcularGenerarNomina</b>"]
    IndexNominas["«index»<br/><b>HistoricoPlanillas</b>"]
    ColillaView["«navigationClass»<br/><b>ColillaPagoOficial</b>"]
    NavHigiene["«navigationClass»<br/><b>HigieneSeguridadLey618</b>"]

    MenuRRHH --> IndexEmpleados
    IndexEmpleados -->|Alta personal| ProcNuevoEmpleado
    IndexEmpleados -->|Ver expediente| ExpedienteView
    MenuRRHH --> NavAsistencia
    MenuRRHH -->|Procesar quincena| ProcGenerarNomina
    ProcGenerarNomina --> IndexNominas
    IndexNominas -->|Ver colilla| ColillaView
    MenuRRHH --> NavHigiene
```

---

### 5.2.2.7 Navegación de Portal Web y Catálogo Público
Espacio navegable de cara al cliente web para descubrir repuestos de motos, consultar especificaciones técnicas, gestionar su carrito y formalizar pedidos.

```mermaid
flowchart TD
    HomeWeb["«navigationClass»<br/><b>InicioPortalWeb</b>"]
    MenuCatWeb["«menu»<br/><b>CategoriasMotos</b>"]
    QueryWeb["«query»<br/><b>BuscadorRepuestosWeb</b>"]
    IndexGridWeb["«index»<br/><b>CatalogoGridRepuestos</b>"]
    FichaWeb["«navigationClass»<br/><b>DetalleRepuestoWeb</b>"]
    CarritoWeb["«navigationClass»<br/><b>CarritoComprasWeb</b>"]
    ProcCheckout["«processNode»<br/><b>ConfirmarPedidoCheckout</b>"]
    ConfirmacionWeb["«navigationClass»<br/><b>ConfirmacionPedidoWeb</b>"]

    HomeWeb --> MenuCatWeb
    HomeWeb --> QueryWeb
    MenuCatWeb --> IndexGridWeb
    QueryWeb --> IndexGridWeb
    IndexGridWeb -->|Selecciona Repuesto| FichaWeb
    FichaWeb -->|Agregar al carrito| CarritoWeb
    CarritoWeb -->|Continuar a caja| ProcCheckout
    ProcCheckout -->|Pedido registrado| ConfirmacionWeb
```

---

### 5.2.2.8 Navegación de Usuarios y Seguridad
Navegación para la administración de credenciales, asignación de perfiles y monitoreo de accesos.

```mermaid
flowchart TD
    LoginView["«navigationClass»<br/><b>PantallaLogin</b>"]
    ProcAuth["«processNode»<br/><b>AutenticarUsuario</b>"]
    PanelAdminSeg["«menu»<br/><b>MenuUsuariosSeguridad</b>"]
    IndexUsuarios["«index»<br/><b>ListaCuentasSistema</b>"]
    ProcAltaUsuario["«processNode»<br/><b>CrearEditarUsuario</b>"]
    RolesView["«navigationClass»<br/><b>RolesYPermisos</b>"]
    AuditoriaView["«navigationClass»<br/><b>AuditoriaYSesiones</b>"]

    LoginView -->|Ingresa credenciales| ProcAuth
    ProcAuth -->|Credenciales Válidas| PanelAdminSeg
    PanelAdminSeg --> IndexUsuarios
    IndexUsuarios -->|Nuevo usuario| ProcAltaUsuario
    ProcAltaUsuario --> IndexUsuarios
    PanelAdminSeg --> RolesView
    PanelAdminSeg --> AuditoriaView
```

---

# 5.2.3 MODELO DE PRESENTACIÓN

El Modelo de Presentación en UWE describe la arquitectura visual y los componentes interactivos de las interfaces de usuario. Utiliza los siguientes estereotipos normativos:
- `«presentationClass»`: Representa la pantalla o página web completa.
- `«presentationGroup»`: Contenedores lógicos (paneles, tarjetas, barras de herramientas o ventanas modales).
- `«form»`: Formulario estructurado para captura o filtrado de datos.
- `«text»`: Texto informativo, etiquetas o datos de sólo lectura.
- `«textInput»`: Campos de entrada de datos (cajas de texto, fechas, números).
- `«selection»`: Controles de selección múltiple o listas desplegables (dropdowns, selects).
- `«button»`: Botones de comando o ejecución de acciones.
- `«anchor»`: Hipervínculos o pestañas de navegación.
- `«image»`: Elementos visuales, fotografías de repuestos o gráficos estadísticos generados.

---

### 5.2.3.1 Presentación de Productos e Inventario
Representa la interfaz `IU_GestionInventario` con buscador reactivo, alertas visuales de existencias mínimas y modal de registro de repuesto.

```mermaid
classDiagram
    class IU_GestionInventario {
        <<presentationClass>>
    }
    class BarraAccionesInventario {
        <<presentationGroup>>
        +textInput txtBuscarSKU
        +selection cmbCategoriaFiltro
        +selection cmbEstadoStock
        +button btnNuevoProducto
        +button btnExportarInventario
    }
    class TablaCatalogoInventario {
        <<presentationGroup>>
        +text colCodigoSKU
        +text colNombreRepuesto
        +text colCategoria
        +text colPrecioCosto
        +text colPrecioVenta
        +text colStockActual
        +text badgeAlertaMinimo
        +button btnEditarRepuesto
        +button btnAjustarStock
        +button btnVerKardex
    }
    class ModalRegistroProducto {
        <<presentationGroup>>
        +form formProducto
        +textInput txtCodigo
        +textInput txtNombre
        +selection cmbCategoria
        +textInput txtMarca
        +textInput txtModeloCompatible
        +textInput txtUbicacionEstante
        +textInput numCosto
        +textInput numPrecioVenta
        +textInput numStockInicial
        +textInput numStockMinimo
        +button btnGuardarProducto
        +button btnCancelar
    }

    IU_GestionInventario *-- BarraAccionesInventario
    IU_GestionInventario *-- TablaCatalogoInventario
    IU_GestionInventario *-- ModalRegistroProducto
```

---

### 5.2.3.2 Presentación de Ventas y Caja (Punto de Venta)
Representa la interfaz `IU_PuntoDeVenta` con panel de búsqueda rápida, detalle del ticket en córdobas, panel de cobro y ventana emergente de impresión de factura.

```mermaid
classDiagram
    class IU_PuntoDeVenta {
        <<presentationClass>>
    }
    class PanelSeleccionRepuestos {
        <<presentationGroup>>
        +textInput txtBusquedaRapida
        +selection cmbCategoriaFiltro
        +button btnEscanearCodigo
        +anchor gridItemRepuesto
    }
    class PanelTicketVenta {
        <<presentationGroup>>
        +text colItemNombre
        +text colItemCantidad
        +text colItemPrecio
        +text colItemSubtotal
        +button btnModificarCantidad
        +button btnEliminarLinea
        +text lblSubtotal
        +text lblDescuento
        +text lblTotalPagar
    }
    class ModalCobroFacturacion {
        <<presentationGroup>>
        +form formCobro
        +selection cmbFormaPago
        +textInput numMontoRecibido
        +text lblCambioDevolver
        +textInput txtClienteIdentificacion
        +textInput txtClienteNombre
        +button btnConfirmarVenta
        +button btnCancelarCobro
    }
    class ModalComprobanteImpresion {
        <<presentationGroup>>
        +image logoNegocio
        +text txtEncabezadoMasatepe
        +text txtNumeroFactura
        +text txtFechaHora
        +text tablaLineasVendidas
        +text txtTotalFinal
        +button btnImprimirTicket
        +button btnCerrar
    }

    IU_PuntoDeVenta *-- PanelSeleccionRepuestos
    IU_PuntoDeVenta *-- PanelTicketVenta
    IU_PuntoDeVenta *-- ModalCobroFacturacion
    IU_PuntoDeVenta *-- ModalComprobanteImpresion
```

---

### 5.2.3.3 Presentación de Compras y Proveedores
Representa la interfaz `IU_GestionCompras` para el registro de adquisición de repuestos, cálculo de costos e historial de recepciones.

```mermaid
classDiagram
    class IU_GestionCompras {
        <<presentationClass>>
    }
    class FormularioCabeceraCompra {
        <<presentationGroup>>
        +selection cmbProveedor
        +textInput txtFacturaProveedor
        +textInput dtFechaCompra
        +selection cmbCondicionPago
    }
    class TablaPartidasCompra {
        <<presentationGroup>>
        +selection cmbRepuestoAdquirido
        +textInput numCantidadComprada
        +textInput numCostoUnitario
        +text lblSubtotalLinea
        +button btnAgregarLinea
        +button btnRemoverLinea
        +text lblTotalCompra
    }
    class PanelAccionesCompra {
        <<presentationGroup>>
        +button btnGuardarRecepcion
        +button btnLimpiarFormulario
        +button btnVerHistorialCompras
    }

    IU_GestionCompras *-- FormularioCabeceraCompra
    IU_GestionCompras *-- TablaPartidasCompra
    IU_GestionCompras *-- PanelAccionesCompra
```

---

### 5.2.3.4 Presentación de Estados Financieros
Representa la interfaz `IU_EstadosFinancieros` con selector de fechas, pestañas contables y tablas de saldos.

```mermaid
classDiagram
    class IU_EstadosFinancieros {
        <<presentationClass>>
    }
    class BarraFiltrosFinancieros {
        <<presentationGroup>>
        +textInput dtFechaInicio
        +textInput dtFechaFin
        +selection cmbNivelDetalle
        +button btnConsultarEstados
        +button btnExportarPDF
    }
    class PestanasContables {
        <<presentationGroup>>
        +anchor tabBalanceGeneral
        +anchor tabEstadoResultados
        +anchor tabFlujoEfectivo
        +anchor tabConciliacionBancaria
    }
    class ContenedorReporteFinanciero {
        <<presentationGroup>>
        +text txtTituloEstado
        +text txtPeriodoEvaluado
        +text tablaCuentasDebeHaber
        +text lblTotalActivos
        +text lblTotalPasivoPatrimonio
        +text lblUtilidadNeta
        +button btnImprimirDocumento
    }

    IU_EstadosFinancieros *-- BarraFiltrosFinancieros
    IU_EstadosFinancieros *-- PestanasContables
    IU_EstadosFinancieros *-- ContenedorReporteFinanciero
```

---

### 5.2.3.5 Presentación de Estadística, Reportes y Análisis
Representa la interfaz `IU_EstadisticasYReportes` con la barra de filtrado temporal dinámico, tarjetas de KPIs, gráficos estadísticos y modal de Informe Ejecutivo.

```mermaid
classDiagram
    class IU_EstadisticasYReportes {
        <<presentationClass>>
    }
    class BarraFiltrosTemporales {
        <<presentationGroup>>
        +button btnPresetHoy
        +button btnPreset7Dias
        +button btnPresetMesActual
        +button btnPresetAnio
        +button btnPresetHistorico
        +textInput dtInicioPersonalizado
        +textInput dtFinPersonalizado
        +selection cmbMesDirecto
        +selection cmbAnioDirecto
        +button btnToggleComparar
        +selection cmbCategoriaFiltro
        +selection cmbCanalVentaFiltro
    }
    class TarjetasKPIsIndicadores {
        <<presentationGroup>>
        +text cardVentasNetas
        +text cardUnidadesVendidas
        +text cardTransacciones
        +text cardTicketPromedio
        +text cardUtilidadBruta
        +text cardMargenPorcentaje
        +text badgeVariacionPeriodo
    }
    class NavegacionSubpestanas {
        <<presentationGroup>>
        +anchor tabResumenGeneral
        +anchor tabVentasTendencias
        +anchor tabRentabilidadLineas
        +anchor tabInventarioABC
        +anchor tabDevoluciones
        +anchor tabMedidasDescriptivas
        +anchor tabInformesOficiales
    }
    class PanelGraficosYTablas {
        <<presentationGroup>>
        +image chartTendenciaCronologica
        +image chartDistribucionCategorias
        +image chartMetodosPago
        +text tablaRotacionABC
        +text tablaRepuestosSinMovimiento
        +text tablaAlertasStockCritico
    }
    class ModalInformeEjecutivo {
        <<presentationGroup>>
        +image logoEmpresaMasatepe
        +text txtEncabezadoInforme
        +text txtPeriodoAnalizado
        +text tablaResumenEjecutivo
        +text txtMedidasEstadisticas
        +button btnImprimirInformePDF
        +button btnDescargarExcelXLSX
        +button btnCerrarModal
    }

    IU_EstadisticasYReportes *-- BarraFiltrosTemporales
    IU_EstadisticasYReportes *-- TarjetasKPIsIndicadores
    IU_EstadisticasYReportes *-- NavegacionSubpestanas
    IU_EstadisticasYReportes *-- PanelGraficosYTablas
    IU_EstadisticasYReportes *-- ModalInformeEjecutivo
```

---

### 5.2.3.6 Presentación de Recursos Humanos y Nómina
Representa la interfaz `IU_RecursosHumanos` con gestión de personal, cálculo de planilla e impresión de colillas.

```mermaid
classDiagram
    class IU_RecursosHumanos {
        <<presentationClass>>
    }
    class SubmenuRRHH {
        <<presentationGroup>>
        +anchor tabDirectorioPersonal
        +anchor tabAsistenciasHorasExtras
        +anchor tabPlanillaNomina
        +anchor tabHigieneSeguridad
    }
    class PanelGestionNomina {
        <<presentationGroup>>
        +selection cmbMesNomina
        +selection cmbAnioNomina
        +button btnProcesarCalculoNomina
        +text tablaDetallePlanilla
        +text colEmpleadoNombre
        +text colSalarioBase
        +text colHorasExtras
        +text colINSSLaboral
        +text colIRLaboral
        +text colNetoAPagar
        +button btnVerColillaIndividual
    }
    class ModalColillaImprimible {
        <<presentationGroup>>
        +image logoJehovaJireh
        +text txtDatosTrabajador
        +text txtPeriodoQuincenal
        +text tablaIngresosDeducciones
        +text txtFirmaRecibido
        +button btnImprimirColilla
    }

    IU_RecursosHumanos *-- SubmenuRRHH
    IU_RecursosHumanos *-- PanelGestionNomina
    IU_RecursosHumanos *-- ModalColillaImprimible
```

---

### 5.2.3.7 Presentación de Portal Web y Catálogo Público
Representa la interfaz `IU_PortalWebPublico` para clientes en línea, con grid de repuestos y flujo de compra.

```mermaid
classDiagram
    class IU_PortalWebPublico {
        <<presentationClass>>
    }
    class HeaderNavbarPublico {
        <<presentationGroup>>
        +image logoPortal
        +textInput txtBuscadorRepuestos
        +selection cmbMarcaModeloMoto
        +anchor btnVerCarritoBadge
    }
    class GridCatalogoProductos {
        <<presentationGroup>>
        +image imgRepuestoMoto
        +text txtNombreRepuesto
        +text txtMarcaRepuesto
        +text txtPrecioCordobas
        +text badgeDisponibilidad
        +button btnAgregarAlCarrito
    }
    class DrawerCarritoCheckout {
        <<presentationGroup>>
        +text listaItemsCarrito
        +text lblTotalPagar
        +textInput txtNombreContacto
        +textInput txtTelefonoWhatsApp
        +selection cmbModalidadEntrega
        +textInput txtDireccionEnvio
        +button btnFinalizarPedidoWeb
    }

    IU_PortalWebPublico *-- HeaderNavbarPublico
    IU_PortalWebPublico *-- GridCatalogoProductos
    IU_PortalWebPublico *-- DrawerCarritoCheckout
```

---

### 5.2.3.8 Presentación de Usuarios y Seguridad
Representa la interfaz `IU_UsuariosSeguridad` para la gestión de operadores del sistema.

```mermaid
classDiagram
    class IU_UsuariosSeguridad {
        <<presentationClass>>
    }
    class PanelControlUsuarios {
        <<presentationGroup>>
        +button btnCrearNuevoUsuario
        +selection cmbFiltroRol
        +text tablaCuentasUsuario
        +text colUsername
        +text colNombreCompleto
        +text colRolAsignado
        +text colEstadoActivo
        +button btnEditarUsuario
        +button btnDesactivarUsuario
    }
    class ModalFormularioUsuario {
        <<presentationGroup>>
        +form formUsuario
        +textInput txtUsername
        +textInput txtPasswordCredencial
        +textInput txtNombreCompleto
        +textInput txtCorreo
        +selection cmbRolSistema
        +button btnGuardarCuenta
        +button btnCancelar
    }

    IU_UsuariosSeguridad *-- PanelControlUsuarios
    IU_UsuariosSeguridad *-- ModalFormularioUsuario
```

---

## RESUMEN DE COBERTURA UWE EN EL PROYECTO

| N° | Módulo del Sistema | 5.2.1 Modelo Lógico-Conceptual | 5.2.2 Modelo de Navegación | 5.2.3 Modelo de Presentación |
| :---: | :--- | :---: | :---: | :---: |
| **1** | Productos e Inventario | Completado | Completado | Completado |
| **2** | Ventas y Caja (POS) | Completado | Completado | Completado |
| **3** | Compras y Proveedores | Completado | Completado | Completado |
| **4** | Estados Financieros y Contabilidad | Completado | Completado | Completado |
| **5** | Estadística, Reportes y Análisis | Completado | Completado | Completado |
| **6** | Recursos Humanos y Nómina | Completado | Completado | Completado |
| **7** | Portal Web y Catálogo Público | Completado | Completado | Completado |
| **8** | Usuarios y Seguridad | Completado | Completado | Completado |
