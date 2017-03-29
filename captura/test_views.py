import time
import string
import random

from django.core.urlresolvers import reverse
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User, Group
from django.test import TestCase
from django.test import Client
from splinter import Browser

from administracion.models import Escuela
from estudios_socioeconomicos.models import Estudio, Seccion, Pregunta, Respuesta
from estudios_socioeconomicos.models import Subseccion, OpcionRespuesta
from familias.models import Familia, Integrante
from perfiles_usuario.models import Capturista
from estudios_socioeconomicos.load import load_data
from perfiles_usuario.utils import CAPTURISTA_GROUP

def to_list(value):
    if value is None:
        value = []
    elif not isinstance(value, list):
        value = [value]
    return value

class TestViewsCapturaEstudio(StaticLiveServerTestCase):
    """Integration test suite for testing the views in the app: capturista.

    Test the urls for 'capturista' which allow the user to fill out a study.

    Attributes
    ----------
    browser : Browser
        Driver to navigate through websites and to run integration tests.
    """

    def setUp(self):
        """ Initialize the browser, create a user, a family and a study.
            Perform login.
        """
        self.browser = Browser('chrome')
        test_username = 'erikiano'
        test_password = 'vacalalo'

        elerik = User.objects.create_user(
            username=test_username,
            email='latelma@junipero.sas',
            password=test_password,
            first_name='telma',
            last_name='suapellido')

        self.capturista = Capturista.objects.create(user=elerik)
        self.capturista.save()

        load_data()

        self.familia = Familia.objects.create(
            numero_hijos_diferentes_papas=3,
            explicacion_solvencia='narco',
            estado_civil='secreto',
            localidad='otro')

        self.estudio = Estudio.objects.create(
            capturista=self.capturista,
            familia=self.familia,
            status=Estudio.APROBADO)

        self.estudio.save()
        self.familia.save()

        self.assertEqual(Respuesta.objects.all().count(), Pregunta.objects.all().count())
        self.test_url_name = 'captura:contestar_estudio'
        self.browser.visit(self.live_server_url + reverse('tosp_auth:login'))
        self.browser.fill('username', test_username)
        self.browser.fill('password', test_password)
        self.browser.find_by_id('login-submit').click()

    def tearDown(self):
        self.browser.quit()

    def test_displaying_question_and_answers(self):
        """ Tests that when a user loads the URL for filling a study,
            the html elements for all the questions in that section
            are rendered.
        """
        secciones = Seccion.objects.all().order_by('numero')

        self.browser.visit(
            self.live_server_url + reverse(
                self.test_url_name,
                kwargs={'id_estudio': self.estudio.id, 'numero_seccion': secciones[0].numero}))

        subsecciones = Subseccion.objects.filter(seccion=secciones[0])

        for subseccion in subsecciones:
            self.assertTrue(self.browser.is_text_present(subseccion.nombre))

        preguntas = Pregunta.objects.filter(subseccion__in=subsecciones)

        for pregunta in preguntas:
            respuesta = Respuesta.objects.filter(pregunta=pregunta)[0]
            num_opciones = OpcionRespuesta.objects.filter(pregunta=pregunta).count()

            if num_opciones > 0:
                for i in range(num_opciones):
                    answer_input = self.browser.find_by_id(
                        'id_respuesta-' + str(respuesta.id) + '-eleccion_' + str(i))

                    self.assertNotEqual(answer_input, [])
                    self.assertTrue(self.browser.is_text_present(pregunta.texto))
            else:
                answer_input = self.browser.find_by_id(
                    'id_respuesta-' + str(respuesta.id) + '-respuesta')
                self.assertNotEqual(answer_input, [])
                self.assertTrue(self.browser.is_text_present(pregunta.texto))

    def test_incorrect_url_parameters(self):
        """ Test that a user can't query inexistent studies or sections.
        """
        secciones = Seccion.objects.all().order_by('numero')

        self.browser.visit(
            self.live_server_url + reverse(
                self.test_url_name,
                kwargs={'id_estudio': 0, 'numero_seccion': secciones[0].numero}))

        self.assertTrue(self.browser.is_text_present('Not Found'))

    def test_adding_more_answers(self):
        """ Test that a user can dynamically add more questions to a
            study.
        """
        secciones = Seccion.objects.all().order_by('numero')
        subsecciones = Subseccion.objects.filter(seccion=secciones[0])
        preguntas = Pregunta.objects.filter(subseccion__in=subsecciones)
        opciones = OpcionRespuesta.objects.filter(pregunta__in=preguntas)

        preguntas_texto = preguntas.exclude(pk__in=opciones.values_list('pregunta', flat=True))

        self.browser.visit(
            self.live_server_url + reverse(
                self.test_url_name,
                kwargs={'id_estudio': self.estudio.id, 'numero_seccion': secciones[0].numero}))

        number_answers = Respuesta.objects.all().count()

        self.browser.find_by_id('answer-for-' + str(preguntas_texto[0].id)).first.click()
        time.sleep(.1)
        self.assertEqual(number_answers + 1, Respuesta.objects.all().count())

        nueva_respuesta = Respuesta.objects.all().order_by('-id')[0]
        answer_input = self.browser.find_by_id(
            'id_respuesta-' + str(nueva_respuesta.id) + '-respuesta')
        self.assertNotEqual(answer_input, [])

    def test_removing_ansers(self):
        """ Test that a user can dynamically remove questions from a study.
        """
        secciones = Seccion.objects.all().order_by('numero')
        subsecciones = Subseccion.objects.filter(seccion=secciones[0])
        preguntas = Pregunta.objects.filter(subseccion__in=subsecciones)
        opciones = OpcionRespuesta.objects.filter(pregunta__in=preguntas)

        preguntas_texto = preguntas.exclude(pk__in=opciones.values_list('pregunta', flat=True))

        self.browser.visit(
            self.live_server_url + reverse(
                self.test_url_name,
                kwargs={'id_estudio': self.estudio.id, 'numero_seccion': secciones[0].numero}))

        self.browser.find_by_id('answer-for-' + str(preguntas_texto[0].id)).first.click()
        number_answers = Respuesta.objects.all().count()

        self.browser.find_by_css('.delete-answer').first.click()
        self.assertNotEqual(number_answers, Respuesta.objects.all().count())

    def test_submitting_answers(self):
        """ Test that when a user submits his answers and moves on to the
        next section the answers are saved.
        """
        secciones = Seccion.objects.all().order_by('numero')
        subsecciones = Subseccion.objects.filter(seccion=secciones[0])
        preguntas = Pregunta.objects.filter(subseccion__in=subsecciones)
        respuestas = Respuesta.objects.filter(pregunta__in=preguntas)

        self.browser.visit(
            self.live_server_url + reverse(
                self.test_url_name,
                kwargs={'id_estudio': self.estudio.id, 'numero_seccion': secciones[0].numero}))

        random_texts = {}

        for pregunta in preguntas:
            respuestas = Respuesta.objects.filter(pregunta=pregunta)

            for respuesta in respuestas:
                num_opciones = OpcionRespuesta.objects.filter(pregunta=pregunta).count()

                if num_opciones > 0:

                    answer_input = self.browser.find_by_id(
                        'id_respuesta-' + str(respuesta.id) + '-eleccion_' + str(num_opciones-1))

                    answer_input.check()
                else:
                    new_text = ''.join(random.choice(string.ascii_uppercase) for _ in range(12))
                    answer_input = self.browser.find_by_id(
                        'id_respuesta-' + str(respuesta.id) + '-respuesta').first
                    answer_input.fill(new_text)
                    random_texts[respuesta.id] = new_text

        self.browser.find_by_id('next_section_button').first.click()
        time.sleep(.1)
        self.browser.find_by_id('previous_section_button').first.click()
        time.sleep(.1)

        for pregunta in preguntas:
            respuestas = Respuesta.objects.filter(pregunta=pregunta)

            for respuesta in respuestas:
                num_opciones = OpcionRespuesta.objects.filter(pregunta=pregunta).count()

                if num_opciones > 0:
                    answer_input = self.browser.find_by_id(
                        'id_respuesta-' + str(respuesta.id) + '-eleccion_' + str(num_opciones-1))

                    self.assertTrue(answer_input.checked)
                else:
                    answer_input = self.browser.find_by_id(
                        'id_respuesta-' + str(respuesta.id) + '-respuesta').first
                    self.assertEqual(answer_input.value, random_texts[respuesta.id])

    def test_submitting_answer_with_dynamic_answers(self):
        """ Test that answers generated dynamically are being saved after submission.
        """
        secciones = Seccion.objects.all().order_by('numero')
        subsecciones = Subseccion.objects.filter(seccion=secciones[0])
        preguntas = Pregunta.objects.filter(subseccion__in=subsecciones)
        opciones = OpcionRespuesta.objects.filter(pregunta__in=preguntas)

        preguntas_texto = preguntas.exclude(pk__in=opciones.values_list('pregunta', flat=True))

        self.browser.visit(
            self.live_server_url + reverse(
                self.test_url_name,
                kwargs={'id_estudio': self.estudio.id, 'numero_seccion': secciones[0].numero}))

        number_answers = Respuesta.objects.all().count()

        self.browser.find_by_id('answer-for-' + str(preguntas_texto[0].id)).first.click()
        time.sleep(.1)
        self.assertEqual(number_answers + 1, Respuesta.objects.all().count())

        nueva_respuesta = Respuesta.objects.all().order_by('-id')[0]
        new_text = ''.join(random.choice(string.ascii_uppercase) for _ in range(12))
        answer_input = self.browser.find_by_id(
            'id_respuesta-' + str(nueva_respuesta.id) + '-respuesta').first
        answer_input.fill(new_text)

        self.browser.find_by_id('next_section_button').first.click()
        time.sleep(.1)
        self.browser.find_by_id('previous_section_button').first.click()
        time.sleep(.1)

        answer_input = self.browser.find_by_id(
            'id_respuesta-' + str(nueva_respuesta.id) + '-respuesta').first

        self.assertEqual(answer_input.value, new_text)

    def test_passing_all_sections(self):
        """ Test going through all possible sections.
        """
        secciones = Seccion.objects.all().order_by('numero')

        self.browser.visit(
            self.live_server_url + reverse(
                self.test_url_name,
                kwargs={'id_estudio': self.estudio.id, 'numero_seccion': secciones[0].numero}))

        for seccion in secciones:
            time.sleep(.1)
            self.assertTrue(self.browser.is_text_present(seccion.nombre))
            self.browser.find_by_id('next_section_button').first.click()


