from sys import stderr

reservedWordDict={
    'and':1,'array':2,'begin':3,'bool':4,'call':5,'case':6,'char':7,'constant':8,'dim':9,'do':10,'else':11,'end':12,'false':13,'for':14,'if':15,'input':16,
    'integer':17,'not':18, 'of':19,'or':20,'output':21,'procedure':22,'program':23,'read':24,'real':25,'repeat':26,'set':27,'stop':28,'then':29,'to':30,
    'true':31,'until':32,'var':33,'while':34,'write':35
}

Identifier_Code=36
Integer_Code=37
String_Code=38


dlimeterDict={
    '(':39,')':40,'*':41,'*/':42,'+':43,',':44,'-':45,'.':46,'..':47,'/':48,'/*':49,
    ':':50,':=':51,';':52,'<':53,'<=':54,'<>':55,'=':56,'>':57,'>=':58,'[':59,']':60
}



class lexException(Exception):
    def __init__(self,row_i,desc):
        Exception.__init__(self,'词法错误:'+"第"+str(row_i+1)+"行"+desc)



def isReservedWord(colleStr):
    return colleStr in reservedWordDict.keys()

def isDlimeter(colleStr):
    return colleStr in dlimeterDict.keys()



def isAlpha(word):
    try:
        return word.encode('ascii').isalpha()
    except UnicodeEncodeError:
        return False



class Btuple:
    def __init__(self,code,context,row_i):
        self.code,self.context,self.row_i=code,context,row_i
    def __str__(self):
        return '(' + ','.join([str(self.code), str(self.context)]) + ')'


# 扫描
def scan(lines):
    try:
        for row_i,line in enumerate(lines):
            #　处理每一行
            # 读入字符的位置
            pos = -1
            while True:
                # 第一个位置是0
                pos+=1
                # 读取位置不应越界
                if not pos<len(line):
                    break

                # 标识符或保留字
                # 判断第一个字符是否为字母
                if line[pos].isalpha():

                    colleStr=''+line[pos]
                    # 读入一段 标识符或保留字 直到 以及 下一位越界 以及 或下一个字母是非字母，非数字
                    while pos+1<len(line) and (line[pos+1].isalpha() or line[pos+1].isdigit()):
                        pos += 1
                        colleStr+=line[pos]

                    #保留字
                    if isReservedWord(colleStr):
                        code=reservedWordDict[colleStr]
                        yield Btuple(code,colleStr,row_i)
                    #标识符
                    else:
                        yield Btuple(Identifier_Code,colleStr,row_i)

                # 界符或字符串 '\''
                # ps　line[pos]只有一个字符
                elif isDlimeter(line[pos]) or line[pos]=='\'':

                    #分为 /* */  '   '  一般双界符   单界符

                    # A.注释 /* */    '   '
                    # ps 双引号不属于跨越符
                    # 注释和字符串
                    if line[pos] =='/':

                        # 需要结合后一个字符，看两者合起来是否为/*，
                        # 当然，如果当前字符是最后一个字符，则为单界符，该错误交给yacc处理，lex不处理
                        if pos+1<len(line) and line[pos]+line[pos+1]=='/*':
                            # 注释开始
                            pos=pos+1

                            # 在/* */之间都是注释
                            # 如果在这行结束前未能读到*/,则缺右界符*/ 注释错误
                            # 如果pos+1越界,也会发生注释错误（find函数也返回-1）
                            right_pos= line.find( '*/',pos+1)
                            if right_pos==-1:
                                raise lexException(row_i,"注释错误")
                            else:
                                # 如果找到，那么right_pos是*的下标
                                pos=right_pos+1
                        # 单界符/
                        else:
                            yield Btuple(dlimeterDict[line[pos]],line[pos],row_i)

                    # B.字符串 '   'おｒ
                    elif line[pos]== '\'':
                        # 在' '之间都是字符串
                        # 如果在这行结束前未能读到',则缺右界符' 引号错误
                        # 如果pos+1越界,也会发生注释错误（find函数也返回-1）
                        right_pos = line.find('\'', pos + 1)


                        if right_pos==-1:
                            raise lexException(row_i,"引号错误")
                        else:
                            # 如果找到则从pos到right_pos都是字符串 输出时去掉左右两个引号
                            # line[pos:right_pos+1] 是 'xxxx'
                            # 则line[pos+1:right_pos] 是 xxxx
                            yield Btuple(String_Code,line[pos+1:right_pos],row_i)
                            pos=right_pos

                    # C.可能是一般双界符
                    elif line[pos] in {'<','>',':','.'}:
                        # 需要结合后一个字符，看两者合起来是否为双界符，
                        # 当然，如果当前字符是最后一个字符，则为单界符，该错误交给yacc处理，lex不处理
                        right_pos=pos+1
                        if right_pos<len(line) and isDlimeter(line[pos]+line[right_pos]):
                            colleStr = '' + line[pos]+line[right_pos]
                            yield Btuple(dlimeterDict[colleStr], colleStr,row_i)
                            pos=right_pos

                        else:
                            # 找不到，则为单界符
                            yield Btuple(dlimeterDict[line[pos]],line[pos],row_i)

                    # D.剩下的都是单界符
                    else:
                        yield Btuple(dlimeterDict[line[pos]],line[pos],row_i)


                # 数字
                elif line[pos].isdigit():

                    #　一直读到非数字为止

                    colleStr=''+line[pos]
                    # 读入一段 标识符或保留字 直到 以及 下一位越界 以及 下一个字母是非数字
                    while pos+1<len(line) and line[pos+1].isdigit():
                        pos += 1
                        colleStr+=line[pos]

                    yield Btuple(Integer_Code,colleStr,row_i)

                    # 额外的非法判断，当数字后跟着字母时报告非法
                    if pos+1<len(line) and line[pos+1].isalpha():
                        raise lexException(row_i,"出现非法输入")


                # 空格 、制表符、换行
                elif line[pos] in [' ','\t','\r\n','\n','\r']  :
                    # 跳过
                    pass
                # 以上均不满足 非法输入
                else:
                    raise lexException(row_i,"出现非法输入")
    except lexException as e:
        stderr.write(str(e)+'\n')




def simplified_scan(lines):
    # Python 字典 setdefault() 函数和get() 方法类似, 如果键不存在于字典中，将会添加键并将值设为默认值
    name_dict = {}
    for bTuple in scan(lines):
        code = bTuple.code
        context = bTuple.context
        if code in {Identifier_Code,Integer_Code,String_Code}:
            name_dict.setdefault(context,len(name_dict)+1)
            yield Btuple(code,name_dict[context],None)
        else:
            # 非标识符、非整数、非字符串 均不记录
            yield Btuple(code,'-',None)





if __name__ == '__main__':
    pass
    #for i,bTuple in enumerate(scan(lines2)):
    #    print(bTuple,end=' ')
    #    if (i+1)%5==0:
    #        print()