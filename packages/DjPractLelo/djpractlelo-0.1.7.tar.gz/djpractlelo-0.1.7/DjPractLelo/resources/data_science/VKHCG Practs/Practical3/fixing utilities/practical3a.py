import string
import datetime as dt

print('Removing leading or lagging spaces from a data');
mydata = "       Hello My name is Mikka Singh "
print('Original Data:',mydata)
cleandata=mydata.lstrip()
print('After Cleaning:',cleandata)


print('Removing bad characters from a data')
charachter_set = set(string.ascii_letters + string.digits + ' ')
badlink=r'Data\+0+0Science with\+0+2 funny charac*ters is \+10b+ad!!!'
cleanlink = ''.join([char for char in badlink if char in charachter_set])
print('Bad Data : ',badlink);
print('Clean Data : ',cleanlink)


print('Convert YYYY/MM/DD to DD Month YYYY.')
baddate = dt.date(2004,4,3)
baddata=format(baddate,'%Y-%m-%d')
gooddate = dt.datetime.strptime(baddata,'%Y-%m-%d')
gooddata=format(gooddate,'%d %B %Y')
print('Bad Data : ',baddata)
print('Good Data : ',gooddata)
