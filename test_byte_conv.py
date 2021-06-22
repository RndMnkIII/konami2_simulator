#byte conversion to integer

import array as arr

ba= arr.array('B', [0x80, 0x01])

ba[0]=0xff

#modificar array

# print(ba)

# print(type(ba[0]))

#forma incorrecta de concatenar varios bytes para formar valor: devuelve 10000
#print('Address: {:04x}'.format(ba[0]<<8 + ba[1]))

#Forma correcta de concatenar varios bytes para formar valor: 8001
print('Address: {:04x}'.format(int.from_bytes(ba[0:2].tobytes(), byteorder='big', signed=False)))


offset = int.from_bytes(ba[0:1].tobytes(), byteorder='big', signed=False)
print('Unsigned 8 bit:{}'.format(offset))

offset = int.from_bytes(ba[0:1].tobytes(), byteorder='big', signed=True)
print('Signed 8 bit:{}'.format(offset))


offset = int.from_bytes(ba[0:2].tobytes(), byteorder='big', signed=False)
print('Big-endian unsigned 16 bit:{}'.format(offset))

offset = int.from_bytes(ba[0:2].tobytes(), byteorder='little', signed=False)
print('Little-endian unsigned 16 bit:{}'.format(offset))

offset = int.from_bytes(ba[0:2].tobytes(), byteorder='big', signed=True)
print('Big-endian signed 16 bit:{}'.format(offset))

offset = int.from_bytes(ba[0:2].tobytes(), byteorder='little', signed=True)
print('Little-endian signed 16 bit:{}'.format(offset))