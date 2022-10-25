"""Stores helper functions of the workers.py module

Author: Matthias van den Belt
"""

# package imports
import shutil
import subprocess
import os

# own project imports
import datetime
from pathlib import Path

import pytz

from Bio.SeqIO.FastaIO import SimpleFastaParser
from flask_sqlalchemy import SQLAlchemy

from cagecat.general_utils import send_email
from cagecat.file_utils import write_to_log_file, generate_filepath, get_log_file_path, generate_sanitization_filepath
from cagecat.db_utils import fetch_job_from_db, Job, fetch_statistic_from_db
from cagecat import db
from config_files.config import cagecat_version, domain, server_prefix, sanitized_folder, finished_hmm_db_folder
from cagecat.const import genbank_extensions, fasta_extensions, jobs_dir

# typing imports
from werkzeug.datastructures import ImmutableMultiDict
import typing as t

# Function definitions

timezone = pytz.timezone('Europe/Amsterdam')

def create_filtering_command(options: ImmutableMultiDict,
                             is_cluster_related: bool) -> t.List[str]:
    """Forges command for filtering based on submitted options

    Input:
        - options: user submitted parameters via HTML form
        - is_cluster_related: indicates if the filtering command is meant
            for filtering clusters
    """
    partly_cmd = []

    if not is_cluster_related:
        if options["selectedQueries"]:
            partly_cmd.append("--queries")
            partly_cmd.extend(options["selectedQueries"].split())

    if options["selectedOrganisms"]:
        partly_cmd.extend(["--organisms", options['selectedOrganisms']])
        # TODO future: could also that user gives multiple patterns. separated by ;?

    if is_cluster_related:
        if options["clusterNumbers"]:
            partly_cmd.append("--clusters")
            partly_cmd.extend(options["clusterNumbers"].strip().split())

        if options["clusterScoreThreshold"]:
            partly_cmd.extend(["--score_threshold",
                               options["clusterScoreThreshold"]])

        partly_cmd.extend(["--maximum_clusters", options["maxclusters"]])

    return partly_cmd


def create_summary_table_commands(
        module: str, options: ImmutableMultiDict) \
        -> t.List[str]:
    """Generates commands for creating a summary table

    Input:
        - module: name of used cblaster module to create commands for.
            Currently available are: ["search", "gne"]
        - options: user submitted options (values) via HTTP form of front-end

    Output:
        - summary_cmds: commands to enable creation of a custom-defined
            summary table

    Depending on the module, a prefix is required for the commands to work.
    """
    summary_cmds = []

    if module == "search":
        prefix = "output_"
    elif module == "gne":
        prefix = ""
    else:
        raise IOError("Invalid module")

    sum_table_delim = options[f"{module}SumTableDelim"]
    if sum_table_delim:  # evalutes to True if not an empty string
        summary_cmds.extend([f"--{prefix}delimiter", sum_table_delim])

    summary_cmds.extend([f"--{prefix}decimals",
                         options[f"{module}SumTableDecimals"]])

    if f"{module}SumTableHideHeaders" in options:
        summary_cmds.append(f"--{prefix}hide_headers")

    return summary_cmds


def run_command(cmd: t.List[str], job_id: str, log_output: bool = True, **kwargs) -> int:
    """Executes a command on the command line

    Input:
        - cmd: split command to be executed. All elements in the
            list are joined together with a space to form a full command
        - job_id: ID corresponding to the job the function is called for
        - log_output: log the output of the command to a file

    Output:
        - return_code: exit code of the executed command. A non-zero exit
            code indicates something went wrong. An exit code of 0 indicates
            the command has executed without any problems.

    """
    if log_output:
        log_command(cmd, job_id)
        fp = get_log_file_path(job_id)

        with open(fp, 'a') as outf: # if the log file exists, a sanitization step already has occurred
            try:
                res = subprocess.run(cmd, stderr=outf, stdout=outf, text=True, **kwargs)
                return_code = res.returncode
            except Exception as e:  # purposely broad except clause to catch all exceptions
                print(e)
                return_code = 1
    else:
        try:
            res = subprocess.run(cmd, **kwargs)
            return_code = res.returncode
        except Exception as e:  # purposely broad except clause to catch all exceptions
            print(e)
            return_code = 1

    return return_code


