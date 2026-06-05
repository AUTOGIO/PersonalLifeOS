# Generated manually for TideEvent (model added after initial migration)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TideEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('port_name', models.CharField(default='Porto de Cabedelo', max_length=100)),
                ('date', models.DateField(db_index=True)),
                ('time', models.TimeField()),
                ('datetime_local', models.DateTimeField()),
                ('height_m', models.FloatField()),
                ('tide_type', models.CharField(choices=[('HIGH', 'High Tide'), ('LOW', 'Low Tide'), ('UNKNOWN', 'Unknown')], default='UNKNOWN', max_length=10)),
                ('source', models.CharField(default='Porto de Cabedelo 2026 tide table', max_length=200)),
                ('timezone', models.CharField(default='America/Fortaleza', max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Tide Event',
                'verbose_name_plural': 'Tide Events',
                'ordering': ['date', 'time'],
                'unique_together': {('port_name', 'date', 'time')},
            },
        ),
    ]
