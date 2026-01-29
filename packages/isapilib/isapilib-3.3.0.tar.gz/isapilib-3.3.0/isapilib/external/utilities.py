from functools import lru_cache

from django.db import router, connections
from django.db.models import Q

from isapilib.logging import logger


class ExecutionException(Exception):
    def __init__(self, exception, query, params, using):
        self.exception = exception
        self.params = params
        self.query = query
        self.using = using

    def __str__(self):
        return f'{self.using}: \n{self.query} ({self.params})\n{self.exception}'


class ExecutionQuery:
    def __init__(self, using):
        self._alias = using
        self.cursor = connections[using].cursor()

        self._query = None
        self._params = None
        self._log = True

        self.name_normalize = self.__class__.__name__.replace('Execution', '')

    def execute_query(self, query, params):
        try:
            self._query = query
            self._params = params

            if self._log: logger.debug('Execution %s, Query: "%s" %s (%s)', self.name_normalize, query, params,
                                       self._alias)
            self.cursor.execute(query, params)
        except Exception as e:
            raise ExecutionException(e, self._query, self._params, self._alias)

    def get_dataset(self):
        dataset = self.cursor.fetchall()
        return dataset

    def get_results(self):
        try:
            datasets: list = [self.get_dataset()]

            while self.cursor.nextset():
                datasets.append(self.get_dataset())

            if self._log: logger.debug('Results %s, Datasets: %s', self.name_normalize, datasets)
            return datasets
        except Exception as e:
            raise ExecutionException(e, self._query, self._params, self._alias)

    def execute(self, query, params):
        self.execute_query(query, params)
        try:
            return self.get_results()
        except Exception as e:
            if 'Previous SQL was not a query' in str(e):
                if self._log: logger.debug('Results %s, Datasets: %s', self.name_normalize, str(e))
                return None
            raise e

    def wrapper_query(self, query, _):
        return query

    def wrapper_params(self, params):
        if params is None: return []

        if not isinstance(params, list):
            return [params]

        return params

    def __call__(self, query, params=None, log=True):
        self._log = log

        params = self.wrapper_params(params)
        query = self.wrapper_query(query, params)
        return self.execute(query, params)


class ExecutionFunction(ExecutionQuery):
    def wrapper_query(self, function_name, params):
        return f"dbo.[{function_name}]({','.join('%s' for _ in params)})"


class ExecutionScalarFunction(ExecutionFunction):
    def wrapper_query(self, function_name, params):
        function_definition = super().wrapper_query(function_name, params)
        return f'SELECT {function_definition}'

    def get_results(self):
        results = super().get_results()
        return results[0][0][0]


class ExecutionTableFunction(ExecutionFunction):
    def __init__(self, using):
        super().__init__(using)
        self.fields = []

    def wrapper_query(self, function_name, params):
        function_definition = super().wrapper_query(function_name, params)

        fields_string = '*'
        if isinstance(self.fields, list):
            fields_string = ','.join(self.fields)

        return f'''SELECT {fields_string} FROM {function_definition}'''

    def __call__(self, query, params=None, fields=None, *args, **kwargs):
        self.fields = fields
        return super().__call__(query, params, *args, **kwargs)


class ExecutionStoredProcedure(ExecutionQuery):
    def __init__(self, using):
        super().__init__(using)
        self.only_output = True
        self.has_outputs = False

    def get_outputs(self, procedure_name):
        query = (
            "SELECT PARAMETER_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH "
            "FROM information_schema.parameters "
            "WHERE SPECIFIC_NAME = %s AND PARAMETER_MODE = 'INOUT'"
        )
        self.cursor.execute(query, [procedure_name])
        results = self.cursor.fetchall()
        return 0 < len(results), results

    def wrapper_params(self, params):
        if isinstance(params, dict):
            return params

        return super().wrapper_params(params)

    def execute(self, query, params):
        if isinstance(params, dict): params = list(params.values())
        return super().execute(query, params)

    @staticmethod
    def get_parameters(params):
        if isinstance(params, list):
            return ','.join('%s' for _ in params)

        if isinstance(params, dict):
            return ','.join([f'@{i}=%s' for i in params.keys()])

        raise Exception('Invalida params type, excepted (list, dict)')

    def wrapper_query(self, procedure_name, params):
        def get_parameters_definition(name, kind, attr):
            if kind.lower() in ('nvarchar', 'varchar', 'char'):
                length = 'max' if attr == -1 else attr
                kind = f'{kind}({length})'

            return f'{name} {kind}'

        self.has_outputs, outputs = self.get_outputs(procedure_name)

        procedure_params = self.get_parameters(params)
        query = f"EXEC {procedure_name} {procedure_params}"

        if self.has_outputs:
            query = (
                f'''DECLARE {','.join([get_parameters_definition(*output) for output in outputs])}\n'''
                f'''{query}{',' if len(params) > 0 else ''}{','.join([f'{o[0]}={o[0]} OUTPUT' for o in outputs])}\n'''
                f'''SELECT 'OUTPUT',{','.join([o[0] for o in outputs])}'''
            )

        return f'SET NOCOUNT ON\n{query}'

    def get_results(self):
        datasets: list = super().get_results()

        last = datasets[-1]
        for row in last:
            if row[0] == 'OUTPUT':
                results = [row[1:] for row in last]

                if self.has_outputs:
                    datasets[-1] = results

                if self.only_output:
                    return results

        if self.only_output:
            return None

        return datasets

    def __call__(self, query, params=None, only_output=True, *args, **kwargs):
        self.only_output = only_output
        return super().__call__(query, params, *args, **kwargs)


