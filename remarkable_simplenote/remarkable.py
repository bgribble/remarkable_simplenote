#! /usr/bin/env python3
'''
remarkable.py
pull, push, convert for reMarkable cloud sync
'''
from rmapy.api import Client
from rmapy.document import Document, ZipDocument
from rmapy.folder import Folder
from .conf import config
from .utils import get_pdf_title

class Remarkable:
    converters = {}

    def __init__(self, *, sync_manager):
        self.rm_api = Client()
        self.rm_meta = None
        self.sync_manager = sync_manager

    def connect(self):
        self.rm_api.renew_token()

    def get_meta(self):
        self.rm_meta = list(self.rm_api.get_meta_items())

    def toc(self):
        if not self.rm_meta:
            self.get_meta()

        documents = [
            item for item in self.rm_meta
            if isinstance(item, Document)
        ]
        toc = {
            d.ID: d.Version
            for d in documents
        }
        folders = [
            item for item in self.rm_meta
            if isinstance(item, Folder)
        ]
        return toc

    def folder_children(self, parent=''):
        if not self.rm_meta:
            self.get_meta()

        return {
            d: self.folder_children(d.ID)
            for d in self.rm_meta
            if isinstance(d, Folder) and d.Parent == parent
        }

    def pull(self):
        pass

    def upload_document(self, local_id, local_version, mapping_info):
        content_dir = self.sync_manager.push_dir(Remarkable) + f'/{local_id}/{local_version}'
        content_path = f'{content_dir}/{local_id}.pdf'
        current_version = mapping_info.remote_version or 1

        doc = ZipDocument(doc=content_path, _id=mapping_info.remote_id)
        folder = self.get_or_create_folder(mapping_info.remote_path)
        doc.metadata['VissibleName'] = get_pdf_title(content_path) 
        doc.metadata['version'] = current_version + 1
        print(f"push: document '{doc.metadata['VissibleName']}' {local_id} to {mapping_info.remote_path})")
        print(f"version: {current_version + 1}, folder: {folder.VissibleName} {folder.ID}")
        self.rm_api.upload(doc, folder)
        mapping_info.remote_id = doc.ID
        mapping_info.remote_version = current_version + 1
        return mapping_info

    def get_or_create_folder(self, path, parent=None, subtree=None):
        match_start = config.get('folder_match', 'exact') == 'start'
        if not path:
            return None
        if not subtree:
            subtree = self.folder_children()

        top = path[0]
        matched_folder = None
        for folder in subtree:
            if not match_start and folder.VissibleName == top:
                matched_folder = folder
                break
            elif match_start and folder.VissibleName.startswith(top):
                matched_folder = folder
                break

        if not matched_folder:
            matched_folder = Folder(top)
            if parent:
                matched_folder.Parent = parent.ID
            self.rm_api.create_folder(matched_folder)
            self.rm_meta.append(matched_folder)
            children = {}
        else:
            children = subtree[matched_folder]
    
        if len(path) > 1:
            return self.get_or_create_folder(path[1:], parent=matched_folder, subtree=children)
        else:
            return matched_folder


    def push(self, force=False):
        local_toc = self.sync_manager.local_toc(Remarkable, "push")
        cloud_toc = self.toc()

        if force:
            print("push: Force push requested")

        for item_id, local_version in local_toc.items():
            mapping_info = self.sync_manager.get_mapping(
                Remarkable, item_id, local_version
            )
            cloud_ver = None
            if mapping_info.remote_id:
                cloud_ver = cloud_toc.get(mapping_info.remote_id)

            if not cloud_ver or local_version > cloud_ver or force:
                mapping_info = self.upload_document(
                    item_id, local_version, mapping_info
                )

            self.sync_manager.update_mapping(
                Remarkable, item_id, local_version, mapping_info
            )
