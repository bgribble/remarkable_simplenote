import os
import json
from .conf import config

class SyncMapping:
    def __init__(self, *, remote_path=None, remote_id=None, remote_version=None):
        self.remote_path = remote_path
        self.remote_id = remote_id
        self.remote_version = remote_version

    def to_file(self, path):
        with open(path, "w") as mapfile:
            mapfile.write(
                json.dumps(dict(
                    remote_path=self.remote_path,
                    remote_id=self.remote_id,
                    remote_version=self.remote_version
                ), indent=4)
            )

    @staticmethod
    def from_file(path):
        if os.path.exists(path):
            with open(path, "r") as mapfile:
                return SyncMapping(**json.loads(mapfile.read()))
        return SyncMapping()


class SyncManager:
    def __init__(self, local_dir):
        self.local_storage = local_dir
        pass

    def ensure_local(self, source_type):
        base_path = self.local_storage
        paths = [
            self.pull_dir(source_type),
            self.push_dir(source_type),
        ]

        for path in paths:
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
            if not os.path.isdir(path):
                print(f"ERROR: `{path} exists and is not a directory")

    def pull_dir(self, source_type):
        return self.local_dir(source_type, "pull")

    def push_dir(self, source_type):
        return self.local_dir(source_type, "push")

    def local_dir(self, source_type, operation):
        return f'{self.local_storage}/{operation}/{source_type.__name__}'

    def get_mapping(self, source_type, item_id, item_version):
        item_path = f"{self.push_dir(source_type)}/{item_id}/{item_version}"
        map_path = f"{item_path}/mapping"
        if not os.path.exists(map_path):
            print("get_mapping: can't find", map_path)
            return SyncMapping()
        else:
            return SyncMapping.from_file(map_path)

    def update_mapping(self, source_type, item_id, item_version, mapping):
        item_path = f"{self.push_dir(source_type)}/{item_id}/{item_version}"
        map_path = f"{item_path}/mapping"
        return mapping.to_file(map_path)

    def local_toc(self, source_type, operation):
        self.ensure_local(source_type)

        basedir = self.local_dir(source_type, operation)
        itemids = os.listdir(basedir)
        toc = {}
        for itemid in itemids:
            versions = os.listdir(basedir + f'/{itemid}')
            if not versions:
                continue
            maxversion = max([int(v) for v in versions])
            toc[itemid] = maxversion

        return toc

    def local_sync(self, pull_type, push_type, force=False):
        pull_base = self.pull_dir(pull_type)
        push_base = self.push_dir(push_type)
        pull_toc = self.local_toc(pull_type, "pull")
        push_toc = self.local_toc(push_type, "push")

        converter = pull_type.converters.get(push_type.__name__)

        if force:
            print("sync: Force sync requested ({pull_type.__name__} --> {push_type.__name__}")

        for item_id, version in pull_toc.items():
            push_version = push_toc.get(item_id, 0)
            if version <= push_version and not force:
                continue

            push_dir = f'{push_base}/{item_id}'
            dest_dir = f'{push_dir}/{version}'
            pull_path = f'{pull_base}/{item_id}/{version}'

            converter(pull_path, dest_dir, item_id)
