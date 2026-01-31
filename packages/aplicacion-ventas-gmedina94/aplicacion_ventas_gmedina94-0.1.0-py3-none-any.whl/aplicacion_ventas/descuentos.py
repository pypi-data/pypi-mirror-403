from .exceptions import DescuentoInvalidoError
class Descuentos:
    def __init__(self,porcentaje):
        if not (0<= porcentaje <= 1):
            raise DescuentoInvalidoError("El porcentaje de descuento debe estar entre cero y uno")
        self.porcentaje = porcentaje
    
    def aplicar_descuento(self, precio):
        return precio * self.porcentaje