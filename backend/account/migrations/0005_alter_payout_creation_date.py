# Generated by Django 3.2.13 on 2022-05-26 17:39

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0004_auto_20220515_1534'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payout',
            name='creation_date',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='Дата создания'),
        ),
    ]
