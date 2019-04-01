import random

from django.db import models
from django.utils import timezone

class Field(models.Model):
  nice_id = models.IntegerField(default=0)

  def warnings(self):
    warns = []
    if self.irrigation.bar_color() == "bg-danger":
      warns.append("Irrigation amount is too low!")
    if self.fertilizer.bar_color() == "bg-danger":
      warns.append("Fertilizer amount is too low!")
    if self.pesticide.bar_color() == "bg-danger":
      warns.append("Pesticide amount is too low!")
    return warns

  def verbose_warnings(self):
    warns = []
    if self.irrigation.bar_color() == "bg-danger":
      warns.append("Field #%i: Irrigation amount is too low!" % self.nice_id)
    if self.fertilizer.bar_color() == "bg-danger":
      warns.append("Field #%i: Fertilizer amount is too low!" % self.nice_id)
    if self.pesticide.bar_color() == "bg-danger":
      warns.append("Field #%i: Pesticide amount is too low!" % self.nice_id)
    return warns

  def color(self):
    statuses = [self.irrigation, self.fertilizer, self.pesticide]
    if any([s.bar_color() == "bg-danger" for s in statuses]):
      return "red"
    elif any([s.bar_color() == "bg-warning" for s in statuses]):
      return "yellow"
    else:
      return "green"

  @classmethod
  def too_low_helper(cls):
    lst = [i.key for i in cls.objects.all() if i.too_low()]
    if len(lst) == 0:
      return ""
    elif len(lst) == 1:
      return "%s is" % lst[0]
    elif len(lst) == 2:
      return "%s and %s are" % (lst[0], lst[1])
    else:
      return "%s, and %s are" % (", ".join(lst[:-1]), lst[-1])


class Status(models.Model):
  field = models.OneToOneField(
    Field,
    on_delete=models.CASCADE,
    primary_key=True,
  )
  value = models.FloatField(default=0)

  def bar_color(self):
    if self.value < 20:
      return "bg-danger"
    elif self.value < 50:
      return "bg-warning"
    else:
      return "bg-success"

  def too_low(self):
    return self.value < 20

  class Meta:
    abstract = True


class Irrigation(Status):
  pass


class Fertilizer(Status):
  pass


class Pesticide(Status):
  pass


class Harvest(models.Model):
  field = models.OneToOneField(
    Field,
    on_delete=models.CASCADE,
    primary_key=True,
  )
  description = models.CharField(max_length=200)
  value = models.FloatField(default=0)
