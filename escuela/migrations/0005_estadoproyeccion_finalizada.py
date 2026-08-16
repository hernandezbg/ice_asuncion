from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('escuela', '0004_presentacion_estadoproyeccion'),
    ]

    operations = [
        migrations.AddField(
            model_name='estadoproyeccion',
            name='finalizada',
            field=models.BooleanField(default=False, verbose_name='Finalizada'),
        ),
    ]
