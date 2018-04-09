from hashlib import sha1


def get_hash1(str):
	'''去一个字符串的hash值'''
	sh = sha1()
	sh.update(str.encode('utf8'))
	return sh.hexdigest()
