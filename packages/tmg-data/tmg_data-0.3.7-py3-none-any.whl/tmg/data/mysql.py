import parse
from collections import OrderedDict
import mysql.connector
from jinja2 import Template
from tmg.data import logs
from urllib.parse import urlparse

class Client:
    """
    Client to bundle MySQL functions.

    Args:
        connection_string (str): The MySQL connection string. For example: ``{my-username}:{my-password}@{mysql-host}:{mysql-port}/{my-database}``

    """

    def __init__(self, connection_string):

        if not connection_string.startswith("//"):
            connection_string = "//" + connection_string

        parsed_connection = urlparse(connection_string)

        self.connection = mysql.connector.connect(
            host=parsed_connection.hostname,
            port=parsed_connection.port,
            user=parsed_connection.username,
            password=parsed_connection.password,
            database=parsed_connection.path[1:]
        )

    def get_table_schema(self, database, table):
        """ Get the table schema from MySQL database

        Args:
            database (str): The Database name
            table (str): The Table name

        Returns:
            dict: Schema. For example: ``{column_name: {'type':'some_type', 'default':'some_default_value'}}``
        """

        cursor = self.connection.cursor()
        logs.client.logger.info('Getting Columns from MySQL table {}.{}'.format(database, table))
        cursor.execute("SHOW columns from `{database}`.`{table}`".format(
            database=database, table=table
        ))

        fields = OrderedDict({
            column[0]: {"type": column[1], "default": column[4]} for column in cursor.fetchall()
        })

        cursor.close()

        return fields

    def upload_table(self, file_path, database, table, mode = 'replace'):
        """Upload CSV file to MySQL from local path

        Args:
            file_path (str): The CSV file local path
            database (str): The database name
            table (str): The table name
            mode (str): Mode to replace/truncate the table.
        """
        
        cursor = self.connection.cursor()
        if mode == 'truncate':
            logs.client.logger.info(f'Truncating MySQL {database}.{table} table.')
            query = f"TRUNCATE TABLE {database}.{table};"
            cursor.execute(query)

            logs.client.logger.info(f'Table Truncate Complete.')
        
        # get table schema
        fields = self.get_table_schema(database, table)

        # make the load infile query
        load_data_infile_query = Template("""
            LOAD DATA LOCAL infile '{{ file_path }}'
            REPLACE
            INTO TABLE `{{database}}`.`{{table}}`
            CHARACTER SET 'utf8mb4'
            FIELDS TERMINATED BY ','
            OPTIONALLY ENCLOSED BY '\"'
            ESCAPED BY '\"'
            (
            {% for field in fields %}
                @{{field}}
                {% if not loop.last %}, {% endif %}
            {% endfor %}
            )
            SET
            {% for field in fields %}
            {{ field }} = nullif(@{{field}}, '')
            {% if not loop.last %},{% endif %}
            {% endfor %}
            ;
        """).render(file_path=file_path, database=database, table=table, fields=fields)

        logs.client.logger.info('Loading to MySQL table {}.{} from file {}'.format(database, table, file_path))

        cursor.execute("ALTER TABLE `{}`.`{}` DISABLE KEYS;".format(database, table))
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        cursor.execute("SET UNIQUE_CHECKS = 0;")
        cursor.execute(load_data_infile_query)
        cursor.execute("SET UNIQUE_CHECKS = 1;")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        cursor.execute("ALTER TABLE `{}`.`{}` ENABLE KEYS;".format(database, table))

        cursor.close()