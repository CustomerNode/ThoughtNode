from celery import shared_task
from django.utils.timezone import localtime
from .models import Thoughtnode
from .views import thoughtnode_run

@shared_task
def scheduled_thoughtnode_run():
    thoughtnodes = Thoughtnode.objects.filter(frequency="Daily")
    time = localtime()
    if time.isoweekday() == 1:
        thoughtnodes = thoughtnodes.union(Thoughtnode.objects.filter(frequency="Weekly"))
    if time.day == 1:
        thoughtnodes = thoughtnodes.union(Thoughtnode.objects.filter(frequency="Monthly"))
    for thoughtnode in thoughtnodes:
        thoughtnode_run(thoughtnode.slug)
        print(f"thoughtnode started: {thoughtnode.title}")