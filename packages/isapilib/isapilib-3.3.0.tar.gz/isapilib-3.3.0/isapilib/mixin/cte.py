from isapilib.core.utilities import get_default_user
from isapilib.external.utilities import execute_sp
from isapilib.logging import logger


class CteMixin:
    def new_cte(self):
        usuario = get_default_user()

        self.cliente = execute_sp('spConsecutivo', ['CTE', 0])[0]
        self.colonia = 'NA'
        self.rfc = 'XAXX010101000'
        self.direccion = 'NA'
        self.direccion_numero = '1'
        self.tipo = 'Cliente'
        self.estado = 'NA'
        self.pais = 'NA'
        self.estatus = 'ALTA'
        self.usuario = usuario

        logger.debug("Create a new client %s", self.cliente)