def zip_results(job_id: str) -> None:
    """Zips all files belonging to a job (logs, results, uploads)

    Input:
        - job_id: ID corresponding to the job the function is called for

    Output:
        - None
        - A .zip file containing all files which are part of a job

    We change directories to the {job_id} folder, which contains 3 folders:
    1. logs; 2. results; 3. uploads; Therefore, the paths used in this
    function are relative to the {job_id} folder.
    """
    os.chdir(Path(server_prefix, jobs_dir, job_id))  # go 1 level up

    fp = generate_filepath(
        job_id=job_id,
        jobs_folder='results',
        suffix=None,
        extension='zip',
        return_absolute_path=True
    )

    cmd = ["zip", "-r", fp, "."]
    # all files and folders in the current directory
    # (cagecat/jobs/{job_id}/ under the base folder

    run_command(cmd, job_id, log_output=False)


def log_command(cmd: t.List[str], job_id: str) -> None:
    """Logs the executed command to a file

    Input:
        - cmd: split command to be executed. All elements in the
            list are joined together with a space to form a full command
        - job_id: ID corresponding to the job the function is called for

    Output:
        - None
        - .txt file with the executed command
    """
    fp = generate_filepath(
        job_id=job_id,
        jobs_folder='logs',
        suffix='command',
        extension='txt',
        return_absolute_path=True
    )

    with open(fp, 'a') as outf:
        outf.write(" ".join(cmd))


def pre_job_formalities(job_id: str) -> None:
    """Wrapper function for functions to be executed pre-job execution

    Input:
        - job_id: ID corresponding to the job the function is called for

    Output:
        - None
        - See documentation of executed functions for their corresponding
            outputs
    """
    add_time_to_db(job_id, "start", db)
    mutate_status(job_id, "start", db)


def send_notification_email(job: Job) -> None:
    """Sends notification mail when a job has finished running

    Input:
        - job: a job entry in the SQL database (is an object, stores all
            job-specific details as attributes)

    Output:
        - None, an e-mail being sent to the user-defined e-mail address
    """
    contents = f'''Dear CAGECAT user,
    
The job (type: {job.job_type}) you submit on {job.post_time} has finished running on {job.finish_time}.'''

    contents += f'''

You are able to perform additional downstream analysis by navigating to the results page of your job by going to:\n{domain}results/{job.id}\n
Also, downloading your results is available on this web page.''' \
        if job.status == 'finished' else f'''

To investigate why your job has failed, please visit {domain}results/{job.id}.\nIf the failure reason is unknown, please submit feedback to help us improve CAGECAT.\n'''

    send_email(f'Your job: {job.title}' if job.title else f'Your job with ID {job.id} has {job.status}',
               contents,job.email)


def log_cagecat_version(job_id: str) -> None:
    """Logs the version of CAGECAT to the job's logs folder

    Input:
        - job_id: ID of job for which CAGECAT's version should be logged

    Output:
        - written file with CAGECAT's version

    """
    fp = generate_filepath(
        job_id=job_id,
        jobs_folder='logs',
        suffix=None,
        extension='txt',
        return_absolute_path=True,
        override_filename='CAGECAT_version'
    )

    with open(fp, 'w') as outf:
        outf.write(f'CAGECAT_version={cagecat_version}')


def post_job_formalities(job_id: str, return_code: int) -> None:
    """Wrapper function for functions to be executed post-job execution

    Input:
        - job_id: ID corresponding to the job the function is called for
        - return_code: exit code of the executed command. A non-zero exit
            code indicates something went wrong. An exit code of 0 indicates
            the command has executed without any problems.

    Output:
        - None
        - See documentation of executed functions for their corresponding
            outputs
    """
    log_cagecat_version(job_id)
    zip_results(job_id)

    j = fetch_job_from_db(job_id)

    add_time_to_db(job_id, "finish", db)
    mutate_status(job_id, "finish", db, return_code=return_code)
    if j.email:
        send_notification_email(j)

    remove_email_from_db(j)
    db.session.commit()


