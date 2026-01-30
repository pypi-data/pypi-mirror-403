
import delegator
import os,zipfile
import pandas as pd

from google.cloud import bigquery


def merge_files(files_path, output_file_path=None):

    output = 'merged.csv'

    with open(output_file_path if output_file_path else output, 'w') as outfile:
        for file_path in files_path:
            with open(file_path) as infile:
                outfile.write(infile.read())

    return output


def clean_mysql_export(file_path):
    """Cleans MySQL export (CSV) format removing "N values and replacing them with null.
    Args:
        file_path (str): CSV file path

    Returns:
        str: Cleaned CSV file name
    """

    # Crazy SED command to clean Cloud SQL CSV export
    # that doesn't support Null values which are written as "N....seriously.
    command = "cat {file_path} | sed 's/,\"N,/,,/g' | sed 's/,\"N,/,,/g' | sed 's/^\"N,/,/g' | sed 's/,\"N$/,/g'" \
              " >> {file_name}_cleaned.csv"
    file_name = os.path.splitext(file_path)[0]
    command = command.format(file_path=file_path, file_name=file_name)
    delegator.run(command, block=True)

    return "{}_cleaned.csv".format(file_name)


def get_bq_write_disposition(write_preference):
    """Convert write_preference string to BigQuery WriteDisposition values

    Args:
        write_preference (str): The write preference string which should be 'truncate', 'append' or 'empty'

    Returns:
        bigquery.WriteDisposition: The BigQuery WriteDisposition value

    """

    disposition = {
        'truncate': bigquery.WriteDisposition.WRITE_TRUNCATE,
        'append': bigquery.WriteDisposition.WRITE_APPEND,
        'empty': bigquery.WriteDisposition.WRITE_EMPTY
    }

    return disposition.get(write_preference, None)

def unzip_merge_csv(zip_file,extract_to_path):
    '''
    unzip folder and merge all csv files and create a new merged csv file

    Args :
        zip_file : absolute path of the zip file
        extract_to_path : path of folder to keep merged file

    '''
    if zipfile.is_zipfile(zip_file):
        zip_ref = zipfile.ZipFile(zip_file)
        zip_ref.extractall(extract_to_path)
        zip_ref.close()

        folders = [folder for folder in os.listdir(extract_to_path) if folder != '__MACOSX' and folder != '.DS_Store']

        for folder in folders:
            updated_dir = extract_to_path + folder + "/"
            files = [updated_dir + file for file in os.listdir(updated_dir)]

        # merging all csv files
        final_df = pd.DataFrame()
        for file in files:
            df = pd.read_csv(file)
            final_df = pd.concat([final_df, df], axis=0, ignore_index=True)

        # keeping merged files inside merge folder
        output_dir = extract_to_path + "/merged/"
        output = 'merged.csv'
        if not os.path.exists(output_dir):os.mkdir(output_dir)
        output = os.path.join(output_dir, output)
        final_df.to_csv(output, index=False)
        return output
    else:
        raise RuntimeError("Provided file is not zip file. ")