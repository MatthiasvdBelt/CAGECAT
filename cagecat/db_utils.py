"""Stores models of entities for SQL database interacted by with SQLAlchemy,
along with functionality to query the SQL database

Author: Matthias van den Belt
"""

import typing as t

from werkzeug.utils import secure_filename

from cagecat import db

## SQLAlchemy database classes
class Job(db.Model):
    """Model for creating a job entry

        Inherits from db.Model
    """
    id = db.Column(db.String(15), primary_key=True)
    job_type = db.Column(db.String(10), nullable=False)
    redis_id = db.Column(db.String(80))
    status = db.Column(db.Text, nullable=False)
    options = db.Column(db.String(100))

    # user-specified items
    title = db.Column(db.String(60))
    email = db.Column(db.String(100))

    # connecting jobs
    main_search_job = db.Column(db.String(15))
    child_jobs = db.Column(db.String(), default="")
    depending_on = db.Column(db.String(10))

    # timing
    post_time = db.Column(db.String(50))
    start_time = db.Column(db.String(50))
    finish_time = db.Column(db.String(50))

    def __repr__(self):
        return f"ID: {self.id}; Type: {self.job_type}; " \
               f"Status: {self.status}; " \
               f"Finished: {self.finish_time}; Main job{self.main_search_job}"


class Statistic(db.Model):
    """Model for creating an entry for job statistics

    Inherits from db.Model

    """
    name = db.Column(db.String(20), primary_key=True)
    count = db.Column(db.Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f"{self.name.capitalize()}: {self.count} jobs"


class Versions(db.Model):
    """Model for logging of versions of used packages/tools

    """

    cagecat_version = db.Column(db.String(), primary_key=True)
    pfam = db.Column(db.String(), nullable=False)
    pip = db.Column(db.String(), nullable=False)

    def __repr__(self) -> str:
        return f'\nCAGECAT version: {self.cagecat_version}\n\n' \
               f'Pfam version\n: {self.pfam}\n' \
               f'Python packages (pip)\n: {self.pip}\n'

# Functions to query the database
def fetch_job_from_db(job_id: str) -> t.Optional[Job]:
    """Checks if a job with a specific job ID exists in the database

    Input:
        - job_id: ID of a job to search for

    Output:
        - Job instance if present in the database OR
        - None if no job with the given ID was found in the database
    """
    job_id = secure_filename(job_id)
    return Job.query.filter_by(id=job_id).first()


def fetch_statistic_from_db(name: str):
    return Statistic.query.filter_by(name=name).first()
