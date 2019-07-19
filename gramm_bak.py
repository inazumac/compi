from lexx import *


class Qtuple:
    def __init__(self, id, op, arg1, arg2, res):
        self.id, self.op, self.arg1, self.arg2, self.res = id, op, arg1, arg2, res

    def __str__(self):
        return '(' + ','.join([str(self.id), str(self.op), str(self.arg1), str(self.arg2), str(self.res)]) + ')'


class gramException(Exception):
    def __init__(self, row_i, desc):
        Exception.__init__(self, '语法错误:' + "第" + str(row_i + 1) + "行" + desc)


def genqs(lines):
    # 四元组
    qTupleList = []
    # 变量池
    varDict = {}
    # 临时变量池
    tmpDict = {}

    # 词法分析迭代
    it = iter(scan(lines))

    # token 语义约束
    # 进入分析时 踩在片段上的第一个词上
    # 离开分析时 踩在下一个片段的第一个词上，不在之前的片段内
    # 【务必确认】踩在终结符上才可进行 next操作



    # 申请一个新临时变量
    def talloc(tmpType=None):
        tmpName = 'T' + str(len(tmpDict) + 1)
        tmpDict[tmpName] = tmpType
        return tmpName

    # 生成四元组
    def gen(op, arg1, arg2, res):
        qTupleList.append(Qtuple(len(qTupleList), op, arg1, arg2, res))

    def var_def(token):
        varColle = []

        # 标识符表部分开始
        while token.code != dlimeterDict[':']:
            if token.code != Identifier_Code:
                raise gramException(token.row_i, "标识符错误")
            else:
                # 收集标识符
                varColle.append(token.context)

            token = next(it)
            # [此时token可能踩在: 上]
            if token.code == dlimeterDict[',']:
                # 读取下一个标识符
                token = next(it)
        # 标识符表部分结束
        # [此时token踩在:上]

        token = next(it)
        # 类型部分开始
        if not token.code in {reservedWordDict['integer'], reservedWordDict['bool'], reservedWordDict['char']}:
            raise gramException(token.row_i, "变量类型错误")
        else:
            varType = token.code
        # 类型部分结束


        token = next(it)
        # [此时token踩在;上]
        if token.code != dlimeterDict[';']:
            raise gramException(token.row_i, "变量定义缺少;")

        # 注册变量
        for var in varColle:
            varDict[var] = varType

        # 尝试离开
        token = next(it)
        if token.code != reservedWordDict['begin']:
            # 继续进入变量定义
            token = var_def(token)

        # [此时token踩在begin上]
        return token

    def assign(token):

        # [此时token踩在标识符上]
        res = None
        if token.code != Identifier_Code:
            raise gramException(token.row_i, "非标识符")
        else:
            if not token.context in varDict:
                raise gramException(token.row_i, "未定义的标识符")
            res = token.context

        token = next(it)
        # [此时token踩在:=上]
        op = None
        if token.code != dlimeterDict[':=']:
            raise gramException(token.row_i, "赋值符错误")
        else:
            op = token.context

        token = next(it)
        # 进入算术表达式
        arg1, token = ar_exp(token)
        gen(op, arg1, None, res)
        # 离开算术表达式
        return token

    # <算术表达式> →<项>+ <算术表达式>│<项>-<算术表达式>│<项>
    def ar_exp(token):
        # 返回value

        value, token = ar_term(token)
        # [此时token踩在 + 或 - 上]或者已经离开了算术表达式

        while token.code == dlimeterDict['+'] or token.code == dlimeterDict['-']:
            # [此时token踩在+ 或-上]
            # 计算新返回值
            op = token.context
            token = next(it)
            right_fac, token = ar_term(token)
            tmp = talloc()
            gen(op, value, right_fac, tmp)
            value = tmp

        return value, token

    # <项> → <因子> * <项>│<因子> / <项>│<因子>
    def ar_term(token):
        # 返回value
        value, token = ar_fac(token)
        # [此时token可能踩在* 或/上]或已经离开了项
        while token.code == dlimeterDict['*'] or token.code == dlimeterDict['/']:
            # [此时token踩在* 或/上]
            # 计算新返回值
            op = token.context
            token = next(it)
            right_fac, token = ar_fac(token)
            tmp = talloc()
            gen(op, value, right_fac, tmp)

            # 更新新返回值
            value = tmp

        # 离开项
        return value, token

    # <因子> → <算术量>│- <因子>
    # 算术量> → <整数>│<标识符>│（ <算术表达式> ）
    def ar_fac(token):
        # 返回value
        value = None
        if token.code == Identifier_Code:
            # 标识符
            if not token.context in varDict:
                raise gramException(token.row_i, "未定义的标识符")
            value = token.context
        elif token.code == Integer_Code:
            # 整数
            value = token.context
        elif token.code == dlimeterDict['(']:
            # (算术表达式)
            token = next(it)
            value, token = ar_exp(token)
            if token.code != dlimeterDict[')']:
                raise gramException(token.row_i, "缺少右括号")

        elif token.code == dlimeterDict['-']:
            # 负号
            token = next(it)
            value, token = ar_term(token)
            tmp = talloc()
            gen('-', value, None, tmp)
            value = tmp
        else:
            raise gramException(token.row_i, "?????")

        # 离开因子
        token = next(it)
        return value, token

    # 序号为0，则为空链
    # 合并链
    # ????
    def merge(qti, qtj):
        qti = int(qti)
        qtj = int(qtj)
        if qtj == 0:
            return qti
        else:
            k = qtj
            while qTupleList[k].res != 0:
                k = qTupleList[k].res
            qTupleList[k].res = qti
            return qtj

    # 回填出口
    # 把p为链首的四元式链的四元式的跳转口均换成t
    def backpatch(qtp, t):
        while qtp != 0:
            i = int(qTupleList[qtp].res)
            qTupleList[qtp].res = t
            qtp = i

    # <布尔表达式> → <布尔项> or <布尔表达式>│<布尔项>
    def bool_exp(token):
        trueEx_term, falseEx_term, token = bool_term(token)
        if token.code == reservedWordDict['or']:
            # 回填假出口
            backpatch(falseEx_term, len(qTupleList))
            token = next(it)
            trueEx_exp, falseEx_exp, token = bool_exp(token)
            # 合并真出口
            trueEx_term, falseEx_term = merge(trueEx_term, trueEx_exp), falseEx_exp
        return trueEx_term, falseEx_term, token

    # <布尔项> → <布因子> and <布尔项>│<布因子>
    def bool_term(token):

        trueEx_fac, falseEx_fac, token = bool_fac(token)

        if token.code == reservedWordDict['and']:
            # 回填真出口
            backpatch(trueEx_fac, len(qTupleList))

            token = next(it)
            trueEx_term, falseEx_term, token = bool_term(token)
            # 合并假出口
            trueEx_fac, falseEx_fac = trueEx_term, merge(falseEx_fac, falseEx_term)

        return trueEx_fac, falseEx_fac, token

    # <布因子> → <布尔量>│not <布因子>
    def bool_fac(token):
        trueEx, falseEx = None, None
        if token.code == reservedWordDict['not']:

            token = next(it)
            falseEx, trueEx, token = bool_fac(token)
        else:
            trueEx, falseEx, token = bool_val(token)
        return trueEx, falseEx, token

    # <布尔量> → <布尔常量>│<标识符>│（ <布尔表达式> ）│
    # <标识符> <关系符> <标识符>│<算术表达式> <关系符> <算术表达式>

    def bool_val(token):
        trueEx, falseEx = None, None
        if token.code == reservedWordDict['true']:
            trueEx, falseEx = len(qTupleList), 0
            gen('j', None, None, 0)
            token = next(it)
        elif token.code == reservedWordDict['false']:
            trueEx, falseEx = 0, len(qTupleList)
            gen('j', None, None, 0)
            token = next(it)
        elif token.code == dlimeterDict['(']:
            token = next(it)
            trueEx, falseEx, token = bool_exp(token)
            if token != dlimeterDict[')']:
                raise gramException(token.row_i, "缺少右括号")
            token = next(it)
        else:
            # 关系表达式
            trueEx, falseEx, token = re_exp(token)

        return trueEx, falseEx, token

    def re_exp(token):
        value1, token = ar_exp(token)

        tureEx, falseEx = None, None
        if token.code in {dlimeterDict['<'], dlimeterDict['<>'], dlimeterDict['<='], dlimeterDict['>='],
                          dlimeterDict['>'], dlimeterDict['=']}:
            op = 'j' + token.context
            token = next(it)
            value2, token = ar_exp(token)
            # 真出口
            tureEx = len(qTupleList)
            gen(op, value1, value2, 0)

            # 假出口
            falseEx = len(qTupleList)
            gen('j', None, None, 0)

        return tureEx, falseEx, token

    def if_stm(token):
        # [此时token踩在if上]
        token = next(it)

        trueEx, falseEx, token = bool_exp(token)

        # 回填真出口
        backpatch(trueEx, len(qTupleList))

        # [此时token踩在then上]
        if token.code != reservedWordDict['then']:
            raise gramException(token.row_i, "缺少then")

        token = next(it)

        if_quit = falseEx

        # 执行语句
        stm1_quit, token = stm(token)

        if token.code == reservedWordDict['else']:

            tmp = len(qTupleList)
            # 无条件转移
            gen('j', None, None, 0)

            # 回填出口
            backpatch(if_quit, len(qTupleList))
            # [此时token踩在else上]

            token = next(it)
            stm2_quit, token = stm_lis(token)
            qui = merge(merge(tmp, stm1_quit), stm2_quit)
        else:
            qui = merge(if_quit, stm1_quit)

        return qui, token

    def while_stm(token):
        # [此时token踩在while上]
        token = next(it)
        codebegin = len(qTupleList)
        trueEx, falseEx, token = bool_exp(token)

        backpatch(trueEx, len(qTupleList))

        # [此时token踩在do上]
        if token.code != reservedWordDict['do']:
            raise gramException(token.row_i, "缺少do")
        token = next(it)

        # 执行语句
        stm_quit, token = stm(token)
        backpatch(stm_quit, codebegin)
        gen('j', None, None, codebegin)

        qui = falseEx
        return qui, token

    def repeat_stm(token):
        # [此时token踩在repeat上]

        token = next(it)
        codebegin = len(qTupleList)
        # 执行语句
        stm_quit, token = stm(token)

        # [此时token踩在until上]
        if token.code != reservedWordDict['until']:
            raise gramException(token.row_i, "缺少until")
        else:
            token = next(it)

        backpatch(stm_quit, len(qTupleList))

        trueEx, falseEx, token = bool_exp(token)

        #  回填假出口
        backpatch(falseEx, codebegin)

        qui = trueEx

        return qui, token

    def stm(token):
        qui = 0
        if token.code == Identifier_Code:
            # 赋值句
            qui, token = 0, assign(token)
        elif token.code == reservedWordDict['if']:
            # if 句
            qui, token = if_stm(token)

        elif token.code == reservedWordDict['while']:
            # while 句
            qui, token = while_stm(token)

        elif token.code == reservedWordDict['repeat']:
            # repeat 句
            qui, token = repeat_stm(token)
        else:
            # 剩下的是复合语句
            # [此时token踩在begin上]
            qui, token = com_stm(token)

        return qui, token

    def stm_lis(token):

        while True:
            # 语句部分开始
            qui, token = stm(token)
            # 语句部分结束

            # [此时token可能踩在end或;上]
            # 如果是end则结束语句表,如果是;,则继续
            if token.code == dlimeterDict[';']:
                backpatch(qui, len(qTupleList))
                token = next(it)
            else:
                # end
                break

        # [此时token踩在end上]
        return qui, token

    def com_stm(token):
        # [此时token踩在begin上]
        if token.code != reservedWordDict['begin']:
            raise gramException(token.row_i, "缺少begin")
        token = next(it)

        # 进入语句表部分
        qui, token = stm_lis(token)
        # 　离开语句表部分
        # [此时token踩在end上]
        if token.code != reservedWordDict['end']:
            raise gramException(token.row_i, "缺少end")

        return qui, token

    # 递归下降
    def recursiveDescent():
        try:
            token = next(it)
            # [此时token踩在prgram上]
            # 程序头部开始
            if token.code != reservedWordDict['program']:
                raise gramException(token.row_i, "缺少program")
            token = next(it)
            if token.code != Identifier_Code:
                raise gramException(token.row_i, "缺少程序名")
            programName = token.context
            token = next(it)
            # [此时token踩在;上]
            if token.code != dlimeterDict[';']:
                raise gramException(token.row_i, "缺少;")

            gen("program", programName, None, None)
            token = next(it)
            # 程序头部结束

            # [此时token可能踩在var上]
            # 变量说明开始
            if token.code == reservedWordDict['var']:
                token = next(it)
                # 变量定义开始
                token = var_def(token)
            # 变量说明结束

            # [此时token踩在begin上]
            # 可执行部分开始
            if token.code == reservedWordDict['begin']:

                # 进入复合语句部分
                qui, token = com_stm(token)
            else:
                raise gramException(token.row_i, "缺少begin")

            # [此时token踩在end上]
            if token.code != reservedWordDict['end']:
                raise gramException(token.row_i, "缺少end")

            token = next(it)
            # 可执行部分结束

            # [此时token踩在.上]
            # 程序结尾开始
            if token.code == dlimeterDict['.']:
                # 回填所有出口
                backpatch(qui, len(qTupleList))
                gen("sys", None, None, None)
            else:
                raise gramException(token.row_i, "缺少.")
            # 程序结尾结束
            # 结束分析
            return

        # 结束迭代，终止分析
        except lexException as el:
            stderr.write(str(el) + '\n')
        except gramException as eg:
            stderr.write(str(eg) + '\n')
        # 非正常结束迭代
        except StopIteration:
            stderr.write("语法错误:缺少程序结尾" + '\n')

    recursiveDescent()
    return qTupleList


if __name__ == '__main__':
    pass
    # for qT in genQs():
    #   print(qT)
