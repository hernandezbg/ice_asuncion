from datetime import date

from django.contrib.auth.models import User, Group
from django.test import TestCase
from django.urls import reverse

from eventos.models import Evento
from .permisos import GRUPO_EVENTOS


class PermisosEventosTests(TestCase):
    def setUp(self):
        self.grupo, _ = Group.objects.get_or_create(name=GRUPO_EVENTOS)
        self.secre = User.objects.create_user('secre', password='clave1234')
        self.secre.groups.add(self.grupo)
        self.evento = Evento.objects.create(nombre='Cena', slug='cena', fecha=date(2026, 12, 12),
                                            precio_adulto=10000, precio_nino=5000)

    def test_grupo_creado_por_migracion(self):
        self.assertTrue(Group.objects.filter(name='Eventos').exists())

    def test_login_lleva_a_eventos(self):
        r = self.client.post(reverse('panel:login'), {'username': 'secre', 'password': 'clave1234'})
        self.assertRedirects(r, reverse('eventos:panel_lista'))

    def test_login_ignora_next_externo(self):
        r = self.client.post(reverse('panel:login') + '?next=https://malo.com/',
                             {'username': 'secre', 'password': 'clave1234'})
        self.assertRedirects(r, reverse('eventos:panel_lista'))

    def test_secre_ve_y_edita_eventos(self):
        self.client.login(username='secre', password='clave1234')
        r = self.client.get(reverse('eventos:panel_lista'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Eventos')
        self.assertNotContains(r, reverse('panel:hermanos_lista'))
        self.assertNotContains(r, reverse('panel:usuarios_lista'))
        self.assertEqual(self.client.get(reverse('eventos:panel_editar', args=[self.evento.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse('eventos:panel_exportar', args=[self.evento.pk])).status_code, 200)

    def test_secre_no_entra_a_otras_secciones(self):
        self.client.login(username='secre', password='clave1234')
        for nombre in ['panel:hermanos_lista', 'panel:escuela_alumnos', 'panel:noticias_lista', 'panel:usuarios_lista']:
            r = self.client.get(reverse(nombre))
            self.assertEqual(r.status_code, 302, nombre)
            self.assertIn(reverse('panel:login'), r['Location'])
        # El dashboard la manda a eventos (sin loop de redirecciones)
        self.assertRedirects(self.client.get(reverse('panel:dashboard')), reverse('eventos:panel_lista'))

    def test_usuario_sin_permisos_no_entra(self):
        User.objects.create_user('comun', password='clave1234')
        r = self.client.post(reverse('panel:login'), {'username': 'comun', 'password': 'clave1234'})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'No tienes permisos')

    def test_staff_sigue_viendo_todo(self):
        User.objects.create_user('staff', password='clave1234', is_staff=True)
        self.client.login(username='staff', password='clave1234')
        r = self.client.get(reverse('eventos:panel_lista'))
        self.assertContains(r, reverse('panel:hermanos_lista'))
        self.assertNotContains(r, reverse('panel:usuarios_lista'))
        self.assertEqual(self.client.get(reverse('panel:usuarios_lista')).status_code, 302)


class UsuariosPanelTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('admin', password='clave1234', email='a@a.com')
        self.client.login(username='admin', password='clave1234')

    def test_crear_usuario_solo_eventos(self):
        r = self.client.post(reverse('panel:usuario_crear'), {
            'username': 'Maria', 'first_name': 'María', 'last_name': 'Gómez', 'email': '',
            'is_active': 'on', 'rol': 'eventos', 'password': 'secreta123'})
        self.assertRedirects(r, reverse('panel:usuarios_lista'))
        u = User.objects.get(username='maria')
        self.assertFalse(u.is_staff)
        self.assertTrue(u.groups.filter(name=GRUPO_EVENTOS).exists())
        self.assertTrue(u.check_password('secreta123'))
        r = self.client.get(reverse('panel:usuarios_lista'))
        self.assertContains(r, 'maria')
        self.assertContains(r, 'Solo Eventos')

    def test_password_obligatoria_y_minima(self):
        datos = {'username': 'x', 'is_active': 'on', 'rol': 'eventos', 'password': ''}
        r = self.client.post(reverse('panel:usuario_crear'), datos)
        self.assertEqual(r.status_code, 200)
        datos['password'] = 'corta'
        r = self.client.post(reverse('panel:usuario_crear'), datos)
        self.assertContains(r, 'al menos 8')
        self.assertFalse(User.objects.filter(username='x').exists())

    def test_cambiar_rol_y_desactivar(self):
        u = User.objects.create_user('ana', password='clave1234')
        u.groups.add(Group.objects.get(name=GRUPO_EVENTOS))
        r = self.client.post(reverse('panel:usuario_editar', args=[u.pk]), {
            'username': 'ana', 'rol': 'staff', 'password': ''})  # is_active sin marcar = desactivar
        self.assertRedirects(r, reverse('panel:usuarios_lista'))
        u.refresh_from_db()
        self.assertTrue(u.is_staff)
        self.assertFalse(u.is_active)
        self.assertFalse(u.groups.filter(name=GRUPO_EVENTOS).exists())
        self.assertTrue(u.check_password('clave1234'))  # vacía = no cambia

    def test_admin_no_se_desactiva_ni_pierde_rol(self):
        r = self.client.post(reverse('panel:usuario_editar', args=[self.admin.pk]), {
            'username': 'admin', 'rol': 'eventos', 'password': ''})
        self.assertRedirects(r, reverse('panel:usuarios_lista'))
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)
        self.assertTrue(self.admin.is_superuser)
        self.assertTrue(self.admin.is_staff)

    def test_usuario_duplicado(self):
        User.objects.create_user('pepe', password='clave1234')
        r = self.client.post(reverse('panel:usuario_crear'), {
            'username': 'PEPE', 'is_active': 'on', 'rol': 'eventos', 'password': 'secreta123'})
        self.assertContains(r, 'Ya existe')
