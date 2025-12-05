from django.urls import include, path

from . import views

app_name = "users"

urlpatterns = [
    # user authentication urls
    path("", include("django.contrib.auth.urls")),
    # user accounts
    path("account/", views.AccountPage.as_view(), name="accounts"),
    # user registration
    path("register/", views.UserCreateView.as_view(), name="register"),
    path("register/done/", views.RegisterDone.as_view(), name="register_done"),
    # user editing
    path("edit/", views.UserEditView.as_view(), name="edit"),
    path("settings/", views.user_settings, name="settings"),
    path("organizations/", views.user_organizations, name="organizations"),
    path(
        "study_organizations/",
        views.user_study_organizations,
        name="study_organizations",
    ),
    path("invitations/", views.user_invitations, name="invitations"),
    path("notifications/", views.user_notifications, name="notifications"),
    # path(
    #     "notifications/action",
    #     views.user_notifications_action,
    #     name="notifications_action",
    # ),
    # path(
    #     "notification/<int:notification_id>/action",
    #     views.user_notification_action,
    #     name="notification_action",
    # ),
    path(
        "invitation_accept/<uuid:pk>",
        views.user_invitation_accept,
        name="invitation_accept",
    ),
    path(
        "invitation_rejected/<uuid:pk>",
        views.user_invitation_rejected,
        name="invitation_rejected",
    ),
    # path(
    #     "organizations_dashboard/",
    #     views.organizations_report,
    #     name="organizations_dashboard",
    # ),
]