def store_query_sequences_headers(log_path: Path, input_type: str, data: str):
    """Saves the submitted query headers to a .csv file

    Input:
        - log_path: path to the log directory of this job
        - input_type: selected input_type by the user
        - data: query headers (NCBI entries) or file_path to the uploaded
            FASTA file

    Output:
        - None, written file
    """
    if input_type == "ncbi_entries":  # ncbi_entries
        headers = data
    elif input_type == "file":
        ext = '.' + data.split('.')[-1]
        if ext in fasta_extensions:
            with open(data) as inf:
                headers = [line.strip()[1:].split()[0] for line in
                           inf.readlines() if line.startswith(">")]
        elif ext in genbank_extensions:
            with open(data) as inf:
                headers = [line.strip().split('"')[1] for line in inf.readlines() if '/protein_id=' in line]
        else:
            raise ValueError(f'Invalid extension: {ext}. Did the user upload a file with dots in it?')

    fp = log_path / "query_headers.csv"
    with open(fp.as_posix(), "w") as outf:
        outf.write(",".join(headers))


def forge_database_args(options: ImmutableMultiDict) -> t.List[str]:
    """Forges command for database selection based on submitted options

    Input:
        - options: user submitted parameters via HTML form

    Output:
        - base: appropriate (based on submitted options) argument list
    """
    # TODO future: handle recompute scenario as now mode is always given as remote, which is not always the case. The search type should be fetched from the initial search job
    base = ['--database']
    if options['mode'] in ('hmm', 'combi_remote'):
        splitted = options["selectedGenus"].split('_')
        kingdom = splitted[0].lower()
        genus = splitted[1]

        db_path = finished_hmm_db_folder / kingdom / genus
        db_path = db_path.with_suffix('.fasta')

        base.append(db_path.as_posix())

    if options['mode'] in ('remote', 'combi_remote'):
        if 'database_type' in options:
            base.append(options['database_type'])
        else:  # when recomputing it's not there
            return []

    if len(base) not in (2, 3):
        raise IOError('Incorrect database arguments length')

    return base


def log_threshold_exceeded(parameter: int, threshold: int, job_id: str, error_message: str) -> bool:
    """Logs an error message if the given threshold was exceeded

    Input:
        - parameter: the given value by the user for a parameter
        - threshold: the corresponding threshold for that parameter
        - job_id: id of the current job
        - error_message: message technically describing what is incorrect.
            Is formatted in a user-friendly error description later.

    Output:
        - boolean: whether or not the threshold was exceeded, and the worker
            function from which this function is called should return (exit)

    The logged error message will be used by when the results of a job are
    requested to find the appropriate error message to display to the user.
    """

    if parameter > threshold:
        fp = generate_filepath(
            job_id=job_id,
            jobs_folder='logs',
            suffix='threshold',
            extension='log',
            return_absolute_path=True
        )

        with open(fp, 'w') as outf:
            outf.write(f'{error_message} ({parameter} > {threshold})')

        post_job_formalities(job_id, 997)
        return True

    return False


def add_time_to_db(job_id: str, time_type: str, db: SQLAlchemy) -> None:
    """Adds timestamp to job entry with given ID in SQL database

    Input:
        - job_id: ID corresponding to the job the function is called for
        - time_type: column in the SQL table to which a timestamp should be
            added. Available options are: ["start", "finish"]
        - db: SQL database connection with the Flask application

    Output:
        - None
        - Stored time at given column in the SQL database
    """
    job = fetch_job_from_db(job_id)

    formatted_time = datetime.datetime.now(timezone).strftime('%B %d %Y - %H:%M:%S')

    if time_type == "start":
        job.start_time = formatted_time
    elif time_type == "finish":
        job.finish_time = formatted_time
    else:
        raise IOError("Invalid time type")

    db.session.commit()


def mutate_status(job_id: str, stage: str, db: SQLAlchemy,
                  return_code: t.Optional[int] = None) -> None:
    """Mutates status of job entry with given ID in SQL database

    Input:
        - job_id: ID corresponding to the job the function is called for
        - stage: stage the job has entered. Available options are:
            ["start", "finish"]
        - db: SQL database connection with the Flask application
        - return_code: exit code of the command ran. 0 indicates command
            execution without errors

    Output:
        - None
        - Mutated job status in the SQL database

    Raises:
        - IOError: when the given stage is invalid
    """
    job = fetch_job_from_db(job_id)

    if stage == "start":
        new_status = "running"
    elif stage == "finish":
        if return_code is None:
            raise IOError("Return code should be provided")
        elif not return_code:  # return code of 0
            new_status = "finished"
        else:
            print('Return code is:', return_code)
            new_status = "failed"

        fetch_statistic_from_db(new_status).count += 1

    else:
        raise IOError("Invalid stage")

    job.status = new_status
    db.session.commit()


def remove_email_from_db(db_job: Job):
    if db_job.email != '':
        db_job.email = '-'


