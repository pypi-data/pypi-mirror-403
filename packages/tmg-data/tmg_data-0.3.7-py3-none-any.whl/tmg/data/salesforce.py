import parse
import csv
import os
import sys
from time import sleep

from simple_salesforce import Salesforce, exceptions
from tmg.data import logs


class Client:
    """
    Client to bundle Salesforce functionality.

    Args:
        connection_string (str): The Salesforce connection string in the format {username}:{password}:{token}@{domain}
                                 Domain should be either ``'login'`` for production server or ``'test'`` for UAT servers

    """

    MAX_RETRIES = 10
    WAIT_BETWEEN_RETRY = 10

    def __init__(self, connection_string):

        parsed_connection = parse.parse(
            '{username}:{password}:{token}@{domain}', connection_string)
        try_count = 0
        while True:
            try:
                self.sf = Salesforce(
                    username=parsed_connection['username'],
                    password=parsed_connection['password'],
                    security_token=parsed_connection['token'],
                    domain=parsed_connection['domain']
                )
                break
            except exceptions.SalesforceAuthenticationFailed as e:

                if try_count == self.MAX_RETRIES:
                        raise Exception(
                            "Connection to Salesforce failed. Reached maximum number of retries.")

                logs.client.logger.warning(
                    "Connection to Salesforce failed with this message: {message}."
                    "Sleeping for {wait_time} seconds before next try".format(
                        message=e,
                        wait_time=self.WAIT_BETWEEN_RETRY
                    )
                )

                sleep(self.WAIT_BETWEEN_RETRY)
                try_count += 1
        self.domain = parsed_connection['domain']

    def run_query(self, query, include_deleted=False):
        """Run the query on Salesforce server and return the result

        Args:
            query (str): The query string.
            include_deleted (:obj:`boolean`, Optional): Include deleted records in the returned result.
                                                        IsDeleted field is available for each record. Defaults to :data:`False`
        Returns:
            The query results

        """

        logs.client.logger.info(
            'Running query on Salesforce: {}'.format(query))
        return self.sf.query_all_iter(query, include_deleted=include_deleted)

    def download_table(self, table, columns, condition=None, include_deleted=False, local_folder='.', separator=',',
                       print_header=True, fields_transform=[]):
        """
        Export the table to the local file in CSV format.

        Args:
            table (str):  Table name. For example: ``Account``.
            columns (tuple): Table columns. For example: ``('Id', 'FirstName', 'LastName')``.
            condition (:obj:`str`, Optional): The condition which should apply to the table. For example: ``ModifiedDate > 2020-01-01``. Defaults to :data:`None`
            include_deleted (:obj:`boolean`, Optional): Include deleted records in the returned result.
                                                        IsDeleted field is available for each record. Defaults to :data:`False`
            local_folder (:obj:`str`, Optional):  The local folder with out the slash at end. For example: ``/some_path/some_inside_path``. Defaults to current path :data:`.`
            separator (:obj:`str`, Optional): The separator. Defaults to :data:`,`
            print_header (:obj:`boolean`, Optional):  True to print a header row in the exported file otherwise False. Defaults to :data:`True`.
            fields_transform(:obj:`list`, Optional): List of transformation functions per field. For example: ``[('FirstName', lambda name: name.lower())]``

        Returns:
            str: The output file path

        Examples:
            >>> from tmg.data import salesforce
            >>> client = salesforce.Client(username='username',password='password',token='token')
            >>> client.download_table(table='Account',columns=('Id', 'FirstName', 'LastName'))
        """

        query_str = 'SELECT {columns} FROM {table} {where_clause}'.format(
            columns=','.join(columns),
            table=table,
            where_clause='WHERE {}'.format(condition) if condition else ''

        )
        rows = self.run_query(query_str, include_deleted)

        output_file = '{}/{}.csv'.format(local_folder, table)
        logs.client.logger.info('Exporting data into {}'.format(output_file))

        csv_file = open(output_file, 'w')
        writer = csv.DictWriter(
            csv_file, fieldnames=columns, delimiter=separator)
        if print_header:
            writer.writeheader()

        # it's best to handle the exception inside the generator query_all_iter
        # but because the generator handled by simple_salesforce library it's not possible to do it.
        # the workaround is to handle the exception while using the generator. if the exception happens
        # then the generator starts from beginning. Unfortunately there is no way around it.
        try_count = 0
        while True:
            try:
                row = next(rows)  # get the next row from generator
            except StopIteration:  # end of iteration so break!
                break
            except (exceptions.SalesforceExpiredSession,
                    exceptions.SalesforceMalformedRequest,
                    exceptions.SalesforceAuthenticationFailed) as e:

                if try_count == self.MAX_RETRIES:
                    raise Exception(
                        "Reading from Salesforce failed. Reached maximum retries.")

                logs.client.logger.warning(
                    "Reading from Salesforce failed with this message: {message}."
                    "Sleeping for {wait_time} seconds before next try".format(
                        message=e.content[0]["message"],
                        wait_time=self.WAIT_BETWEEN_RETRY
                    )
                )

                sleep(self.WAIT_BETWEEN_RETRY)
                try_count += 1

                # cleanup and reset the generator
                os.remove(output_file)
                csv_file = open(output_file, 'w')
                writer = csv.DictWriter(
                    csv_file, fieldnames=columns, delimiter=separator)
                if print_header:
                    writer.writeheader()
                rows = self.run_query(query_str, include_deleted)

            else:
                row.pop('attributes')
                for field_transform in fields_transform:
                    row[field_transform[0]] = field_transform[1](
                        row[field_transform[0]])
                writer.writerow(row)

        csv_file.close()

        return output_file

    def update_salesforce(self, sf_table: str,  data: list):
        '''
        Bulk updates a table in salesforce
        Args:
            sf_table (str):  Table name. For example: ``Account``.
            data (list): List data to be sent to salesforce. For example: ``[{"FirstName": "abcd", "LastName":"xyz"}, {...}]``

        Returns:
            int: Number of records successfully updated
        Raises: General Salesforce Error

        Examples:
            >>> from tmg.data import salesforce
            >>> client = salesforce.Client("username:password:token@domain")
            >>> client.update_salesforce(sf_table='Account',data=[{"FirstName": "abcd", "LastName":"xyz"}, {...})
        '''
        logs.client.logger.info(f"Updating {sf_table} table in Salesforce domain {self.domain}")
        
        # Creating a SFBulkType object
        sf_table_object = self.sf.bulk.sf_table
        # Substituting sf_table into object_name variable
        setattr(sf_table_object, 'object_name', sf_table)
        # Most errors are handled in the salesforce library
        update = sf_table_object.update(data)

        success_ids = []
        for row in update:
            if row['success']:
                success_ids.append(row['id'])
            else:
                # When the update fails, the 'id' value is 'None'. Doesn't make sense to capture it then.
                logs.client.logger.error(f"Update failed with the following error {row['errors']}")
        
        logs.client.logger.info(
            f"Update process complete in table {sf_table} in {self.domain} with {len(success_ids)} successful and {len(data) - len(success_ids)} errors."
        )
 
        return len(success_ids)
