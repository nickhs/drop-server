from core import db
import datetime


class ModelMixin():
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    modified_at = db.Column(db.DateTime, default=datetime.datetime.now,
            onupdate=datetime.datetime.now)
    deleted_at = db.Column(db.DateTime)

    @property
    def deleted(self):
        if self.deleted_at:
            return True
        return False

    def to_dict(self):
        d = {}
        for column in self.__table__.columns:
            d[column.name] = getattr(self, column.name)
            if isinstance(d[column.name], datetime.datetime):
                d[column.name] = d[column.name].isoformat()

        return d
