import os
from django.shortcuts import get_object_or_404
from rest_framework import renderers, status
from django.http import HttpResponse, StreamingHttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.db.models import Q
from rest_framework import routers, viewsets, views, mixins, permissions
from rest_framework.response import Response

from rest_framework.decorators import api_view, detail_route, list_route, permission_classes, renderer_classes, parser_classes
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from wsgiref.util import FileWrapper

from .models import Case
from .view_helpers import *
from .serializers import *
from .permissions import IsCaseUser
from .filters import *

from resources import scp_get

class JSONResponse(HttpResponse):
    """
    An HttpResponse that renders its content into JSON.
    """
    def __init__(self, data, **kwargs):
        content = renderers.JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)


class CaseViewSet(viewsets.GenericViewSet):
    """
    # Browse all cases
    """
    permission_classes = (IsCaseUser,)
    serializer_class = CaseSerializer
    http_method_names = ['get']
    queryset = Case.objects.all()
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filter_class = CaseFilter
    renderer_classes = (renderers.BrowsableAPIRenderer, renderers.JSONRenderer)
    lookup_field='jurisdiction'

    def case_list(self, *args, **kwargs):
        query = Q()
        kwargs = self.kwargs

        if len(self.request.query_params.items()):
            kwargs = format_date_queries(self.request.query_params, kwargs)

        if len(kwargs.items()):
            query = map(make_query, kwargs.items())
            query = merge_filters(query, 'AND')

        cases = self.queryset.filter(query)
        page = self.paginate_queryset(cases)
        if page is not None:
            serializer = self.get_serializer(page, many=True)

            if not self.request.query_params.get('type') == 'download':
                return self.get_paginated_response(serializer.data)
            else:
                has_permissions = self.check_case_permissions(cases)
                if has_permissions:
                    try:
                        zip_file_name = self.download_cases(cases)
                        response = StreamingHttpResponse(FileWrapper(open(zip_file_name, 'rb')), content_type='application/zip')
                        response['Content-Length'] = os.path.getsize(zip_file_name)
                        response['Content-Disposition'] = 'attachment; filename="%s"' % zip_file_name
                        return response
                    except Exception as e:
                        Exception("Download file error: %s" % e)
                else:
                    raise Exception("You have reached your limit of allowed cases")

    def check_case_permissions(self, cases):
        return self.request.user.case_allowance >= len(cases)

    def download_cases(self, cases):
        case_ids = cases.values_list('caseid', flat=True)
        try:
            cases = scp_get(self.request.user.id, case_ids)
            self.request.user.case_allowance -= len(case_ids)
            self.request.user.save()
            return cases
        except Exception as e:
            raise Exception("Download cases error %s" % e)

@api_view(http_method_names=['GET'])
@permission_classes((IsCaseUser,))
@renderer_classes((renderers.BrowsableAPIRenderer,renderers.JSONRenderer,))
def list_jurisdictions(request):
    """
    GET a list of all jurisdictions available
    """
    jurisdictions = Case.objects.values_list('jurisdiction', flat=True).distinct().order_by('jurisdiction')
    return Response(jurisdictions)

@api_view(http_method_names=['GET'])
@permission_classes((IsCaseUser,))
@renderer_classes((renderers.BrowsableAPIRenderer,renderers.JSONRenderer,))
def list_volumes(request, *args, **kwargs):
    """
    GET a list of all volumes in the specified jurisdiction
    """
    jurisdiction = kwargs.get('jurisdiction')
    reporter = kwargs.get('reporter')
    volumes = Case.objects.filter(jurisdiction__iexact=jurisdiction, reporter__iexact=reporter).values_list('volume', flat=True).distinct().order_by('volume')
    return Response(volumes)

@api_view(http_method_names=['GET'])
@permission_classes((IsCaseUser,))
@renderer_classes((renderers.BrowsableAPIRenderer,renderers.JSONRenderer,))
def list_reporters(request, *args, **kwargs):
    """
    GET a list of all reporters in the specified jurisdiction
    """
    jurisdiction = kwargs.get('jurisdiction')
    reporters = Case.objects.filter(jurisdiction__iexact=jurisdiction).values_list('reporter', flat=True).distinct().order_by('reporter')
    return Response(reporters)

@api_view(http_method_names=['GET'])
@permission_classes((IsCaseUser,))
@renderer_classes((renderers.BrowsableAPIRenderer,renderers.JSONRenderer,))
def get_case(request, *args, **kwargs):
    jurisdiction = kwargs.get('jurisdiction')
    reporter = kwargs.get('reporter')
    firstpage = kwargs.get('firstpage')
    name_abbreviation = kwargs.get('name_abbreviation')
    case = Case.objects.filter(
            jurisdiction__iexact=jurisdiction,
            reporter__iexact=reporter,
            firstpage=firstpage,
            name_abbreviation__icontains=name_abbreviation,
        )

    serializer = CaseSerializer(case)
    return Response(serializer.data)

@api_view(http_method_names=['GET'])
@permission_classes((IsCaseUser,))
@renderer_classes((renderers.BrowsableAPIRenderer,renderers.JSONRenderer,))
def get_case_by_citation(request, *args, **kwargs):
    """
    GET a single case using its canonical citation
    """
    citation = kwargs.get('citation')
    case = Case.objects.get(citation__iexact=citation,)
    redirect_url = "%s/cases/%s" % (settings.BASE_URL, format_url_from_case(case))
    return HttpResponseRedirect(redirect_url)
