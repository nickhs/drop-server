import mcrypt
import base64
import requests
import tempfile
import os
from datetime import datetime
from models import Photo, Services
from core import config, db


SERVICE = Services.SNAPCHAT

CREDS = {
    'birwin93': {
        'req_token': 'ddf25476f9064b0a8052c76f7a9a94e82c662a766f3c09554e84af41cc928146',
        'timestamp': '1415391674222',
        'username': 'birwin93'
    },
    'cconeil': {
        'req_token': '6c5d3758db73277de63d93dc8aff1a073aab28cd43e6c177eaec58413f6e9839',
        'timestamp': '1414981556372',
        'username': 'cconeil'
    },
    'eflatt': {
        'req_token': 'bb4d7fd460d8eef68af888875d151adc407ad862ceb5efb1471b5942a50909ee',
        'timestamp': '1414957873399',
        'username:': 'eflatt'
    }
}

API_SERVER = 'https://feelinsonice-hrd.appspot.com'
ENDPOINT = '/bq/stories'


class SnapchatStatics:
    IMAGE = 0
    VIDEO = 1
    VIDEO_NOAUDIO = 2
    FRIEND_REQUEST = 3
    FRIEND_REQUEST_IMAGE = 4
    FRIEND_REQUEST_VIDEO = 5
    FRIEND_REQUEST_VIDEO_NOAUDIO = 6


def get_relative_filename(media_id, timestamp, user_id):
    try:
        time = datetime.utcfromtimestamp(timestamp / 1e3)
        year = str(time.year)
        month = str(time.month)
        day = str(time.day)
    except ValueError as e:
        print "Failed to process timestamp %s: %s" % (timestamp, e)
        year = 'FAIL'
        month = 'FAIL'
        day = 'FAIL'

    dest = os.path.join(year, month, day,
            "%s-%s-%s.jpg" % (media_id, timestamp, SERVICE))
    return dest


def get_absolute_filename(media_id, timestamp, user_id):
    return os.path.join(config['LOCAL_SERVER_LOCATION'],
            get_relative_filename(media_id, timestamp, user_id))


def scrape(endpoint, username, form_payload=None):
    resp = requests.post(API_SERVER + endpoint, data=form_payload)
    if not resp.ok:
        print "Failed to make request %s" % resp
        # import pdb; pdb.set_trace()
        return []

    payload = resp.json()

    if 'friend_stories' not in payload:
        print "Found no friend_stories to scrape for request %s" % resp
        # import pdb; pdb.set_trace()
        return []

    friend_stories = payload['friend_stories']
    extracted = []
    for friend in friend_stories:
        for story in friend['stories']:
            story_data = story['story']

            if story_data['media_type'] != SnapchatStatics.IMAGE:
                continue

            potential_filename = get_absolute_filename(story_data['media_id'],
                    story_data['timestamp'], username)
            if os.path.exists(potential_filename):
                print "Skipping %s as it exists" % potential_filename
                continue

            try_count = 0
            while try_count != 3:
                try:
                    resp = requests.get(story_data['media_url'])
                except:
                    pass

                if resp.ok:
                    break
                else:
                    print "Failed to download %s [%s]: %s" % (story_data['media_url'], try_count, resp)
                    try_count += 1

            if try_count >= 3:
                continue

            t = tempfile.NamedTemporaryFile(prefix='drop-', delete=False)
            t.write(resp.content)
            t.close()
            print "Saved %s" % t.name
            story_data['local_location'] = t.name

            extracted.append(story_data)

    return extracted


def extract_media(key, iv, infile, outfile, delete=True):
    key = base64.b64decode(key)
    iv = base64.b64decode(iv)
    m = mcrypt.MCRYPT("rijndael-128", "cbc")
    m.init(key, iv)
    f = open(infile, 'r')
    f_data = f.read()
    decr_data = m.decrypt(f_data)

    f2 = open(outfile, 'w')
    f2.write(decr_data)
    f2.close()
    f.close()

    if delete:
        os.remove(infile)

if __name__ == '__main__':
    new_snaps = 0

    for username, value in CREDS.iteritems():
        print "Fetching %s snap stories" % username
        media_items = scrape(ENDPOINT, username, form_payload=value)
        new_snaps += len(media_items)

        for item in media_items:
            dest = get_absolute_filename(item['media_id'], item['timestamp'], username)
            try:
                os.makedirs(os.path.sep.join(dest.split(os.path.sep)[:-1]))
            except:
                pass

            extract_media(item['media_key'], item['media_iv'], item['local_location'], dest)
            photo = Photo(
                rel_location=get_relative_filename(item['media_id'], item['timestamp'], username),
                external_id=item['media_id'],
                owner=username,
                service=SERVICE
            )

            db.session.add(photo)

            print "Extracted to %s" % dest

    print "\nDownloaded %s new images" % new_snaps
    db.session.commit()
    print "All saved."
