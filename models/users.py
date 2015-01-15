from core import db
from mixins import ModelMixin
from photo import Services
import json

SNAPCHAT_TEMPLATE = {
    'req_token': None,
    'timestamp': None,
    'username': None,
    'features_map': {'stories_delta_response': True},
    'checksum': ''
}


class User(db.Model, ModelMixin):
    id = db.Column(db.Integer, primary_key=True)
    service = db.Column(db.Integer)
    data = db.Column(db.String)
    username = db.Column(db.String)

    def __init__(self, username, service=Services.SNAPCHAT):
        self.username = username
        self.service = service

    def change_data(self, req_token=None,
            timestamp=None, username=None,
            data=None):

        if data is not None:
            if type(data) == dict:
                data = json.dumps(data)

            self.data = data

        else:
            d = SNAPCHAT_TEMPLATE
            d['req_token'] = req_token
            d['timestamp'] = timestamp

            if username:
                d['username'] = username
            else:
                d['username'] = self.username

            self.data = json.dumps(d)

    def to_dict(self):
        d = ModelMixin.to_dict(self)
        d['data'] = json.loads(self.data)
        return d
