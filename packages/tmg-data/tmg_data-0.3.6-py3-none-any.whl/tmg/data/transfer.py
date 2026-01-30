import time
import uuid
import os,zipfile
import boto3
import parse
import sys

from google.cloud import bigquery
from google.cloud import storage
from oauth2client.client import GoogleCredentials
from googleapiclient import discovery
from google.api_core import exceptions
from tmg.data import mysql
from tmg.data import ftp
from tmg.data._helper import merge_files,unzip_merge_csv
from tmg.data._helper import clean_mysql_export, get_bq_write_disposition
from tmg.data import logs
from tmg.data import salesforce
from tmg.data import gs
from tmg.data import s3
from tmg.data import bq
from tmg.data.auth import get_credentials


class Client:
    """
    Client to bundle transfers from a source to destination.

    Args:
        project (str): The Project ID for the project which the client acts on behalf of.
        credentials (optional): Google Cloud credentials to use. If not provided, uses default credentials.
    """

    def __init__(self, project, credentials=None):
        self.project = project

        if credentials is None:
            credentials = get_credentials()

        self.credentials = credentials

    def bq_to_gs(self, table, bucket_name, separator=',', print_header=True, compress=False, partition=False, file_type="csv", extend_prefix=None, partition_column=None):
        """Extract BigQuery table into the GoogleStorage.

        Args:
            table (str):  The BigQuery table name. For example: ``my-project-id.you-dataset.my-table`` or ``my-project-id.you-dataset.my-table_<date>`` or ``my-project-id.you-dataset.my-table$<date>``
            bucket_name (str):  The name of the bucket in GoogleStorage.
            separator (:obj:`str`, optional): The separator. Defaults to :data:`,`.
            print_header (:obj:`boolean`, optional):  True to print a header row in the exported data otherwise False. Defaults to :data:`True`.
            compress (:obj:`boolean`, optional): True to apply a GZIP compression. False to export without compression.
            partition (:obj:`boolean`, optional): Whether table to be exported is partitioned, in this case use following table format: ``my-project-id.you-dataset.my-table$<date>``. Defaults to :data:`False`.
            file_type (:obj:`str`, optional): `csv` to export in CSV format. `parquet` or `pq` to export in Parquet format. Defaults to :data:`csv`.
            extend_prefix (:obj:`str`, optional): The prefix to extend the object name in the GoogleStorage. Defaults to :data:`None`. For example: ``my-table`` will be exported as ``my-table/<prefix>/...``.
            partition_column (:obj:`str`, optional): The column the table is partitioned by. Defaults to :data:`None`.

        Returns:
            list: The list of GoogleStorage paths for the uploaded files into the GoogleStorage.
            if the table is big, the exported files will be multiple.

        Examples:
            >>> from tmg.data import transfer
            >>> client = transfer.Client(project='my-project-id')
            >>> client.bq_to_gs('my-project-id.some_dataset.some_table', 'some-bucket-name')
            GS object: some_bucket_name/some_dataset/some_table_000000000000.csv.gzip
        """
        bq_client = bigquery.Client(project=self.project, credentials=self.credentials)

        project, dataset_id, table_id = table.split('.')

        if partition_column not in ("_PARTITIONTIME", None):
            sql_query = f"""
            SELECT * FROM `{project}.{dataset_id}.{table_id.split('$')[0]}`
            WHERE DATE({partition_column}) = DATE('{table_id.split('$')[1]}')
            """

            project_destination = "tmg-pii-dev-179113"
            dataset_destination = "retention_temp_tables"
            table_destination = table_id.replace('$', '_') + "_temp"
            job_config = bigquery.QueryJobConfig(destination=f"{project_destination}.{dataset_destination}.{table_destination}")

            query_job = bq_client.query(sql_query, job_config=job_config)
            query_job.result()

        obj = table.replace(".", "/")
        if partition:
            if extend_prefix:
                obj = obj.split('$')[0] + extend_prefix
            else:
                obj = obj.replace('$', '_')
            if partition_column not in ("_PARTITIONTIME", None):
                table_id = table_destination
                dataset_id = dataset_destination
                project = project_destination
            else:
                table_id = table_id.replace('-', '')
        else:
            if extend_prefix and "shard" in extend_prefix:
                obj = obj[:-8] + "<date>"
                table_id = table_id.replace("-", "")
            if extend_prefix:
                obj += extend_prefix

        if file_type in ['parquet', 'pq']:
            extension = '.parquet'
            destination_format = bigquery.SourceFormat.PARQUET
            delimiter = None
        elif file_type == 'csv':
            extension = '.csv'
            destination_format = bigquery.SourceFormat.CSV
            delimiter = separator
        else:
            raise ValueError('Invalid file type. Please use `csv` or `parquet`')

        if compress:
            extension += '.gz'

        dataset_ref = bigquery.DatasetReference(
            project=project, dataset_id=dataset_id)
        table_ref = bigquery.TableReference(dataset_ref, table_id)


        if extend_prefix:
            gs_url = "gs://{bucket_name}/{obj}/*{extension}".format(
                bucket_name=bucket_name, obj=obj, extension=extension
            )
        else:
            gs_url = "gs://{bucket_name}/{obj}_*{extension}".format(
                bucket_name=bucket_name, obj=obj, extension=extension
            )
        logs.client.logger.info('Extracting from {project}:{dataset_id}.{table_id} to {gs_url}'.format(
            project=project, dataset_id=dataset_id, table_id=table_id, gs_url=gs_url)
        )
        
        extract_job = bq_client.extract_table(
            source=table_ref,
            destination_uris=gs_url,
            job_config=bigquery.ExtractJobConfig(
                field_delimiter=delimiter,
                print_header=print_header,
                destination_format = destination_format,
                compression=bigquery.Compression.GZIP if compress else None
            ),
        )
        extract_job.result()

        if partition_column not in ("_PARTITIONTIME", None):
            logs.client.logger.info(f"Deleting temp table {project}.{dataset_destination}.{table}")
            bq_client.delete_table(f"{project_destination}.{dataset_destination}.{table_destination}")

    def gs_to_bq(self, gs_uris, table, write_preference, auto_detect=True, skip_leading_rows=True, separator=',',
                 schema=(), partition_date=None, partition_field=None, max_bad_records=0, csv=True):
        """Load file from Google Storage into the BigQuery table

        Args:
            gs_uris (Union[str, Sequence[str]]):  The Google Storage uri(s) for the file(s). For example: A single file: ``gs://my_bucket_name/my_filename``, multiple files: ``[gs://my_bucket_name/my_first_file, gs://my_bucket_name/my_second_file]``.
            table (str): The BigQuery table name. For example: ``project.dataset.table``.
            write_preference (str): The option to specify what action to take when you load data from a source file. Value can be on of
                                              ``'empty'``: Writes the data only if the table is empty.
                                              ``'append'``: Appends the data to the end of the table.
                                              ``'truncate'``: Erases all existing data in a table before writing the new data.
            auto_detect (boolean, Optional):  True if the schema should automatically be detected otherwise False. Defaults to :data:`True`.
            skip_leading_rows (boolean, Optional):  True to skip the first row of the file otherwise False. Defaults to :data:`True`.
            separator (str, Optional): The separator. Defaults to :data:`,`
            schema (tuple): The BigQuery table schema. For example: ``(('first_field','STRING'),('second_field', 'STRING'))``
            partition_date (str, Optional): The ingestion date for partitioned BigQuery table. For example: ``20210101``. The partition field name will be __PARTITIONTIME.
            partition_field (str, Optional): The field on which the destination table is partitioned. The field must be a top-level TIMESTAMP or DATE field. Only used if partition_date is not set.
            max_bad_records (int, Optional): The maximum number of rows with errors. Defaults to :data:0
            csv (boolean, Optional): True to load CSV file. False to load Parquet file. Defaults to :data:`True`.

        Examples:
            >>> from tmg.data import transfer
            >>> client = transfer.Client(project='my-project-id')
            >>> client.gs_to_bq(gs_uris='gs://my-bucket-name/my-filename',table='my-project-id.my_dataset.my_table')
        """

        project, dataset_id, table_id = table.split('.')
        dataset_ref = bigquery.DatasetReference(
            project=project, dataset_id=dataset_id)

        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.CSV if csv else bigquery.SourceFormat.PARQUET,
            autodetect=auto_detect,
            field_delimiter=separator,
            write_disposition=get_bq_write_disposition(write_preference),
            allow_quoted_newlines=True,
            max_bad_records=max_bad_records
        )
        if csv:
            job_config.skip_leading_rows = 1 if skip_leading_rows else 0
        if partition_date:
            job_config.time_partitioning = bigquery.TimePartitioning(type_=bigquery.TimePartitioningType.DAY)
            table_id += '${}'.format(partition_date)
        elif partition_field:
            job_config.time_partitioning = bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY, field=partition_field)

        table_ref = bigquery.TableReference(dataset_ref, table_id=table_id)

        bq_client = bq.Client(project)
        try:
            bq_client.create_dataset(dataset_id)
        except exceptions.Conflict:
            logs.client.logger.info(
                'Dataset {} Already exists'.format(dataset_id))

        if schema:
            job_config.schema = [bigquery.SchemaField(
                schema_field[0], schema_field[1]) for schema_field in schema]

        bigquery_client = bigquery.Client(project=self.project, credentials=self.credentials)
        logs.client.logger.info(
            'Loading BigQuery table {} from {}'.format(table, gs_uris))
        job = bigquery_client.load_table_from_uri(
            gs_uris, table_ref, job_config=job_config)

        job.result()

    def bq_to_mysql(self, connection_string, bq_table, mysql_table, mode = 'replace'):
        """Export from BigQuery table to MySQL table

        .. note:: The CloudSQL service account which can be found in Cloud SQL UI
              needs to have a storage object admin access.

        Args:
            connection_string (str): The MySQL connection string. For example: ``{my-username}:{my-password}@{mysql-host}:{mysql-port}/{my-database}``
            bq_table (str): The BigQuery table. For example: ``my-project-id.my-dataset.my-table``
            mysql_table (str):  The MySQL table. For example: ``my-mysql-database.my-table``
            mode (str): Mode to replace/truncate the table.

        Examples:
            >>> from tmg.data import transfer
            >>> client = transfer.Client(project='my-project-id')
            >>> client.bq_to_mysql(
            >>>     connection_string='{my-username}:{my-password}@{mysql-host}:{mysql-port}/{my-database}'
            >>>     bq_table='my-project-id.my-dataset.my-table'
            >>>     mysql_table='my-mysql-database.my-mysql-table'
            >>>     mode='replace'
            >>> )
        """

        # download the files locally
        bq_client = bq.Client(self.project)
        file_names = bq_client.download_table(bq_table, print_header=False)

        # merge the downloaded files
        if len(file_names) > 1:
            logs.client.logger.info('Merging {}'.format(','.join(file_names)))
            output_file_name = merge_files(file_names)
        else:
            output_file_name = file_names[0]

        # upload the merged file into mysql
        database, table = mysql_table.split(".")
        mysql_client = mysql.Client(connection_string)
        mysql_client.upload_table(
            file_path=output_file_name, database=database, table=table, mode=mode)

    def mysql_to_gs(self, instance_name, database, query, gs_uri):
        """Export from MySQL to Google Storage in CSV format

        .. note:: Be aware that the exported CSV file has "N as a field value when there is no value for that field.

        Args:
            instance_name (str): The CloudSQL instance name. It's the instance name in CloudSQL UI but without project.location
            database (str): The MySQL database name
            query (str): The query to get the data from MySQL
            gs_uri (str): The GoogleStorage uri. For example: ``gs://bucket_name/file_name``

        Examples:
            >>> from tmg.data import transfer
            >>> client = transfer.Client(project='my-project-id')
            >>> client.mysql_to_gs(
            >>>     instance_name='{my-mysql-instance-name}',
            >>>     database='my-database',
            >>>     query='SELECT * FROM my-table',
            >>>     gs_uri='gs://my-bucket-name/my-filename'
            >>> )
        """

        # make the discovery service
        credentials = self.credentials
        service = discovery.build(
            'sqladmin', 'v1beta4', credentials=credentials)

        # make the request body
        instances_export_request_body = {
            "exportContext": {
                "fileType": "CSV",
                "uri": gs_uri,
                "databases": [database],
                "csvExportOptions": {
                    "selectQuery": query
                }
            }
        }

        # send the request and get the operation id
        logs.client.logger.info(
            'Exporting from MySQL database {} with query "{}" to {}'.format(database, query, gs_uri))
        request = service.instances().export(
            project=self.project,
            instance=instance_name,
            body=instances_export_request_body
        )
        response = request.execute()
        operation_id = response['name']

        # wait until the job is done
        status = 'PENDING'
        while status in ['PENDING', 'RUNNING']:
            request = service.operations().get(project=self.project, operation=operation_id)
            status = request.execute()['status']
            # Avoid to hammer the APIs (100queries per users every 100seconds is the maximum).
            time.sleep(2)

        if status != 'DONE':
            raise Exception(
                'Failed to export data from MySQL, process status {}'.format(status))

    def mysql_to_bq(self, instance_name, database, query, bq_table, bq_table_schema, write_preference, partition_date=None):
        """Export from MySQL to BigQuery

        Args:
            instance_name (str): The CloudSQL instance name. It's the instance name in CloudSQL UI but without project.location
            database (str):  The MySQL database name
            query (str): The query to get the data from MySQL
            bq_table (str): The BigQuery table. For example: ``my-project-id.my-dataset.my-table``
            bq_table_schema (tuple): The BigQuery table schema. For example: ``(('first_field','STRING'),('second_field', 'STRING'))``
            write_preference (str): The option to specify what action to take when you load data from a source file. Value can be on of
                                              ``'empty'``: Writes the data only if the table is empty.
                                              ``'append'``: Appends the data to the end of the table.
                                              ``'truncate'``: Erases all existing data in a table before writing the new data.
            partition_date (str, Optinal): The ingestion date for partitioned BigQuery table. For example: ``20210101``. The partition field name will be __PARTITIONTIME


        Examples:
            >>> from tmg.data import transfer
            >>> client = transfer.Client(project='my-project-id')
            >>> client.mysql_to_bq(
            >>>     instance_name='{my-mysql-instance-name}',
            >>>     database='my-database',
            >>>     query='SELECT * FROM my-table',
            >>>     bq_table='my-project-id.my-dataset.my-table',
            >>>     bq_table_schema=(('first_field','STRING'),('second_field', 'STRING'))
            >>> )

        """

        # make the temp bucket
        storage_client = storage.Client(project=self.project, credentials=self.credentials)
        tmp_bucket_name = str(uuid.uuid4())
        logs.client.logger.info(
            'Creating the temporary bucket {}'.format(tmp_bucket_name))
        tmp_bucket = storage_client.create_bucket(
            tmp_bucket_name, location='EU')
        tmp_file_name = str(uuid.uuid4())

        # export from mysql to temp bucket
        self.mysql_to_gs(
            instance_name=instance_name,
            database=database,
            query=query,
            gs_uri='gs://{}/{}.csv'.format(tmp_bucket_name, tmp_file_name)
        )

        # download the exported file from the temp bucket into local
        blob = tmp_bucket.blob('{}.csv'.format(tmp_file_name))
        logs.client.logger.info('Downloading {}'.format(blob.name))
        blob.download_to_filename('{}.csv'.format(tmp_file_name))

        # clean the file by replacing ,"N with space
        logs.client.logger.info(
            'Cleaning the exported file {}.csv'.format(tmp_file_name))
        cleaned_file_name = clean_mysql_export('{}.csv'.format(tmp_file_name))

        # upload the cleaned file into BigQuery
        bq_client = bq.Client(project=self.project)
        bq_client.upload_table(
            file_path=cleaned_file_name,
            table=bq_table,
            auto_detect=False,
            schema=bq_table_schema,
            skip_leading_rows=False,
            write_preference=write_preference,
            partition_date=partition_date
        )

        # cleanup
        blob.delete()
        logs.client.logger.info(
            'Deleting temporary bucket {}'.format(tmp_bucket_name))
        tmp_bucket.delete()

    def ftp_to_bq(self, ftp_connection_string, ftp_filepath, bq_table, write_preference, separator=',',
                  skip_leading_rows=True, bq_table_schema=[], partition_date=None):
        """Export from FTP to BigQuery

        Args:
            ftp_connection_string (str): The FTP connection string in the format {username}:{password}@{host}:{port}
            bq_table (str): The BigQuery table. For example: ``my-project-id.my-dataset.my-table``
            write_preference (str): The option to specify what action to take when you load data from a source file. Value can be on of
                                              ``'empty'``: Writes the data only if the table is empty.
                                              ``'append'``: Appends the data to the end of the table.
                                              ``'truncate'``: Erases all existing data in a table before writing the new data.
            ftp_filepath (str): The path to the file to download.
            separator (:obj:`str`, Optional): The separator. Defaults to :data:`,`.
            skip_leading_rows (boolean, Optional):  True to skip the first row of the file otherwise False. Defaults to :data:`True`.
            bq_table_schema (tuple, Optional): The BigQuery table schema. For example: ``(('first_field','STRING'),('second_field','STRING'))``
            partition_date (str, Optional): The ingestion date for partitioned BigQuery table. For example: ``20210101``. The partition field name will be __PARTITIONTIME

        Examples:
            >>> from tmg.data import transfer
            >>> client = transfer.Client(project='my-project-id')
            >>> client.ftp_to_bq(
            >>>     ftp_connection_string='username:password@hots:port',
            >>>     ftp_filepath='/my-path/to-the-ftp-file',
            >>>     bq_table='my-project-id.my-dataset.my-table'
            >>> )

        """

        # download the ftp file
        ftp_client = ftp.Client(connection_string=ftp_connection_string)
        local_file = ftp_client.download_file(ftp_filepath)

        bq_client = bq.Client(project=self.project)

        # adding code to unzip files
        if zipfile.is_zipfile(local_file):
            extract_to_path = os.getcwd() + "/temp_zip/"
            merged_file = unzip_merge_csv(local_file, extract_to_path)

            # upload the ftp files into BigQuery
            bq_client.upload_table(
                file_path=merged_file,
                table=bq_table,
                separator=separator,
                skip_leading_rows=skip_leading_rows,
                write_preference=write_preference,
                schema=bq_table_schema,
                partition_date=partition_date
            )
        else:
            # upload the ftp file into BigQuery
            bq_client.upload_table(
                file_path=local_file,
                table=bq_table,
                separator=separator,
                skip_leading_rows=skip_leading_rows,
                write_preference=write_preference,
                schema=bq_table_schema,
                partition_date=partition_date
            )

    def bq_to_ftp(self, bq_table, ftp_connection_string, ftp_filepath, separator=',', print_header=True):
        """Export from BigQuery to FTP

        Args:
            bq_table (str): The BigQuery table. For example: ``my-project-id.my-dataset.my-table``
            ftp_connection_string (str): The FTP connection string in the format {username}:{password}@{host}:{port}
            ftp_filepath (str): The path to the file to download.
            separator (:obj:`str`, optional): The separator. Defaults to :data:`,`.
            print_header (boolean, Optional):  True to write header for the CSV file, otherwise False. Defaults to :data:`True`.

        Examples:
            >>> from tmg.data import transfer
            >>> client = transfer.Client(project='my-project-id')
            >>> client.bq_to_ftp(
            >>>     bq_table='my-project-id.my-dataset.my-table',
            >>>     ftp_connection_string='username:password@hots:port',
            >>>     ftp_filepath='/my-path/to-the-ftp-file'
            >>> )

        """
        # download the the BigQuery table into local
        bq_client = bq.Client(project=self.project)
        local_files = bq_client.download_table(
            table=bq_table,
            separator=separator,
            print_header=print_header
        )

        # merge the files if they are more than one
        if len(local_files) > 1:
            logs.client.logger.info('Merging {}'.format(','.join(local_files)))
            merged_file = merge_files(local_files)
        else:
            merged_file = local_files[0]

        # upload the merged file
        ftp_client = ftp.Client(connection_string=ftp_connection_string)
        ftp_client.upload_file(local_path=merged_file,
                               remote_path=ftp_filepath)

    def salesforce_to_bq(self, salesforce_connection_string, salesforce_table, salesforce_columns, bq_table, bq_table_schema,
                         write_preference, salesforce_condition=None, salesforce_include_deleted=False,
                         fields_transform=[], partition_date=None):
        """Export from Salesforce to BigQuery

        Args:
            salesforce_connection_string (str): The Salesforce connection string in the format {username}:{password}:{token}@{domain}
                                                Domain should be either ``'login'`` for production server or ``'test'`` for UAT servers
            salesforce_table (str):  Saleforce Table name. For example: ``Account``.
            salesforce_columns (tuple): Salesforce Table columns. For example: ``('Id', 'FirstName', 'LastName')``.
            salesforce_condition (:obj:`str`, Optional): The condition which should apply to the table. For example: ``ModifiedDate > 2020-01-01``. Defaults to :data:`None`
            salesforce_include_deleted (:obj:`boolean`, Optional): Include deleted records in the returned result.
                                                                   IsDeleted field is available for each record. Defaults to :data:`False`

            bq_table (str): The BigQuery table. For example: ``my-project-id.my-dataset.my-table``
            bq_table_schema (tuple): The BigQuery table schema. For example: ``(('first_field','STRING'),('second_field','STRING'))``
            write_preference (str): The option to specify what action to take when you load data from a source file. Value can be on of
                                              ``'empty'``: Writes the data only if the table is empty.
                                              ``'append'``: Appends the data to the end of the table.
                                              ``'truncate'``: Erases all existing data in a table before writing the new data.
            fields_transform(:obj:`list`, Optional): List of transformation functions per field. For example: ``[('FirstName', lambda name: name.lower())]``
            partition_date (str, Optional): The ingestion date for partitioned BigQuery table. For example: ``20210101``. The partition field name will be __PARTITIONTIME

        Examples:
            >>> from tmg.data import transfer
            >>> client = transfer.Client(project='my-project-id')
            >>> client.salesforce_to_bq(
            >>>     salesforce_connection_string='username:password:token@domain',
            >>>     salesforce_table='Account'
            >>>     salesforce_columns=('Id', 'FirstName', 'LastName')
            >>>     bq_table='my-project-id.my-dataset.account'
            >>>     bq_table_schema=(('id','STRING'),('first_name','STRING'),('last_name', 'STRING'))
            >>> )

        """

        # download the Salesforce table into a local file
        salesforce_client = salesforce.Client(
            connection_string=salesforce_connection_string)
        local_file = salesforce_client.download_table(
            table=salesforce_table,
            columns=salesforce_columns,
            condition=salesforce_condition,
            include_deleted=salesforce_include_deleted,
            fields_transform=fields_transform
        )

        # upload the downloaded file into BigQuery
        bq_client = bq.Client(project=self.project)
        bq_client.upload_table(
            file_path=local_file,
            table=bq_table,
            write_preference=write_preference,
            schema=bq_table_schema,
            partition_date=partition_date
        )

    def gs_to_s3(self, gs_uri, s3_connection_string, s3_bucket):
        """
        Exports file from Google storage bucket to S3 bucket

        Args:
        gs_uri (str): Google storage uri path
        s3_connection_string (str): The S3 connection string in the format
                                    {region}:{access_key}:{secret_key}
        s3_bucket (str): s3 bucket name

        Example:
            >>> from tmg.data import transfer
            >>> client = transfer.Client(project='my-project-id')
            >>> client.gs_to_s3(gs_uri='gs://my-bucket-name/my-filename',
            >>>                 s3_connection_string='region:access_key:secret_key',
            >>>                 s3_bucket='bucket_name')
        """

        local_file = os.path.basename(gs_uri)
        gs_client = gs.Client(self.project)
        gs_client.download(gs_uri, local_file)

        s3_client = s3.Client(s3_connection_string)
        s3_client.upload(local_file,
                         s3_bucket)

    def s3_to_gs(self, s3_connection_string, s3_bucket_name,
                 s3_object_name, gs_bucket_name, gs_file_name=None):
        """
        Exports file(s) from S3 bucket to Google storage bucket

        Args:
          s3_connection_string (str): The S3 connection string in the format
                                   {region}:{access_key}:{secret_key}
          s3_bucket_name (str): s3 bucket name
          s3_object_name (str): s3 object name or prefix to match multiple files to copy
          gs_bucket_name (str): Google storage bucket name
          gs_file_name (str): GS file name

        Example:
            >>> from tmg.data import transfer
            >>> client = transfer.Client(project='my-project-id')
            >>> client.s3_to_gs(s3_connection_string='region:access_key:secret_key',
            >>>                 s3_bucket_name='my-s3-bucket_name',
            >>>                 s3_object_name='my-s3-file-prefix',
            >>>                 gs_bucket_name='my-gs-bucket-name',
            >>>                 gs_file_name='gs_file_name')
        """

        parsed_connection = parse.parse(
            '{region}:{access_key}:{secret_key}', s3_connection_string)

        # Retrieve the file(s) from S3 matching to the object
        logs.client.logger.info('Finding files in S3 bucket')
        s3_client = boto3.client('s3',
                                 region_name=parsed_connection['region'],
                                 aws_access_key_id=parsed_connection['access_key'],
                                 aws_secret_access_key=parsed_connection['secret_key'])
        response = s3_client.list_objects_v2(
            Bucket=s3_bucket_name, Prefix=s3_object_name)
        s3_files = []
        for content in response.get('Contents', []):
            s3_files.append(content.get('Key'))
        logs.client.logger.info(f'Found {str(s3_files)} files in S3')

        s3_client = s3.Client(s3_connection_string)
        gs_client = gs.Client(self.project)
        for s3_file in s3_files:
            s3_client.download(s3_bucket_name, s3_file)

            gs_file_name = (gs_file_name if gs_file_name is not None else s3_file) \
                if len(s3_files) == 1 else s3_file
            gs_client.upload(os.path.basename(s3_file),
                             gs_bucket_name, gs_file_name)

    def s3_to_bq(self, s3_connection_string, bucket_name, object_name,
                 bq_table, write_preference, auto_detect=True, separator=',',
                 skip_leading_rows=True, schema=[], partition_date=None):
        """
        Exports S3 file to BigQuery table

        Args:
          s3_connection_string (str): The S3 connection string in the format
                                      {region}:{access_key}:{secret_key}
          bucket_name (str): s3 bucket name
          object_name (str): s3 object name to copy
          bq_table (str): The BigQuery table. For example: ``my-project-id.my-dataset.my-table``
          write_preference (str): The option to specify what action to take when you load data from a source file. Value can be on of
                                            ``'empty'``: Writes the data only if the table is empty.
                                            ``'append'``: Appends the data to the end of the table.
                                            ``'truncate'``: Erases all existing data in a table before writing the new data.
          auto_detect (boolean, Optional):  True if the schema should automatically be detected otherwise False. Defaults to `True`.
          separator (str, optional): The separator. Defaults to `,`.
          skip_leading_rows (boolean, Optional):  True to skip the first row of the file otherwise False. Defaults to `True`.
          schema (list of tuples, optional): The BigQuery table schema. For example: ``[('first_field','STRING'),('second_field', 'STRING')]``
          partition_date (str, Optional): The ingestion date for partitioned BigQuery table. For example: ``20210101``. The partition field name will be __PARTITIONTIME

        Example:
            >>> from tmg.data import transfer
            >>> client = transfer.Client(project='my-project-id')
            >>> client.s3_to_bq(s3_connection_string='region:access_key:secret_key',
            >>>                 bucket_name='my-s3-bucket_name',
            >>>                 object_name='my-s3-object-name',
            >>>                 bq_table='my-project-id.my-dataset.my-table')
        """

        # Download S3 file to local
        s3_client = s3.Client(s3_connection_string)
        s3_client.download(bucket_name, object_name,
                           os.path.join('/tmp/', object_name))

        logs.client.logger.info('Loading S3 file to BigQuery table')
        bq_client = bq.Client(bq_table.split('.')[0])
        bq_client.upload_table(
            file_path=os.path.join('/tmp/', object_name),
            table=bq_table,
            write_preference=write_preference,
            separator=separator,
            auto_detect=auto_detect,
            skip_leading_rows=skip_leading_rows,
            schema=schema,
            partition_date=partition_date
        )
        logs.client.logger.info('Loading completed')

    def bq_to_salesforce(self, query: str, salesforce_connection_string: str, salesforce_table: str,
                         salesforce_bq_mapping: dict, time_field: dict = None) -> str:
        """Export from BigQuery to Salesforce

       Args:
           query (str): The Query to be sent to BigQuery. For example: `` Select * from project.database.table ``
           salesforce_connection_string (str): The Salesforce connection string in the format {username}:{password}:{token}@{domain}
                                               Domain should be either ``'login'`` for production server or ``'test'`` for UAT servers
           salesforce_table (str):  Saleforce Table name. For example: ``Account``.
           salesforce_bq_mapping (dict): Salesforce columns that map to BigQuery fields. For example: ``{'Id': 'id', 'FirstName':'first_name', 'LastName':'last_name'}``
                                           The Salesforce column should be the key and the Big Query field should be the value.
           time_field (:obj:`dict`, optional): Any timefields from BigQuery that will need to be converted to strings.
                                               The field name and desired format must be provided. For example: ``{"DateField": "%Y-%m-%dT%H:%M:%S"}``

       Examples:
           >>> from tmg.data import transfer
           >>> client = transfer.Client(project='my-project-id')
           >>> client.bq_to_salesforce(
           >>>     query='SELECT * FROM TABLE'    
           >>>     salesforce_connection_string='username:password:token@domain',
           >>>     salesforce_table='Account'
           >>>     salesforce_bq_mapping={'Id': 'id', 'FirstName':'first_name', 'LastName':'last_name'}
           >>>     time_fields={"DateField": "%Y-%m-%dT%H:%M:%S"}
           >>> )

        """
        # getting data from bq
        bq_client = bq.Client(project=self.project)
        bq_data = bq_client.run_query(query=query)
        if bq_data.total_rows == 0:
            logs.client.logger.error(
                "No data returned from bq please check your query")
            sys.exit(1)

        # building data list to be send to SF from BQ using field mapping
        sf_fields = salesforce_bq_mapping.keys()
        data = []
        for row in bq_data:
            sf_row = {}
            for field in sf_fields:
                try:
                    sf_row[field] = row[salesforce_bq_mapping[field]]
                    # udating time fields according for the format string
                    if time_field:
                        for tf, fs in time_field.items():
                            if field == tf:
                                sf_row[tf] = sf_row[tf].strftime(
                                    fs)
                except KeyError:
                    logs.client.logger.error(
                        f"Big Query row does not contain field {field}")
                    sys.exit(1)
            data.append(sf_row)
        # to check the data comming out of bq
        for i in range(len(data[:3])):
            logs.client.logger.info(
                f"showing line {i} of bq data \n {data[i]}")
        # sending data to salesforce via tmg salesforce client lib
        sf_client = salesforce.Client(salesforce_connection_string)
        update = sf_client.update_salesforce(salesforce_table, data)

        return update

    def gs_to_external_bq(self,
                          project_id,
                          dataset_id,
                          table_id,
                          table_type,
                          gcs_uri_prefix,
                          gcs_uri
                          ):
        """ Create a Hive partitioned external table in BigQuery.
            Args:
                project_id (str): The GCP project ID.
                dataset_id (str): The BigQuery dataset ID.
                table_id (str): The BigQuery table ID.
                table_type (str): The type of the table. Can be "PARTITIONED", "SHARDED", or "SNAPSHOT".
                gcs_uri_prefix (str): The GCS URI prefix for Hive partitioning.
                gcs_uri (list): List of GCS URIs for the external data.
        """
        # Initialize BigQuery client
        bq_client = bigquery.Client(project=project_id, credentials=self.credentials)

        # Set up external config
        external_config = bigquery.ExternalConfig("PARQUET")
        external_config.source_uris = [gcs_uri]
        external_config.autodetect = True

        # Configure Hive partitioning

        hive_partitioning = bigquery.external_config.HivePartitioningOptions()
        if table_type in ("PARTITIONED", "SHARD"):
            hive_partitioning.require_partition_filter = True
        hive_partitioning.mode = "AUTO"
        hive_partitioning.source_uri_prefix = gcs_uri_prefix

        external_config.hive_partitioning = hive_partitioning
        # Define the table
        table_ref = bigquery.DatasetReference(project_id, dataset_id).table(table_id)
        table = bigquery.Table(table_ref)
        table.external_data_configuration = external_config

        # Ensure dataset exists
        try:
            bq_client.create_dataset(dataset_id)
        except exceptions.Conflict:
            logs.client.logger.info(
                'Dataset {} Already exists'.format(dataset_id))
        # Create or update the table
        table = bq_client.create_table(table, exists_ok=True)
        logs.client.logger.info('Created external table: {}'.format(table.full_table_id))