def execute_query(*args, using=None, **kwargs):
    if not using: using = router.db_for_write(None)
    return ExecutionQuery(using)(*args, **kwargs)


def execute_fn(*args, using=None, **kwargs):
    if not using: using = router.db_for_write(None)
    return ExecutionScalarFunction(using)(*args, **kwargs)


def execute_table_fn(*args, using=None, **kwargs):
    if not using: using = router.db_for_write(None)
    return ExecutionTableFunction(using)(*args, **kwargs)


def execute_sp(*args, using=None, **kwargs):
    if not using: using = router.db_for_write(None)
    return ExecutionStoredProcedure(using)(*args, **kwargs)


def get_sucursal(mov='Servicio', sucursal=0):
    from isapilib.models import Sucursal
    if issubclass(type(sucursal), Sucursal): sucursal = getattr(sucursal, 'pk')

    if (mov in ['Venta Perdida', 'Dias', 'Reservar'] or 'Nota' in mov) and sucursal % 2 == 1:
        sucursal -= 1

    if mov in ['Cita Servicio'] and int(sucursal) % 2 == 0:
        sucursal += 1

    return Sucursal.objects.get(pk=sucursal).pk


def get_almacen(mov='Servicio', sucursal=0):
    from isapilib.models import Sucursal, Almacen
    if issubclass(type(sucursal), Sucursal): sucursal = getattr(sucursal, 'pk')

    if (mov in ['Venta Perdida', 'Hist Refacc', 'Reservar'] or 'Nota' in mov) and sucursal % 2 == 1:
        sucursal -= 1
        return Almacen.objects.get(Q(sucursal=sucursal), Q(almacen='R') | Q(almacen__istartswith='RS')).pk
    else:
        return Almacen.objects.get(sucursal=sucursal, almacen__istartswith='S').pk


def get_uen(modulo="VTAS", mov='Servicio', sucursal=0, concepto='Publico', using=None):
    from isapilib.models import Sucursal
    if issubclass(type(sucursal), Sucursal): sucursal = getattr(sucursal, 'pk')
    return execute_fn("fnCA_GeneraUENValida", [modulo, mov, sucursal, concepto], using=using)


def get_param_empresa(interfaz, clave, default=None, using=None):
    from isapilib.models import InterfacesPredefinidasDEmpresa as Data
    if not using: using = router.db_for_write(None)
    valor = Data.objects.using(using).filter(clave=clave, interfaces__interfaz=interfaz).first()
    return getattr(valor, 'valor_default', default)


def get_param_sucursal(sucursal, clave, default=None, using=None):
    from isapilib.models import Sucursal, ParametrosSucursal as Data
    if not using: using = router.db_for_write(None)
    if issubclass(type(sucursal), Sucursal): sucursal = sucursal.pk
    valor = Data.objects.using(using).filter(sucursal=sucursal, clave=clave).first()
    return getattr(valor, 'valor', default)


def verify_col(table, column, using=None) -> bool:
    try:
        query = f"SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table}' AND COLUMN_NAME = '{column}'"
        result = execute_query(query, using)
        exists = result[0][0][0]
        return bool(exists)
    except IndexError:
        return False


@lru_cache
def get_utc_offset(using=None) -> int:
    result = execute_query('SELECT DATEPART(TZOFFSET, SYSDATETIMEOFFSET())', [], using=using)[0][0][0]
    return int(result)
