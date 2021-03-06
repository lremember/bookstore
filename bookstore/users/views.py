from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http import JsonResponse
from django.shortcuts import render,redirect
from django.http import HttpResponse
from django_redis import get_redis_connection

from books.models import Books
from bookstore import settings
from order.models import OrderInfo, OrderGoods
from .models import Passport, Address
import re
from utils.decorators import login_required
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
# Create your views here.
from users.models import Passport
from users.tasks import send_active_email

def register(request):
	'''显示用户注册页面'''
	return render(request,'users/register.html')

def register_handle(request):
	'''进行用户注册处理'''
	username = request.POST.get('user_name')
	password = request.POST.get('pwd')
	email = request.POST.get('email')

	#进行数据校验
	if not all([username,password,email]):
		#数据为空
		return render(request,'users/register.html',{'errmsg':'参数不能为空'})
	#判断邮箱是否合法
	if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9]+(\.[a-z]{2,5}){1,2}$',email):
		return render(request,'users/register.html',{'errmg':'邮箱不合法!'})
	#惊醒业务处理:注册,向账户系统添加账户
	p = Passport.objects.check_passport(username=username)
	if p:
		return render(request,'users/register.html',{'errmsg':'用户名已存在'})
	passport = Passport.objects.add_one_passport(username=username, password=password, email=email)

	# 生成激活的token itsdangerous
	print("000000000000000000000000")
	serializer = Serializer(settings.SECRET_KEY, 3600)
	token = serializer.dumps({'confirm': passport.id})  # 返回bytes
	token = token.decode()
	send_mail('尚硅谷书城用户激活','',settings.EMAIL_FROM,[email],html_message='<a href="http://127.0.0.1:8000/user/active/%s/">http://127.0.0.1:8000/user/active/</a>' % token)
	send_active_email.delay(token, username, email)
	print('1111111111111111111111111')
	return redirect(reverse('books:index'))


def login(request):
	'''显示登录界面'''
	username = ''
	checked = ''
	context = {
		'username':username,
		'checked':checked,
	}
	return render(request,'users/login.html',context)

def login_check(request):
	'''进行用户登录校验'''
	#获取数据
	username = request.POST.get('username')
	password = request.POST.get('password')
	remember = request.POST.get('remember')
	verifycode =request.POST.get('verifycode')


	#数据校验
	if not all([username,password,remember,verifycode]):
		#有数据为空
		return JsonResponse({'res':2})

	#进行处理:根据用户名和密码查询账户信息
	if verifycode.upper() != request.session['verifycode']:
		return JsonResponse({'res': 2})

	passport = Passport.objects.get_one_passport(username=username,password=password)

	if passport:
		#用户密码正确
		#获取session中的url_path
		# if request.session.has_key('url_path'):
		# 	next_url = request.session.get('url_path')
		# else:
		# 	next_url = reverse('book:index')
		next_url = request.session.get('url_path',reverse('books:index'))
		jres = JsonResponse({'res':1,'next_url':next_url})

		#判断是否需要记住用户名
		if remember == 'true':
			#记住用户名
			jres.set_cookie('username',username,max_age=7*24*3600)
		else:
			#不记住用户名
			jres.delete_cookie('username')

		#记住用户的登录状态
		request.session['islogin'] = True
		request.session['username'] = username
		request.session['passport_id'] = passport.id
		return jres
	else:
		#用户名或密码错误
		return JsonResponse({'res':0})

def logout(request):
	request.session.flush()
	return redirect(reverse('books:index'))

@login_required
def user(request):
	'''用户中心-信息页'''
	passport_id = request.session.get('passport_id')
	addr = Address.objects.get_default_address(passport_id=passport_id)
	con = get_redis_connection('default')
	key = 'history_%d' % passport_id
	history_li = con.lrange(key, 0, 4)
	books_li = []
	for id in history_li:
		books = Books.objects.get_books_by_id(books_id=id)
		books_li.append(books)
	context = {
		'addr':addr,
		'page':'user',
		'books_li':books_li
	}
	return render(request,'users/user_center_info.html',context)

