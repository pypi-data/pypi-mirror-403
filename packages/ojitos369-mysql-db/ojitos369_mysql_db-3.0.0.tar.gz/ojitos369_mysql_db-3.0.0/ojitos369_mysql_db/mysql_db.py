import math
from ojitos369.utils import print_line_center as plc
import mysql.connector
import pandas as pd

class ConexionMySQL:
    def __init__(self, db_data, **kwargs):
        host = db_data["host"]
        user = db_data["user"]
        password = db_data["password"]
        database = db_data.get("database", None) or db_data.get("name", None)
        port = int(db_data.get("port", 3306))
        
        self.db_data = {
            "host": host,
            "user": user,
            "password": password,
            "database": database,
            "port": port,
        }
        
        # Connect using mysql-connector-python
        db_conn = mysql.connector.connect(**self.db_data)
        
        self.cursor = db_conn.cursor()
        self.db_conn = db_conn

        self.ce = None
        self.send_error = False
        self.raise_error = False
        self.closed = False
        self.mode = "pd"

        for k in kwargs:
            setattr(self, k, kwargs[k])
    
    def local_base(func):
        def wrapper(*args, **kwargs):
            ele = args[0]
            try:
                return func(*args, **kwargs)
            except Exception as e:
                ele.rollback()
                query = ele.query if hasattr(ele, "query") else ""
                params = ele.params if hasattr(ele, "params") else {}
                ce = ele.ce if hasattr(ele, "ce") else None
                send_error = ele.send_error if hasattr(ele, "send_error") else False
                raise_error = ele.raise_error if hasattr(ele, "raise_error") else False
                
                if ce:
                    ex = Exception(f"{plc(query)}{plc(params)}{plc(str(e))}")
                    error = ce.show_error(ex, send_email=send_error)
                    print(error)
                if raise_error:
                    raise e
                else:
                    return False
        return wrapper

    @local_base
    def consulta(self, query, params=None):
        self.query = query
        self.params = self.validate_params(params)
        if self.params:
            self.cursor.execute(query, self.params)
        else:
            self.cursor.execute(query)
        r = self.cursor.fetchall()
        if self.mode == "pd":
            return pd.DataFrame(r)
        else:
            return r

    @local_base
    def ejecutar_funcion(self, query, params=None):
        self.query = query
        self.params = self.validate_params(params)
        self.cursor.callproc(query, self.params)
        return True

    @local_base
    def consulta_asociativa(self, query, params=None):
        self.query = query
        self.params = self.validate_params(params)
        if self.params:
            self.cursor.execute(query, self.params)
        else:
            self.cursor.execute(query)
        
        descripcion = [d[0].lower() for d in self.cursor.description]
        if self.mode == "pd":
            r = pd.DataFrame(self.cursor.fetchall(), columns=descripcion)
            return r
        else:
            resultado = [dict(zip(descripcion, linea)) for linea in self.cursor.fetchall()]
            return resultado

    @local_base
    def ejecutar(self, query, params=None):
        self.query = query
        self.params = self.validate_params(params)
        if not self.params:
            self.cursor.execute(self.query)
            return True
        else:
            if type(self.params) in (dict, list, tuple, set):
                self.cursor.execute(self.query, self.params)
            else:
                raise Exception("Parametros: tipo no valido")
            return True
    
    @local_base
    def ejecutar_multiple(self, query, params):
        self.query = query
        self.params = self.validate_params(params)

        if type(self.params) in (list, tuple):
            self.cursor.executemany(self.query, self.params)
            return True
        elif type(self.params) == dict:
            raise Exception("Para ejecutar un solo registro usar la funcion ejecutar")
        else:
            raise Exception("Tipo de parametro no valido")

    @local_base
    def paginador(self, query, registros_pagina=10, pagina=1, params=None, totales=None):
        self.query = query
        self.params = self.validate_params(params)
        
        if totales is None:
            if self.params:
                num_registros = len(self.consulta_asociativa(query, self.params))
            else:
                num_registros = len(self.consulta_asociativa(query))
        else:
            num_registros = totales
            
        paginas = math.ceil(num_registros / registros_pagina)
        if paginas < pagina: pagina = paginas
        limite_superior = registros_pagina * pagina
        limite_inferior = limite_superior - registros_pagina

        query = """ SELECT *
                    FROM ({0}) A
                    LIMIT {1}, {2}
                """.format(query, limite_inferior, registros_pagina)
        self.query = query
        self.params = self.validate_params(params)
        if self.params:
            registros = self.consulta_asociativa(query, self.params)
        else:
            registros = self.consulta_asociativa(query)

        if num_registros < registros_pagina:
            pagina = 1
        return {
            "registros": registros,
            "num_registros": num_registros,
            "paginas": paginas,
            "pagina": pagina,
        }

    @local_base
    def commit(self):
        self.db_conn.commit()
        return True

    @local_base
    def validate_params(self, params):
        if type(params) == pd.DataFrame:
            return params.to_dict(orient="records")
        elif not params:
            return params
        if type(params) in (dict, set, list, tuple):
            return params
        elif type(params) == pd.Series:
            return params.to_dict()
        else:
            raise Exception("Tipo de parametro no valido")
            
    def consulta_chunks(self, query, params=None, chunk_size=10000):
        # Create a separate connection for chunks to avoid cursor interference
        conn_lotes = mysql.connector.connect(**self.db_data)
        try:
            cursor_lotes = conn_lotes.cursor(dictionary=True)
            self.query = query
            self.params = self.validate_params(params)
            if self.params:
                cursor_lotes.execute(query, self.params)
            else:
                cursor_lotes.execute(query)
            
            while True:
                registros = cursor_lotes.fetchmany(chunk_size)
                if not registros:
                    break
                
                descripcion = [d[0].lower() for d in cursor_lotes.description]
                if self.mode == "pd":
                    # Convert list of dicts to DataFrame
                    yield pd.DataFrame(registros)
                else:
                    yield registros
        finally:
            conn_lotes.close()

    def rollback(self):
        self.db_conn.rollback()
        return True
    
    def close(self):
        if not self.closed:
            self.cursor.close()
            self.db_conn.close()
            self.closed = True
        return True
    
    def set_ce(self, ce):
        self.ce = ce
        return True

    def set_envio_errores(self, send_error):
        self.send_error = send_error
        return True

    def set_raise_error(self, raise_error):
        self.raise_error = raise_error
        return True

    def activar_envio_errores(self):
        self.send_error = True
        return True

    def activar_raise_error(self):
        self.raise_error = True
        return True

    def desactivar_envio_errores(self):
        self.send_error = False
        return True

    def desactivar_raise_error(self):
        self.raise_error = False
        return True

    def __del__(self):
        try:
            self.close()
        except:
            pass
        return True

# Required pips:
# pip install mysql-connector-python pandas
