# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-07-25 21:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('familias', '0041_merge_20170725_1644'),
    ]

    operations = [
        migrations.AddField(
            model_name='alumno',
            name='estatus_ingreso',
            field=models.CharField(choices=[('reingreso', 'Reingreso'), ('nuevo', 'Nuevo')], default='reingreso', max_length=10),
        ),
        migrations.AlterField(
            model_name='integrante',
            name='sacramentos_faltantes',
            field=models.TextField(blank=True, verbose_name='Sacramentos que le falten… bautizo, comunion, confirmación, matrimonio iglesia'),
        ),
    ]
