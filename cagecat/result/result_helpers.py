"""Helper functions involved in results

Author: Matthias van den Belt
"""
import copy
import os
import re
import typing as t

from cagecat.const import failure_reasons, jobs_dir, regex_failure_reasons, execution_stages
from cagecat.file_utils import generate_filepath
from cagecat.general_utils import send_email
from cagecat.db_utils import fetch_job_from_db, Job as dbJob
from config_files.sensitive import sender_email, persistent_jobs


def get_failure_reason(job_id: str) -> str:
    """Gets the user-friendly failure reason when a job has failed

    Input:
        - job_id: job id which has failed and the reason should be looked
            up for

    Output:
        - user-friendly failure reason
    """
    msg = None
    try:
        log_file = jobs_dir / job_id / "logs" / f"{job_id}"
        log_file = log_file.with_suffix('.log')

        with open(log_file) as inf:
            logs = inf.readlines()

        for l in logs:
            for fail in failure_reasons:
                if fail in l:
                    if fail == 'NotImplementedError':
                        send_email(
                            subject=f'{job_id} failed with an NotImplementedError',
                            message=f'The job {job_id} failed with an NotImplementedError and should be investigated.\n',
                            receiving_email=sender_email
                        )
                    return failure_reasons[fail]

            for fail_pattern, message in regex_failure_reasons:
                if re.findall(pattern=fail_pattern, string=l):
                    return message

    except FileNotFoundError:
        msg = 'No log file was found for your analysis. The developers have been notified to investigate your scenario.'

    send_email(
        subject=f'{job_id} failed with an unknown reason',
        message=f'The job {job_id} failed with an unknown reason and should be investigated.\n',
        receiving_email=sender_email
    )

    if msg is None:
        return 'Unknown failure reason. The developers have been notified to investigate your scenario.'
    else:
        return msg


def prepare_finished_result(job_id: str,
                            module: str,
                            size_limit=15000000) -> \
        t.Tuple[t.Union[str, None], str, t.Union[int, None]]:
    """Returns HTML code of plots if applicable and appropriate program

    Input:
        - job_id: ID corresponding to the job the results are requested for
        - module: module type of given job id for which the results are
            requested

    Output:
        - plot_contents: HTML code of a plot
        - program: the program that was executed by this job
        - size: size of the returned plot in bytes
    """
    plot_path = jobs_dir / job_id / "results" / f"{job_id}_plot"
    plot_path = plot_path.with_suffix('.html')

    size = None
    get_size = False

    if module == "extract_sequences" or module == "extract_clusters":
        program = "cblaster"
        plot_contents = None

    elif module == "search" or module == "recompute" or module == "gne":
        program = "cblaster"
        get_size = True

    elif module == "clinker":
        program = "clinker"
        get_size = True

    elif module == "clinker_query":
        program = "cblaster"  # as it uses plot_clusters functionality of cblaster
        get_size = True

    else:
        raise NotImplementedError(
            f"Module {module} has not been implemented yet in results")

    if get_size:
        with open(plot_path) as inf:
            plot_contents = inf.read()
        size = os.path.getsize(plot_path)  # intentionally with os module

    if size is not None:
        if size > size_limit:
            return "Your file is too large to be shown here. You can download your results manually via the \"Download\" button.", program, 0

    return plot_contents, program, size


def get_connected_jobs(job: t.Optional[dbJob]) -> \
        t.List[t.Tuple[str, str, str, str, str], ]:
    """Gets the connected (children, main_search, depending) jobs of a job

    Input:
        - job entry in SQL db for which connected jobs are requested

    Output:
        - connected jobs. Format of connected job:
            [job_id, job_title, job_type, job_status, connection_type]

    Child jobs: jobs which use the output of preceding jobs as input
    Main search: job which was used to search (initial job)
    Depending: jobs on which the current job depends to start
    """
    connected_jobs = []

    if job.id in persistent_jobs:
        return connected_jobs

    if job.main_search_job == "null": # current job is an initial job (search of clinker)
        children = job.child_jobs

        if children:  # empty string evaluates to False
            for j_id in children.split(","):
                child_job = fetch_job_from_db(j_id)
                if child_job is not None:
                    connected_jobs.append((child_job.id, child_job.title, child_job.job_type, child_job.status, "child"))

    else:
        main_job = fetch_job_from_db(job.main_search_job)
        connected_jobs.append((main_job.id, main_job.title, main_job.job_type, main_job.status, "main search"))

        if job.depending_on != "null":
            parent_job = fetch_job_from_db(job.depending_on)
            if parent_job is not None:
                connected_jobs.append((parent_job.id, parent_job.title, parent_job.job_type, parent_job.status, "depending"))

    return connected_jobs


stack_to_text_index = {
    'front-end': 0,
    'back-end': 1
}
mode_pattern = re.compile('mode=(.*)&')
intermediate_gene_text = ('Fetching intermediate genes from NCBI', 'Searching for intermediate genes')
download_sequences_text = ('Fetching sequences from NCBI', 'Querying NCBI')


def get_stages(job_type, contents, options, job_id):
    if job_type != 'search':
        stages: list = copy.deepcopy(execution_stages[job_type])
    else:
        stages = None

    if job_type == 'search':
        if '--recompute' in contents:
            stages = copy.deepcopy(execution_stages['recompute'])
            insert_stage_index = 2
        else:
            insert_stage_index = 5

            mode = parse_search_mode(options)
            stages = copy.deepcopy(execution_stages[job_type][mode])

        if 'intermediate_genes' in options:
            stages.insert(insert_stage_index, intermediate_gene_text)

    elif job_type == 'extract_sequences':
        if '--extract_sequences' in contents:
            stages.insert(2, download_sequences_text)

    elif job_type == 'extract_clusters':
        parent_job_id = fetch_job_from_db(job_id).main_search_job

        if parent_job_id == 'null':
            raise ValueError('An extract cluster job should have a main search job')
        parent_job_options = fetch_job_from_db(job_id).options

        mode = parse_search_mode(parent_job_options)
        if mode == 'hmm':
            stages.pop(3)  # removes ('Query NCBI for cluster sequences', 'Querying NCBI')

    return stages


def parse_search_mode(options):
    if options is None:
        return options

    if options.count('&') == 0:
        mode = options.split('=')[-1]
    else:
        mode = re.findall(pattern=mode_pattern, string=options)[0]
        if mode not in ('hmm', 'remote', 'combi_remote'):
            raise ValueError('Error when extracting mode')
    return mode


def create_execution_stages(job_type: str, job_id: str, options: str, stack: str):
    """

    options: can be empty. Indicates which options of the given job type have
    been selected by the user (e.g. searching for intermediate genes at a
    cblaster search job). Is stored in the database in enqueue_jobs function
    stack: used to select either front-end texts ore back-end log-descriptors
    """

    if stack not in ('front-end', 'back-end'):
        raise ValueError('Invalid stack')

    cmd_fp = generate_filepath(
        job_id=job_id,
        jobs_folder='logs',
        suffix='command',
        extension='txt',
        return_absolute_path=True
    )

    with open(cmd_fp) as inf:
        contents = inf.read()

    stages = get_stages(job_type, contents, options, job_id)
    text_index = stack_to_text_index[stack]

    return [stage[text_index] for stage in stages]
