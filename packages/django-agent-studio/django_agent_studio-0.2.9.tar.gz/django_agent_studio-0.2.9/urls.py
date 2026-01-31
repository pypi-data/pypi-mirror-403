"""
URL configuration for django_agent_studio.
"""

from django.urls import path, include

from django_agent_studio import views
from django_agent_studio.api import urls as api_urls

app_name = "agent_studio"

urlpatterns = [
    # Main studio interface
    path("", views.StudioHomeView.as_view(), name="home"),
    
    # Agent builder/editor
    path("agents/", views.AgentListView.as_view(), name="agent_list"),
    path("agents/new/", views.AgentBuilderView.as_view(), name="agent_create"),
    path("agents/<uuid:agent_id>/", views.AgentBuilderView.as_view(), name="agent_edit"),
    path("agents/<uuid:agent_id>/test/", views.AgentTestView.as_view(), name="agent_test"),
    
    # API endpoints
    path("api/", include(api_urls)),
]

