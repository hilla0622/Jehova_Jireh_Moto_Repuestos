from datetime import date
from decimal import Decimal
import unittest
from unittest.mock import MagicMock
from seed_negocio import Carga, dinero, jornada_comercial


class CargaNegocioTests(unittest.TestCase):
    def carga(self, movimientos):
        c=object.__new__(Carga);c.cur=MagicMock();c.cur.fetchall.return_value=movimientos
        c.cuentas={'1.1.02':2};c.inicio=date(2024,1,1);c.fin=date(2026,11,2)
        c.asiento=MagicMock();return c

    def test_capital_cubre_necesidad_historica_no_solo_saldo_final(self):
        c=self.carga([('2024-01-01',Decimal('100000')),
            ('2026-07-13',Decimal('-369302.59')),('2026-11-02',Decimal('140766.45'))])
        c.asegurar_liquidez(aporte_confirmado=Decimal(300000))
        self.assertEqual(c.financiacion['aporte_adicional'],'300000')
        self.assertEqual(c.financiacion['minimo_bancario_posterior'],'30697.41')
        lineas=c.asiento.call_args.args[2]
        self.assertEqual(sum(d for _,d,_ in lineas),sum(h for _,_,h in lineas))

    def test_capital_suficiente_no_genera_otro_aporte(self):
        c=self.carga([('2024-01-01',Decimal(80000)),('2024-01-02',Decimal(-40000))])
        c.asegurar_liquidez();c.asiento.assert_not_called()
        self.assertEqual(c.financiacion['aporte_adicional'],'0')

    def test_no_aplica_un_importe_distinto_del_autorizado(self):
        c=self.carga([('2024-01-01',Decimal(-500000))])
        with self.assertRaises(ValueError):c.asegurar_liquidez(aporte_confirmado=Decimal(300000))
        c.asiento.assert_not_called()

    def test_centavos_y_cierres_de_negocio(self):
        self.assertEqual(dinero('123.455'),Decimal('123.46'))
        self.assertFalse(jornada_comercial(date(2026,11,1)))
        self.assertFalse(jornada_comercial(date(2025,12,25)))
        self.assertTrue(jornada_comercial(date(2026,11,2)))


if __name__=='__main__':unittest.main()
