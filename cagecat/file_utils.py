from pathlib import Path

from cagecat.const import jobs_dir, folders_to_create
from config_files.config import server_prefix, sanitized_folder


def write_to_log_file(job_id: str, text: str):
    fp = get_log_file_path(job_id)

    with open(fp, 'a') as outf:
        outf.write(f'{text}\n')


def get_log_file_contents(job_id: str):
    fp = get_log_file_path(job_id)

    with open(fp) as inf:
        logs = inf.read()

    return logs


def get_log_file_path(job_id: str):
    fp = generate_filepath(
        job_id=job_id,
        jobs_folder='logs',
        suffix=None,
        extension='log',
        return_absolute_path=True
    )

    return fp

def generate_filepath(
        job_id: str,
        jobs_folder: str,
        suffix: str,
        extension: str,
        return_absolute_path: bool,
        override_filename: str = None) -> Path:

    assert override_filename is None or type(override_filename) == str
    assert type(return_absolute_path) == bool
    assert len(extension) > 0

    check_valid_jobs_folder(jobs_folder)

    fn = f'{job_id}_{suffix}' if suffix is not None else f'{job_id}'
    ext = f'.{extension}' if not extension.startswith('.') else extension

    if override_filename is not None:
        fn = override_filename

    return get_absolute_path(
        inpath=Path(server_prefix, jobs_dir, job_id, jobs_folder, fn).with_suffix(ext),
        return_absolute_path=return_absolute_path
    )


def check_valid_jobs_folder(jobs_folder: str):
    if jobs_folder not in folders_to_create:
        raise IOError('Invalid jobs folder given')


def get_job_folder_path(job_id: str, jobs_folder: str):
    check_valid_jobs_folder(jobs_folder)

    return Path(server_prefix, jobs_dir, job_id, jobs_folder)

def generate_sanitization_filepath(job_id: str):
    # is ok
    return Path(sanitized_folder, job_id)

def get_absolute_path(inpath, return_absolute_path: bool):
    if return_absolute_path:
        return inpath.as_posix()
    else:
        return inpath
