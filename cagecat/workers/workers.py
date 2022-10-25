"""Stores functions to execute when a submitted job will be executed

Author: Matthias van den Belt
"""

# import statements
import os.path

# own project imports

from cagecat.file_utils import get_job_folder_path
from cagecat.workers.workers_helpers import *

### redis-queue functions
from config_files.config import thresholds, pfam_db_folder



def cblaster_search(
        job_id: str,
        options: ImmutableMultiDict = None,
        file_path: t.Union[str, None] = None) \
        -> None:
    """Executed when requested job is cblaster_search (forges + exec. command)

    Input:
        - job_id: ID of the submitted job
        - options: user submitted parameters via HTML form
        - file_path: path to an uploaded file (or session file)

    Output:
        - None, execution of this module

    This function forges and executes a cblaster command.
    """
    try:
        recompute = False
        if file_path is not None and not file_path.endswith('.json'):  # .json indicates this is a recompute job
            file_path = sanitize_file(file_path, job_id)

        results_folder = get_job_folder_path(
            job_id=job_id,
            jobs_folder='results'
        )

        log_folder = get_job_folder_path(
            job_id=job_id,
            jobs_folder='logs'
        )

        # create the base command, with all required fields
        cmd = [
            "cblaster", "search",
            "--output", Path(results_folder / f'{job_id}_summary.txt').as_posix(),
            "--plot", Path(results_folder / f"{job_id}_plot.html").as_posix(),
            "--blast_file", Path(results_folder, f"{job_id}_blasthits.txt").as_posix(),
            "--mode", Path(options["mode"]).as_posix()
        ]

        cmd.extend(forge_database_args(options))

        # add input options
        if options['mode'] in ('remote', 'combi_remote'):
            input_type = options["inputType"]

            if input_type == "file":
                cmd.extend(["--query_file", file_path])
                session_path = Path(results_folder / f"{job_id}_session.json").as_posix()
                store_query_sequences_headers(log_folder, input_type, file_path)
            elif input_type == "ncbi_entries":
                entries = options["ncbiEntriesTextArea"].split()

                cmd.append("--query_ids")
                cmd.extend(entries)

                session_path = Path(results_folder / f"{job_id}_session.json").as_posix()
                store_query_sequences_headers(log_folder, input_type, entries)
            elif input_type == "prev_session":
                recompute = True
                cmd.extend(
                    ["--recompute", Path(results_folder / f"{job_id}_session.json").as_posix()]
                )
                session_path = file_path

            else:  # future input types and prev_session
                raise NotImplementedError(f"Input type {input_type} is not supported "
                                          f"in cblaster_search")

                # add search options
            if not recompute:
                cmd.extend([
                    # "--database", options["database_type"],
                    "--hitlist_size", options["hitlist_size"]])

                if options["entrez_query"]:
                    cmd.extend(["--entrez_query", options["entrez_query"]])

        if options['mode'] in ('hmm', 'combi_remote'):
            session_path = Path(results_folder / f"{job_id}_session.json").as_posix()

            # add HMM profiles
            cmd.append('--query_profiles')
            cmd.extend(options["hmmProfiles"].split())

            # PFAM database
            cmd.extend(['--database_pfam', pfam_db_folder])

            # database to search in was added in forge_database_args

        cmd.extend(["--session_file", session_path])

        # add filtering options
        if options['mode'] != 'hmm':
            cmd.extend(
                [
                    "--max_evalue", options["max_evalue"],
                    "--min_identity", options["min_identity"],
                    "--min_coverage", options["min_query_coverage"]
                ]
            )

        # add clustering options
        cmd.extend(
            [
                "--gap", options["max_intergenic_gap"],
                "--unique", options["min_unique_query_hits"],
                "--min_hits", options["min_hits_in_clusters"],
                "--percentage", options["percentageQueryGenes"]
            ]
        )

        if options["requiredSequences"]:  # as empty string evaluates to False
            cmd.append("--require")
            for q in options["requiredSequences"].split(";"):
                cmd.append(f"{q.strip().split()[0]}")  # to prevent 1 header to be interpreted
                # as multiple due to spaces in header

        # add summary table
        cmd.extend(create_summary_table_commands('search', options))

        # add binary table
        cmd.extend(
            ["--binary", Path(results_folder / f"{job_id}_binary.txt").as_posix()]
        )

        bin_table_delim = options["searchBinTableDelim"]
        if bin_table_delim:
            cmd.extend(["--binary_delimiter", bin_table_delim])

        cmd.extend(["--binary_decimals", options["searchBinTableDecimals"]])

        if "searchBinTableHideHeaders" in options:
            cmd.append("--binary_hide_headers")

        cmd.extend(["--binary_key", options["keyFunction"]])

        if "hitAttribute" in options:  # only when keyFunction is not len
            cmd.extend(["--binary_attr", options["hitAttribute"]])

        # add additional options
        if "sortClusters" in options:
            cmd.append("--sort_clusters")

        # add intermediate genes options
        if "intermediate_genes" in options:
            cmd.extend(
                [
                    "--intermediate_genes",
                    "--max_distance", options["intermediate_max_distance"],
                    "--maximum_clusters", options["intermediate_max_clusters"],
                    "--ipg_file", Path(results_folder / f"{job_id}_ipg.txt").as_posix()
                ]
            )

        return_code = run_command(cmd, job_id)
        return return_code
    except Exception as e:  # intentionally broad except clause
        print('Exception occurred:', e)
        return 999