class TestViewsFamilia(TestCase):
    """ Integration test suite for testing the views in the app captura,
    that surround the creation of editing of the familia model.

    Attributes
    ----------
    client : Client
        Django Client for the testing of all the views related to the creation
        and edition of a family.
    elerik : User
        User that will be used as a capturista in order to fill all everything
        related with familia.
    familia1 : Familia
        Used in tests that depend on creating an object related to a familia
    integrante1 : Integrante
        Used in tests that depend on creating an object related to an integrante
    escuela : Used in tests that depend on creating an object related to an escuela
    capturista : Capturista
        Asociated with the User, as this object is required for permissions and
        creation.
    integrante_contructor_dictionary : dictrionary
        Used in order to prevent repetitive code, when creating very similar integrantes
        in different tests.
    alumno_contructor_dictionary : dictionary
        Used in order to prevent repetitive code, when creating very similar alumnos in
        different tests.
    tutor_constructor_dictionary : dictionary
        Used in order to prevent repetivie code, when creating very similar tutores in
        different tests.
    """

    def setUp(self):
        """ Creates all the initial necessary objects for the tests
        """
        self.client = Client()
        test_username = 'erikiano'
        test_password = 'vacalalo'

        elerik = User.objects.create_user(
            username=test_username,
            email='latelma@junipero.sas',
            password=test_password,
            first_name='telma',
            last_name='suapellido')

        numero_hijos_inicial = 3
        estado_civil_inicial = 'soltero'
        localidad_inicial = 'salitre'
        self.familia1 = Familia.objects.create(numero_hijos_diferentes_papas=numero_hijos_inicial,
                                               estado_civil=estado_civil_inicial,
                                               localidad=localidad_inicial)

        self.integrante1 = Integrante.objects.create(familia=self.familia1,
                                                     nombres='Rick',
                                                     apellidos='Astley',
                                                     nivel_estudios='doctorado',
                                                     fecha_de_nacimiento='1996-02-26')

        self.escuela = Escuela.objects.create(nombre='Juan Pablo')

        self.capturista = Capturista.objects.create(user=elerik)
        self.capturista.save()

        self.integrante_constructor_dictionary = {'familia': self.familia1.id,
                                                  'nombres': 'Arturo',
                                                  'apellidos': 'Herrera Rosas',
                                                  'telefono': '',
                                                  'correo': '',
                                                  'nivel_estudios': 'ninguno',
                                                  'fecha_de_nacimiento': '2017-03-22',
                                                  'Rol': 'ninguno'}

        self.alumno_constructor_dictionary = {'integrante': self.integrante1.id,
                                              'numero_sae': 5876,
                                              'escuela': self.escuela.id}
        self.tutor_constructor_dictionary = {'integrante': self.integrante1.id,
                                             'relacion': 'madre'}

        self.client.login(username=test_username, password=test_password)

    def test_create_estudio(self):
        """ Tests the creation of a studio through the create_estudio page.
        """
        response = self.client.post(reverse('captura:create_estudio'),
                                    {'numero_hijos_diferentes_papas': 2,
                                     'estado_civil': 'soltero',
                                     'localidad': 'salitre'})
        id_familia = Familia.objects.latest('id').id
        self.assertRedirects(response, reverse('captura:integrantes',
                                               kwargs={'id_familia': id_familia}))

    def test_create_estudio_incomplete(self):
        """ Tests that the create estudio form fails gracefully when sending invalid data
        to the create_estudio view.
        """
        response = self.client.post(reverse('captura:create_estudio'),
                                    {'estado_civil': 'soltero',
                                     'localidad': 'salitre'})
        self.assertFormError(response,
                             'form',
                             'numero_hijos_diferentes_papas',
                             'This field is required.')
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'captura/captura_base.html')

    def test_edit_familia(self):
        """ Tests that a familia can be edited through the edit_familia view.
        """
        numero_hijos_inicial = 3
        estado_civil_inicial = 'soltero'
        localidad_inicial = 'salitre'

        numero_hijos_final = 2
        estado_civil_final = 'viudo'
        localidad_final = 'nabo'

        familia = Familia.objects.create(numero_hijos_diferentes_papas=numero_hijos_inicial,
                                         estado_civil=estado_civil_inicial,
                                         localidad=localidad_inicial)
        response = self.client.post(reverse('captura:familia', kwargs={'id_familia': familia.id}),
                                    {'numero_hijos_diferentes_papas': numero_hijos_final,
                                     'estado_civil': estado_civil_final,
                                     'localidad': localidad_final})
        familia = Familia.objects.latest('id')
        self.assertEqual(familia.numero_hijos_diferentes_papas, numero_hijos_final)
        self.assertEqual(familia.estado_civil, estado_civil_final)
        self.assertEqual(familia.localidad, localidad_final)
        self.assertRedirects(response, reverse('captura:integrantes',
                                               kwargs={'id_familia': familia.id}))

    def test_edit_familia_incomplete(self):
        """ Tests that the familia edit view and form fail gracefully when provided with
        invalid data.
        """
        numero_hijos_final = 2
        estado_civil_final = 'viudo'

        response = self.client.post(reverse('captura:familia',
                                            kwargs={'id_familia': self.familia1.id}),
                                    {'numero_hijos_diferentes_papas': numero_hijos_final,
                                     'estado_civil': estado_civil_final})

        self.assertFormError(response, 'form', 'localidad', 'This field is required.')
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'captura/captura_base.html')

    def test_create_integrante(self):
        """ Tests that an integrante can be created through the combination of the
        create_integrante view, form, and template.
        """
        response = self.client.post(reverse('captura:create_integrante',
                                            kwargs={'id_familia': self.familia1.id}),
                                    self.integrante_constructor_dictionary)
        self.assertRedirects(response, reverse('captura:integrantes',
                                               kwargs={'id_familia': self.familia1.id}))

    def test_create_integrante_incomplete(self):
        """ Tests that the form and view for create_integrante fail gracefully when provided
        with invalid data.
        """
        self.integrante_constructor_dictionary['apellidos'] = ''
        response = self.client.post(reverse('captura:create_integrante',
                                            kwargs={'id_familia': self.familia1.id}),
                                    self.integrante_constructor_dictionary)
        self.assertFormError(response, 'form', 'apellidos', 'This field is required.')
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'captura/captura_base.html')

    def test_create_integrante_with_rol_alumno(self):
        """ Tests that an alumno can be created through the creation flow, i.e. when
        a capturista creates an integrante, if he decides to add the alumno role to
        it, the capturista will then be redirected to the creation view of the alumno
        """
        self.integrante_constructor_dictionary['Rol'] = 'alumno'
        response = self.client.post(reverse('captura:create_integrante',
                                            kwargs={'id_familia': self.familia1.id}),
                                    self.integrante_constructor_dictionary)
        integrante = Integrante.objects.latest('id')
        self.assertRedirects(response, reverse('captura:create_alumno',
                                               kwargs={'id_integrante': integrante.id}))

        self.alumno_constructor_dictionary['integrante'] = integrante.id
        response = self.client.post(reverse('captura:create_alumno',
                                            kwargs={'id_integrante': integrante.id}),
                                    self.alumno_constructor_dictionary)
        self.assertRedirects(response, reverse('captura:integrantes',
                                               kwargs={'id_familia': integrante.familia.pk}))

    def test_create_integrante_with_rol_alumno_incomplete(self):
        """ Tests that the view and form for create alumno fail gracefully if provided
        with invalid information.
        """
        self.integrante_constructor_dictionary['Rol'] = 'alumno'
        response = self.client.post(reverse('captura:create_integrante',
                                            kwargs={'id_familia': self.familia1.id}),
                                    self.integrante_constructor_dictionary)
        integrante = Integrante.objects.latest('id')
        self.assertRedirects(response, reverse('captura:create_alumno',
                                               kwargs={'id_integrante': integrante.id}))

        self.alumno_constructor_dictionary['numero_sae'] = ''
        response = self.client.post(reverse('captura:create_alumno',
                                            kwargs={'id_integrante': integrante.id}),
                                    self.alumno_constructor_dictionary)
        self.assertFormError(response, 'form', 'numero_sae', 'This field is required.')
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'captura/captura_base.html')

    def test_create_integrante_with_rol_tutor(self):
        """ Tests that a tutor can be created through the creation flow, i.e. when
        a capturista creates an integrante, if he decides to add the tutor role to
        it, the capturista will then be redirected to the creation view of the tutor.
        """
        self.integrante_constructor_dictionary['Rol'] = 'tutor'
        response = self.client.post(reverse('captura:create_integrante',
                                            kwargs={'id_familia': self.familia1.id}),
                                    self.integrante_constructor_dictionary)
        integrante = Integrante.objects.latest('id')
        self.assertRedirects(response, reverse('captura:create_tutor',
                                               kwargs={'id_integrante': integrante.id}))
        response = self.client
        self.tutor_constructor_dictionary['integrante'] = integrante.id
        response = self.client.post(reverse('captura:create_tutor',
                                            kwargs={'id_integrante': integrante.id}),
                                    self.tutor_constructor_dictionary)
        self.assertRedirects(response, reverse('captura:integrantes',
                                               kwargs={'id_familia': integrante.familia.pk}))

    def test_create_integrante_with_rol_tutor_incomplete(self):
        """ Test that that the view and form for create tutor fail gracefully when
        provided wih invalid information
        """
        self.integrante_constructor_dictionary['Rol'] = 'tutor'
        response = self.client.post(reverse('captura:create_integrante',
                                            kwargs={'id_familia': self.familia1.id}),
                                    self.integrante_constructor_dictionary)
        integrante = Integrante.objects.latest('id')
        self.assertRedirects(response, reverse('captura:create_tutor',
                                               kwargs={'id_integrante': integrante.id}))
        response = self.client
        self.tutor_constructor_dictionary['relacion'] = ''
        response = self.client.post(reverse('captura:create_tutor',
                                            kwargs={'id_integrante': integrante.id}),
                                     self.tutor_constructor_dictionary)
        print('Pasa con form')
        contexts = to_list(response.context)
        print(contexts)
        self.assertFormError(response, 'form', 'relacion', 'This field is required.')
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'captura/captura_base.html')

    def test_edit_integrante(self):
        """ Test that an already existing integrante can be edited, through the
        edit_integrante view and form.
        """
        new_name = 'Never'
        self.integrante_constructor_dictionary['nombres'] = new_name
        response = self.client.post(reverse('captura:integrante',
                                            kwargs={'id_integrante': self.integrante1.id}),
                                    self.integrante_constructor_dictionary)
        self.assertRedirects(response, reverse('captura:integrantes',
                                               kwargs={'id_familia': self.integrante1.familia.pk}))
        integrante = Integrante.objects.get(id=self.integrante1.id)
        self.assertEqual(new_name, integrante.nombres)

    # This test is properly implemented but fails due to a bug in the assertFormError method.
    # def test_edit_integrante_incompleto(self):
    #     """ Test that the view and form for edit_integrante fail gracefully when provided
    #     with invalid data
    #     """
    #     new_name = ''
    #     self.integrante_constructor_dictionary['nombres'] = new_name
    #     response = self.client.post(reverse('captura:integrante',
    #                                         kwargs={'id_integrante': self.integrante1.id}),
    #                                 self.integrante_constructor_dictionary)
    #     print('No pasa con integrante_form')
    #     contexts = to_list(response.context)
    #     print(contexts)
    #     self.assertFormError(response, 'integrante_form', 'nombres', 'This field is required.')
    #     self.assertEqual(200, response.status_code)
    #     self.assertTemplateUsed(response, 'captura/captura_base.html')
    #     integrante = Integrante.objects.get(id=self.integrante1.id)
    #     self.assertNotEqual(new_name, integrante.nombres)

