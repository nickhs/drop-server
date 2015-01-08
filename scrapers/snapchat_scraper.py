import mcrypt
import base64
import requests
import tempfile
import os
from datetime import datetime
from models import Photo, Services
from core import config, db
import zipfile
import StringIO

'''
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
'''

SERVICE = Services.SNAPCHAT

CREDS = {
    'birwin93': {
        'req_token': '567ce9dcea9cd60288e103555030554eec1d349511c0d0fe7850fd315fd9455c',
        'timestamp': '1420750724488',
        'username': 'birwin93',
        'features_map': {"stories_delta_response": True},
        'checksum': ''
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


def get_relative_filename(media_id, timestamp, user_id, file_type):
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

    if file_type in (SnapchatStatics.VIDEO, SnapchatStatics.VIDEO_NOAUDIO):
        file_type = '.mp4'
    elif file_type == SnapchatStatics.IMAGE:
        file_type = '.jpg'
    else:
        raise RuntimeError("Wat?!")

    dest = os.path.join(year, month, day,
            "%s-%s-%s%s" % (media_id, timestamp, SERVICE, file_type))
    return dest


def get_absolute_filename(media_id, timestamp, user_id, file_type):
    return os.path.join(config['LOCAL_SERVER_LOCATION'],
            get_relative_filename(media_id, timestamp, user_id, file_type))


def scrape(endpoint, username, form_payload=None):
    s = requests.Session()
    s.headers.update({
        'User-Agent': 'Snapchat/8.1.0.12 (iPhone7,2; iOS 8.1; gzip)',
        'Accept': '*/*',
        'Accenpt-Encoding': 'gzip'
    })

    resp = s.post(API_SERVER + endpoint, data=form_payload)
    if not resp.ok:
        print "Failed to make request %s" % resp
        import pdb; pdb.set_trace()
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

            if story_data['media_type'] not in (SnapchatStatics.VIDEO, SnapchatStatics.VIDEO_NOAUDIO, SnapchatStatics.IMAGE):
                continue

            potential_filename = get_absolute_filename(story_data['media_id'],
                    story_data['timestamp'], username, story_data['media_type'])
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


def extract_media(key, iv, infile, outfile, delete=True, item=None):
    key = base64.b64decode(key)
    iv = base64.b64decode(iv)
    m = mcrypt.MCRYPT("rijndael-128", "cbc")
    m.init(key, iv)
    f = open(infile, 'r')
    f_data = f.read()
    decr_data = m.decrypt(f_data)

    if item:
        if item.get('zipped', False) is True:
            zipped_file = zipfile.ZipFile(StringIO.StringIO(decr_data))
            names = zipped_file.namelist()
            names = [x for x in names if 'media' in x]
            if len(names) == 0:
                raise RuntimeError("No media found in video?!")

            decr_data = zipped_file.read(names[0])

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
            dest = get_absolute_filename(item['media_id'], item['timestamp'], username, item['media_type'])
            try:
                os.makedirs(os.path.sep.join(dest.split(os.path.sep)[:-1]))
            except:
                pass

            extract_media(item['media_key'], item['media_iv'], item['local_location'], dest, item=item)
            is_video = True if item['media_type'] in (SnapchatStatics.VIDEO, SnapchatStatics.VIDEO_NOAUDIO) else False

            photo = Photo(
                rel_location=get_relative_filename(item['media_id'], item['timestamp'], username, item['media_type']),
                external_id=item['media_id'],
                owner=username,
                service=SERVICE,
                is_video=is_video
            )

            db.session.add(photo)

            print "Extracted to %s" % dest

    print "\nDownloaded %s new images" % new_snaps
    db.session.commit()
    print "All saved."
