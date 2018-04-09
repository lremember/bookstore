from django.conf.urls import url
from users import views


urlpatterns = [
	#用户注册
	url(r'register/$',views.register,name='register'),
	url(r'^register_handle/$',views.register_handle,name='register_handle'),
	url(r'login/$',views.login,name='login'),
	url(r'login_check/$',views.login_check,name='login_check'),
	url(r'logout/$',views.logout,name='logout'),
	url(r'^address/$', views.address, name='address'),  # 用户中心-地址页
	url(r'^order/$', views.order, name='order'),  # 用户中心-订单页面
	url(r'^$',views.user,name='user'),

]