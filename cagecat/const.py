"""Module to store constants such as help texts

Author: Matthias van den Belt
"""
import os
import re

from config_files.config import thresholds

clinker_modules = ('clinker_query', 'clinker')
modules_with_plots = ["search", "recompute", "gne", "clinker", "clinker_query"]

fasta_extensions = (".fa", ".fsa", ".fna", ".fasta", ".faa")
genbank_extensions = (".gbk", ".gb", ".genbank", ".gbf", ".gbff")

submit_url = "/submit_job"
hmm_database_kingdoms = ('bacteria', 'fungi')

clust_number_with_score_pattern = r"\(Cluster (\d+), score: \d+\.\d+\)"
clust_number_without_score_pattern = r"\(Cluster (\d+)"
clust_number_with_clinker_score_pattern = r"\(Cluster (\d+), \d+\.\d+ score\)"
jobs_dir = os.path.join("cagecat", "jobs")
folders_to_create = ["uploads", "results", "logs"]

connection_error_user_friendly_message = 'A connection error between CAGECAT and NCBI occurred. The NCBI servers are probably experiencing difficulties processing our requests. Please try again at a later moment. If this problem persists, please let us know by providing feedback.'
no_hits_message = 'Your search with the specified parameters did not return any {} hits. Check your input, and try to loosen your search parameters to get results.'
sanitization_message = 'An error occurred during sanitization of your input file. Please make sure your input file adheres to the standardized format and does not contain any special characters.'
invalid_ncbi_response = 'The response CAGECAT received from NCBI was not as expected. Please retry submitting your job. If this error persists, submit feedback to notify the developers of this specific situation.'

failure_reasons = {
    'ValueError: not enough values to unpack':  # cblaster remote search, when people DNA sequences, in FASTA or GBK file. Was because of invalid NCBI response
        invalid_ncbi_response,
    'ERROR - No valid profiles could be selected':  # module search, hmm/hmm+remote mode, incorrect HMM profiles;
    # Results in the following exception: TypeError: object of type 'NoneType' has no len()
        'No valid HMM profiles have been entered. Check the entered HMM profile for potential spelling errors and make sure all entered HMM profile identifiers are valid Pfam identifiers (https://pfam.xfam.org/). GenPept accessions of NCBI are not valid.',
    'ValueError: Search completed, but found no hits':  # module search, no hits found
        no_hits_message.format('blast'),
    'ValueError: No results found':
        no_hits_message.format('cluster'),

    'Too many selected clusters':  # clinker, clinker_query, extract_clusters
        'You have selected too many clusters to use in your downstream analysis. Check the maximum number of clusters for the analysis you were trying to execute, and try again.',
    'Too many samples':  # gne module
        'You set the value for the number of samples parameter too high. Change it to the maximum value and try again.',

    # Connection errors. Intentionally broad exceptions as should handle all exceptions from the requests and urllib packages
    'requests.exceptions':
        connection_error_user_friendly_message,
    'urllib.error':
        connection_error_user_friendly_message,
    'Failed to fetch sequences':
        'An error occurred when fetching sequences from NCBI. Did you enter your NCBI identifiers correctly?',

    'sqlite3.OperationalError: unable to open database file':
        'Internally, CAGECAT was unable to open the selected genus database. Please submit feedback as this should not happen.',

    'Failed to read the Blast query: Nucleotide FASTA provided for protein sequence':
        'The NCBI identifiers you entered refer to nucleotide sequences. Currently, cblaster only accepts GenPept NCBI identifiers (protein sequences). As a solution, you are able to manually download the nucleotide FASTA/GenBank files of the entered NCBI identifiers, and upload these files in your cblaster search job.',
    
    'OSError: Unable to parse NCBI response':
        invalid_ncbi_response,

    'NotImplementedError':
        'The settings you submitted are not implemented in the analysis tool you selected. The developers have been notified of this scenario and this scenario will be hidden in a future update.',
    # 'No protocol for mode':
    #     'The used search mode is not yet implemented for the extract_clusters module. Please submit feedback to the developers to notify of this scenario.',

    'ERROR - No files found':
        'No files were given when trying to execute clinker. Please retry to submit your analysis.',

    "'utf-8' codec can't decode byte":
        sanitization_message,

    'Error when parsing FASTA file':
        'Your FASTA file could not be parsed successfully. Please make sure that your input file adheres to the standardized FASTA format.',

    'Your total query length is greater than allowed on the BLAST webserver.':
        'The length of your input sequence(s) exceeds the limit of the BLAST webserver. Did you upload a whole genome file? If yes, reduce your input file to the regions of interest.',

    'RecursionError: maximum recursion depth exceeded while encoding a JSON object':
        'An error occurred when writing your results (maximum recursion depth). Please notify the developers.',

    'Invalid extension found':
        'You submitted a file with an invalid extension. Please refer to the documentation to check the allowed file types.',

    'Incorrect FASTA file type':
        'An incorrect FASTA file was provided. Your FASTA file should either contain nucleotides or amino acids, not both.',

    'Error during sanitization by antiSmash':
        sanitization_message,

    'argument session: Invalid path:':  # occurs when workflow is:  cblaster search -> cblaster recompute -> cblaster plot_queries -> cblaster extract_clusters.
        'Referencing to a file during a process of CAGECAT failed. This happens in the workflow: cblaster search -> cblaster recompute -> cblaster plot_queries -> cblaster extract_clusters.\n It is a known bug, and will be fixed in a future release. Please submit feedback to notify the developers that you encountered this bug. For now, you can directly extract clusters from your recompute job. Apologies for the inconvenience.',
}

