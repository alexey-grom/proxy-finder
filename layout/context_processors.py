from api import get_layout


def layout(request):
    instance = get_layout(request)
    return {
        'layout': instance.values,
    }
