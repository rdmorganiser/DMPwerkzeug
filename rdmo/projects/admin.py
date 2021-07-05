from django.contrib import admin

from .models import (Continuation, Integration, IntegrationOption, Invite,
                     Issue, IssueResource, Membership, Project, Snapshot,
                     Value)


class ProjectAdmin(admin.ModelAdmin):
    search_fields = ('title', 'user__username')
    list_display = ('title', 'owners')

    def owners(self, obj):
        return ', '.join([user.username for user in obj.owners])


class MembershipAdmin(admin.ModelAdmin):
    search_fields = ('project__title', 'user__username', 'role')
    list_display = ('project', 'user', 'role')


class ContinuationAdmin(admin.ModelAdmin):
    search_fields = ('project__title', 'user__username')
    list_display = ('project', 'user', 'questionset')


class IntegrationAdmin(admin.ModelAdmin):
    search_fields = ('project__title', 'provider_key')
    list_display = ('project', 'provider_key')


class IntegrationOptionAdmin(admin.ModelAdmin):
    search_fields = ('integration__project__title', 'key', 'value')
    list_display = ('integration', 'key', 'value')


class InviteAdmin(admin.ModelAdmin):
    search_fields = ('project__title', 'user__username', 'email', 'role')
    list_display = ('project', 'user', 'email', 'token', 'timestamp')
    readonly_fields = ('token', 'timestamp')


class IssueAdmin(admin.ModelAdmin):
    search_fields = ('project__title', 'task', 'status')
    list_display = ('project', 'task', 'status')
    list_filter = ('status', )


class IssueResourceAdmin(admin.ModelAdmin):
    search_fields = ('issue__project__title', 'url')
    list_display = ('issue', 'url')


class SnapshotAdmin(admin.ModelAdmin):
    search_fields = ('title', 'project__title', 'project__user__username')
    list_display = ('title', 'project')


class ValueAdmin(admin.ModelAdmin):
    search_fields = ('attribute__uri', 'project__title', 'snapshot__title', 'project__user__username')
    list_display = ('attribute', 'set_prefix', 'set_index', 'collection_index', 'project', 'snapshot_title')
    list_filter = ('value_type', )

    def snapshot_title(self, obj):
        if obj.snapshot:
            return obj.snapshot.title


admin.site.register(Project, ProjectAdmin)
admin.site.register(Membership, MembershipAdmin)
admin.site.register(Continuation, ContinuationAdmin)
admin.site.register(Integration, IntegrationAdmin)
admin.site.register(IntegrationOption, IntegrationOptionAdmin)
admin.site.register(Invite, InviteAdmin)
admin.site.register(Issue, IssueAdmin)
admin.site.register(IssueResource, IssueResourceAdmin)
admin.site.register(Snapshot, SnapshotAdmin)
admin.site.register(Value, ValueAdmin)
