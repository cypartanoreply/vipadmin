# Generated by Django 4.2.7 on 2024-02-16 21:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vipadmin', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='alltypemodel',
            name='decimal_range_field',
        ),
        migrations.RemoveField(
            model_name='alltypemodel',
            name='float_range_field',
        ),
        migrations.RemoveField(
            model_name='alltypemodel',
            name='integer_range_field',
        ),
        migrations.AlterField(
            model_name='alltypemodel',
            name='file_path_field',
            field=models.FilePathField(path='/home/eslam/Documents/core/staticfiles'),
        ),
    ]
