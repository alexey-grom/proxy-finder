# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Site'
        db.create_table(u'proxyfinder_site', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('domain', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255, db_index=True)),
        ))
        db.send_create_signal(u'proxyfinder', ['Site'])

        # Adding model 'Url'
        db.create_table(u'proxyfinder_url', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('site', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['proxyfinder.Site'])),
            ('path', self.gf('django.db.models.fields.CharField')(max_length=10240)),
            ('checked', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
            ('count', self.gf('django.db.models.fields.SmallIntegerField')()),
        ))
        db.send_create_signal(u'proxyfinder', ['Url'])


    def backwards(self, orm):
        # Deleting model 'Site'
        db.delete_table(u'proxyfinder_site')

        # Deleting model 'Url'
        db.delete_table(u'proxyfinder_url')


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
        },
        u'proxyfinder.site': {
            'Meta': {'object_name': 'Site'},
            'domain': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'proxyfinder.url': {
            'Meta': {'object_name': 'Url'},
            'checked': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'count': ('django.db.models.fields.SmallIntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '10240'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['proxyfinder.Site']"})
        }
    }

    complete_apps = ['proxyfinder']