from sqlalchemy.ext.declarative import declarative_base
from service_forge.db.trace_mixin import register_trace_events

Base = declarative_base()
register_trace_events(Base)