def cblaster_gne(
        job_id: str,
        options: ImmutableMultiDict = None,
        file_path: t.Union[str, None] = None) \
        -> None:
    """Executed when requested job is cblaster_gne (forges + exec. command)

    Input:
        - job_id: ID of the submitted job
        - options: user submitted parameters via HTML form
        - file_path: path to previous job's session file

    Output:
        - None, execution of this module

    This function forges and executes a cblaster command.
    """

    exceeded = log_threshold_exceeded(
        parameter=int(options["sample_number"]),
        threshold=thresholds['maximum_gne_samples'],
        job_id=job_id,
        error_message='Too many samples'
    )
    if exceeded:
        return

    session_path = file_path
    results_folder = get_job_folder_path(
        job_id=job_id,
        jobs_folder='results'
    )

    cmd = [
        "cblaster", "gne", session_path,
        "--max_gap", options["max_intergenic_distance"],
        "--samples", options["sample_number"],
        "--scale", options["sampling_space"],
        "--plot", Path(results_folder / f"{job_id}_plot.html").as_posix(),
        "--output", Path(results_folder / f"{job_id}_summary.txt").as_posix()
    ]

    cmd.extend(create_summary_table_commands('gne', options))

    return_code = run_command(cmd, job_id)
    return return_code


def cblaster_extract_sequences(
        job_id: str,
        options: ImmutableMultiDict = None,
        file_path: t.Union[str, None] = None) \
        -> None:
    """Executed when requested job is extract sequences of cblaster

    Input:
        - job_id: ID of the submitted job
        - options: user submitted parameters via HTML form
        - file_path: path to previous job's session file

    Output:
        - None, execution of this module

    This function forges and executes a cblaster command.
    """

    results_folder = get_job_folder_path(
        job_id=job_id,
        jobs_folder='results'
    )

    extension = "txt"
    if "downloadSeqs" in options:
        extension = "fasta"

    cmd = [
        "cblaster", "extract", file_path,
        "--output", Path(results_folder / f"{job_id}_sequences.{extension}").as_posix()
    ]

    cmd.extend(create_filtering_command(options, False))

    if "outputDelimiter" in options and options["outputDelimiter"]:
        cmd.extend(
            ["--delimiter", options["outputDelimiter"]]
        )

    if "nameOnly" in options:
        cmd.append("--name_only")

    if "downloadSeqs" in options:
        cmd.append("--extract_sequences")

    return_code = run_command(cmd, job_id)
    return return_code


