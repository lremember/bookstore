from django.db import models
from db.base_model import BaseModel
from tinymce.models import HTMLField
from books.enums import *

# Create your models here.

class BooksManager(models.Manager):

	def get_books_by_type(self,type_id,limit=None,sort='default'):
		'''根据商品类型id查询商品信息'''
		if sort == 'new':
			order_by = ('-create_time',)
		elif sort == 'hot':
			order_by = ('-sales',)
		elif sort == 'price':
			order_by = ('price',)
		else:
			order_by = ('-pk',)#按照主键降序排序

		#查询数据
		book_li = self.filter(type_id=type_id).order_by(*order_by)#*order_by解包

		#查询结果集的限制
		if limit:
			book_li = book_li[:limit]
		return book_li

	def get_books_by_id(self,books_id):
		'''根据商品的id获取商品信息'''
		try:
			books = self.get(id=books_id)
		except self.model.DoesNotExist:
			#不存在商品信息
			books = None
		return books


class Books(BaseModel):
	books_type_choices = ((k,v) for k,v in BOOKS_TYPE.items())
	status_choices = ((k,v) for k,v in STATUS_CHOICE.items())
	type_id = models.SmallIntegerField(default=PYTHON,choices=books_type_choices,verbose_name='商品种类')
	name = models.CharField(max_length=20,verbose_name='商品名称')
	desc = models.CharField(max_length=128,verbose_name='商品简介')
	price = models.DecimalField(max_digits=10,decimal_places=2,verbose_name='商品价格')
	unit = models.CharField(max_length=20,verbose_name='商品单位')
	stock = models.IntegerField(default=1,verbose_name='商品库存')
	sales = models.IntegerField(default=0,verbose_name='商品销量')
	detail = HTMLField(verbose_name='商品详情')
	image = models.ImageField(upload_to='books',verbose_name='商品图片')
	status = models.SmallIntegerField(default=ONLINE,choices=status_choices,verbose_name='商品状态')

	objects = BooksManager()

	class Meta:
		db_table = 's_books'
		verbose_name = '书籍'
		verbose_name_plural = verbose_name

