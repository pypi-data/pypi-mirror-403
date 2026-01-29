from .exceptions import DescuentoInvalidoError

class Descuentos:
    def __init__(self, porcentaje):
        if not (0<= porcentaje <= 1):
            raise DescuentoInvalidoError("Porcentaje debe ser entre 0 y 1")
        self.porcentaje = porcentaje

    def aplicar_descuentos(self,precio):
        return precio * self.porcentaje