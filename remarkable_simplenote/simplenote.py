#! /usr/bin/env python3

'''
simplenote.py
Pull, push, transform for Simplenote notes
'''

import simplenote
import json
import os
import re

from .utils import write_pdf
from .sync import SyncManager, SyncMapping
from .conf import config

def convert_to_pdf(source_path, dest_dir, note_id):
    with open(source_path, "r") as notefile:
        note = json.loads(notefile.read())

    if note.get("deleted"):
        print(f"convert: skipping deleted note {note_id}")
        return

    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir, exist_ok=True)

    mapfile = f'{dest_dir}/mapping'
    mapping = SyncMapping.from_file(mapfile)
    note_title = note['content'].split('\n')[0].strip()

    print(f"convert: rendering '{note_title}' to PDF")

    if config.get('folder_strategy') == 'jd_title':
        first_word = note_title.split(' ')[0].strip()
        if re.match('^[0-9.]+$', first_word):
            mapping.remote_path = first_word.split('.')[:2]
        else:
            mapping.remote_path = config.get('folder_bucket', '')
    else:
        mapping.remote_path = config.get('folder_bucket', '')
    mapping.to_file(mapfile)

    write_pdf(
        title=note_title,
        body=note['content'], 
        destination=f'{dest_dir}/{note_id}.pdf'
    )
    return True


class SimpleNote:
    converters = {
        'Remarkable': convert_to_pdf
    }

    def __init__(self, *, username, password, sync_manager):
        self.username = username
        self.password = password
        self.sn_api = None
        self.sync_mgr = sync_manager

    def connect(self):
        self.sn_api = simplenote.Simplenote(self.username, self.password)
    
    def toc(self):
        notes, status = self.sn_api.get_note_list(data=False)
        if status == 0:
            return {
                note['key']: note['version']
                for note in notes
            }
        else:
            return None

    def pull(self):
        pull_base = self.sync_mgr.pull_dir(SimpleNote)

        remote_toc = self.toc()
        local_toc = self.sync_mgr.local_toc(SimpleNote, "pull")

        for note_id, version in remote_toc.items():
            local_version = local_toc.get(note_id, 0)
            if version > local_version:
                noteinfo, status = self.sn_api.get_note(note_id, version)
                title = noteinfo.get('content').split('\n')[0]
                print(f"pull: fetched '{title}' ver {noteinfo.get('version')}")

                localdir = f'{pull_base}/{note_id}'
                if not os.path.exists(localdir):
                    os.mkdir(localdir)
                localpath = f'{pull_base}/{note_id}/{version}'
                with open(localpath, 'w+') as notefile:
                    notefile.write(json.dumps(noteinfo, indent=4))

    def push(self):
        pass


