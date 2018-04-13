from django.shortcuts import redirect
from django.http import HttpResponse
from django.core.urlresolvers import reverse


def login_required(view_func):
	'''登陆判断装饰器'''
	def wrapper(request,*view_args,**view_kwargs):
		if request.session.has_key('islogin'):
			print("aaa")
			#用户已登陆
			return view_func(request,*view_args,**view_kwargs)
		else:
			print("bbbb")
			#跳转到登录界面
			return redirect(reverse('user:login'))
	return wrapper