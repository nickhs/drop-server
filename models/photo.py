from core import db, config
from mixins import ModelMixin
import os
import datetime
from flask import url_for


class Services:
    SNAPCHAT = 1


class Photo(db.Model, ModelMixin):
    id = db.Column(db.Integer, primary_key=True)
    service = db.Column(db.Integer)
    owner = db.Column(db.String)
    rel_location = db.Column(db.String, unique=True, index=True)
    external_id = db.Column(db.String, index=True)
    seen_at = db.Column(db.DateTime)
    is_video = db.Column(db.Boolean)

    def init(self, rel_location, service=Services.SNAPCHAT, owner=None, external_id=None, is_video=False):
        self.rel_location = rel_location
        self.service = service
        self.owner = owner
        self.external_id = external_id
        self.is_video = is_video

    @property
    def location(self):
        return os.path.join(config.LOCAL_SERVER_LOCATION, self.rel_location)

    def mark_seen(self, commit=True):
        self.seen_at = datetime.datetime.utcnow()

        if commit:
            db.session.add(self)
            db.session.commit()

    def to_dict(self):
        d = ModelMixin.to_dict(self)
        d['url_location'] = url_for('get_photo', local_path=self.rel_location)
        return d
