from pathlib import Path
import __main__
from hdbcli import dbapi
from configparser import ConfigParser
from polars import read_database

class QueryLoader:

    def __init__(self):
        
        configFilepath = list(Path(__main__.__file__).parent.rglob("*.ini"))
        if len(configFilepath) > 0:
            self.config = ConfigParser()
            self.config.read(configFilepath[0])
        else:
            raise Exception("File .ini not found!")
        self.connect()
        
    def connect(self):

        try:
            self.conn = dbapi.connect(
                address=self.config["credentials"]["HOST"], 
                port=self.config["credentials"]["PORT"], 
                user=self.config["credentials"]["USERNAME"], 
                password=self.config["credentials"]["PASSWD"],
                sslValidateCertificate=self.config["credentials"]["SSL_CERTIFICATE"],
                proxyHttp = self.config["credentials"]["PROXY_HTTP"],
                proxy_host = self.config["credentials"]["PROXY_HOST"],
                proxy_port = self.config["credentials"]["PROXY_PORT"],
                proxy_userid = self.config["credentials"]["PROXY_USERID"],
                proxy_password = self.config["credentials"]["PROXY_PASSWD"]
            )
            print("Conexão estabelecida com sucesso!")
            return True
        except Exception as exc:
            print("Conexão falhou...")
            exit(1)

    def search(self, query: str):
        
        query = """
            SELECT *
            FROM S10606."Relatorio_Cobranca"
            WHERE "Data Faturamento" BETWEEN '202501' AND '202512'
        """
        data = read_database(query, self.conn)
        return data