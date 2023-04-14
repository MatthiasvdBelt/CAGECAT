"""Stores routes for Flask web application for job result pages

Author: Matthias van den Belt
"""

# package imports
import copy
import json
from typing import Union, Any, Tuple

import flask
import markupsafe
from flask import Blueprint, request, url_for, send_file, Response

# own project imports
from werkzeug.utils import secure_filename

from cagecat.routes.routes_helpers import format_size
from cagecat.const import modules_with_plots, downstream_modules
from cagecat.general_utils import show_template
from cagecat.file_utils import get_log_file_contents, generate_filepath
from cagecat.db_utils import fetch_job_from_db
from cagecat.result.result_helpers import prepare_finished_result, get_connected_jobs, get_failure_reason, create_execution_stages

# typing imports
import typing as t

from cagecat.tools.tools_helpers import get_search_mode_from_job_id

result = Blueprint('result', __name__, template_folder="templates")

### Route function definitions
@result.route("/<job_id>")
def show_result(job_id: str, pj=None, store_job_id=False, j_type=None) -> str: # parent_job should be
    """Shows the results page for the given job ID

    Input:
        - job_id: job ID for a previously submitted job for which the user
            would like to view the results

    Output:
        - HTML represented in string format. Renders different templates based
            on the status of the given job ID

    Raises:
        - IOError: when for some reason a job's status is not valid. Currently
            valid options are: ["finished", "failed", "queued", "running"]

    Shows the "job_not_found.html" template when the given job ID was not
    found in the SQL database
    """
    job = fetch_job_from_db(job_id)
    scripts = []

    if job is not None:
        status = job.status

        kwargs = {
            'status': status,
            'j_id': job_id,
            'job_title': job.title,
            'help_enabled': False
        }

        if status == "finished":
            module = job.job_type
            _, program, size = prepare_finished_result(
                job_id, module)

            modules: list = copy.deepcopy(downstream_modules[module])
            if module =='search' and get_search_mode_from_job_id(job.id) == 'combi_remote':
                modules.remove('extract_clusters')  # this can be removed when it is implemented in cblaster

            kwargs.update(
                {
                    'template_name': 'result_page.html',
                    'content_size': format_size(size),
                    'module': module,
                    'modules_with_plots': modules_with_plots,
                    'downstream_modules': modules,
                    'connected_jobs': get_connected_jobs(job)
                }
            )

            scripts.append('addResultPageListeners()')

        elif status == "failed":
            kwargs.update(
                {
                    'template_name': 'failed_job.html',
                    'module': job.job_type,
                    'failure_reason': get_failure_reason(job_id)
                }
            )

        elif status == "queued" or status == "running":
            if "pj" not in request.args:
                pj = "null"
            else:
                pj = request.args["pj"]

            if status == 'queued':
                stages = []
            else:
                stages = create_execution_stages(
                    job_type=job.job_type,
                    job_id=job_id,
                    options=job.options,
                    stack='front-end'
                )

            kwargs.update(
                {
                    'template_name': 'status_page.html',
                    'parent_job': pj,
                    'store_job_id': store_job_id,
                    'j_type': j_type,
                    'stat_code': 302,
                    'stages': stages
                }
            )

            if status == 'running':
                scripts.append(f"startJobExecutionStageUpdater('{job_id}')")

        elif status == "waiting":
            pj = fetch_job_from_db(job_id).depending_on\
                if "pj" not in request.args else request.args["pj"]

            kwargs.update(
                {
                    'template_name': 'status_page.html',
                    'parent_job': pj,
                    'store_job_id': store_job_id,
                    'j_type': j_type,
                }
            )

        elif 'Removed' in status:
            kwargs.update(
                {
                    'template_name': 'status_page.html',
                    'status': 'removed',  # override old status for use during template rendering
                    'parent_job': pj
                }
            )

        else:
            raise IOError(f"Incorrect status of job {job_id} in database")

    else:  # indicates no such job exists in the database
        kwargs = {
            'template_name': 'job_not_found.html',
            'job_id': secure_filename(job_id),
            'help_enabled': False
        }

    if kwargs['template_name'] == 'status_page.html':
        if request.args.get('store_job_id') == 'True':  # explicitly left as str
            scripts.append(f"storeJobId('{job_id}','{job.job_type}', '{job.title}')")
            scripts.append(f"redirect('{url_for('result.show_result', job_id=job_id)}')")

        if status in ('waiting', 'queued'):  # status will never be
                # unassigned as it is always assigned if the template name is status_page.html
            scripts.append("setTimeout(function () { location.reload(true); }, 15000)")

    kwargs.update(
        {'scripts_to_execute': markupsafe.Markup(';'.join(scripts))}
    )

    return show_template(**kwargs)


