import os

from .simplenote import SimpleNote
from .remarkable import Remarkable
from .sync import SyncManager
from . import conf
from .conf import load_config

from argparse import ArgumentParser

def main():
    
    parser = ArgumentParser(
        description="Sync reMarkable and Simplenote",
    )
    parser.add_argument(
        '--pull', 
        nargs='*',
        choices=['remarkable', 'simplenote'],
        default=[],
        help="Pull content from the specified source(s)"
    )
    parser.add_argument(
        '--push', 
        nargs="*",
        choices=['remarkable', 'simplenote'],
        default=[],
        help="Push content to the specified destination(s)"
    )
    parser.add_argument(
        '--path', help="Local config/cache folder",
        default=os.path.expanduser("~/.remarkable_simplenote")
    )
    parser.add_argument(
        '--force-pull', help="Pull remote content even if unneeded",
        action="store_true",
    )
    parser.add_argument(
        '--force-sync', help="Convert pull to push even if unneeded",
        action="store_true",
    )
    parser.add_argument(
        '--force-push', help="Push data to remote even if unneeded",
        action="store_true",
    )
    cmdline = vars(parser.parse_args())
    
    config = load_config(cmdline['path'])

    sync = SyncManager(config['local_storage'])

    if 'simplenote' in cmdline.get('pull'):
        snote = SimpleNote(
            username=config['simplenote_user'],
            password=config['simplenote_pass'],
            sync_manager=sync
        )
        snote.connect()
        snote.pull(force=cmdline['force_pull'])

    sync.local_sync(SimpleNote, Remarkable, force=cmdline['force_sync'])

    if 'remarkable' in cmdline.get('pull'):
        print("pull: reMarkable pull not implemented yet")

    if 'remarkable' in cmdline.get('push'):
        remark = Remarkable(sync_manager=sync)
        remark.connect()
        remark.push(force=cmdline['force_push'])
   
    if 'simplenote' in cmdline.get('push'):
        print("push: Simplenote push not implemented yet")

    print("done.")

if __name__ == '__main__':
    main()
