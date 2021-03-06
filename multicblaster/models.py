from datetime import datetime
from multicblaster import db

## SQLAlchemy database classes #TODO: move it to another file
class Job(db.Model):
    id = db.Column(db.String(15), primary_key=True)
    redis_id = db.Column(db.String(80))
    post_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    start_time = db.Column(db.DateTime)
    finish_time = db.Column(db.DateTime)

    status = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"ID: {self.id}; Status: {self.status}; Posted: {self.post_time}; Started: {self.start_time}; Finished: {self.finish_time}"

class Statistic(db.Model):
    name = db.Column(db.String(20), primary_key=True)
    count = db.Column(db.Integer, default=0, nullable=False)

    def __repr__(self):
        return f"{self.name.capitalize()}: {self.count} jobs"