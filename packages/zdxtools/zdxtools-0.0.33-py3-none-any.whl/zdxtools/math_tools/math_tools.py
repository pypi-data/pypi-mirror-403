#数学方面的处理
class math_tools:
    #中文数字转阿拉伯数字
    @classmethod
    def chinesenum_alabo_num(cls,chinese):
        strNum = chinese
        result = 0
        temp = 1  # 存放一个单位的数字如：十万
        count = 0  # 判断是否有chArr
        cnArr = ['一', '二', '三', '四', '五', '六', '七', '八', '九']
        chArr = ['十', '百', '千', '万', '亿']
        for i in range(len(strNum)):
            b = True
            c = strNum[i]
            for j in range(len(cnArr)):
                if c == cnArr[j]:
                    if count != 0:
                        result += temp
                        count = 0
                    temp = j + 1
                    b = False
                    break
            if b:
                for j in range(len(chArr)):
                    if c == chArr[j]:
                        if j == 0:
                            temp *= 10
                        elif j == 1:
                            temp *= 100
                        elif j == 2:
                            temp *= 1000
                        elif j == 3:
                            temp *= 10000
                        elif j == 4:
                            temp *= 100000000
                    count += 1
            if i == len(strNum) - 1:
                result += temp
        return result
    #阿拉伯数字转中文
    @classmethod
    def alabo_num_chinesenum(cls,number):
        numdict = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "七", 8: "八", 9: "九", 0: "零"}  # 个位数的字典
        digitdict = {1: "十", 2: "百", 3: "千", 4: "万"}  # 位称的字典

        def maxdigit(number, count):
            num = number // 10  # 整除是//
            if num != 0:
                return maxdigit(num, count + 1)  # 加上return才能进行递归
            else:
                digit_num = number % 10  # digit_num是最高位上的数字
                return count, digit_num  # count记录最高位

        def No2Cn(number):
            max_digit, digit_num = maxdigit(number, 0)

            temp = number
            num_list = []  # 储存各位数字（最高位的数字也可以通过num_list[-1]得到
            while temp > 0:
                position = temp % 10
                temp //= 10  # 整除是//
                num_list.append(position)

            chinese = ""
            if max_digit == 0:  # 个位数
                chinese = numdict[number]
            elif max_digit == 1:  # 十位数
                if digit_num == 1:  # 若十位上是1，则称为“十几”，而一般不称为“一十几”（与超过2位的数分开讨论的原因）
                    chinese = "十" + numdict[num_list[0]]
                else:
                    chinese = numdict[num_list[-1]] + "十" + numdict[num_list[0]]
            elif max_digit > 1:  # 超过2位的数
                while max_digit > 0:
                    if num_list[-1] != 0:  # 若当前位上数字不为0，则加上位称
                        chinese += numdict[num_list[-1]] + digitdict[max_digit]
                        max_digit -= 1
                        num_list.pop(-1)
                    else:  # 若当前位上数字为0，则不加上位称
                        chinese += numdict[num_list[-1]]
                        max_digit -= 1
                        num_list.pop(-1)
                chinese += numdict[num_list[-1]]

            while chinese.endswith("零") and len(chinese) > 1:  # 个位数如果为0，不读出
                chinese = chinese[:-1]
            if chinese.count("零") > 1:  # 中文数字中最多只有1个零
                count_0 = chinese.count("零")
                chinese = chinese.replace("零", "", count_0 - 1)
            return chinese
        return  No2Cn(number = number)