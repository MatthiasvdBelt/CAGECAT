"""Stores routes for Flask web application for downstream analyses

Author: Matthias van den Belt
"""

# package imports
from flask import Blueprint, request

# own project imports
from cagecat.tools.tools_helpers import read_headers, parse_selected_cluster_numbers, get_search_mode_from_job_id
from cagecat.forms.forms import CblasterSearchForm, CblasterGNEForm, CblasterExtractSequencesForm, \
    CblasterExtractClustersForm, CblasterVisualisationForm, ClinkerDownstreamForm, ClinkerInitialForm, CblasterExtractSequencesFormHMM
from cagecat.general_utils import show_template, available_hmm_databases
from cagecat.db_utils import fetch_job_from_db
from cagecat.const import tool_explanations, clinker_modules, genbank_extensions, fasta_extensions, clust_number_with_score_pattern, \
    clust_number_with_clinker_score_pattern
from config_files.config import thresholds

tools = Blueprint('tools', __name__, template_folder="templates")


### Route function definitions
@tools.route('/')
def tools_page() -> str:
    """Shows page to user showing all available tools

    Output:
        - HTML represented in string format
    """
    return show_template('implemented_tools.html', help_enabled=False)


@tools.route("/explanation")
def tools_explanation() -> str:
    """Shows page for explanation about implemented tools

    Output:
        - HTML represented in string format
    """
    return show_template("tools_explanation.html", help_enabled=False, helps=tool_explanations)


@tools.route("/search/rerun/<prev_run_id>")
@tools.route("/search")
def cblaster_search(prev_run_id: str = None) -> str:
    """Shows home page to the user

    Input:
        - prev_run_id: job ID of a previous run.

    Output:
        - HTML represented in string format

    When the /rerun/<prev_run_id> is visited, the input fields where the user
    can enter previous job IDs are pre-filled with the given job ID
    """
    if "type" in request.args:
        query_headers = [] if prev_run_id is None and request.args["type"] == "recompute" else read_headers(prev_run_id)
        module_to_show = request.args["type"]
        show_examples = False if request.args['type'] == 'recompute' else 'cblaster_search'
    else:
        query_headers = []
        module_to_show = None
        show_examples = 'cblaster_search'

    form = CblasterSearchForm(formdata=None)
    form.base.clustering.requiredSequencesSelector.choices = query_headers

    if module_to_show == 'recompute':
        scripts = ["$(':radio:not(:checked)').attr('disabled', true)"]
    else:
        scripts = ["initReadQueryFile()"]

    scripts.extend(["addAccordionListeners()", 'addCblasterSearchListeners()'])

    return show_template("cblaster_search.html",
                         all_forms=form,
                         prev_run_id=prev_run_id,
                         module_to_show=module_to_show,
                         organism_databases=available_hmm_databases,
                         query_file_extensions=','.join(fasta_extensions + genbank_extensions),
                         show_examples=show_examples,
                         scripts_to_execute=';'.join(scripts))


@tools.route("/clinker_query", methods=["POST"])
def clinker_query() -> str:
    """Shows page for selecting options to run clinker with query genes

    Output:
        - HTML represented in string format
    """
    clusters = parse_selected_cluster_numbers(
        request.form["selectedClusters"], clust_number_with_score_pattern)

    return show_template("cblaster_plot_clusters.html",
                         all_forms=CblasterVisualisationForm(formdata=None),
                         prev_job_id=request.form["job_id"],
                         cluster_headers=
                         request.form["selectedClusters"].split('\r\n'),
                         selected_clusters=clusters,
                         max_clusters_to_plot=thresholds['max_clusters_to_plot'])


@tools.route("/extract-sequences", methods=["GET", "POST"])
def extract_sequences() -> str:
    """Shows page for extracting sequences from a previous job

    Input:
        No inputs

    Output:
        - HTML represented in string format showing options for extracting
            sequences in the client's browser
    """
    parent_job_id = request.form["job_id"]
    prev_job_search_mode = get_search_mode_from_job_id(
        job_id=parent_job_id
    )

    if prev_job_search_mode in ('hmm', 'combi_remote'):
        form = CblasterExtractSequencesFormHMM()
        show_download = False
    else:
        form = CblasterExtractSequencesForm(formdata=None)
        show_download = True

    return show_template(
        template_name="cblaster_extract_sequences.html",
        all_forms=form,
        selected_queries=request.form["selectedQueries"].split('\r\n'),
        prev_job_id=parent_job_id,
        show_download=show_download
    )


@tools.route("/extract-clusters", methods=["GET", "POST"])
def extract_clusters() -> str:
    """Shows page for extracting clusters from a previous job

    Input:
        No inputs

    Output:
        - HTML represented in string format showing options for extracting
            clusters in the client's browser
    """
    selected_clusters = request.form["selectedClusters"]
    prev_job_id = request.form["job_id"]
    prev_job = fetch_job_from_db(prev_job_id)

    pattern = clust_number_with_score_pattern if \
        fetch_job_from_db(prev_job_id).job_type not in \
        clinker_modules else \
        clust_number_with_clinker_score_pattern

    cluster_numbers = parse_selected_cluster_numbers(selected_clusters, pattern)

    return show_template("cblaster_extract_clusters.html",
                         # selected_scaffolds=selected_scaffolds,
                         all_forms=CblasterExtractClustersForm(formdata=None),
                         cluster_headers=selected_clusters.split('\r\n'),
                         cluster_numbers=cluster_numbers,
                         prev_job_id=prev_job_id, prev_job_type=prev_job.job_type,
                         main_search_id=prev_job.main_search_job,
                         max_clusters_to_extract=thresholds['maximum_clusters_to_extract'])


@tools.route('/gne', methods=['GET', 'POST'])
def gene_neighbourhood_estimation() -> str:
    return show_template('cblaster_gene_neighbourhood_estimation.html',
                         all_forms=CblasterGNEForm(formdata=None),
                         max_samples=thresholds['maximum_gne_samples'],
                         prev_job_id=request.form['job_id'])


@tools.route('/clinker', methods=['GET', 'POST'])
def clinker() -> str:
    prev_job_id = None if 'job_id' not in request.form else request.form['job_id']

    if prev_job_id is None:
        form = ClinkerInitialForm(formdata=None)
    else:
        form = ClinkerDownstreamForm(formdata=None)

    scripts = ['addAccordionListeners()']
    if request.method == 'GET':
        show_examples = 'clinker'
        scripts.append('addClinkerStartPointListeners()')
    else:
        show_examples = None

    return show_template('clinker.html',
                         all_forms=form,
                         query_file_extensions=','.join(genbank_extensions),
                         show_examples=show_examples, thresholds=thresholds,
                         prev_job_id=prev_job_id,
                         scripts_to_execute=';'.join(scripts))
