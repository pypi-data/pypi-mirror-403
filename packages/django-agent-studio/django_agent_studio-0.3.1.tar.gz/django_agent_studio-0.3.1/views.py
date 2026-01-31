"""
Views for django_agent_studio.
"""

from django.db.models import Q
from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin

from django_agent_runtime.models import AgentDefinition, AgentSystem


class AgentAccessMixin:
    """
    Mixin that provides consistent agent access logic.

    - Superusers can access all agents
    - Regular users can access their own agents
    """

    def get_user_agents_queryset(self):
        """Get queryset of agents accessible to the current user."""
        if self.request.user.is_superuser:
            return AgentDefinition.objects.all()
        return AgentDefinition.objects.filter(owner=self.request.user)

    def get_agent_for_user(self, agent_id):
        """
        Get a specific agent if the user has access.

        - Superusers can access any agent
        - Regular users can access their own agents
        """
        if self.request.user.is_superuser:
            return AgentDefinition.objects.get(id=agent_id)
        return AgentDefinition.objects.get(id=agent_id, owner=self.request.user)


class SystemAccessMixin:
    """
    Mixin that provides consistent system access logic.

    - Superusers can access all systems
    - Regular users can access their own systems
    """

    def get_user_systems_queryset(self):
        """Get queryset of systems accessible to the current user."""
        if self.request.user.is_superuser:
            return AgentSystem.objects.all()
        return AgentSystem.objects.filter(owner=self.request.user)

    def get_system_for_user(self, system_id):
        """
        Get a specific system if the user has access.

        - Superusers can access any system
        - Regular users can access their own systems
        """
        if self.request.user.is_superuser:
            return AgentSystem.objects.select_related('entry_agent').get(id=system_id)
        return AgentSystem.objects.select_related('entry_agent').get(
            id=system_id, owner=self.request.user
        )


class StudioHomeView(LoginRequiredMixin, AgentAccessMixin, SystemAccessMixin, TemplateView):
    """Home page for the agent studio."""

    template_name = "django_agent_studio/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Systems (shown above agents)
        context["recent_systems"] = self.get_user_systems_queryset().select_related(
            'entry_agent'
        ).order_by("-updated_at")[:5]
        # Agents
        context["recent_agents"] = self.get_user_agents_queryset().order_by("-updated_at")[:5]
        context["template_agents"] = AgentDefinition.objects.filter(
            is_template=True,
            is_public=True,
        ).order_by("-updated_at")[:10]
        return context


class AgentListView(LoginRequiredMixin, AgentAccessMixin, ListView):
    """List all agents for the current user."""

    template_name = "django_agent_studio/agent_list.html"
    context_object_name = "agents"

    def get_queryset(self):
        return self.get_user_agents_queryset().order_by("-updated_at")


class AgentBuilderView(LoginRequiredMixin, AgentAccessMixin, TemplateView):
    """
    Two-pane agent builder interface.

    Left pane: Test the agent (agent-frontend instance)
    Right pane: Builder agent conversation (agent-frontend instance)
    """

    template_name = "django_agent_studio/builder.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        agent_id = kwargs.get("agent_id")

        if agent_id:
            context["agent"] = self.get_agent_for_user(agent_id)
            context["is_new"] = False
        else:
            context["agent"] = None
            context["is_new"] = True

        # Configuration for the builder agent
        context["builder_agent_key"] = "agent-builder"

        return context


class AgentTestView(LoginRequiredMixin, AgentAccessMixin, TemplateView):
    """Full-screen agent testing interface."""

    template_name = "django_agent_studio/test.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        agent_id = kwargs.get("agent_id")
        context["agent"] = self.get_agent_for_user(agent_id)
        return context


class SystemListView(LoginRequiredMixin, SystemAccessMixin, ListView):
    """List all systems for the current user."""

    template_name = "django_agent_studio/system_list.html"
    context_object_name = "systems"

    def get_queryset(self):
        return self.get_user_systems_queryset().select_related(
            'entry_agent'
        ).prefetch_related('members__agent').order_by("-updated_at")


class SystemTestView(LoginRequiredMixin, SystemAccessMixin, TemplateView):
    """
    Full-screen system testing interface.

    Uses the system's entry_agent as the starting point for conversations.
    """

    template_name = "django_agent_studio/system_test.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        system_id = kwargs.get("system_id")
        system = self.get_system_for_user(system_id)
        context["system"] = system
        context["agent"] = system.entry_agent  # The entry point agent
        return context

