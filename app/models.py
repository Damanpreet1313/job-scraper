from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text

from app.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    company = Column(String, index=True, nullable=False)
    title = Column(String, nullable=False)
    location = Column(String, nullable=True)
    url = Column(String, nullable=False)
    source = Column(String, nullable=False)  # greenhouse | lever | ashby | remoteok | weworkremotely
    posted_date = Column(String, nullable=True)  # kept as raw string, sources format this differently
    description = Column(Text, nullable=True)

    content_hash = Column(String, unique=True, index=True, nullable=False)

    match_score = Column(Float, nullable=True)
    matched = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "company": self.company,
            "title": self.title,
            "location": self.location,
            "url": self.url,
            "source": self.source,
            "posted_date": self.posted_date,
            "match_score": self.match_score,
            "matched": self.matched,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