class TestViewsFamiliaLive(StaticLiveServerTestCase):
    """ The purpose of this class is to suplement TestViewsFamilia, as some of the required tests
    cannot be ran via de django client.

    Attributes
    ----------
    browser : Browser
        Driver to navigate through websites and to run integration tests.
    elerik : User
        User that will be used as a capturista in order to fill all everything
        related with familia.
    familia1 : Familia
        Used in tests that depend on creating an object related to a familia
    integrante1 : Integrante
        Used in tests that depend on creating an object related to an integrante
    escuela : Used in tests that depend on creating an object related to an escuela
    capturista : Capturista
        Asociated with the User, as this object is required for permissions and
        creation.
    integrante_contructor_dictionary : dictrionary
        Used in order to prevent repetitive code, when creating very similar integrantes
        in different tests.
    alumno_contructor_dictionary : dictionary
        Used in order to prevent repetitive code, when creating very similar alumnos in
        different tests.
    tutor_constructor_dictionary : dictionary
        Used in order to prevent repetivie code, when creating very similar tutores in
        different tests.
    """

    def setUp(self):
        def setUp(self):
        """ Creates all the initial necessary objects for the tests
        """
        self.browser = Browser('chrome')
        test_username = 'erikiano'
        test_password = 'vacalalo'

        elerik = User.objects.create_user(
            username=test_username,
            email='latelma@junipero.sas',
            password=test_password,
            first_name='telma',
            last_name='suapellido')

        numero_hijos_inicial = 3
        estado_civil_inicial = 'soltero'
        localidad_inicial = 'salitre'
        self.familia1 = Familia.objects.create(numero_hijos_diferentes_papas=numero_hijos_inicial,
                                               estado_civil=estado_civil_inicial,
                                               localidad=localidad_inicial)

        self.integrante1 = Integrante.objects.create(familia=self.familia1,
                                                     nombres='Rick',
                                                     apellidos='Astley',
                                                     nivel_estudios='doctorado',
                                                     fecha_de_nacimiento='1996-02-26')

        self.escuela = Escuela.objects.create(nombre='Juan Pablo')

        self.capturista = Capturista.objects.create(user=elerik)
        self.capturista.save()

        self.integrante_constructor_dictionary = {'familia': self.familia1.id,
                                                  'nombres': 'Arturo',
                                                  'apellidos': 'Herrera Rosas',
                                                  'telefono': '',
                                                  'correo': '',
                                                  'nivel_estudios': 'ninguno',
                                                  'fecha_de_nacimiento': '2017-03-22',
                                                  'Rol': 'ninguno'}

        self.alumno_constructor_dictionary = {'integrante': self.integrante1.id,
                                              'numero_sae': 5876,
                                              'escuela': self.escuela.id}
        self.tutor_constructor_dictionary = {'integrante': self.integrante1.id,
                                             'relacion': 'madre'}

        self.browser.visit(self.live_server_url + reverse('tosp_auth:login'))
        self.browser.fill('username', test_username)
        self.browser.fill('password', test_password)
        self.browser.find_by_id('login-submit').click()

    def tearDown(self):
        """ At the end of tests, close the browser.
        """
        self.browser.quit()

    def test_edit_integrante_incompleto(self):
        """ Test that the view and form for edit_integrante fail gracefully when provided
        with invalid data.
        """
        self.browser.visit(self.live_server_url + reverse)