@login_required
def address(request):
	'''用户中心-地址页'''
	#获取登陆用户的id
	passport_id = request.session.get('passport_id')

	if request.method == 'GET':
		#显示地址页面
		#查询用户的默认地址
		addr = Address.objects.get_default_address(passport_id=passport_id)
		return render(request,'users/user_center_site.html',{'addr':addr,'page':'address'})
	else:
		#添加收货地址
		#1.接收数据
		recipient_name = request.POST.get('username')
		recipient_addr = request.POST.get('addr')
		zip_code = request.POST.get('zip_code')
		recipient_phone =request.POST.get('phone')
		#进行校验
		if not all([recipient_name,recipient_addr,zip_code,recipient_phone]):
			return render(request,'users/user_center_site.html',{'errmsg':'参数不能为空'})
		#添加收货地址
		Address.objects.add_one_address(passport_id=passport_id,
										recipient_name=recipient_name,
										recipient_addr=recipient_addr,
										zip_code=zip_code,
										recipient_phone=recipient_phone)
		#返回应答
		return redirect(reverse('user:address'))

@login_required
def order(request):
	'''用户中心-订单页'''
	#查询用户的订单信息
	passport_id = request.session.get('passport_id')
	#获取订单信息
	order_li = OrderInfo.objects.filter(passport_id=passport_id)
	#遍历获取订单的商品订单
	#order-->OrderInfo实力对象
	for order in order_li:
		#根据订单id查询订单商品信息
		order_id = order.order_id
		order_books_li = OrderGoods.objects.filter(order_id=order_id)
		#计算商品的小计
		#order_books-->OrderBooks实力对象
		for order_books in order_books_li:
			count = order_books.count
			price = order_books.price
			amount = count * price
			#保存订单中每一个商品的小计
			order_books.amount = amount

		#给order对象动态增加一个order_books_li,保存订单中商品的信息
		order.order_books_li = order_books_li
	context = {
		'order_li':order_li,
		'page':'order'
	}
	return render(request,'users/user_center_order.html',context)


def verifycode(request):
	from PIL import Image,ImageDraw,ImageFont
	import random
	bgcolor = (random.randrange(20,120),random.randrange(20,100),255)
	width = 100
	height =25
	im = Image.new('RGB',(width,height),bgcolor)
	draw = ImageDraw.Draw(im)
	for i in range(0,100):
		xy=(random.randrange(0,width),random.randrange(0,height))
		fill = (random.randrange(0,255),255,random.randrange(0,255))
		draw.point(xy,fill=fill)
	str1 = 'ABCD123EFGHIJK456LMNOPQRS789TUVWXYZ0'
	rand_str = ''
	for i in range(0,4):
		rand_str += str1[random.randrange(0,len(str1))]
	font = ImageFont.truetype("/usr/share/fonts/truetype/ubuntu-font-family/Ubuntu-R.ttf",15)
	fontcolor = (255,random.randrange(0,255),random.randrange(0,255))
	draw.text((5,2),rand_str[0],font=font,fill=fontcolor)
	draw.text((25,2),rand_str[1],font=font,fill=fontcolor)
	draw.text((50,2),rand_str[2],font=font,fill=fontcolor)
	draw.text((75,2),rand_str[3],font=font,fill=fontcolor)
	del draw
	request.session['verifycode'] = rand_str
	import io
	buf =io.BytesIO()
	im.save(buf,'png')
	return HttpResponse(buf.getvalue(),'image/png')

def register_active(request, token):
	serializer = Serializer(settings.SECRET_KEY, 3600)
	try:
		info = serializer.loads(token)
		passport_id = info['confirm']
		passport = Passport.objects.get(id=passport_id)
		passport.is_active = True
		passport.save()
		return redirect(reverse('user:login'))
	except SignatureExpired:
		return HttpResponse('激活链接已过期')


