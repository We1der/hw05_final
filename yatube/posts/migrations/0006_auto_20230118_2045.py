# Generated by Django 2.2.16 on 2023-01-18 17:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0005_auto_20230117_0056'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='image',
            field=models.ImageField(blank=True, height_field=339, null=True, upload_to='posts/', verbose_name='Картинка', width_field=960),
        ),
    ]
