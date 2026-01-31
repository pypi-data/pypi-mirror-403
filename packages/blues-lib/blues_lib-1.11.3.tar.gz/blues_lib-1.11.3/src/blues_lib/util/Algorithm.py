import hashlib,math
class Algorithm():

  @classmethod
  def md5(cls,text):
    # 单向不可逆，作为数据存储密码，如果忘了只能重置
    md_5 = hashlib.md5()
    # update入参必须时 bytes类型
    md_5.update(text.encode())
    return md_5.hexdigest()
  
  @classmethod
  def sha1(cls,text):
    sha_1 = hashlib.sha1()
    sha_1.update(text.encode())
    return sha_1.hexdigest()

  @classmethod
  def get_cn_length(cls, text: str) -> int:
    """
    计算字符串长度，中文按长度1计算；英文和符号按0.5计算，结果向上取整
    """
    length = 0
    for char in text:
      if '\u4e00' <= char <= '\u9fff': # 判断是否为中文字符
        length += 1
      else:
        length += 0.5
    return math.ceil(length) # 向上取整，确保返回整数
