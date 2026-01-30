import unittest
import csv
from mysql import connector

from tmg.data import mysql
from tests.setup import setup


def setUpModule():
    setup.create_mysql_db()
    setup.create_mysql_table()


def tearDownModule():
    setup.delete_mysql_db()


class TestMySQL(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestMySQL, self).__init__(*args, **kwargs)
        self.setup = setup

    def test_upload_table(self):

        # create uploaded_actors MySQL table
        connection = connector.connect(
            host=self.setup.mysql_ip_address,
            port=self.setup.mysql_port,
            user=self.setup.mysql_username,
            password=self.setup.mysql_password,
            database=self.setup.mysql_database
        )
        create_table_query = """
            CREATE TABLE uploaded_actors (
                profile_id int,
                first_name varchar(255),
                last_name varchar(255)
            )
        """
        connection.autocommit = True
        cursor = connection.cursor()
        cursor.execute(create_table_query)

        # remove the first row from sample file to make it ready to upload to MySQL
        with open('tests/data/sample.csv') as input_file_obj:
            with open('sample_to_load_to_mysql.csv', 'w+') as output_file_obj:
                first_row = True
                for line in input_file_obj:
                    if first_row:
                        first_row = False
                        continue
                    else:
                        output_file_obj.write(line)

        # run upload
        mysql_client = mysql.Client(
            connection_string='{username}:{password}@{host}:{port}/{database}'.format(
                username=self.setup.mysql_username,
                password=self.setup.mysql_password,
                host=self.setup.mysql_ip_address,
                port=self.setup.mysql_port,
                database=self.setup.mysql_database
            )
        )
        mysql_client.upload_table(
            file_path='sample_to_load_to_mysql.csv',
            database=self.setup.mysql_database,
            table='uploaded_actors'
        )

        # creating list based on destination bucket file values
        with open('tests/data/sample.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            storage_keys = []
            for row in reader:
                storage_keys.append('{}{}{}'.format(
                    row['profile_id'],
                    row['first_name'] if row['first_name'] else 'NULL',
                    row['last_name'] if row['last_name'] else 'NULL'
                ))

        # creating list based on mysql uploaded table values
        cursor.execute('SELECT profile_id, first_name, last_name from uploaded_actors')
        mysql_keys = []
        for row in cursor.fetchall():
            last_row_element = row[2]
            if last_row_element is not None:
                last_row_element = last_row_element.replace("\r", "")
            mysql_keys.append('{}{}{}'.format(
                row[0],
                'NULL' if row[1] is None else row[1],
                'NULL' if last_row_element is None or last_row_element=='' else last_row_element
            ))
        cursor.close()
        connection.close()

        self.assertEqual(storage_keys, mysql_keys)
