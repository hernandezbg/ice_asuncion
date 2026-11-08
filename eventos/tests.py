from datetime import date, timedelta
import io

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from escuela.models import Alumno, ClaseEscuela
from miembros.models import Hermano
from .models import Evento, Inscripcion, Inscripto


@override_settings(RECAPTCHA_SITE_KEY='', RECAPTCHA_SECRET_KEY='')
class InscripcionTests(TestCase):
    def setUp(self):
        self.evento = Evento.objects.create(
            nombre='Cena fin de año', slug='fin-2026', fecha=date(2026, 12, 12),
            precio_adulto=10000, precio_nino=5000,
        )
        self.hermano = Hermano.objects.create(apellidos='Pérez', nombres='Juan', sexo='M')
        clase = ClaseEscuela.objects.create(nombre='Verde', color='verde', edad_desde=3, codigo_acceso='X')
        self.alumno = Alumno.objects.create(apellidos='Pérez', nombres='Sofía', clase=clase,
                                            fecha_nacimiento=date(2018, 12, 13))  # 7 años al evento
        self.url = reverse('eventos:inscripcion', args=['fin-2026'])

    def post(self, filas, celular='+54 9 3511234567', **extra):
        data = {'celular': celular, 'apellido': [], 'nombre': [], 'parentesco': [], 'edad': [],
                'hermano_id': [], 'alumno_id': []}
        for f in filas:
            for k in ['apellido', 'nombre', 'parentesco', 'edad', 'hermano_id', 'alumno_id']:
                data[k].append(str(f.get(k, '')))
        data.update(extra)
        return self.client.post(self.url, data)

    def test_categorias(self):
        e = self.evento
        self.assertEqual(e.categoria_para_edad(None), 'adulto')
        self.assertEqual(e.categoria_para_edad(12), 'adulto')
        self.assertEqual(e.categoria_para_edad(11), 'nino')
        self.assertEqual(e.categoria_para_edad(3), 'nino')
        self.assertEqual(e.categoria_para_edad(2), 'gratis')
        self.assertEqual(e.categoria_para_edad(0), 'gratis')

    def test_inscripcion_familia(self):
        r = self.post([
            {'apellido': 'Perez', 'nombre': 'juan', 'parentesco': 'responsable', 'edad': '45',
             'hermano_id': self.hermano.pk},
            {'apellido': 'Gómez', 'nombre': 'Ana', 'parentesco': 'conyuge', 'edad': '40'},
            {'apellido': 'Pérez', 'nombre': 'Sofía', 'parentesco': 'hijo', 'edad': '7', 'alumno_id': self.alumno.pk},
            {'apellido': 'Pérez', 'nombre': 'Bebé', 'parentesco': 'hijo', 'edad': '1'},
            {'apellido': '', 'nombre': '', 'parentesco': 'hijo', 'edad': ''},  # fila vacia
        ])
        self.assertRedirects(r, reverse('eventos:exito', args=['fin-2026']))
        insc = Inscripcion.objects.get()
        self.assertEqual(insc.personas.count(), 4)
        self.assertEqual(insc.total(), 25000)
        self.assertEqual(insc.responsable().hermano, self.hermano)  # sin acentos coincide igual
        self.assertFalse(insc.personas.get(nombre='Ana').en_base())
        self.assertEqual(insc.personas.get(nombre='Sofía').alumno, self.alumno)

        r = self.client.get(reverse('eventos:exito', args=['fin-2026']))
        self.assertContains(r, '25.000')

    def test_vinculo_descartado_si_nombre_no_coincide(self):
        self.post([{'apellido': 'Otro', 'nombre': 'Nombre', 'edad': 40, 'hermano_id': self.hermano.pk}])
        self.assertIsNone(Inscripto.objects.get().hermano)

    def test_edad_obligatoria_para_familiares(self):
        r = self.post([{'apellido': 'Perez', 'nombre': 'Juan', 'edad': 40}, {'apellido': 'Perez', 'nombre': 'Hijo', 'edad': ''}])
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'ingresá la edad')
        self.assertContains(r, 'Hijo')  # se conservan los datos cargados
        self.assertFalse(Inscripcion.objects.exists())

    def test_responsable_debe_ser_adulto(self):
        r = self.post([{'apellido': 'Perez', 'nombre': 'Juan', 'edad': 10}])
        self.assertContains(r, 'El responsable debe tener 12 años o más')
        self.assertFalse(Inscripcion.objects.exists())

    def test_edad_guardada_para_todos(self):
        self.post([{'apellido': 'Perez', 'nombre': 'Juan', 'edad': 45},
                   {'apellido': 'Gomez', 'nombre': 'Ana', 'parentesco': 'conyuge', 'edad': 43}])
        self.assertEqual(sorted(Inscripto.objects.values_list('edad', flat=True)), [43, 45])
        self.assertEqual(Inscripcion.objects.get().total(), 20000)

    def test_normalizar_celular(self):
        from .views import normalizar_celular
        self.assertEqual(normalizar_celular('351 1234567'), ('+54 9 3511234567', None))
        self.assertEqual(normalizar_celular('+54 9 3511234567')[0], '+54 9 3511234567')
        self.assertEqual(normalizar_celular('+543511234567')[0], '+54 9 3511234567')
        self.assertEqual(normalizar_celular('11 23456789')[0], '+54 9 1123456789')
        self.assertIn('sin el 0', normalizar_celular('0351 1234567')[1])
        self.assertIn('sin el 15', normalizar_celular('351 15 1234567')[1])
        self.assertIsNotNone(normalizar_celular('1512345678')[1])
        self.assertIsNotNone(normalizar_celular('351123')[1])
        self.assertEqual(normalizar_celular('+595981123456'), ('+595981123456', None))

    def test_celular_obligatorio(self):
        r = self.post([{'apellido': 'Perez', 'nombre': 'Juan', 'edad': 40}], celular='12')
        self.assertContains(r, 'celular')
        self.assertFalse(Inscripcion.objects.exists())

    def test_cupo(self):
        self.evento.cupo = 2
        self.evento.save()
        r = self.post([{'apellido': 'Aa', 'nombre': 'Bb', 'edad': 40}, {'apellido': 'Aa', 'nombre': 'Dd', 'edad': '40'},
                       {'apellido': 'Aa', 'nombre': 'Cc', 'edad': '5'}])
        self.assertContains(r, 'Solo quedan 2 lugares')
        self.post([{'apellido': 'Aa', 'nombre': 'Bb', 'edad': 40}, {'apellido': 'Aa', 'nombre': 'Cc', 'edad': '5'}])
        self.assertEqual(Inscripto.objects.count(), 2)
        r = self.client.get(self.url)
        self.assertContains(r, 'Se completó el cupo')

    def test_fecha_cierre(self):
        self.evento.fecha_cierre = timezone.now() - timedelta(hours=1)
        self.evento.save()
        r = self.post([{'apellido': 'Perez', 'nombre': 'Juan', 'edad': 40}])
        self.assertContains(r, 'La inscripción ya cerró')
        self.assertFalse(Inscripcion.objects.exists())

    def test_buscar(self):
        url = reverse('eventos:buscar', args=['fin-2026'])
        res = self.client.get(url, {'q': 'perez so'}).json()['resultados']
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]['tipo'], 'alumno')
        self.assertEqual(res[0]['edad'], 7)
        res = self.client.get(url, {'q': 'perez juan'}).json()['resultados']
        self.assertEqual(res[0]['tipo'], 'hermano')
        self.assertIsNone(res[0]['edad'])  # sin fecha de nacimiento
        # Apellido precompletado distinto (ej: el de la mama): busca solo por nombre
        r = self.client.get(url, {'apellido': 'Gomez', 'nombre': 'sofi', 'modo': 'familiar'}).json()
        self.assertTrue(r['aproximado'])
        self.assertEqual(r['resultados'][0]['nombre'], 'Sofía')
        # Muchos hermanos con el mismo apellido no tapan al alumno en modo familiar
        for i in range(10):
            Hermano.objects.create(apellidos='Pérez', nombres=f'Socorro {i}', sexo='F')
        r = self.client.get(url, {'apellido': 'Perez', 'nombre': 'so', 'modo': 'familiar'}).json()
        self.assertEqual(r['resultados'][0]['tipo'], 'alumno')
        res = self.client.get(url, {'q': 'pe'}).json()['resultados']
        self.assertEqual(res, [])  # minimo 3 letras

    def test_panel_y_excel(self):
        import openpyxl
        self.post([{'apellido': 'Pérez', 'nombre': 'Juan', 'edad': 45, 'hermano_id': self.hermano.pk},
                   {'apellido': 'Pérez', 'nombre': 'Sofía', 'parentesco': 'hijo', 'edad': '7', 'alumno_id': self.alumno.pk}])
        # Otra familia anota a la misma nena -> duplicado
        self.post([{'apellido': 'Gómez', 'nombre': 'Ana', 'edad': 38},
                   {'apellido': 'Perez', 'nombre': 'Sofia', 'parentesco': 'hijo', 'edad': '7'}])

        self.assertEqual(self.client.get(reverse('eventos:panel_lista')).status_code, 302)  # requiere login
        User.objects.create_user('staff', password='x', is_staff=True)
        self.client.login(username='staff', password='x')

        r = self.client.get(reverse('eventos:panel_detalle', args=[self.evento.pk]))
        self.assertContains(r, 'Posible duplicado')
        self.assertContains(r, 'No está en la base')
        self.assertEqual(r.context['totales']['monto'], 30000)
        self.assertEqual(r.context['totales']['revisar'], 2)

        r = self.client.get(reverse('eventos:panel_exportar', args=[self.evento.pk]))
        wb = openpyxl.load_workbook(io.BytesIO(r.content))
        fam = wb['Familias']
        self.assertEqual(fam.cell(row=5, column=2).value, 'Pérez, Juan')
        self.assertEqual(fam.cell(row=5, column=8).value, 15000)
        self.assertEqual(fam.cell(row=7, column=8).value, 30000)  # fila de totales
        self.assertEqual(wb['Personas'].max_row, 8)

        # Marcar pagado
        primera = Inscripcion.objects.first()
        self.client.post(reverse('eventos:panel_inscripcion_pagado', args=[primera.pk]))
        primera.refresh_from_db()
        self.assertTrue(primera.pagado)
        self.assertIsNotNone(primera.fecha_pago)
        r = self.client.get(reverse('eventos:panel_detalle', args=[self.evento.pk]), {'pago': 'pendiente'})
        self.assertEqual(r.context['totales']['cobrado'], 15000)
        self.assertEqual(r.context['totales']['pendiente'], 15000)
        self.assertEqual(len(r.context['inscripciones']), 1)
        r = self.client.get(reverse('eventos:panel_exportar', args=[self.evento.pk]))
        wb = openpyxl.load_workbook(io.BytesIO(r.content))
        self.assertTrue(wb['Familias'].cell(row=5, column=11).value.startswith('SÍ'))
        self.assertIsNone(wb['Familias'].cell(row=6, column=11).value)
        self.client.post(reverse('eventos:panel_inscripcion_pagado', args=[primera.pk]))
        primera.refresh_from_db()
        self.assertFalse(primera.pagado)

        r = self.client.get(reverse('eventos:panel_qr', args=[self.evento.pk]))
        self.assertEqual(r['Content-Type'], 'image/png')
        from PIL import Image
        img = Image.open(io.BytesIO(r.content))
        self.assertGreater(img.width, 800)
        self.assertGreater(img.height, img.width)  # texto debajo

        r = self.client.get(reverse('eventos:panel_editar', args=[self.evento.pk]))
        self.assertEqual(r.status_code, 200)
        r = self.client.post(reverse('eventos:panel_inscripcion_eliminar', args=[Inscripcion.objects.last().pk]))
        self.assertEqual(Inscripcion.objects.count(), 1)

    def test_panel_crear_evento(self):
        User.objects.create_user('staff', password='x', is_staff=True)
        self.client.login(username='staff', password='x')
        r = self.client.post(reverse('eventos:panel_crear'), {
            'nombre': 'Otro', 'slug': 'otro', 'fecha': '2026-12-20', 'informacion': '<p>Info</p>',
            'precio_adulto': 100, 'precio_nino': 50, 'edad_max_nino': 11, 'edad_min_paga': 3, 'activo': 'on',
        })
        ev = Evento.objects.get(slug='otro')
        self.assertRedirects(r, reverse('eventos:panel_detalle', args=[ev.pk]))
        self.assertContains(self.client.get(reverse('eventos:inscripcion', args=['otro'])), '<p>Info</p>')


class ChatDeshabilitadoTests(TestCase):
    def test_api_chat_rechaza_si_esta_deshabilitado(self):
        from contenido.models import DatosIce
        datos = DatosIce.load()
        datos.chat_habilitado = False
        datos.save()
        r = self.client.post(reverse('chat:send_code'), '{}', content_type='application/json')
        self.assertEqual(r.status_code, 403)