regex_failure_reasons = [
    # contains patterns
    (
        re.compile('Entrez Query: .+ is not supported'),
        'An invalid Entrez query was submitted. Did you forget to add "[organism]" at the end?'
    ),
    (
        re.compile('ERROR\s+\d+\/\d+\s\d+:\d+:\d+\s+no valid records found in file'),
        'Your input file did not contain any valid records. Does your file have the correct extension/content combination? (e.g. a file with FASTA contents with a GenBank extension could cause this error)'
    ),

    (
        re.compile('ERROR\s+\d+\/\d+\s\d+:\d+:\d+\s+protein records are not supported'),
        'Your input file is a GenPept file. The supported file formats for a cblaster search are: nucleotide FASTA, protein FASTA, GenBank. For a clinker job, the supported file format is the GenBank format.'  # check if this also occurs for a clinker job
    )


]

module_to_tool = {
    'search': 'cblaster',
    'gne': 'cblaster',
    'recompute': 'cblaster',
    'extract': 'cblaster',
    'extract_clusters': 'cblaster',
    'clinker_query': 'cblaster',
    'clinker': 'clinker'
}

extract_clusters_options = {
    'job_type': 'extract_clusters',
    "selectedOrganisms": "",
    "selectedScaffolds": "",  # empty strings as
    "clusterNumbers": "",  # if nothing was
    "clusterScoreThreshold": "",  # filled in in the
    "prefix": "",  # submission form
    "format": "genbank",
    "maxclusters": str(thresholds['maximum_clusters_to_extract'])}  # indicates no maximum

# values can also be tuples
downstream_modules = {
    "search": [
        "recompute",
        "gne",
        "extract_sequences",
        "extract_clusters",
        "clinker",
        "clinker_query"],
    "recompute": [
        "gne",
        "extract_sequences",
        "extract_clusters",
        "clinker",
        "clinker_query"],
    "gne": [],
    "extract_sequences": [],
    "extract_clusters": ["clinker"],  # also possible: corason and clinker_query. Get query headers from .csv file
    "clinker": [],
    "clinker_query": ["extract_clusters"]  # possibly also corason?
}

### Post-analysis explanation section

