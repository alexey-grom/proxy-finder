# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'ProxyIP'
        db.create_table(u'proxyfinder_proxyip', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'proxyfinder', ['ProxyIP'])


    def backwards(self, orm):
        # Deleting model 'ProxyIP'
        db.delete_table(u'proxyfinder_proxyip')


    models = {
        u'proxyfinder.proxyip': {
            'Meta': {'object_name': 'ProxyIP'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['proxyfinder']