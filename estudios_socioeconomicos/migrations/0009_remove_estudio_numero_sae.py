# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-03-23 18:19

from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('estudios_socioeconomicos', '0008_auto_20170318_2102'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='estudio',
            name='numero_sae',
        ),
    ]
