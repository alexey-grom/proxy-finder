# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'ProxyIP'
        db.delete_table(u'proxyfinder_proxyip')

        # Adding model 'Proxy'
        db.create_table(u'proxyfinder_proxy', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ip', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('port', self.gf('django.db.models.fields.PositiveSmallIntegerField')(db_index=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
            ('checked', self.gf('django.db.models.fields.DateTimeField')()),
            ('type', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('state', self.gf('django.db.models.fields.SmallIntegerField')()),
        ))
        db.send_create_signal(u'proxyfinder', ['Proxy'])

        # Adding unique constraint on 'Proxy', fields ['ip', 'port']
        db.create_unique(u'proxyfinder_proxy', ['ip', 'port'])


    def backwards(self, orm):
        # Removing unique constraint on 'Proxy', fields ['ip', 'port']
        db.delete_unique(u'proxyfinder_proxy', ['ip', 'port'])

        # Adding model 'ProxyIP'
        db.create_table(u'proxyfinder_proxyip', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'proxyfinder', ['ProxyIP'])

        # Deleting model 'Proxy'
        db.delete_table(u'proxyfinder_proxy')


    models = {
        u'proxyfinder.proxy': {
            'Meta': {'unique_together': "[['ip', 'port']]", 'object_name': 'Proxy'},
            'checked': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'port': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'}),
            'state': ('django.db.models.fields.SmallIntegerField', [], {}),
            'type': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['proxyfinder']