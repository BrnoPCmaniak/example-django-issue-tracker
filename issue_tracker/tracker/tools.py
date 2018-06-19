from functools import reduce
from typing import Callable, Dict, List, Optional, Union

from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models import Q, QuerySet
from django.forms import forms
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.views import View
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import FormMixin


class NoDefaultProvided(object):
    """Exception for *attr functions."""

    pass


def getattrd(obj, name: str, default=NoDefaultProvided):
    """Better version of getattr().

    Same as getattr(), but allows dot notation lookup.
    Discussed in:
    http://stackoverflow.com/questions/11975781
    """
    try:
        return reduce(getattr, name.split("."), obj)
    except (AttributeError,):
        if default != NoDefaultProvided:
            return default
        raise


def getattrd_last_but_one(obj, name: str, default=NoDefaultProvided):
    """Same as getattrd(), but leaves out last ".foo" part.

    e.g. name="branch.apple.color" obj = tree -> tree.branch.apple
    """
    try:
        return reduce(getattr, name.split(".")[:-1], obj)
    except (AttributeError,):
        if default != NoDefaultProvided:
            return default
        raise


def setattrd(obj, name: str, value):
    """Better version of setattr().

    Same as setattr(), but allows dot notation lookup.
    """
    try:
        name = name.split(".")
        return setattr(reduce(getattr, name[:-1], obj), name[-1], value)
    except AttributeError:
        raise


def http_response_code(code: int, message: str = None) -> HttpResponse:
    """Return HttpResponse with error code, can also include message."""
    if message is not None:
        tmp = HttpResponse(message, content_type="application/javascript")
    else:
        tmp = HttpResponse(content_type="application/javascript")
    tmp.status_code = code
    return tmp


def merge_queries(queries: List[Q], func: Callable[[Q, Q], Q]) -> Q:
    """Merge list of Q into single Q."""
    fin_query = queries.pop()
    for q in queries:
        fin_query = func(fin_query, q)

    return fin_query


def or_merge_queries(queries: List[Q]) -> Q:
    """Or merge list of Q into single Q."""
    return merge_queries(queries, lambda fin, q: fin | q)


def and_merge_queries(queries: List[Q]) -> Q:
    """And merge list of Q into single Q."""
    return merge_queries(queries, lambda fin, q: fin & q)


class BootstrapEditableView(FormMixin, SingleObjectMixin, View):
    """View for working with Bootstrap-editable.

    * Basic:
      e.g. {<POST["name"]>: (<form_field>, <model_field>)}

    * Optionaly you can specify model which will be saved:
      e.g. {<POST["name"]>: (<form_field>, <model_field>, <model_to_save>)}

    * Or if POST name and form_field and model_field is same you can use it like this:
      e.g. {<POST["name"]>: None} or [<POST["name"]>]
      In this case model_to_save is considered as not present.
    """

    fields: Union[dict, list, None] = None

    def get_fields(self) -> Union[dict, list, None]:
        """Get self.fields."""
        return self.fields

    def test_func(self) -> bool:
        """Here you can check user. Return False to HttpResponseForbidden."""
        return True

    def get_object(self, POST: dict) -> models.Model:
        """Return object."""
        return super(BootstrapEditableView, self).get_object()

    def save_object(self, model: models.Model, model_to_save: models.Model, model_field: str, data: dict):
        """Save the object.

        :param model: model on which the data will be saved
        :param model_to_save: model on which .save() will be called.
        :param model_field: Field on model to which data will be set
        :param data: data to be saved
        """
        setattrd(model, model_field, data)
        model_to_save.save()

    def get_form_instance(self, form_class: forms.Form, post: dict) -> forms.Form:
        """Get from form class form object.

        :param form_class: Form class
        :param post: POST data
        :return: Form instance
        """
        return form_class(post)

    def post(self, request, *args, **kwargs) -> HttpResponse:
        """Work with POST from Bootstrap-editable."""

        self.object = self.get_object(request.POST)
        if not self.test_func():
            return HttpResponseForbidden()
        post = request.POST.copy()
        fields = self.get_fields()

        found = False
        found_key = None
        for key in fields:
            if request.POST["name"] == key:
                found_key = key
                found = True

        if not found:
            return http_response_code(400)

        if type(fields) == dict:
            if fields[found_key] is None:
                found_form_field = found_key
                found_model_field = found_key
            else:
                found_form_field = fields[found_key][0]
                found_model_field = fields[found_key][1]
            if len(fields[found_key]) == 3:
                found_model_to_save = getattrd(self.object, fields[found_key][2])
            else:
                found_model_to_save = getattrd_last_but_one(self.object, found_model_field)
        elif type(fields) == list:
            found_form_field = found_key
            found_model_field = found_key
            found_model_to_save = getattrd_last_but_one(self.object, found_model_field)
        else:
            raise AttributeError("BootstrapEditableView: fields attribute has wrong format.")
        # move POST["value"] into POST["form_field"] for form cleaning
        post[found_form_field] = request.POST["value"]

        form_class = self.get_form_class()
        form_instance = self.get_form_instance(form_class, post)
        form_field = form_instance[found_form_field]

        if form_field.errors:
            return http_response_code(406, "Error: " + form_field.errors)
        else:
            self.save_object(self.object, found_model_to_save, found_model_field,
                             form_instance.cleaned_data[found_form_field])
            return http_response_code(200)


class AjaxBootstrapSelectView(View):
    """Return JSON data from search for Ajax-Bootstrap-Select."""

    # names to be compatible with SingleObjectMixin
    search_model = None
    search_queryset = None
    field = "name"
    enable_empty_requests = False

    def get_query(self) -> Q:
        """Return query used for looking for object."""
        return Q(**{self.get_field() + "__icontains": self.request.POST["q"]})

    def get_objects(self, queryset=None) -> QuerySet:
        """Filter given queryset and returns list of objects."""
        if queryset is None:
            queryset = self.get_search_queryset()

        try:
            if self.request.POST["q"].strip() is "":
                return self.get_objects_on_empty(queryset)
        except KeyError:
            return self.get_objects_on_empty(queryset)

        return queryset.filter(self.get_query())

    def get_objects_on_empty(self, queryset=None) -> Union[QuerySet, list]:
        """Called when POST["q"].strip() is ""."""
        if not self.enable_empty_requests:
            return []
        else:
            return queryset

    def get_field(self) -> Optional[str]:
        """Return self.field."""
        return self.field

    def get_search_queryset(self) -> QuerySet:
        """Get QuerySet for searching.

        Return the `QuerySet` that will be used to look up the object.
        Note that this method is called by the default implementation of
        `get_object` and may not be called if `get_object` is overridden.
        """
        if self.search_queryset is None:
            if self.search_model:
                return self.search_model._default_manager.all()
            else:
                raise ImproperlyConfigured(
                    "%(cls)s is missing a QuerySet. Define "
                    "%(cls)s.search_model, %(cls)s.search_queryset, or override "
                    "%(cls)s.get_search_queryset()." % {
                        'cls': self.__class__.__name__
                    }
                )
        return self.search_queryset.all()

    def prepare_json_list(self, obj_list) -> List[Dict[str, str]]:
        """Create list of dicts for json."""
        return [{"ID": obj.pk, "Name": getattr(obj, self.get_field())}
                for obj in obj_list]

    def post(self, request, *args, **kwargs) -> JsonResponse:
        """Handle POST requests."""
        objects = self.get_objects()
        json_list = self.prepare_json_list(objects)
        return JsonResponse(json_list, safe=False)
