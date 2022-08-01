"""Module storing general utility functions

Author: Matthias van den Belt
"""
import os
import smtplib
import typing as t
from email.message import EmailMessage

import redis
import rq
from flask import render_template
from rq.registry import StartedJobRegistry

from cagecat import q, r
from cagecat.const import jobs_dir, hmm_database_organisms
from cagecat.db_utils import fetch_statistic_from_db
from config_files.config import email_footer_msg, finished_hmm_db_folder, send_mail
from config_files.notifications import notifications
from config_files.sensitive import account, pwd, smtp_server, sender_email, port

available_hmm_databases = None

def send_email(subject: str, message: str, receiving_email: str) -> None:
    """Send an email

    Input:
        - subject: subject of the email
        - message: body content of the email
        - receiving_email: e-mail address of the receiver

    Output:
        - None, sent emails
    """
    if send_mail:
        with smtplib.SMTP(smtp_server, port=port) as server:
            msg = EmailMessage()
            server.starttls()
            server.ehlo()

            server.login(account, pwd)

            msg['Subject'] = subject
            msg['From'] = sender_email
            msg['To'] = receiving_email
            msg.set_content(f'{message}\n{email_footer_msg}')
            server.send_message(msg)


def show_template(template_name: str, help_enabled:bool = True,
                  stat_code=None, show_examples=None, **kwargs) -> t.Union[str, t.Tuple[str, int]]:
    """Returns rendered templates to the client

    Input:
        - template_name: name of template to be rendered. By default,
            templates should be located in the templates/ folder
        - help_enabled: show help pane
        - stat_code, int: HTTP status code to be returned to the client
        - kwargs: keyword arguments used during rendering of the template

    Output:
        - rendered template (HTML code) represented in string format

    Function was created to prevent redundancy when getting the server info
    and uses Flask's render_template function to actually render the templates
    """
    if stat_code is None:
        return render_template(template_name, help_enabled=help_enabled,
                               serv_info=get_server_info(q, r),
                               show_examples=show_examples,
                               notifications=notifications,
                               **kwargs)
    else:
        return render_template(template_name, help_enabled=help_enabled,
                               serv_info=get_server_info(q, r),
                               show_examples=show_examples,
                               notifications=notifications,
                               **kwargs), stat_code


def get_server_info(queue: rq.Queue = None, redis_conn: redis.Redis = None) \
        -> t.Dict[str, t.Union[str, int]]:
    """Returns current server statistics and information

    Input:
        - q, rq.Queue: connection to queue of jobs waiting to be executed
        - redis_conn, redis.Redis: instance of Redis server. Used to connect
            to Redis

    Output:
        - dict: info about the current status of the server and queued
            or running jobs
    """
    # TODO future: optimization: maybe we can instantiate this registry once instead of every time
    if queue is None:
        queue = q
    if redis_conn is None:
        redis_conn = r

    start_registry = StartedJobRegistry('default', connection=redis_conn)
    running = len(start_registry)

    return {
        "server_status": 'idle' if running == 0 else 'running',
        "queued": len(queue),
        "running": running,
        "completed": fetch_statistic_from_db("finished").count
        }


def generate_paths(job_id: str) -> t.Tuple[str, str, str]:
    """Returns paths for logging and result directories

    Input:
        - job_id: ID corresponding to the job the function is called for

    Output:
        - [0]: base path for the job
        - [1]: path for the logging directory
        - [2]: path for the results directory
    """
    base = os.path.join(jobs_dir, job_id)
    return base, os.path.join(base, "logs"), os.path.join(base, "results")


def list_available_hmm_databases():
    all_databases = {}

    for organism_folder in os.listdir(finished_hmm_db_folder):
        genera = set()
        if organism_folder == 'logs':
            continue

        if organism_folder not in hmm_database_organisms:
            return 'Incorrect organism folder in HMM databases'

        organism_path = os.path.join(finished_hmm_db_folder, organism_folder)
        for file in os.listdir(organism_path):
            genus = file.split('.')[0]

            genera.add(genus)

        all_databases[organism_folder.capitalize()] = sorted(list(genera))

    return all_databases


available_hmm_databases = list_available_hmm_databases()
