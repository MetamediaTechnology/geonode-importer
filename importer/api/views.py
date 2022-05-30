#########################################################################
#
# Copyright (C) 2021 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################
import logging

from django.utils.translation import ugettext as _
from dynamic_rest.filters import DynamicFilterBackend, DynamicSortingFilter
from dynamic_rest.viewsets import DynamicModelViewSet
from geonode.base.api.filters import DynamicSearchFilter
from geonode.base.api.pagination import GeoNodeApiPagination
from geonode.base.api.permissions import IsOwnerOrReadOnly
from geonode.storage.manager import StorageManager
from geonode.upload.api.permissions import UploadPermissionsFilter
from geonode.upload.api.views import UploadViewSet
from geonode.upload.models import Upload
from importer.api.exception import ImportException
from importer.api.serializer import ImporterSerializer
from importer.views import start_dataset_import
from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from rest_framework.authentication import (BasicAuthentication,
                                           SessionAuthentication)
from rest_framework.parsers import FileUploadParser, MultiPartParser
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class ImporterViewSet(DynamicModelViewSet):
    """
    API endpoint that allows uploads to be viewed or edited.
    """
    parser_class = [FileUploadParser, MultiPartParser]

    authentication_classes = [BasicAuthentication, SessionAuthentication, OAuth2Authentication]
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [
        DynamicFilterBackend, DynamicSortingFilter, DynamicSearchFilter,
        UploadPermissionsFilter
    ]
    queryset = Upload.objects.all()
    serializer_class = ImporterSerializer
    pagination_class = GeoNodeApiPagination
    http_method_names = ['get', 'post']

    def create(self, request, *args, **kwargs):
        '''
        Main function called by the new import flow.
        It received the file via the front end
        if is a gpkg (in future it will support all the vector file)
        the new import flow is follow, else the normal upload api is used.
        It clone on the local repo the file that the user want to upload
        '''
        _file = request.FILES.get('base_file') or request.data.get('base_file')
        if _file and _file.name.endswith('gpkg'):
            #go through the new import flow
            data = self.serializer_class(data=request.data)
            # data validation
            data.is_valid(raise_exception=True)
            # cloning data into a local folder
            storage_manager = StorageManager(remote_files={"base_file": request.data.get('base_file')})
            storage_manager.clone_remote_files()
            # get filepath
            files = storage_manager.get_retrieved_paths()
            try:
                start_dataset_import.apply_async(
                    (files, data.data.get("store_spatial_files"), request.user.username)
                )
                return Response(status=201)
            except Exception as e:
                # in case of any exception, is better to delete the 
                # cloned files to keep the storage under control
                storage_manager.delete_retrieved_paths(force=True)
                raise ImportException(detail=e.args[0])

        # if is a geopackage we just use the new import flow
        request.GET._mutable = True
        return UploadViewSet().upload(request)
