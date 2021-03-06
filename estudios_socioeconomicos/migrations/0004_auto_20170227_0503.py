# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-02-27 05:03
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('estudios_socioeconomicos', '0003_auto_20170225_0247'),
    ]

    operations = [
        migrations.CreateModel(
            name='Subseccion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.TextField()),
                ('numero', models.IntegerField()),
                ('seccion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='estudios_socioeconomicos.Seccion')),
            ],
        ),
        migrations.RemoveField(
            model_name='pregunta',
            name='seccion',
        ),
        migrations.AddField(
            model_name='pregunta',
            name='orden',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='pregunta',
            name='subseccion',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='estudios_socioeconomicos.Subseccion'),
        ),
    ]
