from django.core.management.base import BaseCommand
from encuestas.models import Encuesta, Pregunta


class Command(BaseCommand):
    help = 'Crea la encuesta "¿Cuál es nuestra esencia?" con 20 preguntas'

    def handle(self, *args, **options):
        # Crear la encuesta
        encuesta = Encuesta.objects.create(
            titulo='¿Cuál es nuestra esencia?',
            descripcion='Midiendo nuestra iglesia a partir de sus fundamentos. Efesios 2:19-22; Mateo 28:19, 20',
            tipo='opinion',
            estado='borrador',
            rango_excelente=85,
            rango_bueno=70,
            rango_regular=55,
            rango_bajo=40,
        )

        # Etiquetas para todas las preguntas
        etiquetas = {
            'etiqueta_1': 'Todavía no hemos pensado en eso',
            'etiqueta_2': 'Apenas comenzando',
            'etiqueta_3': 'En progreso',
            'etiqueta_4': 'Bien encaminados',
            'etiqueta_5': 'En excelente forma',
        }

        # Lista de preguntas
        preguntas = [
            '¿Tenemos una visión común clara?',
            '¿Nuestro culto de adoración pública glorifica a Dios?',
            '¿Se contempla la Palabra de Dios como la base de autoridad?',
            '¿Nuestras celebraciones públicas inspiran la adoración verdadera?',
            '¿Presenta nuestra iglesia un mensaje poderoso del evangelio?',
            '¿Existe un equilibrio entre evangelismo y edificación?',
            '¿La vida de nuestra iglesia se nutre de la oración colectiva?',
            '¿Existe un esfuerzo concertado para llevar a las personas hacia la madurez?',
            '¿Les tendemos la mano a las personas que nos visitan?',
            '¿Está nuestra iglesia consciente del mundo a su alrededor?',
            '¿Procuramos activamente el cumplimiento de la Gran Comisión?',
            '¿Formamos líderes?',
            '¿Nuestros líderes toman en serio sus responsabilidades?',
            '¿Tiene nuestra iglesia estructuras apropiadas y ejerce una administración sabia?',
            '¿Tiene nuestra congregación un sentido de comunidad?',
            '¿Practicamos la responsabilidad y ejercemos la integridad?',
            '¿Practicamos el amor redentor?',
            '¿Se practica abiertamente la confesión?',
            '¿Nos interrelacionamos con otras congregaciones?',
            '¿Vivimos como personas con esperanza?',
        ]

        # Crear las preguntas
        for orden, texto in enumerate(preguntas):
            Pregunta.objects.create(
                encuesta=encuesta,
                texto=texto,
                orden=orden,
                **etiquetas
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Encuesta "{encuesta.titulo}" creada con código: {encuesta.codigo}'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(f'Se crearon {len(preguntas)} preguntas.')
        )
