from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, ARRAY, DateTime, Date, Index
from sqlalchemy.dialects.postgresql import JSONB
from app.dal import Base


class SearchEvent(Base):
    __tablename__ = "search_events"

    id = Column(Integer, primary_key=True, index=True)
    query_text = Column(String(500), nullable=False)
    query_embedding = Column(Text)
    user_id = Column(String(128), index=True)
    dept_id = Column(String(64))
    hit_doc_ids = Column(ARRAY(Text))
    hit_scores = Column(ARRAY(Float))
    filter_conditions = Column(JSONB)
    search_duration_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class HeatmapStats(Base):
    __tablename__ = "heatmap_stats"

    id = Column(Integer, primary_key=True, index=True)
    stat_type = Column(String(20), nullable=False)
    stat_key = Column(String(500), nullable=False)
    stat_date = Column(Date, nullable=False)
    count = Column(Integer, default=0)
    unique_users = Column(Integer, default=0)
    avg_duration_ms = Column(Float)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_heatmap_stats_type_date', 'stat_type', 'stat_date'),
        Index('idx_heatmap_stats_unique', 'stat_type', 'stat_key', 'stat_date', unique=True),
    )
