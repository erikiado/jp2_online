# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-03-29 03:34
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('familias', '0018_auto_20170329_0127'),
    ]

    operations = [
        migrations.AlterField(
            model_name='integrante',
            name='apellidos',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='integrante',
            name='fecha_de_nacimiento',
            field=models.DateField(),
        ),
        migrations.AlterField(
            model_name='integrante',
            name='nombres',
            field=models.CharField(max_length=200),
        ),
    ]
