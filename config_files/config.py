"""Module with changeable parameters if something would change in the future

Author: Matthias van den Belt
"""
cagecat_version = '3.3'
# When the version number is changed, /repo/maintenance/store_version_info.py should be run
# also, the cache busting of the JavaScript file and CSS file in cagecat/templates/base.html
# should be updated. (i.e. scripts.js?v=3.2 -> scripts.js?v=3.3)

# changeable
send_mail = True
period_to_keep_job_results = 31
domain = 'https://cagecat.bioinformatics.nl/'
NCBI_ftp_base_url = 'ftp.ncbi.nlm.nih.gov'

hmm_db_creation_conf = {
    'sleeping_time': 60,
    'cpus': '10',
    'batch_size': '30'}

thresholds = {
    'maximum_clusters_to_extract': 150,
    'maximum_gne_samples': 300,
    'max_clusters_to_plot': 75,
    "prokaryotes_min_number_of_genomes": 50,
    'fungi_min_number_of_genomes': 10
}

email_footer_msg = f'''Thank you for using our service. 

>> If you found this service useful, spread the word.
    
Kind regards,
    
The CAGECAT team
{domain}'''

# folders. Note that if these paths are changed, bash scripts might fail.
maintenance_logs = '/process_logs/maintenance'
server_prefix = '/repo'
sanitized_folder = '/sanitization'
finished_hmm_db_folder = '/hmm_databases'
pfam_db_folder = '/pfam_db'
hmm_db_genome_downloads = '/hmm_db_downloads'

# database
init_config = {
    'SQLALCHEMY_DATABASE_URI': 'sqlite:////repo/cagecat/database.db',
    "SQLALCHEMY_TRACK_MODIFICATIONS": False,
}
