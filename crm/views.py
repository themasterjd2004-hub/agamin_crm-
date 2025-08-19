from django.views.generic import ListView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from .models import Request


@method_decorator(staff_member_required, name='dispatch')
class RequestListView(ListView):
    model = Request
    template_name = 'crm/object_list.html'
    context_object_name = 'objects'
    paginate_by = 25


@method_decorator(staff_member_required, name='dispatch')
class RequestUpdateView(UpdateView):
    model = Request
    template_name = 'crm/object_form.html'
    fields = '__all__'

    def get_success_url(self):
        return reverse('object-detail', args=[str(self.object.pk)])


@method_decorator(staff_member_required, name='dispatch')
class RequestDeleteView(DeleteView):
    model = Request
    template_name = 'crm/object_confirm_delete.html'
    success_url = reverse_lazy('object-list')