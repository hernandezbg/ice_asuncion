from django.db import migrations

TITULO = 'Información institucional'

CONTENIDO = """
<p>IGLESIA CRISTIANA EVANGÉLICA EN ASUNCIÓN, también conocida como ICE Asunción, es una organización religiosa inscripta en el Registro Nacional de Cultos de la República Argentina bajo el N.º 312 desde 1980.</p>
<p>Nuestra sede se encuentra en Asunción 665, San Miguel de Tucumán, provincia de Tucumán, Argentina.</p>
<p>iceasuncion.org es el sitio web oficial de nuestra organización, utilizado para compartir nuestra misión, enseñanzas, noticias y actividades.</p>
<p>Nuestra misión es glorificar a Dios, vivir su Palabra y anunciar el evangelio, promoviendo la comunión, el discipulado y el servicio.</p>
<p>Contacto institucional: <a href="mailto:contacto@iceasuncion.org">contacto@iceasuncion.org</a></p>
""".strip()


def crear_pagina(apps, schema_editor):
    Pagina = apps.get_model('contenido', 'Pagina')
    Pagina.objects.get_or_create(
        titulo=TITULO,
        defaults={'contenido': CONTENIDO, 'orden': 0, 'activo': True},
    )


def eliminar_pagina(apps, schema_editor):
    Pagina = apps.get_model('contenido', 'Pagina')
    Pagina.objects.filter(titulo=TITULO).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('contenido', '0010_fix_tipomensaje_sequence'),
    ]

    operations = [
        migrations.RunPython(crear_pagina, eliminar_pagina),
    ]
