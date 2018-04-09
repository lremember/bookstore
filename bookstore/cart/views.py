from django.shortcuts import render
from django.http import JsonResponse
from books.models import Books
from utils.decorators import login_required
from django_redis import get_redis_connection


# Create your views here.
#前端发过来的数据:商品id,商品数目 books_id books_count
#涉及到数据的修改.使用post方法
def cart_add(request):
	'''向购物车添加数据'''
	#判断用户是否登陆
	if not request.session.has_key('islogin'):
		return JsonResponse({'res':0,'errmsg':'请先登陆'})

	#接收数据
	books_id = request.POST.get('books_id')
	books_count = request.POST.get('books_count')

	#进行数据校验
	if not all([books_id,books_count]):
		return JsonResponse({'res':1,'errmsg':'数据不完整'})

	books = Books.objects.get_books_by_id(books_id=books_id)
	if books is None:
		return JsonResponse({'res':2,'errmsg':'商品不存在'})

	try:
		count = int(books_count)
	except Exception as e:
		return JsonResponse({'res':3,'errmsg':'商品数量必须为数字'})

	#添加商品到购物车
	#每个用户的购物车记录用一条hash数据保存,格式:cart_用户id:商品id 商品数量
	conn = get_redis_connection('default')
	cart_key = 'cart_%d' % request.session.get('passport_id')

	res = conn.hget(cart_key,books_id)
	if res is None:
		res = count
	else:
		res = int(res) + count

	if res > books.stock:
		#库存不足
		return JsonResponse({'res':4,'errmsg':'商品库存不足'})
	else:
		conn.hset(cart_key,books_id,res)
	#返回结果
	return JsonResponse({'res':5})


def cart_count(request):
	'''获取用户购物车商品的数目'''
	#判断用户是否登陆
	if not request.session.has_key('islogin'):
		return JsonResponse({'res':0})

	#计算用户购物车商品的数量
	conn = get_redis_connection('default')
	cart_key = 'cart_%d' % request.session.get('passport_id')

	# res = conn.hlen(cart_key)

	res = 0
	res_list = conn.hvals(cart_key)

	for i in res_list:
		res += int(i)

	return JsonResponse({'res':res})


@login_required
def cart_show(request):
	'''现实用户购物车页面'''
	passport_id = request.session.get('passport_id')
	#获取用户购物车记录
	conn = get_redis_connection('default')
	cart_key = 'cart_%d' % passport_id
	res_dict = conn.hgetall(cart_key)

	books_li = []
	total_count = 0
	total_price = 0

	for id,count in res_dict.items():
		#根据id获取商品的信息
		books = Books.objects.get_books_by_id(books_id=id)
		#保存商品的数量
		books.count = count
		#baocunshangpin的小计
		books.amount = int(count) * books.price
		# books_li.append((books,count))
		books_li.append(books)

		total_count += int(count)
		total_price += int(count) * books.price

	context = {
		'books_li':books_li,
		'total_count':total_count,
		'total_price':total_price,
	}
	return render(request,'cart/cart.html',context)


def cart_del(request):
	'''删除用户购物城中的商品'''
	#判断用户是否登陆
	if not request.session.has_key('islogin'):
		return JsonResponse({'res':0,'errmsg':'请登陆'})

	#接收数据
	books_id = request.POST.get('books_id')

	#校验商品是否存放
	if not all([books_id]):
		return JsonResponse({'res':1,'errmsg':'数据不完整'})

	books = Books.objects.get_books_by_id(books_id=books_id)
	if books is None:
		return JsonResponse({'res':2,'errmsg':'商品不存在'})

	#删除购物车商品信息
	conn = get_redis_connection('default')
	cart_key = 'cart_%d' % request.session.get('passport_id')
	conn.hdel(cart_key,books_id)

	#返回信息
	return JsonResponse({'res':3})


#实现购物车页面编辑商品数量的功能
#前端传来的数据:商品id books_id 更新数目 books_count

def cart_update(request):
	'''更新购物车商品数目'''
	#判断用户是否登陆
	if not request.session.has_key('islogin'):
		return JsonResponse({'res':0,'errmsg':'请登陆'})

	#接收数据
	books_id = request.POST.get('books_id')
	books_count = request.POST.get('books_count')

	#数据校验
	if not all([books_id,books_count]):
		return JsonResponse({'res':1,'errmsg':'数据不完整'})

	books = Books.objects.get_books_by_id(books_id=books_id)
	if books is None:
		return JsonResponse({'res':2,'errmsg':'商品不存在'})
	try:
		books_count = int(books_count)
	except Exception as e:
		return JsonResponse({'res':3,'errmsg':'商品树木必须为数字'})

	#更新操作
	conn = get_redis_connection('default')
	cart_key = 'cart_%d' % request.session.get('passport_id')

	#判断商品库存
	if books_count > books.stock:
		return JsonResponse({'res':4,'errmsg':'商品库存不足'})

	conn.hset(cart_key,books_id,books_count)

	return JsonResponse({'res':5})

