@result.route("/download/<job_id>", methods=["GET", "POST"])
def return_user_download(job_id: str) -> Union[Union[str, Tuple[str, int]], Any]:
    """Returns zipped file to client, enabling the user to download the file

    Input:
        - job_id: job ID for which the results are requested

    Output:
        - Downloads zipped file to the client's side. Therefore, the files
            stored on the server are transferred to the client.

    Currently only supports downloading of the .zip file.
    """
    job_id = secure_filename(job_id)
    # this will cause internal server error if an invalid job_id is given

    # TODO future: send_from_directory is a safer approach and should be used
    # as Flask should not be serving files when deployed. Actually, NGINX should serve the files
    # result_path =
    fp = generate_filepath(
        job_id=job_id,
        jobs_folder='results',
        suffix=None,
        extension='zip',
        return_absolute_path=False
    )
    try:
        resp: Response

        resp = send_file(fp)
        resp.headers['BINARY'] = 1
        return resp
    except FileNotFoundError:
        return show_template("job_not_found.html", job_id=job_id)


@result.route("/", methods=["GET", "POST"])
def result_from_job_id() -> t.Union[str, str]: # actual other Union return type
    # is: werkzeug.wrappers.response.Response
    """Shows page for navigating to results page of job ID or that page itself

    Input:
        No inputs

    Output:
        - HTML represented in string format. Renders different templates
            whether the job ID is present in the SQL database or not ("POST"
            request), or the page for entered a job ID is requested ("GET"
            request).

    """
    if request.method == "GET":
        return show_template("result_from_jobid.html", help_enabled=False)
    else:  # can only be POST as GET and POST are the only allowed methods
        job_id = request.form["job_id"]
        if fetch_job_from_db(job_id) is not None:
            return show_template('redirect.html', url=url_for('result.show_result', job_id=job_id))
        else:
            return show_template("job_not_found.html", job_id=job_id)


@result.route("/stage/<job_id>")
def get_execution_stage(job_id: str):
    job = fetch_job_from_db(job_id)
    if job is None:
        return show_template("job_not_found.html", job_id=job_id)

    # queued situation
    if job.status != 'running':
        return {
            'finished': -1,
            'total': None,
            'jobStatus': job.status
        }

    stages = create_execution_stages(
        job_type=job.job_type,
        job_id=job.id,
        options=job.options,
        stack='back-end'
    )

    # running situation
    logs = get_log_file_contents(job_id)

    if job.status != 'running':  # double check to prevent odd situations
        raise ValueError('Function should not reach this code')

    data = {
        'finished': -1,
        'total': len(stages),
        'jobStatus': job.status
    }

    for stage in stages:
        if stage in logs:
            data['finished'] += 1

    return json.dumps(data)


@result.route("/plots/<job_id>")
def get_plot_contents(job_id) -> str:
    """Returns the HTML code of a plot as a string

    Input:
        - job_id: job ID for which the plot is requested

    """
    job = fetch_job_from_db(job_id)
    if job is None:
        return show_template("job_not_found.html", job_id=job_id)
    html = prepare_finished_result(job_id, job.job_type)[0]
    resp = flask.Response(html)

    resp.headers['NO-CSP'] = 1
    return resp

@result.route("/log/<job_id>")
def get_job_log(job_id) -> str:
    job = fetch_job_from_db(job_id)
    if job is None:
        return show_template("job_not_found.html", job_id=job_id)

    return get_log_file_contents(job_id)
