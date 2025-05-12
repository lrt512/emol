from django.http import JsonResponse

from cards.models.card import Card
from cards.models.waiver import Waiver


def get_valid_objects(request):
    model = request.GET.get("model")
    queryset = Card.objects.none()
    if model == "card":
        queryset = Card.objects.all()
    elif model == "waiver":
        queryset = Waiver.objects.all()
    data = [{"value": obj.pk, "display": str(obj)} for obj in queryset]
    return JsonResponse(data, safe=False)
