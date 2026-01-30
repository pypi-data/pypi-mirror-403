"""
Csv import module related views

1- Download the csv
2- Generate an association form
3- Import datas
4- Return the resume
"""

import csv
import io
import json
import logging
import os
from collections import OrderedDict

from deform import Button
from pyramid.httpexceptions import HTTPBadRequest, HTTPForbidden, HTTPFound

from caerp.celery.models import CsvImportJob
from caerp.celery.tasks.csv_import import async_import_datas, get_csv_import_associator
from caerp.celery.tasks.utils import check_alive
from caerp.consts.permissions import PERMISSIONS
from caerp.forms.csv_import import get_association_schema, get_csv_file_upload_schema
from caerp.models.base import DBSESSION
from caerp.models.config import Config
from caerp.resources import fileupload_js
from caerp.utils.csv import get_csv_reader
from caerp.utils.files import count_lines_in_file
from caerp.views import BaseFormView

log = logging.getLogger(__name__)


# The key we use to store informations about the current imported csv file in
# the user's sessioSESSION_KEY = "csv_import"
SESSION_KEY = "csv_import"

IMPORT_INFO = "Vous vous apprêtez à importer (ou mettre à jour) {count} \
entrée(s)."


class CsvFileUploadView(BaseFormView):
    """
    First step view for csv file importation

    HEre we get :
        1- a csv file
        2- a model type

    2 is carried to the next step view through the request's GET params
    """

    title = "Import des dossiers, étape 1 : chargement d'un fichier csv"
    help_message = "L’import de données permet, depuis un fichier de type csv, \
d'insérer de nouvelle données dans enDI, ou de mettre à jour \
des données existantes. <br /><br />\
Pour importer des données, vous devez disposer d'un \
fichier : <br /> \
            <ul> \
                <li>Enregistré au format csv;</li> \
                <li>Enregistré au format utf-8.</li> \
            </ul> \
Une fois le fichier chargé, vous allez être redirigé vers un formulaire pour \
associer les champs de votre fichier avec les données d'enDI."
    _schema = None
    add_template_vars = ("title", "help_message")
    default_model_type = "userdatas"
    model_types = ("userdatas",)

    def get_bind_data(self):
        return dict(
            request=self.request,
            model_types=self.model_types,
        )

    # Schema is here a property since we need to build it dynamically regarding
    # the current request (the same should have been built using the after_bind
    # method ?)
    @property
    def schema(self):
        """
        The getter for our schema property
        """
        if self._schema is None:
            self._schema = get_csv_file_upload_schema(self.request)
        return self._schema

    @schema.setter
    def schema(self, value):
        """
        A setter for the schema property
        The BaseClass in pyramid_deform gets and sets the schema attribute that
        is here transformed as a property
        """
        self._schema = value

    def before(self, form):
        """
        Ensure the fileupload js stuff is loaded
        """
        fileupload_js.need()
        form.set_appstruct({"model_type": self.default_model_type})

    def submit_success(self, appstruct):
        """
        Launched on successfull file upload
        """
        log.debug("A csv file has been uploaded")
        uid = appstruct["csv_file"]["uid"]
        association = appstruct.get("association")
        _query = dict(
            uid=uid,
            model_type=appstruct["model_type"],
        )
        if association:
            _query["association"] = association
        return HTTPFound(self.get_next_step_route(_query))

    def get_next_step_route(self, args):
        """
        Returns the path to the next step of the import process (should be
        overriden by subclassing views)
        """
        return self.request.route_path("import_step2", _query=args)


def get_current_uploaded_filepath(request, file_uid: str):
    """
    Return the csv filepath currently stored in the user's session

    :returns: a filepath
    :raises KeyError: if no file datas are stored in the current session
    """
    tempdir = request.registry.settings["pyramid_deform.tempdir"]
    file_informations = request.session["substanced.tempstore"][file_uid]
    filename = file_informations["randid"]
    filepath = os.path.join(tempdir, filename)
    return filepath


def get_file_buffer(filepath: str) -> io.BytesIO:
    # Related to pyramid_deform's way to store temporary datas on disk
    with open(filepath, "rb") as fbuf:
        data = io.BytesIO(fbuf.read())
    return data


