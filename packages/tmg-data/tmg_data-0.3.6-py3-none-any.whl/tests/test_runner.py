import unittest
import csv
import time
import mysql.connector
from google.cloud import bigquery
from google.cloud import storage

from tests.setup import setup
from tmg.data import runner, transfer


def setUpModule():
    setup.create_bq_table()
    setup.create_bucket()
    setup.create_mysql_db()
    setup.create_mysql_table()


def tearDownModule():
    setup.delete_bq_dataset()
    setup.delete_bucket()
    setup.delete_mysql_db()


class TestRunner(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestRunner, self).__init__(*args, **kwargs)
        self.setup = setup

    def test_add(self):

        def test(a, b, c=1):
            pass

        parallel_runner = runner.ParallelRunner()
        parallel_runner.add("test1", test, "a", "b", c=2)

        name, function, args, kwargs = parallel_runner.processes[0]

        self.assertEqual(function.__name__, "test")
        self.assertEqual(args, ["a", "b"])
        self.assertDictEqual(kwargs, {"c": 2})

    def test_run(self):

        def test_function(run_name, sleep_length=5):
            print(f"starting run {run_name}")
            time.sleep(sleep_length)
            print(f"finished run {run_name}")

        parallel_runner = runner.ParallelRunner()
        parallel_runner.add("test1", test_function, "run_1")
        parallel_runner.add("test2", test_function, "run_2", sleep_length=10)

        parallel_runner.run(wait_for_result=True)

    def test_run_integration(self):

        parallel_runner = runner.ParallelRunner()

        # First transfer
        bq_gs_client = transfer.Client(project=self.setup.project)
        parallel_runner.add(
            "bq_to_gs",
            bq_gs_client.bq_to_gs,
            table='{}.{}.{}'.format(self.setup.project, self.setup.dataset_id, 'actors'),
            bucket_name=self.setup.bucket_name
        )

        # Second Transfer
        mysql_bq_client = transfer.Client(project=self.setup.project)
        parallel_runner.add(
            "mysql_to_bq",
            mysql_bq_client.mysql_to_bq,
            instance_name=self.setup.mysql_instance_name,
            database=self.setup.mysql_database,
            query='SELECT * from actors',
            bq_table='{}.{}.{}'.format(self.setup.project, self.setup.dataset_id, 'actors_from_mysql'),
            bq_table_schema=(('profile_id', 'STRING'), ('first_name', 'STRING'), ('last_name', 'STRING')),
            write_preference='truncate'
        )

        # Run both transfers in parallel
        results = parallel_runner.run(wait_for_result=True)
        file_names = results[0]

        ### Getting results of first transfer
        # creating list based on source big query table values
        bq_gs_bq_keys = []
        bq_gs_bigquery_client = bigquery.Client(project=self.setup.project)
        job = bq_gs_bigquery_client.query(
            'SELECT profile_id, first_name, last_name from {}.{}'.format(
                self.setup.dataset_id,
                'actors'
            )
        )
        for row in job.result():
            bq_gs_bq_keys.append('{}{}{}'.format(
                row.profile_id,
                '' if row.first_name is None else row.first_name,
                '' if row.last_name is None else row.last_name,
            ))

        # creating list based on destination bucket file values
        bq_gs_storage_client = storage.Client(project=self.setup.project)
        with open('actors.csv', 'wb') as file_obj:
            bq_gs_storage_client.download_blob_to_file(blob_or_uri=file_names[0], file_obj=file_obj)

        with open('actors.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            bq_gs_storage_keys = []
            for row in reader:
                bq_gs_storage_keys.append(
                    str(row['profile_id']) + row['first_name'] + row['last_name']
                )

        ###Getting results based on second transfer
        # creating list based on source mysql table values
        connection = mysql.connector.connect(
            host=self.setup.mysql_ip_address,
            user=self.setup.mysql_username,
            password=self.setup.mysql_password,
            database=self.setup.mysql_database
        )
        cursor = connection.cursor()
        cursor.execute('SELECT profile_id, first_name, last_name from actors')
        mysql_bq_mysql_keys = []
        for row in cursor.fetchall():
            mysql_bq_mysql_keys.append('{}{}{}'.format(
                row[0],
                'NULL' if row[1] is None else row[1],
                'NULL' if row[2] is None else row[2]
            ))
        cursor.close()
        connection.close()

        # creating list based on destination bucket values
        mysql_bq_bq_keys = []
        mysql_bq_bigquery_client = bigquery.Client(project=self.setup.project)
        job = mysql_bq_bigquery_client.query(
            'SELECT profile_id, first_name, last_name from {}.{}'.format(
                self.setup.dataset_id,
                'actors_from_mysql'
            )
        )
        for row in job.result():
            mysql_bq_bq_keys.append(
                str(row.profile_id) +
                ('NULL' if row.first_name is None else row.first_name) +
                ('NULL' if row.last_name is None else row.last_name)
            )

        self.assertListEqual(mysql_bq_mysql_keys, mysql_bq_bq_keys)

