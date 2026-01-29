from .exceptions import ImpuestoInvalidoError


class Impuestos:
    def __init__(self, porcentaje):
        if not (0 <= porcentaje <= 1):
            raise ImpuestoInvalidoError("Tasa de impuesto entre 0 y 1")
        self.porcentaje = porcentaje

    def aplicar_impuesto(self, precio):
            return precio * self.porcentaje