def cblaster_extract_clusters(
        job_id: str,
        options: ImmutableMultiDict = None,
        file_path: t.Union[str, None] = None) \
        -> None:
    """Executed when requested job is extract clusters of cblaster

    Input:
        - job_id: ID of the submitted job
        - options: user submitted parameters via HTML form
        - file_path: path to previous job's session file

    Output:
        - None, execution of this module

    This function forges and executes a cblaster command.
    """
    results_folder = get_job_folder_path(
        job_id=job_id,
        jobs_folder='results'
    )

    exceeded = log_threshold_exceeded(
        parameter=int(options["maxclusters"]),
        threshold=thresholds['maximum_clusters_to_extract'],
        job_id=job_id,
        error_message='Too many selected clusters')

    if exceeded:
        return

    cmd = [
        "cblaster", "extract_clusters", file_path,
        "--output", results_folder.as_posix()
    ]

    cmd.extend(create_filtering_command(options, True))

    if options["prefix"]:
        cmd.extend(
            ["--prefix", options["prefix"]]
        )

    cmd.extend(
        ["--format", options["format"]]
    )

    return_code = run_command(cmd, job_id)
    return return_code


def clinker(
        job_id: str,
        options: ImmutableMultiDict = None,
        file_path: t.Union[Path, None] = None) \
        -> None:
    """Executed when requested job is visualization using clinker.

    Input:
        - job_id: ID of the submitted job
        - options: user submitted parameters via HTML form
        - file_path: path to genbank files (following structure:
            cagecat/jobs/prev_job_id/results/*.gbk
            to select all gbk files)

    Output:
        - None, execution of this module

    This function forges and executes a clinker command.
    """
    assert isinstance(file_path, Path)

    results_folder = get_job_folder_path(
        job_id=job_id,
        jobs_folder='results'
    )

    if 'clinkerEnteredJobId' in options:  # indicates we are a downstream job
        remove_old_files = False
        sanitize_files = False
    else:
        remove_old_files = True
        sanitize_files = True

    try:
        if sanitize_files:
            for file in file_path.iterdir():
                if file.suffix == '.zip':  # indicates we are coming from an extract_clusters job and are going to a clinker job (or the user has uploaded a .zip file)
                    print('Skipped', file)
                    continue
                sanitize_file(file, job_id, remove_old_files=remove_old_files)

        exceeded = log_threshold_exceeded(
            parameter=len(list(file_path.iterdir())),  # should be in list as it actually returns a generator
            threshold=thresholds['max_clusters_to_plot'],
            job_id=job_id,
            error_message='Too many selected clusters'
        )

        if exceeded:
            return

        cmd = [
            "clinker", file_path.as_posix(),
            "--jobs", "2",
            "--session", Path(results_folder / f"{job_id}_session.json").as_posix(),
            "--output", Path(results_folder / "alignments.txt").as_posix(),
            "--plot", Path(results_folder / f"{job_id}_plot.html").as_posix()
        ]

        if "noAlign" in options:
            cmd.append("--no_align")

        cmd.extend(
            ["--identity", options["identity"]]
        )

        if options["clinkerDelim"]:  # empty string evaluates to false
            cmd.extend(
                ["--delimiter", options["clinkerDelim"]]
            )

        cmd.extend(
            ["--decimals", options["clinkerDecimals"]]
        )

        if "hideLinkHeaders" in options:
            cmd.append("--hide_link_headers")

        if "hideAlignHeaders" in options:
            cmd.append("--hide_aln_headers")

        if "useFileOrder" in options:
            cmd.append("--use_file_order")

        return_code = run_command(cmd, job_id)
        return return_code
    except Exception as e:
        write_to_log_file(job_id, text=e)

        return 1


def clinker_query(
        job_id: str,
        options: ImmutableMultiDict = None,
        file_path: t.Union[str, None] = None) \
        -> None:
    """Executed when requested job is visualization using cblaster

    Input:
        - job_id: ID of the submitted job
        - options: user submitted parameters via HTML form
        - file_path: path to previous job's session file

    Output:
        - None, execution of this module

    This function forges and executes a cblaster command.
    """

    exceeded = log_threshold_exceeded(
        parameter=int(options['maxclusters']),
        threshold=thresholds['max_clusters_to_plot'],
        job_id=job_id,
        error_message='Too many selected clusters'
    )

    if exceeded:
        return

    results_folder = get_job_folder_path(
        job_id=job_id,
        jobs_folder='results'
    )

    cmd = [
        "cblaster", "plot_clusters", file_path,
        "--output", Path(results_folder / f"{job_id}_plot.html").as_posix()
    ]

    cmd.extend(create_filtering_command(options, True))

    return_code = run_command(cmd, job_id)
    return return_code
