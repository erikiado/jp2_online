# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-04-29 23:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('indicadores', '0011_auto_20170429_2133'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ingreso',
            name='offline_id',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='transaccion',
            name='offline_id',
            field=models.TextField(blank=True),
        ),
    ]