def sanitize_file(file_path: Path, job_id, remove_old_files=False):
    """Sanitizes input file by piping it through antiSmash

    Called when preparing a cblaster search

    Returns file path of sanitized file to be used in the cblaster search analysis
    """
    assert isinstance(file_path, Path)

    print('Sanitizing ', file_path)
    sanitization_cmd_base = 'antismash --minimal --output-dir {} --minlength -1 --output-basename {} --genefinding-tool prodigal {}'

    # detect input type (NT FASTA / protein FASTA / GBK)
    # extension = f".{file_path.split('.')[-1]}"
    write_to_log_file(job_id, text='-- Executing input file sanitization')

    if file_path.suffix in fasta_extensions:
        # determine what type of FASTA it is.
        with open(file_path) as handle:
            for header, sequence in SimpleFastaParser(handle):
                total = 0

                # check for nucleotide fasta
                for nt in 'ATCGatcg':
                    total += sequence.count(nt)

                if total == len(sequence):
                    file_type = 'nt_fasta'
                else:
                    file_type = 'aa_fasta'

        if 'file_type' not in locals(): # check if the variable exists
            write_to_log_file(job_id, text='-- Error when parsing FASTA file') # manually write to file as there is no log file yet (as we've not executed any command yet)

            raise IOError('Error when parsing FASTA file')

        if file_type == 'aa_fasta':
            return file_path
        elif file_type == 'nt_fasta':  # we should sanitize the file
            pass
        else:
            raise IOError('Incorrect FASTA file type')
    elif file_path.suffix in genbank_extensions:
        pass
        # check if input file is not accidentally a GenPept file
        # this will fail if it is an incorrectly formatted file, so skip it for now
        # for record in Bio.SeqIO.parse(file_path, 'gb'):
        #     total = 0
        #     for nt in 'ATCGatcg':
        #         total += record.seq.count(nt)
        #
        #     if total != len(record.seq):
        #         # TODO: can rewrite records to a protein FASTA and use this as input. But should only be executed when all records are proteins (i.e. mixed DNA/protein records are invalid)
        #         raise IOError('At least one record in the input file is a protein sequence which is not supported. GenBank (nucleotide sequences), nucleotide FASTA and protein FASTA are supported inputs.')

    else:
        raise IOError('Invalid extension found:', file_path.suffix, f'(from file) {file_path}')

    # situations: nt FASTA, GenBank file

    sanitization_folder = generate_sanitization_filepath(job_id=job_id)

    cmd = sanitization_cmd_base.format(
        sanitization_folder.as_posix(),
        job_id,
        file_path.as_posix()
    )

    return_code = run_command(
        cmd=cmd.split(),
        job_id=job_id,
        log_output=True
    )

    if return_code != 0:
        post_job_formalities(job_id, return_code)
        msg = 'Error during sanitization by antiSmash'
        write_to_log_file(job_id, text=msg)
        raise IOError(msg)

    write_to_log_file(
        job_id,
        text=f'-- Finished sanitization of input file: {file_path}'
        # manually write to file as there is no log file yet (as we've not executed any command yet)
    )

    if remove_old_files:
        file_path.unlink()
        print('Removed', file_path)

    sanitized_fn = sanitization_folder / f'{job_id}'
    sanitized_fn = sanitized_fn.with_suffix('.gbk')

    destination = generate_filepath(
        job_id=job_id,
        jobs_folder='uploads',
        suffix=None,
        extension='gbk',
        return_absolute_path=True
    )

    # for case when multiple files are uploaded (clinker)
    num = 1
    if destination.exists():
        destination = generate_clinker_upload_fp(job_id, num)

        while destination.exists():
            num += 1
            destination = generate_clinker_upload_fp(job_id, num)

    shutil.move(sanitized_fn, destination)
    print('Moved sanitized file from', sanitized_fn, 'to', destination)

    shutil.rmtree(sanitization_folder)
    print('Removed folder', sanitization_folder)
    # in case of multiple files, the above folder is recreated and deleted multiple times.
    # This is required, otherwise antiSmash will fail because it detects files in the output folder and will abort for safety reasons..

    return destination


def generate_clinker_upload_fp(job_id, num):
    dest = generate_filepath(
        job_id=job_id,
        jobs_folder='uploads',
        suffix=num,
        extension='gbk',
        return_absolute_path=True
    )
    return dest
