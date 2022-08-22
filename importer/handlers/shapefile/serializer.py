
from rest_framework import serializers


class ShapeFileSerializer(serializers.Serializer):
    class Meta:
        fields = (
            "base_file", "dbf_file", "shx_file", "prj_file", "xml_file",
            "sld_file", "store_spatial_files", "override_existing_layer",
            "skip_existing_layers"
        )

    base_file = serializers.CharField()
    dbf_file = serializers.CharField(required=False)
    shx_file = serializers.CharField(required=False)
    prj_file = serializers.CharField(required=False)
    xml_file = serializers.FileField(required=False)
    sld_file = serializers.FileField(required=False)
    store_spatial_files = serializers.BooleanField(required=False, default=True)
    override_existing_layer = serializers.BooleanField(required=False, default=False)
    skip_existing_layers = serializers.BooleanField(required=False, default=False)
