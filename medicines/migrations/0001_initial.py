import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('kits', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Medicine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150)),
                ('search_name', models.CharField(editable=False, max_length=150)),
                ('form', models.CharField(choices=[('tablet', 'Таблетки'), ('capsule', 'Капсули'), ('syrup', 'Сироп'), ('drops', 'Краплі'), ('ointment', 'Мазь'), ('spray', 'Спрей'), ('injection', 'Ін’єкції'), ('powder', 'Порошок'), ('other', 'Інше')], max_length=20)),
                ('unit', models.CharField(choices=[('pcs', 'шт'), ('ml', 'мл'), ('g', 'г')], max_length=10)),
                ('kit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='medicines', to='kits.kit')),
            ],
            options={
                'ordering': ['search_name', 'id'],
            },
        ),
    ]
