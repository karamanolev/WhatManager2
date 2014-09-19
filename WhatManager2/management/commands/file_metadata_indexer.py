import os
import os.path

from django.core.management.base import BaseCommand

from home.models import DownloadLocation, ReplicaSet, FileMetadataCache


class Command(BaseCommand):
    help = u'Cache all .flac and .mp3 metadata in download locations.'

    def handle(self, *args, **options):
        what_locations = DownloadLocation.objects.filter(zone=ReplicaSet.ZONE_WHAT)
        for what_location in what_locations:
            print u'Indexing download location', what_location.path
            for dirpath, dirnames, filenames in os.walk(what_location.path):
                relevant_files = [
                    os.path.join(dirpath, f) for f in filenames if
                    os.path.splitext(f)[1].lower() in ['.flac', '.mp3']
                ]
                if relevant_files:
                    print u'Indexing', dirpath
                    self.index_files(relevant_files)

    def index_files(self, relevant_files):
        try:
            FileMetadataCache.get_metadata_batch(relevant_files)
        except Exception as ex:
            print 'Error indexing in batch', ex
            print 'Indexing one by one'
            for filename in relevant_files:
                try:
                    FileMetadataCache.get_metadata_batch([filename])
                except Exception as ex:
                    print 'Error indexing', filename, '-', ex