# format is: {module: [(paragraph_title, text), ...]}
# {module: [('list', ('point1', 'point2', ...))]} results in an ordered list being generated
# empty paragraph title means that no header should be generated
tool_explanations = {'cblaster_search':
                         [('',
                           'Query sequences are searched against the NCBI’s BLAST API in remote mode. BLAST hits are filtered according to user defined quality thresholds. In remote mode, each hit is then queried against the NCBI’s Identical Protein Groups (IPG) resource, which, as its name suggests, groups proteins sharing identical amino acid sequence as an anti-redundancy measure. The resulting IPG table contains source genomic coordinates for each hit protein sequence, which cblaster uses to group them by their corresponding organism, scaffold and subject sequences.'),
                          ('',
                           'In order to run a cblaster search, you will need to point the module to a collection of sequences to be used as queries. These can be provided in two ways:'),
                          ('list', ('A FASTA format file containing amino acid sequences',
                                    'A list of valid NCBI sequence identifiers (e.g. accession, GI number)')),
                          ('HMMER searches',
                           'To run a domain search, you need to specify the search mode as HMM, provide an array of query Pfam domain profile names and select a database (consisting of all representative/reference genomes of the selected genus stored at NCBI) to search in. This will extract the specified domain profiles (PF00001 and PF00002) from the Pfam database and search the sequences in the selected genus database for any domain hits.'),
                          ('Result filtering',
                           'The default values for each filter are pretty generous, and may need changing based on your data. The search thresholds should be fairly self explanatory; any hit not meeting them are discarded from the BLAST search results.'),
                          ('',
                           'The clustering thresholds, however, are a bit more interesting. These determine what conditions a candidate hit cluster must satisfy in order to be detected by cblaster. The most important parameter here is Maximum Intergenic Gap, which determines how far (in base pairs) any two hits in a cluster can be from one another. This parameter could vary wildly based on your data set. For example, in bacterial or fungal secondary metabolite gene clusters where genes are typically found very close together, a low value could be used. Conversely, plant clusters, which may involve a collection of key genes spread out over the entire chromosome, would require a much higher value. The Neighbourhood module can used to calibrate this parameter based on your results'),
                          ('Output',
                           'By default, a complete summary is generated and saved to a file after the search has finished. This reports all clusters, as well as the scores and positions of each gene hit, found during the search, organized by the organisms and genomic scaffolds they belong to.'),
                          ('Binary table',
                           'An easier way to digest all of the information that cblaster will produce is by using the binary table output. This generates a matrix which shows the absence/presence of query sequence (columns) hits in each result cluster (rows). By default, the binary table will only report the total number of hits per query sequence in each cluster. However, you can instead change this to some value calculated from the actual scores of hits in the clusters.'),
                          ('',
                           'This is controlled by two additional parameters: Hit attribute, which determines which score attribute (‘identity’, ‘coverage’, ‘bitscore’ or ‘evalue’) to use when calculating cell values, and Key function, which determines the function (‘len’, ‘max’, ‘sum’) applied to the score attribute.'),
                          ('',
                           'Each cell in the matrix refers to multiple hit sequences within each cluster. For every cell, the chosen score attribute is extracted from each hit corresponding to that cell. Then, the key function is applied to the extracted scores. The ‘len’ function calculates the length of each score list - essentially just counting the number of hits in that cell. The ‘max’ and ‘sum’ functions calculate the maximum and sum of each score list, respectively.'),
                          ('Search sessions are saved',
                           'Given that searches can take a significant time to run (i.e. as long as any normal batch BLAST job will take), cblaster is capable of saving a search session to file, and loading it back later for further filtering and visualization. Once the session is saved, any subsequent runs with that session specified will make cblaster try to load it instead of performing a new search.'),
                          ('Finding intermediate genes between hits',
                           'The default output for cblaster is the cluster heatmap, which shows the absence or presence of your query sequences. While we find this is generally the easiest way to pick up on patterns of cluster conservation, we also like to be able to visualize our results in their own genomic contexts so we can see the differences in gene order, orientation, size and so on.'),
                          ('',
                           'For this reason, we added integration to the clinker tool (https://github.com/gamcil/clinker), which can generate highly interactive gene cluster comparison plots. However, in a regular cblaster search, we do not have access to any information about the genes between the BLAST hits shown in the heatmap. This means that if you were to run the Visualize with query clusters module on a previous job, you would produce a figure where most of the clusters are missing genes!'),
                          ('',
                           'To get around this, you can use the Find intermediate genes parameter when performing a cblaster search. After the search has completed, genomic regions corresponding to the detected gene clusters are retrieved from the NCBI, and used to fill in the missing genes.')
                          ],
                     'cblaster_query_visualization':
                         [('',
                           'By default, the visualisation offered by cblaster shows only a heatmap of query hits per result cluster. While this is very useful for quickly identifying patterns in large datasets, we generally still want to see how these clusters compare in a more biologically relevant way.'),
                          ('',
                           'The Visualize with query clusters module allows you to do precisely this. Given a previous job and some selected clusters, this module will automatically extract the clusters, then generate an interactive visualisation showing each cluster to-scale using clinker (doi: 10.1093/bioinformatics/btab007, https://github.com/gamcil/clinker).'),
                          ],
                     'clinker_visualization': [('', 'clinker: generating publication-quality gene cluster comparison figures.'),
                                               ('',
                                                'Given a job, corresponding GenBank files will be downloaded and clinker will automatically extract protein translations, perform global alignments between sequences in each cluster, determine the optimal display order based on cluster similarity, and generate an interactive visualisation that can be extensively tweaked before being exported as an SVG file.'),
                                               ('',
                                                'An overview of usage, as well as all changeable options, is provided in the visualisation sidebar. Briefly:'),
                                               ('list', ('Clusters can be rearranged vertically by dragging cluster names',
                                                         'Loci can be moved or resized by hovering over them and dragging the box',
                                                         'The visualisation can be anchored around a specific gene by clicking on it',
                                                         'Clusters and similarity groups can be renamed by clicking on their text',
                                                         'Similarity group colours can be changed by clicking on the circles in the legend',
                                                         'Groups can be removed by right-clicking their label in the legend',
                                                         'The scale bar can be resized by clicking its text and entering a new value (bp)'))
                                               ],
                     'neighbourhood_estimation': [('',
                                                   'In cblaster, the most important parameter when detecting hit clusters is the maximum inter-hit gap parameter. This determines how far cblaster will look between any two hits before terminating a given cluster. By default, this parameter is set to 20,000 bp; if no new hit is found within 20,000 bp of the previous hit in a cluster, cblaster will terminate extension of that cluster. Though the 20 kb cutoff has worked quite well for us when looking at fungi or bacteria, where gene density within clusters is quite high, it may not work for all datasets. For example, plant gene clusters may have key biosynthetic genes spread out over large stretches of the chromosome, with many genes in between; this is where the gne module comes in.'),
                                                  ('',
                                                   'The Neighbourhood estimation module lets you robustly detect an appropriate value to use for this parameter by continually re-running cluster detection on a saved search session at different gap values over some interval. It then generates plots of the mean and median cluster sizes (bp), as well as the total number of predicted clusters, at each value.'),
                                                  ('',
                                                   'The Neighbourhood estimation module generates a list of gap values (total number determined by the samples parameter) from 0 to some upper limit (determined by the Max. intergenic distance parameter). These numbers can be chosen in two ways. By default, Neighbourhood estimation will take evenly spaced (i.e. linear) values over the range 0-100,000 bp. Alternatively, you can choose to generate these values via a log scale, which will result in more samples at lower values than at higher ones. This can be specified using the sampling space parameter. As these plots typically resemble logarithmic growth (i.e. rise steeply, then level off), it can make sense to sample more heavily in the more unstable region of the curve')
                                                  ],
                     'extract_sequences': [('',
                                            'After a search has been performed, it can be useful to retrieve sequences matching a certain query for further analyses (e.g. sequence comparisons for phylogenies). This is easily accomplished using the Extract sequences module.'),
                                           ('',
                                            'A preceding job is used as input, and extracts sequences matching any filters you have specified. If no filters are specified, ALL hit sequences will be extracted. By default, only sequence names are extracted. This is because cblaster stores no actual sequence data for hit sequences during it’s normal search workflow, only their coordinates. However, sequences can automatically be retrieved from the NCBI by specifying the Download sequences parameter. cblaster will then write them, in FASTA format to a file.'),
                                           ('',
                                            'The Extract sequences can also filter based on the organism that each hit sequence is on. The organism filter uses regular expression patterns based on organism names, but it is not obligatory to use regular expressions.  Multiple patterns can be provided, and are additive (i.e. any organism matching any of the patterns will be saved). ')
                                           ],
                     'extract_clusters': [('',
                                           'A common next step after a cblaster search is to retrieve the identified gene clusters so we can perform additional analysis. cblaster provides the Extract clusters module precisely for this purpose, allowing you to generate GenBank files of specific gene clusters directly from a previous job. Extract all clusters from a job could take a long time for searches with many results.'),
                                          ],
                     'recompute': [('', 'You can recompute a previous job using new filter thresholds to filter previous results.')]
                     }

