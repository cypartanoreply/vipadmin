# Generated by Django 4.2.7 on 2024-08-15 17:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vipadmin', '0027_testmodel'),
    ]

    operations = [
        migrations.DeleteModel(
            name='TestModel',
        ),
        migrations.AddField(
            model_name='employee',
            name='file_field',
            field=models.FileField(blank=True, null=True, upload_to='files/', verbose_name='File Field'),
        ),
    ]