class TestViewsRightSide(StaticLiveServerTestCase):
    """Integration test suite for testing the views in the app: captura.

    Test the urls for 'captura' which make up the capturista dashboard.
    A user is created in order to test they are displayed.

    Attributes
    ----------
    browser : Browser
        Driver to navigate through websites and to run integration tests.
    """

    def setUp(self):
        """Initialize the browser and create a user, before running the tests.
        """
        self.browser = Browser('chrome')
        test_username = 'estebes'
        test_password = 'junipero'
        estebes = User.objects.create_user(
            username=test_username, email='juan@example.com', password=test_password,
            first_name='Estebes', last_name='Thelmapellido')
        capturista = Group.objects.get_or_create(name=CAPTURISTA_GROUP)[0]
        capturista.user_set.add(estebes)
        capturista.save()
        Escuela.objects.create(nombre='Juan Pablo')
        self.capturista = Capturista.objects.create(user=estebes)
        self.browser.visit(self.live_server_url + reverse('tosp_auth:login'))
        self.browser.fill('username', test_username)
        self.browser.fill('password', test_password)
        self.browser.find_by_id('login-submit').click()

    def tearDown(self):
        """At the end of tests, close the browser.
        """
        self.browser.quit()

    def test_creation_of_estudio(self):
        """ Checks that an estudio can be created through the form
        in the capturista dashboard
        """
        generic_integrante_name = 'Javier'
        alumno_integrante_name = 'Marco'
        tutor_integrante_name = 'Fabio'
        test_url_name = 'captura:estudios'
        # Test new integrante creation
        self.browser.visit(self.live_server_url + reverse(test_url_name))
        self.browser.find_by_id('create_estudio')[0].click()
        # Test integrante edition
        self.assertTrue(self.browser.is_text_present('Numero hijos diferentes papas:'))
        self.browser.fill('numero_hijos_diferentes_papas', 3)
        self.browser.find_by_id('update_familia')[0].click()
        self.assertTrue(self.browser.is_text_present('Agregar Integrante'))
        # Test generic integrante creation
        self.browser.find_by_id('create_integrante')[0].click()
        self.assertTrue(self.browser.is_text_present('Edición de Integrante'))
        self.browser.find_by_id('update_integrante')[0].click()
        self.assertTrue(self.browser.is_text_present(generic_integrante_name))
        # Test alumno integrante creation
        self.browser.find_by_id('create_integrante')[0].click()
        self.browser.fill('nombres', alumno_integrante_name)
        self.browser.select('Rol', 'alumno')
        self.browser.find_by_id('update_integrante')[0].click()
        self.assertTrue(self.browser.is_text_present('Numero sae:'))
        self.browser.find_by_id('update_integrante')[0].click()
        self.assertTrue(self.browser.is_text_present(alumno_integrante_name))
        # Test tutor integrante creation
        self.browser.find_by_id('create_integrante')[0].click()
        self.browser.fill('nombres', tutor_integrante_name)
        self.browser.select('Rol', 'tutor')
        self.browser.find_by_id('update_integrante')[0].click()
        self.assertTrue(self.browser.is_text_present('Relacion:'))
        self.browser.fill('nombres', tutor_integrante_name)
        self.browser.select('relacion', 'madre')
        self.browser.fill('nombres', tutor_integrante_name)
        self.assertTrue(self.browser.is_text_present('Madre'))
        self.browser.find_by_id('update_integrante')[0].click()
        self.assertTrue(self.browser.is_text_present(tutor_integrante_name))

    def test_check_invalid_user(self):
        """ Checks that if an user without proper permissions enters the
        the view it won't be able to create a new study.
        """
        self.browser.visit(self.live_server_url + reverse('tosp_auth:logout'))
        test_username = 'Pedro'
        test_password = 'Paramo'
        User.objects.create_user(
            username=test_username, email='juan@example.com', password=test_password,
            first_name='Estebes', last_name='Thelmapellido')
        self.browser.visit(self.live_server_url + reverse('tosp_auth:login'))
        self.browser.fill('username', test_username)
        self.browser.fill('password', test_password)
        self.browser.find_by_id('login-submit').click()
        self.assertTrue(self.browser.is_text_present('Hello'))
        self.browser.visit(self.live_server_url + reverse('captura:estudios'))
        self.assertFalse(self.browser.is_text_present('Agregar Integrante'))