execution_stages = {
    # (front-end, log-descriptor)
    'clinker': [
        ('Sanitizing input files', 'Executing input file sanitization'),
        ('Parse genome files', 'Parsing files:'),
        ('Align clusters', 'Starting cluster alignments'),
        ('Summarizing results', 'Generating results'),
        ('Save session file', 'Saving session to'),
        ('Writing results', 'Writing to'),
    ],
    'search': {
        'remote': [
            ('Send search job to NCBI', 'Launching new search'),
            ('Polling NCBI', 'Polling NCBI for completion status'),
            ('Retrieving results from NCBI', 'Retrieving results for search'),
            ('Parsing results', 'Parsing results'),
            ('Fetching genomic context of hits', 'Fetching genomic context of hits'),
            # 'Searching for intermediate genes' will be inserted if applicable
            ('Writing results', 'Writing current search session'),
        ],
        'hmm': [
            ('Fetching HMM profiles from Pfam database', 'Fetching accessions from Pfam'),
            ('Searching using HMM profiles', 'Performing hmmsearch'),
            ('Fetching genomic context of hits', 'Fetching genomic context of hits'),
            ('Querying genus-specific database', 'Querying local SQLite3 database'),
            ('Writing results', 'Writing current search session'),
        ],
        'combi_remote': [
            # hmm specific
            ('Fetching HMM profiles from Pfam database', 'Fetching accessions from Pfam'),
            ('Searching using HMM profiles', 'Performing hmmsearch'),
            ('Fetching genomic context of hits', 'Fetching genomic context of hits'),
            ('Querying genus-specific database', 'Querying local SQLite3 database'),
            # remote specific
            ('Send search job to NCBI', 'Launching new search'),
            ('Polling NCBI', 'Polling NCBI for completion status'),
            ('Retrieving results from NCBI', 'Retrieving results for search'),
            ('Parsing results', 'Parsing results'),
            ('Fetching genomic context of hits', 'Fetching genomic context of hits'),
            ('Writing results', 'Writing current search session'),
        ]
    },
    'recompute': [
        ('Load previous results', 'Loading session(s)'),
        ('Filtering results with new thresholds', 'Filtering session with new thresholds'),
        # 'Fetching intermediate genes from NCBI' will be inserted if applicable
        ('Writing results', 'Writing recomputed session to'),
    ],
    'gne': [  # finished, no variations of this job type
        ('Load previous results', 'Loading session from'),
        ('Computing gene neighbourhood statistics', 'Computing gene neighbourhood statistics'),
        ('Writing GNE plot to HTML file', 'Writing GNE table to'),
        ('Writing results', 'Saving gne plot HTML'),
    ],
    'extract_clusters': [
        ('Load previous results', 'Loading session from'),
        ('Extract clusters that match threshold', 'Extracting clusters that match the filters'),
        ('Write GenBank files', 'Writing genbank files'),
        ('Query NCBI for cluster sequences', 'Querying NCBI'),
        ('Write results', 'Clusters have been written to'),
    ],
    'clinker_query': [
        ('Generate cluster plot', 'Starting generation of cluster plot with clinker'),
    ],
    'extract_sequences': [
        ('Load previous results', 'Loading session from'),
        ('Extract sequences matching filters', 'Extracting subject sequences matching filters'),
        # 'Fetch sequences from NCBI' will be inserted if applicable
        ('Write results', 'Writing output'),
    ]
}
