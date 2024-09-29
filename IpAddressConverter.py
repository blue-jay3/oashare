def IP4ToUInt(string):
    numbers = string.split(".")
    integer =0
    integer += int(numbers[0])*256*256*256
    integer += int(numbers[1])*256*256
    integer += int(numbers[2])*256
    integer += int(numbers[3])
    return integer

def uIntToIP4(integer):
    num1 = integer % 256
    num2 = (integer)//256 % 256
    num3 = (integer)// (256*256) %256 
    num4 = (integer)//(256*256*256)%256
    return str(num4) +"."+ str(num3)+"."+str(num2) +"."+ str(num1)



print(IP4ToUInt("192.168.1.1"))
print(uIntToIP4(3232235777))
