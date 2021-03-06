from django import forms


class BecaForm(forms.Form):
    """ This form is used to assign a scholarship
    to a set of students. It just has an option for
    the tabulador used, and a list of possible percentages
    of scholarship.
    """

    OPCIONES_TABULADOR = [
        (x, 'Asignar {}%'.format(x)) for x in map(lambda x: str(x), range(1, 60))
    ]

    OPCIONES_TABULADOR += [('fuera_rango', 'Fuera del rango')]

    OPCIONES_PORCENTAJE = [
        (x, x + '%') for x in map(lambda x: str(x), range(1, 101))
    ]

    tabulador = forms.ChoiceField(choices=OPCIONES_TABULADOR,
                                  required=True)

    porcentaje = forms.ChoiceField(choices=OPCIONES_PORCENTAJE,
                                   required=True)

    def __init__(self, *args, **kwargs):
        # Add the class form-control to all of the fields
        super(BecaForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'


class CartaForm(forms.Form):
    """ This form is used to fill in the slots to
    generate the scholarship letter.
    """

    grado = forms.CharField(label='Grado', required=True)
    ciclo = forms.CharField(label='Ciclo Escolar', required=True)
    compromiso = forms.CharField(label='Compromiso de la Familia', required=True)
    a_partir = forms.CharField(label='¿Desde cuándo empieza la aportación?', required=True)

    def __init__(self, *args, **kwargs):
        # Add the class form-control to all of the fields
        super(CartaForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
