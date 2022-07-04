from django.urls import path

from .views import PageListView, PageDetailView

urlpatterns = [
    path('', PageListView.as_view(), name='page_list'),
    path('Volume-<slug:volume>/Page-<slug:page>/<slug:type>/detail/', PageDetailView.as_view(), name='page_detail'),
]
