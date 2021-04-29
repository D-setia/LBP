from Crypto.Util import number

p = number.getPrime(512)
q = number.getPrime(512)

n = p*q
phi = (p-1)*(q-1)

e = pow(2, 16) + 1
d = pow(e, -1, phi)

opFile = open("authKey.txt", 'w');
opString = ""

opString = opString + str(e) + ";;" + str(d) + ";;" + str(n) 
opFile.write(opString)

opFile.close()

