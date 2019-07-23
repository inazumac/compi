from gramm import genqs
from gramm import Qtuple
from lexx import scan
from lexx import simplified_scan

# lines为一行一行





def regularizedPrintScan(lines):
    for i,bTuple in enumerate(simplified_scan(lines)):
        print(bTuple,end=' ')
        if (i+1)%5==0:
            print()
    if (i+1)%5!=0:
        print()

def regularizedPrintGenqs(lines):
    for qTuple in genqs(lines):
        print(qTuple)

def printHeader():
    print('高凯祁','15计科2',201530541272)



def fromFile(option,filename):
    with open(filename+'.txt','r',newline='') as file:
        lines = file.readlines()
        option(lines)



if __name__ == '__main__':
    printHeader()
    while True:
        options=input("输入lex [文件名]进入词法分析，输入gram [文件名]进入语法分析（文件放入项目同目录）:").split(" ")
        if options[0]=='lex':
            fromFile(regularizedPrintScan,options[1])
        elif options[0]=='gram':
            fromFile(regularizedPrintGenqs,options[1])
        else:
            pass
