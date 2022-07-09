from django.db.models import OuterRef, F, Count, Subquery
from django.conf import settings
from django.contrib import admin
from django.contrib.admin.utils import unquote
from django.utils.encoding import force_str
from django.utils.text import capfirst
from simple_history.admin import SimpleHistoryAdmin

admin.site.site_header = "Peling Chhokhor Admin"
admin.site.site_title = "PCDL Admin"
admin.site.index_title = "Library Administration"

USER_NATURAL_KEY = tuple(key.lower() for key in settings.AUTH_USER_MODEL.split(".", 1))


class CustomHistoryAdmin(SimpleHistoryAdmin):

    def history_view(self, request, object_id, extra_context=None):
        """The 'history' admin view for this model."""
        request.current_app = self.admin_site.name
        model = self.model
        opts = model._meta
        app_label = opts.app_label
        pk_name = opts.pk.attname
        history = getattr(model, model._meta.simple_history_manager_attribute)
        object_id = unquote(object_id)
        action_list = history.filter(**{pk_name: object_id})
        previous_records = action_list.filter(history_date__lt=OuterRef("history_date")).order_by("-history_date")
        action_list = action_list.annotate(previous_record_reason=Subquery(previous_records.values("history_change_reason")[:1]))
        if not isinstance(history.model.history_user, property):
            # Only select_related when history_user is a ForeignKey (not a property)
            action_list = action_list.select_related("history_user")
        history_list_display = getattr(self, "history_list_display", [])
        # If no history was found, see whether this object even exists.
        try:
            obj = self.get_queryset(request).get(**{pk_name: object_id})
        except model.DoesNotExist:
            try:
                obj = action_list.latest("history_date").instance
            except action_list.model.DoesNotExist:
                raise http.Http404

        if not self.has_change_permission(request, obj):
            raise PermissionDenied

        # Set attribute on each action_list entry from admin methods
        for history_list_entry in history_list_display:
            value_for_entry = getattr(self, history_list_entry, None)
            if value_for_entry and callable(value_for_entry):
                for list_entry in action_list:
                    setattr(list_entry, history_list_entry, value_for_entry(list_entry))

        content_type = self.content_type_model_cls.objects.get_by_natural_key(
            *USER_NATURAL_KEY
        )
        admin_user_view = "admin:{}_{}_change".format(
            content_type.app_label,
            content_type.model,
        )
        context = {
            "title": self.history_view_title(obj),
            "action_list": action_list,
            "module_name": capfirst(force_str(opts.verbose_name_plural)),
            "object": obj,
            "root_path": getattr(self.admin_site, "root_path", None),
            "app_label": app_label,
            "opts": opts,
            "admin_user_view": admin_user_view,
            "history_list_display": history_list_display,
            "revert_disabled": self.revert_disabled,
        }
        context.update(self.admin_site.each_context(request))
        context.update(extra_context or {})
        extra_kwargs = {}
        return self.render_history_view(
            request, self.object_history_template, context, **extra_kwargs
        )
