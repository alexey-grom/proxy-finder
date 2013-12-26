# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Url.count'
        db.alter_column(u'proxyfinder_url', 'count', self.gf('django.db.models.fields.SmallIntegerField')(null=True))

        # Changing field 'Url.path'
        db.alter_column(u'proxyfinder_url', 'path', self.gf('django.db.models.fields.CharField')(max_length=4096))

    def backwards(self, orm):

        # User chose to not deal with backwards NULL issues for 'Url.count'
        raise RuntimeError("Cannot reverse this migration. 'Url.count' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration
        # Changing field 'Url.count'
        db.alter_column(u'proxyfinder_url', 'count', self.gf('django.db.models.fields.SmallIntegerField')())

        # Changing field 'Url.path'
        db.alter_column(u'proxyfinder_url', 'path', self.gf('django.db.models.fields.CharField')(max_length=10240))

    models = {
        u'proxyfinder.proxy': {
            'Meta': {'unique_together': "[['ip', 'port']]", 'object_name': 'Proxy'},
            'checked': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'country_code': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '5', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'is_anonymously': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'is_get': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'is_post': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'port': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'}),
            'type': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
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
            'count': ('django.db.models.fields.SmallIntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '4096'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['proxyfinder.Site']"})
        }
    }

    complete_apps = ['proxyfinder']