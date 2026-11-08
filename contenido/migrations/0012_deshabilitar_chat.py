from django.db import migrations


def deshabilitar_chat(apps, schema_editor):
    """Oculto el chat del sitio (se puede volver a habilitar desde Configuracion)"""
    apps.get_model('contenido', 'DatosIce').objects.update(chat_habilitado=False)


class Migration(migrations.Migration):

    dependencies = [
        ('contenido', '0011_pagina_informacion_institucional'),
    ]

    operations = [
        migrations.RunPython(deshabilitar_chat, migrations.RunPython.noop),
    ]
