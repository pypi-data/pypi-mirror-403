"""
Forms elements related to csv import


1- Upload a csv file and choose the type of datas you want to import

2- Associate the datas with the model's columns



"""
import json
import logging

import colander
import deform
import deform_extensions
from deform_extensions import DisabledInput

from caerp.celery.tasks import csv_import
from caerp.consts.permissions import PERMISSIONS
from caerp.exception import MessageException
from caerp.forms.files import FileNode
from caerp.utils.csv import test_content_is_csv

IMPORTATION_TYPE_OPTIONS = (
    (
        "insert",
        "Création seulement (les nouvelles entrées seront créées, les entrées "
        "existantes ne seront pas modifiées)",
        "",
    ),
    (
        "only_update",
        "Complétion seulement (aucune nouvelle entrée ne sera créée, les champs "
        "existants seront conservés)",
        "id_key",
    ),
    (
        "only_override",
        "Mise à jour seulement (aucune nouvelle entrée ne sera créée, les champs "
        "existants seront mis à jour)",
        "id_key",
    ),
    (
        "update",
        "Création + Complétion (les nouvelles entrées seront créées, les champs "
        "existants seront conservés)",
        "id_key",
    ),
    (
        "override",
        "Création + Mise à jour (les nouvelles entrées seront créées, les champs "
        "existants seront mis à jour)",
        "id_key",
    ),
)


logger = logging.getLogger(__name__)


def csv_file_validator(node, value):
    """
    check the file datas are composed of csv datas
    """
    file_obj = value.get("fp")
    if file_obj:
        try:
            test_content_is_csv(file_obj)
        except MessageException as exc:
            raise colander.Invalid(node, exc.message)


@colander.deferred
def deferred_preferences(node, kw):
    request = kw["request"]
    associations = json.loads(request.config.get("csv_import", "{}"))

    options = list(zip(list(associations.keys()), list(associations.keys())))
    options.insert(0, ("", "- Sélectionner des préférences -"))
    return deform.widget.SelectWidget(values=options)


@colander.deferred
def deferred_model_type_widget(node, kw):
    model_types = kw["model_types"]

    if len(model_types) == 1:
        result = deform.widget.HiddenWidget()
    else:
        request = kw["request"]
        values = []
        for key in model_types:
            value = csv_import.MODELS_CONFIGURATION.get(key)
            if value is None:
                logger.warning(
                    "The following importation model type doesn't \
exists : {0}".format(
                        key
                    )
                )

            permission = value["permission"]
            if request.has_permission(permission, request.context):
                values.append((key, value["label"]))

        result = deform.widget.SelectWidget(values=values)

    return result


class CsvFileUploadSchema(colander.Schema):
    """
    Csv import first step schema
    """

    csv_file = FileNode(
        title="Fichier csv",
        description="Fichier csv contenant les données à importer le fichier doit être enregistré au format utf-8",
        validator=csv_file_validator,
    )
    model_type = colander.SchemaNode(
        colander.String(),
        widget=deferred_model_type_widget,
        title="Type de données",
    )
    association = colander.SchemaNode(
        colander.String(),
        widget=deferred_preferences,
        title="Type de fichiers",
        description="Permet de pré-charger automatiquement des associations \
de champs pour l'étape 2",
        missing=colander.drop,
    )


def get_csv_file_upload_schema(request):
    """
    Return an import csv file upload schema regarding the current user's rights
    """
    schema = CsvFileUploadSchema().clone()
    if not request.has_permission(PERMISSIONS["global.access_ea"], request.context):
        del schema["association"]
    return schema


@colander.deferred
def deferred_model_attribute_list_schema(node, kw):
    """
    Return the widget for field attributes selection
    """
    associator_object = kw["associator"]
    values = [("", "Ne pas importer")]
    for column in list(associator_object.get_columns().values()):
        values.append((column["name"], column["label"]))
    return deform.widget.SelectWidget(values=values)


@colander.deferred
def deferred_id_key_widget(node, kw):
    """
    Return the radio choice widget used to define which field should be used as
    id key
    """
    csv_headers = kw["csv_headers"]
    for key in "Identifiant", "ID Gestion sociale":
        if key in csv_headers:
            csv_headers.remove(key)
            csv_headers.insert(0, key)
    return deform.widget.SelectWidget(
        values=list(zip(csv_headers, csv_headers)),
    )


@colander.deferred
def deferred_seq_widget(node, kw):
    """
    Dynamically return a sequence widget with fixed length
    """
    csv_headers = kw["csv_headers"]
    return deform.widget.SequenceWidget(
        min_len=len(set(csv_headers)),
        max_len=len(set(csv_headers)),
    )


class AssociationEntry(colander.MappingSchema):
    """
    A form entry for csv field <-> model's attribute association
    """

    csv_field = colander.SchemaNode(
        colander.String(),
        title="Libellé dans le fichier Csv que vous avez déposé",
        widget=DisabledInput(),
    )
    model_attribute = colander.SchemaNode(
        colander.String(),
        title="Correspond au champ suivant dans MoOGLi ",
        widget=deferred_model_attribute_list_schema,
        missing=colander.drop,
    )


class AssociationEntries(colander.SequenceSchema):
    entry = AssociationEntry(title="")


class AssociationSchema(colander.MappingSchema):
    action = colander.SchemaNode(
        colander.String(),
        title="Type d'importation",
        description="Définit la politique d'insertion d'informations dans la \
base de données.",
        widget=deform_extensions.RadioChoiceToggleWidget(
            values=IMPORTATION_TYPE_OPTIONS
        ),
        default="only_update",
        missing="only_update",
    )
    id_key = colander.SchemaNode(
        colander.String(),
        title="Identifiant unique",
        description="Dans le cas de mise à jour de données, vous pouvez \
définir quel champ doit être utilisé pour retrouver des entrées existantes \
dans la base de données.",
        widget=deferred_id_key_widget,
        missing="id",  # par défaut on identifie grâce à l'attribut id
    )
    entries = AssociationEntries(
        widget=deferred_seq_widget, title="Association des données"
    )
    record_association = colander.SchemaNode(
        colander.Boolean(),
        title="Enregistrer ?",
        description="Voulez-vous conserver cette association de champ pour de \
futures importations ?",
    )
    record_name = colander.SchemaNode(
        colander.String(),
        title="Nom de l'enregistrement",
        description="Ce nom vous permettra de recharger cette association",
        missing=colander.drop,
    )
    force_rel_creation = colander.SchemaNode(
        colander.Boolean(),
        title="Forcer la création d'élément de configuration",
        description="Si des entrées correspondent à des champs à valeur \
multiple dont les options sont configurables depuis l'interface \
d'administration, et qu'aucun option ne correspond, une nouvelle option \
sera créée automatiquement.",
        default=False,
    )


def check_record_name(form, values):
    """
    If we record an association schema, we need the name
    """
    if values.get("record_association", False):
        if not values.get("record_name"):
            exc = colander.Invalid(form, "Vous devez saisir un nom")
            exc["record_name"] = "Ce paramètre est requis"
            raise exc


def get_association_schema(request):
    """
    Returns a form schema used to configure field association for csv import
    """
    schema = AssociationSchema(validator=check_record_name).clone()

    if not request.has_permission(PERMISSIONS["global.access_ea"], request.context):
        del schema["force_rel_creation"]
        del schema["record_association"]
        del schema["record_name"]
    return schema
