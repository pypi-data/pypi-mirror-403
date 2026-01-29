import unittest
from aplicacion_ventas.aplicacion_ventas.gestor_ventas import GestorVentas
from aplicacion_ventas.aplicacion_ventas.exceptions import ImpuestoInvalidoError, DescuentoInvalidoError

class TestGestorVentas(unittest.TestCase):

    def test_calculo_precio_final(self):
        gestor=GestorVentas(100,0.05,0.1)
        self.assertEqual(gestor.calcular_precio_final(),95.0)

    def test_impuesto_invalido(self):
        with self.assertRaises(ImpuestoInvalidoError):
            GestorVentas(100,1.5,0.1)

    def test_descuento_invalido(self):
        with self.assertRaises(DescuentoInvalidoError):
            GestorVentas(100,0.5,1.5)


if __name__ == '__main__':
    unittest.main()