from django.db import connection


class LockModelTables(object):
    def __init__(self, *models):
        self.models = models

    def __enter__(self):
        locks = set()
        for model in self.models:
            locks.add(model._meta.db_table + ' WRITE')
        cursor = connection.cursor()
        try:
            cursor.execute('LOCK TABLES {0}'.format(', '.join(locks)))
            cursor.fetchone()
        finally:
            cursor.close()

    def __exit__(self, exc_type, exc_val, exc_tb):
        cursor = connection.cursor()
        try:
            cursor.execute("UNLOCK TABLES")
            cursor.fetchone()
        finally:
            cursor.close()
