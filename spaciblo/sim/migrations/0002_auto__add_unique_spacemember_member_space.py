# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding unique constraint on 'SpaceMember', fields ['member', 'space']
        db.create_unique('sim_spacemember', ['member_id', 'space_id'])

    def backwards(self, orm):
        # Removing unique constraint on 'SpaceMember', fields ['member', 'space']
        db.delete_unique('sim_spacemember', ['member_id', 'space_id'])

    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'sim.asset': {
            'Meta': {'object_name': 'Asset'},
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'file_type': ('django.db.models.fields.CharField', [], {'default': "'text'", 'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'prepped_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'sim.simulatorpoolregistration': {
            'Meta': {'object_name': 'SimulatorPoolRegistration'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'}),
            'port': ('django.db.models.fields.IntegerField', [], {})
        },
        'sim.space': {
            'Meta': {'object_name': 'Space'},
            'default_body': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sim.Template']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_guests': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'scene_document': ('django.db.models.fields.TextField', [], {'default': 'u\'{\\n    "username": null,\\n    "uid": "654B802C-D0AC-4A59-8739F826A4DEEFCB373",\\n    "lastFrame": null,\\n    "frameRate": 25,\\n    "rotOrder": 1,\\n    "paused": false,\\n    "fogFar": 80,\\n    "blendTime": 0,\\n    "animationStart": null,\\n    "matrix": [\\n        [\\n            1,\\n            0,\\n            0,\\n            0\\n        ],\\n        [\\n            0,\\n            1,\\n            0,\\n            0\\n        ],\\n        [\\n            0,\\n            0,\\n            1,\\n            0\\n        ],\\n        [\\n            0,\\n            0,\\n            0,\\n            1\\n        ]\\n    ],\\n    "scaleX": 1,\\n    "scaleY": 1,\\n    "scaleZ": 1,\\n    "fogType": 1,\\n    "animation": null,\\n    "dLocZ": 0,\\n    "dLocY": 0,\\n    "dLocX": 0,\\n    "locZ": 0,\\n    "blendStart": 0,\\n    "locX": 0,\\n    "locY": 0,\\n    "dRotX": 0,\\n    "dRotY": 0,\\n    "group_type": 1,\\n    "quatW": 1,\\n    "rotY": 0,\\n    "rotX": 0,\\n    "rotZ": 0,\\n    "backgroundColor": [\\n        0.3,\\n        0.3,\\n        1.0,\\n        1.0\\n    ],\\n    "dScaleY": 0,\\n    "dScaleX": 0,\\n    "dScaleZ": 0,\\n    "group_template": null,\\n    "fogColor": [\\n        0.5,\\n        0.5,\\n        0.5\\n    ],\\n    "dRotZ": 0,\\n    "fogNear": 10,\\n    "name": null,\\n    "pausedTime": null,\\n    "children": [],\\n    "ambientColor": [\\n        0.3,\\n        0.3,\\n        0.3\\n    ],\\n    "mode": 2,\\n    "quatZ": 0,\\n    "quatX": 0,\\n    "quatY": 0,\\n    "loop": true\\n}\''}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '1000'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'admin_only'", 'max_length': '20'})
        },
        'sim.spacemember': {
            'Meta': {'unique_together': "(('space', 'member'),)", 'object_name': 'SpaceMember'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_admin': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_editor': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'space': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sim.Space']"})
        },
        'sim.template': {
            'Meta': {'object_name': 'Template'},
            'assets': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['sim.Asset']", 'null': 'True', 'through': "orm['sim.TemplateAsset']", 'blank': 'True'}),
            'children': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'parents'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['sim.TemplateChild']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "'A Template'", 'max_length': '1000'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'seat_orientation': ('django.db.models.fields.CharField', [], {'default': "'1,0,0,0'", 'max_length': '1000', 'null': 'True', 'blank': 'True'}),
            'seat_position': ('django.db.models.fields.CharField', [], {'default': "'0,0,0'", 'max_length': '1000', 'null': 'True', 'blank': 'True'}),
            'settings': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['sim.TemplateSetting']", 'null': 'True', 'blank': 'True'})
        },
        'sim.templateasset': {
            'Meta': {'object_name': 'TemplateAsset'},
            'asset': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sim.Asset']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'template': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'templateassets'", 'to': "orm['sim.Template']"})
        },
        'sim.templatechild': {
            'Meta': {'object_name': 'TemplateChild'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'orientation': ('django.db.models.fields.CharField', [], {'default': "'1,0,0,0'", 'max_length': '1000'}),
            'position': ('django.db.models.fields.CharField', [], {'default': "'0,0,0'", 'max_length': '1000'}),
            'settings': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['sim.TemplateSetting']", 'null': 'True', 'blank': 'True'}),
            'template': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sim.Template']"})
        },
        'sim.templatesetting': {
            'Meta': {'object_name': 'TemplateSetting'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'value': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['sim']