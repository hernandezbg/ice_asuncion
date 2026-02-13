from django.core.management.base import BaseCommand
from encuestas.models import Encuesta, Pregunta


class Command(BaseCommand):
    help = 'Crea la encuesta predefinida "Salud de la Iglesia" con sus preguntas'

    def handle(self, *args, **options):
        # Verificar si ya existe
        if Encuesta.objects.filter(titulo__icontains='Salud de la Iglesia').exists():
            self.stdout.write(self.style.WARNING('Ya existe una encuesta de Salud de la Iglesia'))
            return

        # Crear la encuesta
        encuesta = Encuesta.objects.create(
            titulo='Evaluacion de Salud de la Iglesia',
            descripcion='Encuesta para evaluar diferentes aspectos de la salud y funcionamiento de nuestra iglesia.',
            estado='borrador'
        )

        # Etiquetas por defecto para Salud de la Iglesia
        etiquetas = {
            'etiqueta_1': 'Todavia no hemos pensado en eso',
            'etiqueta_2': 'Apenas comenzando',
            'etiqueta_3': 'En progreso',
            'etiqueta_4': 'Bien encaminados',
            'etiqueta_5': 'En excelente forma',
        }

        # Preguntas de Salud de la Iglesia
        preguntas = [
            'Nuestra iglesia tiene una vision clara y compartida por todos los miembros.',
            'Los lideres de nuestra iglesia sirven con humildad y transparencia.',
            'Tenemos programas efectivos para discipular a los nuevos creyentes.',
            'La adoracion en nuestros servicios es genuina y participativa.',
            'Existe un ambiente de comunion y familia entre los miembros.',
            'Nuestra iglesia esta comprometida con la evangelizacion local.',
            'Apoyamos activamente misiones nacionales e internacionales.',
            'Los jovenes y ninos tienen espacios adecuados para su crecimiento espiritual.',
            'La ensenanza biblica es solida y aplicable a la vida diaria.',
            'Nuestra iglesia responde a las necesidades sociales de la comunidad.',
            'Los miembros estan involucrados en algun ministerio o servicio.',
            'Existe un sistema efectivo de cuidado pastoral para los miembros.',
            'La comunicacion interna de la iglesia es clara y oportuna.',
            'Los recursos financieros se administran con integridad y sabiduria.',
            'Nuestra iglesia promueve la oracion como prioridad.',
        ]

        for i, texto in enumerate(preguntas):
            Pregunta.objects.create(
                encuesta=encuesta,
                texto=texto,
                orden=i,
                **etiquetas
            )

        self.stdout.write(self.style.SUCCESS(
            f'Encuesta "{encuesta.titulo}" creada exitosamente con {len(preguntas)} preguntas.'
        ))
        self.stdout.write(self.style.SUCCESS(f'Codigo de acceso: {encuesta.codigo}'))
