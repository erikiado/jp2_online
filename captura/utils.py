from estudios_socioeconomicos.models import Subseccion, Pregunta, Estudio
from estudios_socioeconomicos.models import OpcionRespuesta, Respuesta, Seccion
from estudios_socioeconomicos.forms import RespuestaForm

from perfiles_usuario.utils import is_capturista, is_administrador
"""
    Mapping of next and previous section to fill in study.
"""

SECTIONS_FLOW = {
    1: {'next': 2, 'previous': False},
    2: {'next': 3, 'previous': 1},
    3: {'next': 4, 'previous': 2},
    4: {'next': 5, 'previous': 3},
    5: {'next': 6, 'previous': 4},
    6: {'next': 7, 'previous': 5},
    7: {'next': False, 'previous': 6}}


def user_can_modify_study(user, estudio):
    """ Checks whether a user can modify a given study. A capturista
        user can only modify studies that are in borrador or rechazado
        status, at the same time. A administrador can only modify studies
        that are not in these status.

        Returns
        -------
            True if user can modify.

            False if user can not modify.
    """
    if is_capturista(user):
        if estudio.status == Estudio.BORRADOR:
            return True
        if estudio.status == Estudio.RECHAZADO:
            return True

    if is_administrador(user):
        if estudio.status != Estudio.BORRADOR and estudio.status != Estudio.RECHAZADO:
            return True

    return False


def get_study_info(estudio):
    """ Returns all structured information for a complete study.

        We query each section and get all information for that
        section using get_study_info_for_section.
    """
    secciones = Seccion.objects.all().values()

    for seccion in secciones:
        seccion_instance = Seccion.objects.get(pk=seccion['id'])
        subsecciones, respuestas = get_study_info_for_section(estudio, seccion_instance)
        seccion['subsecciones'] = subsecciones

    return secciones


def get_study_info_for_section(estudio, seccion):

    """ Return structured information for a study's section.

        For each section, we query all subsections that branch out and
        for each subsection we query all the questions that branch out.
        After that, for each question we query all the answers that have
        been created (When a study is generated a trigger automatically
        generates an empty answer for each question).  Finally we create
        a form for each answer and send the complete object back to view
        for rendering.

        Notes
        ----------
        .values() is being used to append new values into the queried data.
        We need to create a nested object that already has the information
        ordered based on the stored indexes. There might me a way to nest
        objects using django queries, but we also need to create a form for
        each answer and nest it to its related question.

        Returns
        ----------
        Tuple containing the object that will help rendering and all answers.

        The first object in the tuple is all the nested information for this
        section. The second object is just the answers. This is usefull so
        that in post we can just iterate the answers and get the form back
        using the prefixes.
    """
    subsecciones = Subseccion.objects.filter(seccion=seccion).order_by('numero').values()
    answers_objects = list()

    for subseccion in subsecciones:
        preguntas = Pregunta.objects.filter(subseccion=subseccion['id']).order_by('orden').values()

        for pregunta in preguntas:

            respuestas = Respuesta.objects.filter(
                pregunta=pregunta['id'],
                estudio=estudio).values()

            opciones_respuesta = OpcionRespuesta.objects.filter(pregunta=pregunta['id'])

            for respuesta in respuestas:
                respuesta_obj = Respuesta.objects.get(pk=respuesta['id'])

                answers_objects.append(respuesta_obj)

                respuesta['form'] = RespuestaForm(
                    instance=respuesta_obj,  # Prefix allows binding form back to object on POST.
                    prefix='respuesta-{}'.format(respuesta_obj.id),
                    pregunta=pregunta['id'])  # Question for queryset involving the Options.

            pregunta['respuestas'] = respuestas
            pregunta['opciones_respuesta'] = opciones_respuesta

        subseccion['preguntas'] = preguntas

    return (subsecciones, answers_objects)
