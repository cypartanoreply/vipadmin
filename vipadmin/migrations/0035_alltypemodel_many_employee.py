# Generated by Django 4.2.7 on 2024-08-26 19:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vipadmin', '0034_remove_alltypemodel_choice_filed2'),
    ]

    operations = [
        migrations.AddField(
            model_name='alltypemodel',
            name='many_Employee',
            field=models.ManyToManyField(related_name='many_to_many_Employee_set', to='vipadmin.employee', verbose_name='Many-to-Many Employee Field'),
        ),
    ]