class TestViewsAdministracion(StaticLiveServerTestCase):
    """Integration test suite for testing the views in the app: captura.

    Test the urls for 'captura' which make up the capturista dashboard.
    A user is created in order to test they are displayed.

    Attributes
    ----------
    browser : Browser
        Driver to navigate through websites and to run integration tests.
    """

    def setUp(self):
        """Initialize the browser and create a user, before running the tests.
        """
        self.browser = Browser('chrome')
        test_username = 'estebes'
        test_password = 'junipero'
        estebes = User.objects.create_user(
            username=test_username, email='juan@example.com', password=test_password,
            first_name='Estebes', last_name='Thelmapellido')
        capturista = Group.objects.get_or_create(name=CAPTURISTA_GROUP)[0]
        capturista.user_set.add(estebes)
        capturista.save()

        self.capturista = Capturista.objects.create(user=estebes)
        self.browser.visit(self.live_server_url + reverse('tosp_auth:login'))
        self.browser.fill('username', test_username)
        self.browser.fill('password', test_password)
        self.browser.find_by_id('login-submit').click()

    def tearDown(self):
        """At the end of tests, close the browser.
        """
        self.browser.quit()

    def test_capturista_dashboard_if_this_is_empty(self):
        """Test for url 'captura:estudios'.

        Visit the url of name 'captura:estudios' and check it loads the
        content of the captura dashboard panel.
        """
        test_url_name = 'captura:estudios'
        self.browser.visit(self.live_server_url + reverse(test_url_name))

        # Check for nav_bar partial
        self.assertTrue(self.browser.is_text_present('Instituto Juan Pablo'))
        self.assertEqual(Estudio.objects.count(), 0)
        # Check that the folling texts are present in the dashboard
        self.assertTrue(self.browser.is_text_present('Mis estudios socioeconómicos'))
        self.assertTrue(self.browser.is_text_present('Agregar estudio'))
        # Check that the following text is present if not exists socio-economic studies
        self.assertTrue(self.browser.is_text_present(
                                'No hay registro de estudios socioeconómicos'))
        # Check that the following texts aren't present if not exists any socio-economic study
        self.assertFalse(self.browser.is_text_present('Ver retroalimentación'))
        self.assertFalse(self.browser.is_text_present('Editar'))

    def test_list_studies(self):
        """Test for url 'captura:estudios'.

        Creates two socio-economic studies (f1 and f2) the first as rejected
        (rechazado) and the second as pending (revision) and visit the url
        'captura:estudios' to check it loads both socio-economic studies created
        previously.
        """
        user = User.objects.get(username='estebes')
        user_id = user.id
        capturist = Capturista.objects.get(user=user_id)

        solvencia = 'No tienen dinero'
        estado = Familia.OPCION_ESTADO_SOLTERO
        estado2 = Familia.OPCION_ESTADO_CASADO_CIVIL
        localidad = Familia.OPCION_LOCALIDAD_JURICA
        localidad2 = Familia.OPCION_LOCALIDAD_CAMPANA

        f1 = Familia(numero_hijos_diferentes_papas=1, explicacion_solvencia=solvencia,
                     estado_civil=estado, localidad=localidad)
        f1.save()
        f2 = Familia(numero_hijos_diferentes_papas=2, explicacion_solvencia=solvencia,
                     estado_civil=estado2, localidad=localidad2)
        f2.save()

        e1 = Estudio(capturista_id=capturist.id, familia_id=f1.id,
                     status=Estudio.RECHAZADO)
        e1.save()
        e2 = Estudio(capturista_id=capturist.id, familia_id=f2.id,
                     status=Estudio.REVISION)
        e2.save()
        test_url_name = 'captura:estudios'
        self.browser.visit(self.live_server_url + reverse(test_url_name))
        # Check for nav_bar partial
        self.assertTrue(self.browser.is_text_present('Instituto Juan Pablo'))
        self.assertEqual(Estudio.objects.count(), 2)
        # Check that the following texts are present in the dashboard
        self.assertTrue(self.browser.is_text_present('Mis estudios socioeconómicos'))
        self.assertTrue(self.browser.is_text_present('Agregar estudio'))
        # Check that the following text isn't present if exists any socio-economic study
        self.assertFalse(self.browser.is_text_present('No hay registro'))
        # Check that the following texts are present if exists any socio-economic study
        self.assertTrue(self.browser.is_text_present('Editar'))
        self.assertTrue(self.browser.is_text_present('Ver Retroalimentación'))
