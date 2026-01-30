import boto3
import os
import time
import csv
import mysql.connector
import pysftp
from google.cloud import bigquery
from google.cloud import storage
from oauth2client.client import GoogleCredentials
from googleapiclient import discovery
from google.cloud import exceptions


class Setup:

    def __init__(self):

        self.project = os.environ.get('PROJECT', None)
        self.dataset_id = os.environ.get('DATASET_ID', None)
        self.table_id = os.environ.get('TABLE_ID', None)
        self.bucket_name = os.environ.get('BUCKET_NAME', None)
        self.bucket_blob_name = os.environ.get('BUCKET_BLOB_NAME', None)
        self.mysql_instance_name = os.environ.get('MYSQL_INSTANCE_NAME', None)
        self.mysql_username = os.environ.get('MYSQL_USERNAME', None)
        self.mysql_password = os.environ.get('MYSQL_PASSWORD', None)
        self.mysql_database = os.environ.get('MYSQL_DATABASE', None)
        self.mysql_ip_address = os.environ.get('MYSQL_IP_ADDRESS', None)
        self.mysql_port = os.environ.get('MYSQL_PORT', None)
        self.ftp_instance_name = os.environ.get('FTP_INSTANCE_NAME', None)
        self.ftp_hostname = os.environ.get('FTP_HOSTNAME', None)
        self.ftp_username = os.environ.get('FTP_USERNAME', None)
        self.ftp_password = os.environ.get('FTP_PASSWORD', None)
        self.ftp_port = int(os.environ.get('FTP_PORT', 0))
        self.zone = os.environ.get('ZONE', None)
        self.s3_region = os.environ.get('S3_REGION', None)
        self.s3_access_key = os.environ.get('S3_ACCESS_KEY', None)
        self.s3_secret_key = os.environ.get('S3_SECRET_KEY', None)
        self.s3_bucket = os.environ.get('S3_BUCKET', None)

    def create_bq_table(self):
        dataset_ref = bigquery.DatasetReference(project=self.project, dataset_id=self.dataset_id)
        table_ref = bigquery.TableReference(dataset_ref, table_id=self.table_id)
        bigquery_client = bigquery.Client(project=self.project)

        try:
            bigquery_client.get_dataset(dataset_ref)
            self.delete_bq_dataset()
        except exceptions.NotFound as error:
            pass
        finally:
            bigquery_client.create_dataset(dataset_ref)

        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.CSV,
            skip_leading_rows=1,
            autodetect=True,
            field_delimiter=','
        )

        with open('tests/data/sample.csv', "rb") as source_file:
            job = bigquery_client.load_table_from_file(source_file, table_ref, job_config=job_config)
        job.result()

    def delete_bq_dataset(self):
        bigquery_client = bigquery.Client(project=self.project)
        bigquery_client.delete_dataset(self.dataset_id, delete_contents=True)

    def create_bucket(self):
        storage_client = storage.Client(project=self.project)

        try:
            storage_client.get_bucket(self.bucket_name)
            self.delete_bucket()
        except exceptions.NotFound:
            pass
        finally:
            bucket = storage_client.create_bucket(self.bucket_name, location='EU')

        blob = bucket.blob(self.bucket_blob_name)
        blob.upload_from_filename('tests/data/sample.csv')

    def delete_bucket(self):

        storage_client = storage.Client(project=self.project)
        bucket = storage_client.get_bucket(self.bucket_name)

        blobs = storage_client.list_blobs(self.bucket_name)
        for blob in blobs:
            blob.delete()

        bucket.delete()

    def create_mysql_instance(self):

        credentials = GoogleCredentials.get_application_default()
        service = discovery.build('sqladmin', 'v1beta4', credentials=credentials)

        # make the request body
        create_request_body = {
            "name": self.mysql_instance_name,
            "region": "europe-west1",
            "settings": {
                "tier": "db-n1-standard-1",
                "backupConfiguration": {
                    "binaryLogEnabled": False,
                    "enabled": False
                },
                "ipConfiguration": {
                    "authorizedNetworks": [
                        {
                            "value": "91.103.133.0/24"
                        },
                        {
                            "value": "91.103.134.0/24"
                        },
                        {
                            "value": "195.162.12.0/23"
                        },
                        {
                            "value": "93.186.36.0/27"
                        },
                    ]

                }
            },
            "rootPassword": self.mysql_password
        }

        # send the request and get the operation id
        request = service.instances().insert(
            project=self.project,
            body=create_request_body
        )
        response = request.execute()
        operation_id = response['name']

        # wait until the job is done
        status = 'PENDING'
        while status in ['PENDING', 'RUNNING']:
            request = service.operations().get(project=self.project, operation=operation_id)
            status = request.execute()['status']
            time.sleep(2)  # Avoid to hammer the APIs (100queries per users every 100seconds is the maximum).

        if status != 'DONE':
            raise Exception('Failed to create CloudSQL instance, process status {}'.format(status))

    def get_mysql_instance(self):

        credentials = GoogleCredentials.get_application_default()
        service = discovery.build('sqladmin', 'v1beta4', credentials=credentials)

        # send the request and get the operation id
        request = service.instances().get(
            project=self.project,
            instance=self.mysql_instance_name
        )

        response = request.execute()
        self.mysql_ip_address = response['ipAddresses'][0]['ipAddress']

    def create_mysql_table(self):

        connection = mysql.connector.connect(
            host=self.mysql_ip_address,
            user=self.mysql_username,
            password=self.mysql_password,
            database=self.mysql_database
        )

        create_table_query = """
            CREATE TABLE actors (
                profile_id int,
                first_name varchar(255),
                last_name varchar(255)
            )
        """

        connection.autocommit = True
        cursor = connection.cursor()
        cursor.execute(create_table_query)

        insert_query = "INSERT INTO actors (profile_id,first_name,last_name) VALUES"

        with open('tests/data/sample.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                insert_query += "({},{},{}),".format(
                    row['profile_id'],
                    "'{}'".format(row['first_name']) if row['first_name'] else 'NULL',
                    "'{}'".format(row['last_name']) if row['last_name'] else 'NULL'
                )

        cursor.execute(insert_query[:-1])

        cursor.close()
        connection.close()

    def delete_mysql_db(self):

        connection = mysql.connector.connect(
            host=self.mysql_ip_address,
            user=self.mysql_username,
            password=self.mysql_password,
        )

        connection.autocommit = True
        cursor = connection.cursor()
        cursor.execute("DROP DATABASE {}".format(self.mysql_database))
        cursor.close()

    def create_mysql_db(self):

        connection = mysql.connector.connect(
            host=self.mysql_ip_address,
            user=self.mysql_username,
            password=self.mysql_password,
        )

        connection.autocommit = True
        cursor = connection.cursor()

        try:
            cursor.execute("CREATE DATABASE {}".format(self.mysql_database))
        except mysql.connector.errors.DatabaseError as error:
            cursor.execute("DROP DATABASE {}".format(self.mysql_database))
            cursor.execute("CREATE DATABASE {}".format(self.mysql_database))

        cursor.close()
        connection.close()

    def wait_for_operation(self, compute_client, operation):
        while True:
            result = compute_client.zoneOperations().get(
                project=self.project,
                zone=self.zone,
                operation=operation).execute()

            if result['status'] == 'DONE':
                if 'error' in result:
                    raise Exception(result['error'])
                return result

            time.sleep(1)

    def start_sftp_instance(self):

        compute = discovery.build('compute', 'v1')
        operation = compute.instances().start(
            project=self.project,
            zone=self.zone,
            instance=self.ftp_instance_name
        ).execute()
        self.wait_for_operation(compute, operation['name'])
        self.wait_for_instance_startup(compute)
        self.set_sftp_instance_address()

    def wait_for_instance_startup(self, compute_connection):

        status = ''
        while status != 'RUNNING':
            status = compute_connection.instances().get(
                project=self.project,
                zone=self.zone,
                instance=self.ftp_instance_name
            ).execute()['status']

    def set_sftp_instance_address(self):

        compute = discovery.build('compute', 'v1')
        instance_details = compute.instances().get(project='tmg-plat-dev', zone='europe-west2-c', instance='library-sftp-tests-instance').execute()
        try:
            self.ftp_hostname = instance_details['networkInterfaces'][0]['accessConfigs'][0]['natIP']
        except IndexError as e:
            print("failed lookup of sftp test instance address")
            raise e
        except KeyError as e:
            print("failed lookup of sftp test instance address")
            raise e

    def upload_ftp_files(self):
        needed_remote_files = [
            "list_sample1.csv",
            "list_sample2.csv",
            "list_sample3.csv",
            "test_dir/test_subdir/list_sample1.csv",
            "test_dir/test_subdir/list_sample2.csv",
            "test_dir/test_subdir/list_sample3.csv",
            "test_dir/download_sample.csv",
            "test_dir/permission_change.csv",
            "test_dir/permission_change2.csv",
            "test_dir/delete_sample.csv"
        ]

        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None

        connection = pysftp.Connection(
            host=self.ftp_hostname,
            username=self.ftp_username,
            password=self.ftp_password,
            port=self.ftp_port,
            cnopts=cnopts
        )

        connection.makedirs("test_dir/test_subdir")

        for file in needed_remote_files:
            if not connection.exists(file):
                connection.put('tests/data/sample.csv', file)

    def remove_ftp_files(self):
        unwanted_remote_files = [
            "sample.csv",
            "test_dir/sample.csv",
            "test_dir/test_subdir/rename_sample.csv",
            "test_dir/bq_to_ftp_test_sample.csv"
        ]

        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None

        connection = pysftp.Connection(
            host=self.ftp_hostname,
            username=self.ftp_username,
            password=self.ftp_password,
            port=self.ftp_port,
            cnopts=cnopts
        )

        for file in unwanted_remote_files:
            if connection.exists(file):
                connection.remove(file)

        unwanted_local_files = [
            "download_sample.csv",
            "tests/data/download_sample.csv",
            "tests/data/rename_sample.csv",
            "tests/data/download_sample.csv",
            "tests/data/bq_to_ftp_test_sample.csv"
        ]

        for file in unwanted_local_files:
            if os.path.exists(file):
                os.remove(file)

    def stop_sftp_instance(self):

        compute = discovery.build('compute', 'v1')
        operation = compute.instances().stop(
            project=self.project,
            zone=self.zone,
            instance=self.ftp_instance_name
        ).execute()
        self.wait_for_operation(compute, operation['name'])

    def upload_s3_files(self):
        s3_client = boto3.resource(service_name='s3',
                                   region_name=self.s3_region,
                                   aws_access_key_id=self.s3_access_key,
                                   aws_secret_access_key=self.s3_secret_key)
        bucket = s3_client.Bucket('tmg-datateam-test-bucket')
        bucket.upload_file('tests/data/sample.csv', 'download_sample.csv')

    def remove_s3_files(self):
        s3_client = boto3.resource(service_name='s3',
                                   region_name=self.s3_region,
                                   aws_access_key_id=self.s3_access_key,
                                   aws_secret_access_key=self.s3_secret_key)

        s3_client.Bucket(self.s3_bucket).Object('sample.csv').delete()
        s3_client.Bucket(self.s3_bucket).Object('schema.csv').delete()
        s3_client.Bucket(self.s3_bucket).Object('s3_upload_file.csv').delete()


setup = Setup()
