import random

from django.shortcuts import render
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
#from django.utils import timezone

from .models import *

def dashboard(request):
  all_warnings = []
  for field in Field.objects.all():
    all_warnings.extend(field.verbose_warnings())
  return render(request, 'dashboard/dashboard.html', {
    'fields': Field.objects.all(),
    'all_warnings': all_warnings,
  })

def info(request, id):
  field = Field.objects.get(nice_id=id)
  
  return render(request, 'dashboard/info.html', {
    'field': field,
    'irrigation': field.irrigation,
    'fertilizer': field.fertilizer,
    'pesticide': field.pesticide,
  })

def placeholder(request):
  #request.POST['foo']
  [f.delete() for f in Field.objects.all()]

  for nice_id in range(1, 13):
    field = Field(nice_id=nice_id)
    field.save()

    i = Irrigation(field=field, value=random.random()*100)
    f = Fertilizer(field=field, value=random.random()*100)
    p = Pesticide(field=field, value=random.random()*100)
    h = Harvest(field=field)

    i.save()
    f.save()
    p.save()
    h.save()
  return HttpResponseRedirect(reverse('dashboard', args=()))


#i = Input(key='coolstuff', value=123.45, timestamp=timezone.now())
#i.key = 'coolerstuff'

#Input.objects.filter(id=1)
#Input.objects.filter(key=1)
#i = Input.objects.get(id=1)
#i.recent()

#Input.objects.order_by('-timestamp')[:5]
