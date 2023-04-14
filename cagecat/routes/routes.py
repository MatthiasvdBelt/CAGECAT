"""Stores routes for Flask web application

Author: Matthias van den Belt
"""

# package imports
import copy
import os
import re

from flask import url_for, redirect, request

from cagecat import app
from cagecat.classes import CAGECATJob

# own project imports
from cagecat.const import submit_url, extract_clusters_options, jobs_dir
from cagecat.db_utils import fetch_job_from_db
from cagecat.docs.help_texts import help_texts
from cagecat.forms.forms import CblasterSearchBaseForm, CblasterRecomputeForm, CblasterSearchForm, CblasterGNEForm, CblasterExtractSequencesForm, \
    CblasterExtractClustersForm, CblasterVisualisationForm, ClinkerBaseForm, ClinkerDownstreamForm, ClinkerInitialForm, CblasterSearchHMMForm, \
    CblasterExtractSequencesFormHMM, GeneralForm
from cagecat.general_utils import show_template, get_server_info, send_email
from cagecat.routes.routes_helpers import show_invalid_submission
from cagecat.routes.submit_job_helpers import validate_full_form, generate_job_id, prepare_search, get_previous_job_properties, \
    save_file, enqueue_jobs
from cagecat.tools.tools_helpers import get_search_mode_from_job_id
from config_files.config import cagecat_version, thresholds
from config_files.sensitive import sender_email


# route definitions

@app.route('/cagecat')
def home_page_old_url():
    return redirect(url_for('home_page'))

@app.route('/')
def home_page():
    return show_template('index.html', help_enabled=False)

@app.route('/output-files')
def output_files_explanation():
    return show_template('output_descriptions.html', help_enabled=False)

@app.route("/help")
def help_page() -> str:
    """Shows the help page to the user

    Output:
        - HTML represented in string format
    """
    return show_template("help.html", version=cagecat_version, help_enabled=False)


@app.route("/docs/<input_type>")
def get_help_text(input_type):
    """Returns help text corresponding to the requested input parameter

    Input:
        - input_type: HTML name of the input parameter

    Output:
        - help texts of input parameter. Keys: "title", "module", "text"
    """

    if input_type not in help_texts:
        return {
            'title': 'Missing help text',
            'module': '',
            'text': 'This help text is missing. Please submit feedback and indicate'
            ' of which parameter the help text is missing.\n\nThanks in advance.'}

    return help_texts[input_type]


@app.route('/status')
def get_server_status():
    return get_server_info()

@app.route('/tutorial')
def tutorial():
    return show_template("tutorial.html", help_enabled=False)

# Error handlers
@app.errorhandler(404)
def page_not_found(error):  # should have 1 parameter, doesn't have to be used
    """Shows page displaying that the requested page was not found

    """
    return show_template("page_not_found.html",
                                               stat_code=404,
                                               help_enabled=False)


@app.errorhandler(405)
def invalid_method(error):  # should have 1 parameter, doesn't have to be used
    """Redirects user to home page if method used for request was invalid

    """
    return redirect(url_for("home_page"))

