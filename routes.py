from flask import abort, jsonify, request
from core import app, config
from models import Photo
import os


@app.route('/')
def index():
    return 'Billy is a filthy jew'


@app.route('/photos', methods=['GET'])
def get_new_ids():
    photo_query = Photo.query.filter(Photo.deleted_at == None) \
                        .filter(Photo.seen_at == None)

    if 'id' in request.args:
        offset = request.args['id']
        try:
            greater_than = int(offset)
            photo_query = photo_query.filter(Photo.id > greater_than)
        except:
            pass

    photos = photo_query.limit(25).all()

    photos = [x.to_dict() for x in photos]
    return jsonify({'results': photos})


@app.route('/photos/<int:id>', methods=['GET', 'DELETE'])
def get_photo_by_id(id):
    photo = Photo.query.get(id)
    if not photo:
        abort(404)

    if request.method == 'DELETE':
        photo.mark_seen()

    return jsonify(photo.to_dict())


@app.route('/static/photos/<path:local_path>')
def get_photo(local_path):
    if '..' in local_path:
        abort(403)

    dest = os.path.join(config['LOCAL_SERVER_LOCATION'], local_path)
    if not os.path.exists(dest):
        abort(404)

    return app.send_static_file(dest)


@app.route('/photos/length')
def get_photo_length():
    photos = Photo.query.filter(Photo.deleted_at == None) \
                        .filter(Photo.seen_at == None) \
                        .count()

    return jsonify({'results': photos})