def get_current_csv_reader(file_buffer: io.BytesIO) -> csv.DictReader:
    """
    Return the csv file currently stored in the user's session

    :returns: a csv dictreader object with the actual csv datas
    :raises KeyError: if no file datas are stored in the current session
    """
    reader = get_csv_reader(file_buffer)
    return reader


def get_preferences_obj():
    """
    Return the config object used to store prefereces
    """
    return Config.get("csv_import") or Config(name="csv_import")


def load_preferences(obj):
    """
    Load preferences from the associated config object using json

    :param obj obj: The config object used to store preferences
    """
    val = obj.value
    if val is None:
        return {}
    else:
        return json.loads(val)


def get_preference(name):
    """
    Return a stored association dict

    :param str name: the name this association was stored under
    """
    config_obj = get_preferences_obj()
    preferences = load_preferences(config_obj)
    return preferences.get(name, {})


def record_preference(request, name, association_dict):
    """
    Record a field association in the request config
    """
    config_obj = get_preferences_obj()
    associations = load_preferences(config_obj)
    associations[name] = association_dict

    if config_obj.value is None:
        # It's a new one
        config_obj.value = json.dumps(associations)
        DBSESSION().add(config_obj)
    else:
        # We edit it
        config_obj.value = json.dumps(associations)
        DBSESSION().merge(config_obj)
    return associations


