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
        # Botones de WhatsApp para coordinar el pago (con el 9 agregado para Argentina)
        self.assertContains(r, 'https://wa.me/5493813419795?text=')
        self.assertContains(r, 'https://wa.me/5493816621117?text=')
        self.assertContains(r, 'Mi%20importe%20a%20pagar%20es%20%2425.000')
        self.assertContains(r, 'Santy o Paula')

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

    def test_reinscripcion_carga_la_previa_y_actualiza(self):
        familia = [{'apellido': 'Pérez', 'nombre': 'Juan', 'edad': 45, 'hermano_id': self.hermano.pk},
                   {'apellido': 'Pérez', 'nombre': 'Sofía', 'parentesco': 'hijo', 'edad': 7, 'alumno_id': self.alumno.pk}]
        self.post(familia, observaciones='Sin TACC')
        primera = Inscripcion.objects.get()

        # Se vuelve a inscribir (mismo responsable y celular) agregando a la esposa, sin saber que ya estaba
        nueva = [{'apellido': 'Perez', 'nombre': 'Juan', 'edad': 45},
                 {'apellido': 'Gómez', 'nombre': 'Ana', 'parentesco': 'conyuge', 'edad': 40}]
        r = self.post(nueva, celular='351 1234567')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Ya te habías inscripto')
        nombres = [f['nombre'] for f in r.context['filas_previas']]
        self.assertEqual(nombres, ['Juan', 'Sofía', 'Ana'])  # sus familiares anteriores + lo que agrego
        self.assertContains(r, 'Sin TACC')
        self.assertEqual(r.context['editar'], str(primera.pk))
        self.assertEqual(Inscripcion.objects.count(), 1)

        # Confirma los cambios: se actualiza la misma inscripcion
        r = self.post(familia + [nueva[1]], editar=primera.pk)
        self.assertRedirects(r, reverse('eventos:exito', args=['fin-2026']))
        self.assertEqual(Inscripcion.objects.count(), 1)
        self.assertEqual(primera.personas.count(), 3)
        self.assertContains(self.client.get(reverse('eventos:exito', args=['fin-2026'])), 'Inscripción actualizada')

    def test_reinscripcion_con_otro_celular_no_muestra_ni_duplica(self):
        self.post([{'apellido': 'Pérez', 'nombre': 'Juan', 'edad': 45},
                   {'apellido': 'Pérez', 'nombre': 'Sofía', 'parentesco': 'hijo', 'edad': 7}])
        r = self.post([{'apellido': 'Perez', 'nombre': 'Juan', 'edad': 45}], celular='351 9999999')
        self.assertContains(r, 'con otro celular')
        self.assertNotIn('Sofía', [f['nombre'] for f in r.context['filas_previas']])
        self.assertEqual(Inscripcion.objects.count(), 1)

    def test_reinscripcion_pagada_no_se_modifica(self):
        self.post([{'apellido': 'Pérez', 'nombre': 'Juan', 'edad': 45}])
        Inscripcion.objects.update(pagado=True)
        insc = Inscripcion.objects.get()
        r = self.post([{'apellido': 'Pérez', 'nombre': 'Juan', 'edad': 45},
                       {'apellido': 'Gómez', 'nombre': 'Ana', 'parentesco': 'conyuge', 'edad': 40}], editar=insc.pk)
        self.assertContains(r, 'figura como pagada')
        self.assertEqual(insc.personas.count(), 1)

    def test_editar_con_cupo_lleno_libera_sus_lugares(self):
        self.evento.cupo = 2
        self.evento.save()
        self.post([{'apellido': 'Pérez', 'nombre': 'Juan', 'edad': 45},
                   {'apellido': 'Pérez', 'nombre': 'Sofía', 'parentesco': 'hijo', 'edad': 7}])
        insc = Inscripcion.objects.get()
        r = self.post([{'apellido': 'Pérez', 'nombre': 'Juan', 'edad': 45},
                       {'apellido': 'Pérez', 'nombre': 'Sofía', 'parentesco': 'hijo', 'edad': 8}], editar=insc.pk)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(insc.personas.get(nombre='Sofía').edad, 8)

    def test_endpoint_inscripcion_previa(self):
        self.post([{'apellido': 'Pérez', 'nombre': 'Juan', 'edad': 45},
                   {'apellido': 'Pérez', 'nombre': 'Sofía', 'parentesco': 'hijo', 'edad': 7}])
        Inscripcion.objects.update(celular='3511234567')  # formato viejo, sin +54
        url = reverse('eventos:inscripcion_previa', args=['fin-2026'])
        d = self.client.post(url, {'apellido': 'perez', 'nombre': 'JUAN', 'celular': '+54 9 3511234567'}).json()
        self.assertTrue(d['encontrada'])
        self.assertEqual([f['nombre'] for f in d['filas']], ['Juan', 'Sofía'])
        d = self.client.post(url, {'apellido': 'perez', 'nombre': 'juan', 'celular': '+54 9 3519999999'}).json()
        self.assertEqual(d, {'encontrada': True, 'otro_celular': True})
        d = self.client.post(url, {'apellido': 'Otro', 'nombre': 'Nombre', 'celular': '+54 9 3511234567'}).json()
        self.assertFalse(d['encontrada'])

    def _con_descuento(self, dias=5):
        self.evento.fecha_limite_descuento = timezone.localdate() + timedelta(days=dias)
        self.evento.precio_adulto_descuento = 8000
        self.evento.precio_nino_descuento = 3000
        self.evento.nota_comprobante = 'Alias: ICE.EVENTOS'
        self.evento.save()

    def test_descuento_en_comprobante_y_whatsapp(self):
        self._con_descuento()
        self.post([{'apellido': 'Pérez', 'nombre': 'Juan', 'edad': 45},
                   {'apellido': 'Pérez', 'nombre': 'Sofía', 'parentesco': 'hijo', 'edad': 7},
                   {'apellido': 'Pérez', 'nombre': 'Bebé', 'parentesco': 'hijo', 'edad': 1}])
        insc = Inscripcion.objects.get()
        self.assertEqual(insc.total(), 15000)
        self.assertEqual(insc.total_descuento(), 11000)
        r = self.client.get(reverse('eventos:exito', args=['fin-2026']))
        self.assertContains(r, 'aplicaremos un descuento')
        self.assertContains(r, '11.000')
        self.assertContains(r, 'Pagando después')
        self.assertContains(r, 'Alias: ICE.EVENTOS')
        self.assertContains(r, 'Mi%20importe%20a%20pagar%20es%20%2411.000%20%28con%20el%20descuento')

    def test_descuento_vencido_cobra_precio_normal(self):
        self._con_descuento(dias=-1)
        self.post([{'apellido': 'Pérez', 'nombre': 'Juan', 'edad': 45}])
        r = self.client.get(reverse('eventos:exito', args=['fin-2026']))
        self.assertNotContains(r, 'aplicaremos un descuento')
        self.assertContains(r, 'Mi%20importe%20a%20pagar%20es%20%2410.000.')

    def test_marcar_pagado_con_y_sin_descuento(self):
        self._con_descuento()
        self.post([{'apellido': 'Pérez', 'nombre': 'Juan', 'edad': 45}])
        self.post([{'apellido': 'Gómez', 'nombre': 'Ana', 'edad': 40}], celular='351 7654321')
        a, b = Inscripcion.objects.order_by('pk')
        User.objects.create_user('staff', password='x', is_staff=True)
        self.client.login(username='staff', password='x')
        self.client.post(reverse('eventos:panel_inscripcion_pagado', args=[a.pk]), {'descuento': '1'})
        self.client.post(reverse('eventos:panel_inscripcion_pagado', args=[b.pk]), {'descuento': '0'})
        a.refresh_from_db(); b.refresh_from_db()
        self.assertTrue(a.con_descuento)
        self.assertFalse(b.con_descuento)
        self.assertEqual(a.total_pagado(), 8000)
        self.assertEqual(b.total_pagado(), 10000)
        r = self.client.get(reverse('eventos:panel_detalle', args=[self.evento.pk]))
        self.assertEqual(r.context['totales']['cobrado'], 18000)
        self.assertEqual(r.context['totales']['monto_descuento'], 16000)
        self.assertContains(r, 'Pagado $8.000 c/desc.')

        import openpyxl
        r = self.client.get(reverse('eventos:panel_exportar', args=[self.evento.pk]))
        ws = openpyxl.load_workbook(io.BytesIO(r.content))['Familias']
        headers = [c.value for c in ws[4]]
        self.assertIn('Monto pagado', headers)
        self.assertTrue(any(h and h.startswith('Total c/desc.') for h in headers))
        col_pagado = headers.index('Pagado') + 1
        col_monto = headers.index('Monto pagado') + 1
        self.assertIn('c/desc.', ws.cell(row=5, column=col_pagado).value)
        self.assertEqual(ws.cell(row=5, column=col_monto).value, 8000)

        # Desmarcar limpia el descuento
        self.client.post(reverse('eventos:panel_inscripcion_pagado', args=[a.pk]))
        a.refresh_from_db()
        self.assertFalse(a.pagado or a.con_descuento)

    def test_form_descuento_incompleto(self):
        from .forms import EventoForm
        datos = {'nombre': 'X', 'slug': 'x', 'fecha': '2026-12-20', 'precio_adulto': 100, 'precio_nino': 50,
                 'edad_max_nino': 11, 'edad_min_paga': 3, 'precio_adulto_descuento': 80}
        f = EventoForm(datos)
        self.assertFalse(f.is_valid())
        self.assertIn('fecha_limite_descuento', f.errors)
        datos.update(fecha_limite_descuento='2026-12-01', precio_nino_descuento=60)
        f = EventoForm(datos)
        self.assertFalse(f.is_valid())
        self.assertIn('precio_nino_descuento', f.errors)  # mayor al normal

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
        # Con el cupo lleno no entra una inscripcion nueva
        r = self.post([{'apellido': 'Nuevo', 'nombre': 'Señor', 'edad': 50}], celular='351 7777777')
        self.assertContains(r, 'Se completó el cupo')
        self.assertEqual(Inscripcion.objects.count(), 1)

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
