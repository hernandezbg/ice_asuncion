from django.core.management.base import BaseCommand
from encuestas.models import Encuesta, Pregunta


class Command(BaseCommand):
    help = 'Crea la trivia de fútbol argentino con 10 preguntas'

    def handle(self, *args, **options):
        # Crear la encuesta
        encuesta = Encuesta.objects.create(
            titulo='Trivia de Fútbol Argentino',
            descripcion='¿Cuánto sabés de fútbol? 10 preguntas para poner a prueba tu conocimiento.',
            tipo='trivia',
            estado='borrador',
            puntos_base=100,
            tiempo_limite=30,
            bonus_tiempo=True,
        )

        # Lista de preguntas con sus opciones y respuesta correcta
        preguntas = [
            {
                'texto': '¿Quién fue el último goleador argentino en salir campeón de la Serie A italiana?',
                'opcion_a': 'Gonzalo Higuaín',
                'opcion_b': 'Mauro Icardi',
                'opcion_c': 'Diego Milito',
                'opcion_d': 'Hernán Crespo',
                'respuesta_correcta': 'C',
            },
            {
                'texto': '¿Qué club argentino ganó la Copa Libertadores invicto en 2018?',
                'opcion_a': 'River Plate',
                'opcion_b': 'Boca Juniors',
                'opcion_c': 'Ninguno',
                'opcion_d': 'Estudiantes',
                'respuesta_correcta': 'C',
            },
            {
                'texto': '¿Quién fue el técnico de Argentina en el Mundial 2002?',
                'opcion_a': 'Marcelo Bielsa',
                'opcion_b': 'José Pekerman',
                'opcion_c': 'Daniel Passarella',
                'opcion_d': 'Alfio Basile',
                'respuesta_correcta': 'A',
            },
            {
                'texto': '¿Qué equipo eliminó a Argentina en la Copa América 2019?',
                'opcion_a': 'Brasil',
                'opcion_b': 'Chile',
                'opcion_c': 'Colombia',
                'opcion_d': 'Uruguay',
                'respuesta_correcta': 'A',
            },
            {
                'texto': '¿Cuál de estos jugadores NO jugó en el Napoli?',
                'opcion_a': 'Diego Maradona',
                'opcion_b': 'Gonzalo Higuaín',
                'opcion_c': 'Ezequiel Lavezzi',
                'opcion_d': 'Javier Mascherano',
                'respuesta_correcta': 'D',
            },
            {
                'texto': '¿Qué club argentino tiene más títulos internacionales oficiales reconocidos por CONMEBOL?',
                'opcion_a': 'Boca Juniors',
                'opcion_b': 'River Plate',
                'opcion_c': 'Independiente',
                'opcion_d': 'Estudiantes',
                'respuesta_correcta': 'A',
            },
            {
                'texto': '¿En qué club europeo debutó profesionalmente Ángel Di María en Europa?',
                'opcion_a': 'Real Madrid',
                'opcion_b': 'Benfica',
                'opcion_c': 'Manchester United',
                'opcion_d': 'PSG',
                'respuesta_correcta': 'B',
            },
            {
                'texto': '¿Quién convirtió el primer gol de Argentina en el Mundial 2022?',
                'opcion_a': 'Julián Álvarez',
                'opcion_b': 'Ángel Di María',
                'opcion_c': 'Lionel Messi',
                'opcion_d': 'Lautaro Martínez',
                'respuesta_correcta': 'C',
            },
            {
                'texto': '¿Qué equipo argentino descendió en 2011 por el sistema de promedio?',
                'opcion_a': 'Independiente',
                'opcion_b': 'Racing',
                'opcion_c': 'River Plate',
                'opcion_d': 'San Lorenzo',
                'respuesta_correcta': 'C',
            },
            {
                'texto': '¿Qué jugador argentino ganó la Champions League con el Inter en 2010?',
                'opcion_a': 'Carlos Tevez',
                'opcion_b': 'Esteban Cambiasso',
                'opcion_c': 'Javier Zanetti',
                'opcion_d': 'Walter Samuel',
                'respuesta_correcta': 'D',
            },
        ]

        # Crear las preguntas
        for orden, datos in enumerate(preguntas):
            Pregunta.objects.create(
                encuesta=encuesta,
                texto=datos['texto'],
                orden=orden,
                opcion_a=datos['opcion_a'],
                opcion_b=datos['opcion_b'],
                opcion_c=datos['opcion_c'],
                opcion_d=datos['opcion_d'],
                respuesta_correcta=datos['respuesta_correcta'],
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Trivia "{encuesta.titulo}" creada con código: {encuesta.codigo}'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(f'Se crearon {len(preguntas)} preguntas.')
        )
