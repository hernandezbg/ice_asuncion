from django.db import migrations


def crear_grupo(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.get_or_create(name='Eventos')


class Migration(migrations.Migration):

    dependencies = [
        ('eventos', '0005_evento_fecha_limite_descuento_and_more'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(crear_grupo, migrations.RunPython.noop),
    ]
