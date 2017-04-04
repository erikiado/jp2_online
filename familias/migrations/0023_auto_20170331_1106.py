# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-03-31 11:06
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('familias', '0022_merge_20170331_0755'),
    ]

    operations = [
        migrations.AlterField(
            model_name='alumno',
            name='escuela',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='escuela_alumno', to='administracion.Escuela'),
        ),
    ]