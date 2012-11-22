# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting field 'SystemPayTransaction.currency'
        db.delete_column('systempay_systempaytransaction', 'currency')

        # Adding field 'SystemPayTransaction.operation_type'
        db.add_column('systempay_systempaytransaction', 'operation_type', self.gf('django.db.models.fields.CharField')(max_length=10, null=True, blank=True), keep_default=False)


    def backwards(self, orm):
        
        # Adding field 'SystemPayTransaction.currency'
        db.add_column('systempay_systempaytransaction', 'currency', self.gf('django.db.models.fields.CharField')(max_length=8, null=True, blank=True), keep_default=False)

        # Deleting field 'SystemPayTransaction.operation_type'
        db.delete_column('systempay_systempaytransaction', 'operation_type')


    models = {
        'systempay.systempaytransaction': {
            'Meta': {'ordering': "('-date_created',)", 'object_name': 'SystemPayTransaction'},
            'amount': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '2', 'blank': 'True'}),
            'auth_result': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'error_message': ('django.db.models.fields.TextField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mode': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'operation_type': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'order_number': ('django.db.models.fields.CharField', [], {'max_length': '127', 'null': 'True', 'blank': 'True'}),
            'raw_request': ('django.db.models.fields.TextField', [], {'max_length': '512'}),
            'result': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'trans_date': ('django.db.models.fields.CharField', [], {'max_length': '14', 'null': 'True', 'blank': 'True'}),
            'trans_id': ('django.db.models.fields.CharField', [], {'max_length': '6', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['systempay']
