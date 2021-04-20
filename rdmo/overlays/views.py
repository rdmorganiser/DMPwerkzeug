import logging

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from rdmo.core.utils import get_next, get_referer_path_info

from .models import Overlay

logger = logging.getLogger(__name__)


@login_required()
def reset_overlays(request):
    if request.method == 'POST':
        Overlay.objects.filter(user=request.user).delete()
        return redirect(get_next(request))

    return render(request, 'overlays/reset_overlays.html', {
        'next': get_referer_path_info(request, default='/')
    })
