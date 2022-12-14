# Generated by Django 4.1.2 on 2022-10-06 03:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('customerapi', '0002_customer_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomerHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('history', models.CharField(max_length=100)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='customerapi.customer')),
            ],
        ),
    ]