# within routes.py to prevent circular import (as it was first in const.py).
# Additionally, this variable does not have to be updated manually, and
# is therefore left out of const.py
@app.route(submit_url, methods=["POST"])
def submit_job() -> str:
    """Handles job submissions by putting it onto the Redis queue
    # TODO: form validation should be before creating directories,
       otherwise many empty directories will be created for jobs that are actually invalid

    Input:
        No inputs

    Output:
        - redirect to results page of the generated job ID

    Raises:
        - NotImplementedError: when functionality that has not been implented
            yet is called.
        - IOError: failsafe for when for some reason no jobID or sessionFile
            was given
    """
    errors = validate_full_form(GeneralForm, request.form)
    if errors:
        return show_invalid_submission(errors)

    new_jobs = []

    job_type = request.form["job_type"]
    job_id = generate_job_id()

    # Note that the "{module}PreviousType" is submitted via the form, but is
    # only used if a previous job ID or previous session file will be used

    if job_type == "search":
        # first check if the base form is valid
        errors = validate_full_form(CblasterSearchBaseForm, request.form)
        if errors:
            return show_invalid_submission(errors)

        forms_to_validate = []
        if job_type == 'recompute':
            forms_to_validate.append(CblasterRecomputeForm)
        elif job_type == 'search':

            if 'mode' in request.form:
                if request.form['mode'] == 'hmm':
                    forms_to_validate.append(CblasterSearchHMMForm)
                elif request.form['mode'] == 'remote':
                    forms_to_validate.append(CblasterSearchForm)
                elif request.form['mode'] == 'combi_remote':
                    forms_to_validate.extend((CblasterSearchForm, CblasterSearchHMMForm))
                else:
                    raise ValueError('Incorrect mode found:', request.form['mode'])
            else:
                print('No mode found')

        else:
            raise ValueError('Incorrect job type returned')

        for form_type in forms_to_validate:
            errors = validate_full_form(form_type, request.form)
            if errors:
                return show_invalid_submission(errors)

        file_path, job_type = prepare_search(job_id, job_type)

        new_jobs.append(CAGECATJob(job_id=job_id,
                                   options=request.form,
                                   job_type=job_type,
                                   file_path=file_path))

    elif job_type == "gne":
        errors = validate_full_form(CblasterGNEForm, request.form)
        if errors:
            return show_invalid_submission(errors)

        new_jobs.append(CAGECATJob(job_id=job_id,
                                   options=request.form,
                                   file_path=get_previous_job_properties(job_id, job_type, "gne")))

    elif job_type == "extract_sequences":
        # For now, only when coming from a results page (using a previous job
        # id) is supported
        parent_job_id = request.form['prev_job_id']
        prev_job_search_mode = get_search_mode_from_job_id(
            job_id=parent_job_id
        )

        if prev_job_search_mode in ('hmm', 'combi_remote'):
            form = CblasterExtractSequencesFormHMM
        else:
            form = CblasterExtractSequencesForm

        errors = validate_full_form(form, request.form)
        if errors:
            return show_invalid_submission(errors)

        new_jobs.append(CAGECATJob(job_id=job_id,
                                   options=request.form,
                                   file_path=os.path.join(jobs_dir,
                                                          parent_job_id,
                                              "results",
                                              f"{request.form['prev_job_id']}_session.json")))

    elif job_type == "extract_clusters":
        errors = validate_full_form(CblasterExtractClustersForm, request.form)
        if errors:
            return show_invalid_submission(errors)

        prev_job_id = fetch_job_from_db(
            request.form["prev_job_id"]).main_search_job

        if prev_job_id == "null":
            prev_job_id = request.form["prev_job_id"]
        # For now, only when coming from a results page (using a previous job
        # id) is supported

        new_jobs.append(CAGECATJob(job_id=job_id,
                                   options=request.form,
                                   file_path=os.path.join(jobs_dir,
                                                          prev_job_id,
                                              "results",
                                              f"{prev_job_id}_session.json")))

    elif job_type == "clinker_query":
        errors = validate_full_form(CblasterVisualisationForm, request.form)
        if errors:
            return show_invalid_submission(errors)

        new_jobs.append(CAGECATJob(job_id=job_id,
                                   options=request.form,
                                   file_path=os.path.join(jobs_dir,
                                                          request.form['prev_job_id'],
                                                          "results",
                                                          f"{request.form['prev_job_id']}_session.json")))

    elif job_type == "clinker":
        errors = validate_full_form(ClinkerBaseForm, request.form)
        if errors:
            return show_invalid_submission(errors)

        if 'clinkerEnteredJobId' in request.form:  # indicates it was downstream
            errors = validate_full_form(ClinkerDownstreamForm, request.form)
            if errors:
                return show_invalid_submission(errors)

            prev_job_id = request.form["clinkerEnteredJobId"]

            if fetch_job_from_db(prev_job_id).job_type == 'extract_clusters':
                genome_files_path = os.path.join(jobs_dir, prev_job_id, "results")
                cluster_number = len(os.listdir(genome_files_path))
                # check if exceeds
                if cluster_number > thresholds['max_clusters_to_plot']:
                    # can be a redirect. now the url remains /submit_job
                    return show_template('clinker_too_many_clusters.html',
                                         cluster_number=cluster_number,
                                         cluster_threshold=thresholds['max_clusters_to_plot'])
                depending_on = None
            else:
                # below is a check if detected cluster count does not exceed the plotting limit

                # load html
                html_path = os.path.join(jobs_dir, prev_job_id, 'results', f'{prev_job_id}_plot.html')
                with open(html_path) as inf:
                    contents = inf.read()

                pattern = re.compile(r'"counts": .+ "clusters": (\d+)')
                cluster_number = int(re.findall(pattern, contents)[0])

                # remove html file from memory
                del contents

                # check if exceeds
                if cluster_number > thresholds['max_clusters_to_plot']:
                    # can be a redirect. now the url remains /submit_job
                    return show_template('clinker_too_many_clusters.html',
                                         cluster_number=cluster_number,
                                         cluster_threshold=thresholds['max_clusters_to_plot'])

                # end of check

                new_jobs.append(CAGECATJob(job_id=job_id,
                                           options=copy.deepcopy(extract_clusters_options),
                                           job_type='extract_clusters',
                                           file_path=os.path.join(jobs_dir,
                                                                  prev_job_id,
                                                                  "results",
                                                                  f"{prev_job_id}_session.json")))

                genome_files_path = os.path.join(jobs_dir, job_id, "results")
                depending_on = new_jobs[-1].job_id

        elif request.files:  # started as individual tool
            errors = validate_full_form(ClinkerInitialForm, request.form)
            if errors:
                return show_invalid_submission(errors)
                # check if exceeds
            cluster_number = len(request.files.getlist('fileUploadClinker'))
            if cluster_number > thresholds['max_clusters_to_plot']:
                # can be a redirect. now the url remains /submit_job
                return show_template('clinker_too_many_clusters.html',
                                         cluster_number=cluster_number,
                                     cluster_threshold=thresholds['max_clusters_to_plot'])
            for f in request.files.getlist('fileUploadClinker'):
                if f.filename:
                    save_file(f, job_id)
                    genome_files_path = os.path.join(jobs_dir, job_id, "uploads")
                else: # indicates the example was posted
                    genome_files_path = os.path.join('cagecat', 'example_files')
            depending_on = None

        else:
            raise ValueError('Incorrect submitted options (clinker)')

        new_jobs.append(CAGECATJob(job_id=job_id if depending_on is None else generate_job_id(),
                                   options=request.form,
                                   file_path=genome_files_path,
                                   depends_on_job_id=depending_on))

    else:  # future input types
        raise NotImplementedError(f"Module {job_type} is not implemented yet in submit_job")

    last_job_id = enqueue_jobs(new_jobs)
    last_job = fetch_job_from_db(last_job_id)

    url = url_for("result.show_result",
                  job_id=last_job.id,
                  pj=last_job.depending_on,
                  store_job_id=True,
                  job_title=last_job.title,
                  email=last_job.email,
                  j_type=last_job.job_type)

    return show_template('redirect.html', url=url)  # redirect to store job info at client side


@app.route('/submit-feedback', methods=['POST'])
def submit_feedback() -> str:
    """Page which handles submitted feedback

    Input:
        - No input

    Output:
        - HTML represented in string format
    """
    for email in (sender_email, request.form['email']):
        send_email('CAGECAT feedback report',
                      f'''

Thank you for your feedback report. The development team will reply as soon as possible. The team might ask you for additional information, so be sure to keep your inbox regularly.

-----------------------------------------
Submitted info:

Feedback type: {request.form['feedback_type']}
E-mail address: {request.form['email']}
Job ID: {request.form['job_id']}
Message: {request.form['message']}

-----------------------------------------''',
                      email)

    return show_template('redirect.html', url=url_for('feedback_submitted'))


@app.route('/feedback-submit')
def feedback_submitted() -> str:
    """Shows a page to the user indicating their feedback has been submitted

    Output:
        - HTML represented in string format
    """
    return show_template('feedback_submitted.html', help_enabled=False)
