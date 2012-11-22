# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Changing field 'SystemPayTransaction.error_message'
        db.alter_column('systempay_systempaytransaction', 'error_message', self.gf('django.db.models.fields.TextField')(max_length=512, null=True))


    def backwards(self, orm):
        
        # Changing field 'SystemPayTransaction.error_message'
        db.alter_column('systempay_systempaytransaction', 'error_message', self.gf('django.db.models.fields.CharField')(max_length=256, null=True))


    models = {
        'systempay.systempaytransaction': {
            'Meta': {'ordering': "('-date_created',)", 'object_name': 'SystemPayTransaction'},
            'amount': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '2', 'blank': 'True'}),
            'auth_result': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'currency': ('django.db.models.fields.CharField', [], {'max_length': '8', 'null': 'True', 'blank': 'True'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'error_message': ('django.db.models.fields.TextField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mode': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'order_number': ('django.db.models.fields.CharField', [], {'max_length': '127', 'null': 'True', 'blank': 'True'}),
            'raw_request': ('django.db.models.fields.TextField', [], {'max_length': '512'}),
            'result': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'trans_date': ('django.db.models.fields.CharField', [], {'max_length': '14', 'null': 'True', 'blank': 'True'}),
            'trans_id': ('django.db.models.fields.CharField', [], {'max_length': '6', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['systempay']
