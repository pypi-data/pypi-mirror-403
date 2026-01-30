from django.http import JsonResponse

from djproviderkit.models import ProviderkitModel


def list_providers(request):  # noqa: ARG001
    qs = ProviderkitModel.objects.all()
    data = [
        {'name': q.name, 'display_name': q.display_name, 'description': q.description} for q in qs
    ]
    return JsonResponse(data, safe=False)
