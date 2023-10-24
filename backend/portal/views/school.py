from codeforlife.user.views import SchoolViewSet as _SchoolViewSet

from ..serializers import SchoolSerializer


class SchoolViewSet(_SchoolViewSet):
    http_method_names = ["get", "post", "patch"]
    serializer_class = SchoolSerializer
