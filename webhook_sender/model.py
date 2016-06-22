import sqlalchemy as sa
import datetime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

__all__ = ['Webhook']

class Webhook(Base):
    __tablename__ = 'webhook'
    __name__ = 'webhook'
    id = sa.Column(sa.Integer, primary_key=True, doc="primary key")
    url = sa.Column(sa.String, nullable=False)
    message = sa.Column(sa.String, nullable=False)
    retryat = sa.Column(sa.DateTime(), default=datetime.datetime.utcnow)
    received = sa.Column(sa.Boolean, default=False)
    attempts = sa.Column(sa.Integer, default=0)

    def __init__(self, url, message, retryat=None, attempts=0):
        self.url = url
        self.message = message
        self.retryat = retryat
        self.attempts = attempts

