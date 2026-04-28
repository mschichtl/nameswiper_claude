from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('groups/', views.group_list, name='group_list'),
    path('groups/new/', views.group_create, name='group_create'),
    path('groups/<int:pk>/', views.group_detail, name='group_detail'),
    path('groups/<int:pk>/remove/<int:user_id>/', views.remove_member, name='remove_member'),
    path('invite/<uuid:token>/', views.invite_view, name='invite'),
    path('swipe/', views.swipe_view, name='swipe'),
    path('swipe/action/', views.swipe_action, name='swipe_action'),
    path('swipe/history/', views.swipe_history, name='swipe_history'),
    path('swipe/<int:swipe_id>/edit/', views.swipe_edit, name='swipe_edit'),
    path('score/<int:group_id>/', views.score_view, name='score'),
    path('score/<int:group_id>/save/', views.score_save, name='score_save'),
    path('results/<int:group_id>/', views.results_view, name='results'),
]
