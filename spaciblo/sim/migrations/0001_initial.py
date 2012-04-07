# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Space'
        db.create_table('sim_space', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=1000)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=1000, db_index=True)),
            ('state', self.gf('django.db.models.fields.CharField')(default='admin_only', max_length=20)),
            ('max_guests', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('scene_document', self.gf('django.db.models.fields.TextField')(default=u'{\n    "username": null,\n    "uid": "D01E28C1-BA1D-416C-AC6B9FB43579A524071",\n    "lastFrame": null,\n    "frameRate": 25,\n    "rotOrder": 1,\n    "paused": false,\n    "fogFar": 80,\n    "blendTime": 0,\n    "animationStart": null,\n    "matrix": [\n        [\n            1,\n            0,\n            0,\n            0\n        ],\n        [\n            0,\n            1,\n            0,\n            0\n        ],\n        [\n            0,\n            0,\n            1,\n            0\n        ],\n        [\n            0,\n            0,\n            0,\n            1\n        ]\n    ],\n    "scaleX": 1,\n    "scaleY": 1,\n    "scaleZ": 1,\n    "fogType": 1,\n    "animation": null,\n    "dLocZ": 0,\n    "dLocY": 0,\n    "dLocX": 0,\n    "locZ": 0,\n    "blendStart": 0,\n    "locX": 0,\n    "locY": 0,\n    "dRotX": 0,\n    "dRotY": 0,\n    "group_type": 1,\n    "quatW": 1,\n    "rotY": 0,\n    "rotX": 0,\n    "rotZ": 0,\n    "backgroundColor": [\n        1,\n        1,\n        1\n    ],\n    "dScaleY": 0,\n    "dScaleX": 0,\n    "dScaleZ": 0,\n    "group_template": null,\n    "fogColor": [\n        0.5,\n        0.5,\n        0.5\n    ],\n    "dRotZ": 0,\n    "fogNear": 10,\n    "name": null,\n    "pausedTime": null,\n    "children": [],\n    "ambientColor": [\n        0,\n        0,\n        0\n    ],\n    "mode": 2,\n    "quatZ": 0,\n    "quatX": 0,\n    "quatY": 0,\n    "loop": true\n}')),
            ('default_body', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sim.Template'])),
        ))
        db.send_create_signal('sim', ['Space'])

        # Adding model 'SpaceMember'
        db.create_table('sim_spacemember', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('space', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sim.Space'])),
            ('member', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('is_admin', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_editor', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('sim', ['SpaceMember'])

        # Adding model 'Asset'
        db.create_table('sim_asset', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('file_type', self.gf('django.db.models.fields.CharField')(default='text', max_length=20)),
            ('file', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('prepped_file', self.gf('django.db.models.fields.files.FileField')(max_length=100, null=True, blank=True)),
        ))
        db.send_create_signal('sim', ['Asset'])

        # Adding model 'TemplateAsset'
        db.create_table('sim_templateasset', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('template', self.gf('django.db.models.fields.related.ForeignKey')(related_name='templateassets', to=orm['sim.Template'])),
            ('asset', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sim.Asset'])),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=1000)),
        ))
        db.send_create_signal('sim', ['TemplateAsset'])

        # Adding model 'TemplateSetting'
        db.create_table('sim_templatesetting', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=1000)),
            ('value', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('sim', ['TemplateSetting'])

        # Adding model 'TemplateChild'
        db.create_table('sim_templatechild', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('template', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sim.Template'])),
            ('position', self.gf('django.db.models.fields.CharField')(default='0,0,0', max_length=1000)),
            ('orientation', self.gf('django.db.models.fields.CharField')(default='1,0,0,0', max_length=1000)),
        ))
        db.send_create_signal('sim', ['TemplateChild'])

        # Adding M2M table for field settings on 'TemplateChild'
        db.create_table('sim_templatechild_settings', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('templatechild', models.ForeignKey(orm['sim.templatechild'], null=False)),
            ('templatesetting', models.ForeignKey(orm['sim.templatesetting'], null=False))
        ))
        db.create_unique('sim_templatechild_settings', ['templatechild_id', 'templatesetting_id'])

        # Adding model 'Template'
        db.create_table('sim_template', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(default='A Template', max_length=1000)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('last_updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('seat_position', self.gf('django.db.models.fields.CharField')(default='0,0,0', max_length=1000, null=True, blank=True)),
            ('seat_orientation', self.gf('django.db.models.fields.CharField')(default='1,0,0,0', max_length=1000, null=True, blank=True)),
        ))
        db.send_create_signal('sim', ['Template'])

        # Adding M2M table for field settings on 'Template'
        db.create_table('sim_template_settings', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('template', models.ForeignKey(orm['sim.template'], null=False)),
            ('templatesetting', models.ForeignKey(orm['sim.templatesetting'], null=False))
        ))
        db.create_unique('sim_template_settings', ['template_id', 'templatesetting_id'])

        # Adding M2M table for field children on 'Template'
        db.create_table('sim_template_children', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('template', models.ForeignKey(orm['sim.template'], null=False)),
            ('templatechild', models.ForeignKey(orm['sim.templatechild'], null=False))
        ))
        db.create_unique('sim_template_children', ['template_id', 'templatechild_id'])

        # Adding model 'SimulatorPoolRegistration'
        db.create_table('sim_simulatorpoolregistration', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ip', self.gf('django.db.models.fields.IPAddressField')(max_length=15)),
            ('port', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('sim', ['SimulatorPoolRegistration'])


    def backwards(self, orm):
        
        # Deleting model 'Space'
        db.delete_table('sim_space')

        # Deleting model 'SpaceMember'
        db.delete_table('sim_spacemember')

        # Deleting model 'Asset'
        db.delete_table('sim_asset')

        # Deleting model 'TemplateAsset'
        db.delete_table('sim_templateasset')

        # Deleting model 'TemplateSetting'
        db.delete_table('sim_templatesetting')

        # Deleting model 'TemplateChild'
        db.delete_table('sim_templatechild')

        # Removing M2M table for field settings on 'TemplateChild'
        db.delete_table('sim_templatechild_settings')

        # Deleting model 'Template'
        db.delete_table('sim_template')

        # Removing M2M table for field settings on 'Template'
        db.delete_table('sim_template_settings')

        # Removing M2M table for field children on 'Template'
        db.delete_table('sim_template_children')

        # Deleting model 'SimulatorPoolRegistration'
        db.delete_table('sim_simulatorpoolregistration')


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
            'scene_document': ('django.db.models.fields.TextField', [], {'default': 'u\'{\\n    "username": null,\\n    "uid": "657EFD6C-DA98-4AE2-AE2149ED6929CBFAB79",\\n    "lastFrame": null,\\n    "frameRate": 25,\\n    "rotOrder": 1,\\n    "paused": false,\\n    "fogFar": 80,\\n    "blendTime": 0,\\n    "animationStart": null,\\n    "matrix": [\\n        [\\n            1,\\n            0,\\n            0,\\n            0\\n        ],\\n        [\\n            0,\\n            1,\\n            0,\\n            0\\n        ],\\n        [\\n            0,\\n            0,\\n            1,\\n            0\\n        ],\\n        [\\n            0,\\n            0,\\n            0,\\n            1\\n        ]\\n    ],\\n    "scaleX": 1,\\n    "scaleY": 1,\\n    "scaleZ": 1,\\n    "fogType": 1,\\n    "animation": null,\\n    "dLocZ": 0,\\n    "dLocY": 0,\\n    "dLocX": 0,\\n    "locZ": 0,\\n    "blendStart": 0,\\n    "locX": 0,\\n    "locY": 0,\\n    "dRotX": 0,\\n    "dRotY": 0,\\n    "group_type": 1,\\n    "quatW": 1,\\n    "rotY": 0,\\n    "rotX": 0,\\n    "rotZ": 0,\\n    "backgroundColor": [\\n        1,\\n        1,\\n        1\\n    ],\\n    "dScaleY": 0,\\n    "dScaleX": 0,\\n    "dScaleZ": 0,\\n    "group_template": null,\\n    "fogColor": [\\n        0.5,\\n        0.5,\\n        0.5\\n    ],\\n    "dRotZ": 0,\\n    "fogNear": 10,\\n    "name": null,\\n    "pausedTime": null,\\n    "children": [],\\n    "ambientColor": [\\n        0,\\n        0,\\n        0\\n    ],\\n    "mode": 2,\\n    "quatZ": 0,\\n    "quatX": 0,\\n    "quatY": 0,\\n    "loop": true\\n}\''}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '1000', 'db_index': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'admin_only'", 'max_length': '20'})
        },
        'sim.spacemember': {
            'Meta': {'object_name': 'SpaceMember'},
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
