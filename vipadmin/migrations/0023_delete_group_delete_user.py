# Generated by Django 4.2.7 on 2024-04-11 02:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vipadmin', '0022_delete_lifecyclegroup_delete_lifecycleuser_group_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Group',
        ),
        migrations.DeleteModel(
            name='User',
        ),
    ]