class ConfigFieldAssociationView(BaseFormView):
    """
    View for field association configuration
    Dynamically build a form regarding the previously stored csv datas

    :param request: the pyramid request object
    """

    help_message = (
        "Vous vous apprêtez à importer des données depuis le "
        "fichier fourni à l'étape précédente. <br /> "
        "À cette étape, vous allez : "
        "<ul>"
        "<li>Choisir la méthode d'import de données (nouvelle entrées, "
        "mise à jour de données)</li>"
        "<li>Sélectionner le champ de votre fichier qui sera utilisé pour retrouver "
        "l'entrée correspondante dans enDI (si la méthode choisir implique une mise "
        "à jour de données)</li>"
        "<li>Associer les colonnes de votre fichier avec les données correspondantes "
        "dans enDI (NB : vous n'êtes pas obligé d'importer toutes les colonnes de "
        "votre fichier)</li>"
    )
    add_template_vars = (
        "title",
        "info_message",
        "help_message",
    )
    title = "Import de données, étape 2 : associer les champs"
    _schema = None
    buttons = (
        Button(
            "submit",
            title="Lancer l'import",
        ),
        Button(
            "cancel",
            title="Annuler l'import",
        ),
    )
    model_types = CsvFileUploadView.model_types

    def __init__(self, context, request):
        BaseFormView.__init__(self, request)
        self.model_type = self.request.GET["model_type"]

        if self.model_type not in self.model_types:
            raise HTTPForbidden()

        # We first count the number of elements in the file
        self.filepath = get_current_uploaded_filepath(
            self.request, self.request.GET["uid"]
        )
        self.file_buffer = get_file_buffer(self.filepath)

        # We build a field - model attr associator
        self.associator = get_csv_import_associator(self.model_type)
        self.csv_reader = get_current_csv_reader(self.file_buffer)
        if not self.csv_reader.fieldnames:
            raise HTTPBadRequest("Le fichier fourni est vide")
        self.headers = [header for header in self.csv_reader.fieldnames if header]

    # Schema is here a property since we need to build it dynamically regarding
    # the current request (the same should have been built using the after_bind
    # method ?)
    @property
    def schema(self):
        """
        The getter for our schema property
        """
        if self._schema is None:
            self._schema = get_association_schema(self.request)
        return self._schema

    @schema.setter
    def schema(self, value):
        """
        A setter for the schema property
        The BaseClass in pyramid_deform gets and sets the schema attribute that
        is here transformed as a property
        """
        self._schema = value

    def get_bind_data(self):
        """
        Returns the datas used whend binding the schema for field association
        """
        return dict(associator=self.associator, csv_headers=self.headers)

    def before(self, form):
        """
        Initialize the datas used in the view process and populate the form
        """
        if "association" in self.request.GET:
            preference_name = self.request.GET["association"]
            preference = get_preference(preference_name)
            association_dict = self.associator.guess_association_dict(
                self.headers,
                preference,
            )
        else:
            # We try to guess the association dict to initialize the form
            association_dict = self.associator.guess_association_dict(self.headers)

        log.info("We initialize the association form")
        log.info(association_dict)
        log.info(self.headers)
        appstruct = {"entries": []}
        for key in ("Identifiant", "ID Gestion sociale"):
            if key in self.headers:
                appstruct["id_key"] = key

        # We initialize the form
        for csv_key, model_attribute in list(association_dict.items()):
            appstruct["entries"].append(
                {"csv_field": csv_key, "model_attribute": model_attribute}
            )

        form.set_appstruct(appstruct)
        return form

    @property
    def info_message(self):
        num_lines = max(0, count_lines_in_file(self.file_buffer) - 1)
        return IMPORT_INFO.format(count=num_lines)

    def get_recording_job(self):
        """
        Initialize a job for importation recording
        """
        # We initialize a job record in the database
        job = CsvImportJob()
        job.set_owner(self.request.identity.login.login)
        DBSESSION().add(job)
        DBSESSION().flush()
        return job

    def build_association_dict(self, importation_datas):
        """
        Build the association dict that describes matching between csv and model
        fields
        """
        # On génère le dictionnaire d'association qui va être utilisé pour
        # l'import
        association_dict = OrderedDict()
        for entry in importation_datas["entries"]:
            if "model_attribute" in entry:
                association_dict[entry["csv_field"]] = entry["model_attribute"]
        return association_dict

    def get_default_values(self):
        """
        Returns default values for object initialization
        Usefull for subclasses to force some attribute values (like company_id)
        """
        return {}

    def submit_success(self, importation_datas):
        """
        Submission has been called and datas have been validated

        :param dict importation_datas: The datas we want to import
        """
        service_ok, msg = check_alive()
        if not service_ok:
            self.request.session.flash(msg, "error")
            return HTTPFound(self.get_previous_step_route())

        log.info(
            "Field association has been configured, we're going to \
import"
        )
        action = importation_datas["action"]
        csv_id_key = importation_datas["id_key"]
        force_rel_creation = importation_datas.get(
            "force_rel_creation",
            False,
        )

        association_dict = self.build_association_dict(importation_datas)

        # On enregistre le dictionnaire d'association de champs
        if importation_datas.get("record_association", False):
            name = importation_datas["record_name"]
            record_preference(self.request, name, association_dict)

        # On traduit la "valeur primaire" configurée par l'utilisateur en
        # attribut de modèle (si il y en a une de configurée)
        # Colonne du fichier csv -> attribut du modèle à importer
        id_key = association_dict.get(csv_id_key, csv_id_key)

        job = self.get_recording_job()

        celery_job = async_import_datas.delay(
            self.model_type,
            job.id,
            association_dict,
            self.filepath,
            id_key,
            action,
            force_rel_creation,
            self.get_default_values(),
        )

        log.info(
            " * The Celery Task {0} has been delayed, its result "
            "should be retrieved from the CsvImportJob : {1}".format(
                celery_job.id,
                job.id,
            )
        )
        return HTTPFound(self.request.route_path("job", id=job.id))

    def get_previous_step_route(self):
        """
        Return the path to the previous step of our importation process
        Should be overriden by subclassing views
        """
        return self.request.route_path("import_step1")

    def cancel_success(self, appstruct):
        return HTTPFound(self.get_previous_step_route())

    cancel_failure = cancel_success


def includeme(config):
    """
    Configure views
    """
    config.add_route("import_step1", "/import/1/")
    config.add_route("import_step2", "/import/2/")
    config.add_view(
        CsvFileUploadView,
        route_name="import_step1",
        permission=PERMISSIONS["global.view_userdata_details"],
        renderer="base/formpage.mako",
    )
    config.add_view(
        ConfigFieldAssociationView,
        route_name="import_step2",
        permission=PERMISSIONS["global.view_userdata_details"],
        renderer="base/formpage.mako",
    )
