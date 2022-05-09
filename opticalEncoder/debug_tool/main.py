from serial import Serial, SerialException
from matplotlib import pyplot as plt
import numpy as np

com_port = 'COM10'
obraz = np.zeros((296, 400))
fig,ax = plt.subplots(1, 1)
moj_obraz = None
plt.ion()
plt.show()

try:
    ser = Serial(port=com_port, baudrate=1000000, timeout=None)
except SerialException:
    print(f"No serial device on port {com_port}")
    exit(0)

while True:
    message = ser.readline() #.decode('UTF-8').rstrip()
    if not message:
        continue

    # print(message)
    text_message = message.decode('UTF-8').rstrip()
    print(text_message)
    if text_message == 'IMG':
        image_size = int(ser.readline().decode('UTF-8').rstrip())
        print(f"Image size = {image_size}")
        bytes = ser.read(400)
        bytes = bytearray(bytes)
        i=0
        while len(bytes) < image_size:
            bytes += ser.read(400)
            print(f"read {i}, len = {len(bytes)}")
            i+=1
        print(len(bytes))
        ser.write("ACK\n".encode())
        image_list = list(bytes)
        # blue = []
        # for i in range(0, 296*400):
        #     b1 = image_list[2*i]
        #     b2 = image_list[2*i + 1]
        #
        #     #
        #     # uint16_t
        #     # c = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3);
        #     # o[ix2 + 1] = c >> 8;
        #     # o[ix2] = c & 0xff;
        #
        #     r = (b1 & 0b11111000) >> 3
        #     g = (((b1 & 0b00000111) << 5) | ((b2 & 0b11100000) >> 5)) >> 3
        #     b = (b2 & 0b00011111)
        #
        #
        #
        #     # Compose into one 3-dimensional matrix of 8-bit integers
        #     # rgb = np.dstack((r, g, b)).astype(np.uint8)
        #     # r =
        #     # b1 = 256*image_list[2*i]
        #     # b2 = image_list[2*i+1]
        #
        #     blue.append(r+g+b)
        #
        # image = np.array(blue)
        # print(f"Shape of blue = {image.shape}")
        image = np.reshape(image_list, (296, 400))
        print(f"Shape of blue = {image.shape}")
        # image = np.bitwise_and(image, 31)
        print(image[:10, :10])
        im_max = np.max(image)
        im_min = np.min(image)
        print(f"Max = {im_max}, min = {im_min}")
        print(f"image dim = {image.shape}")

        if moj_obraz is None:
            moj_obraz = ax.imshow(image, vmin=0, vmax=96, cmap='gray')
        else:
            moj_obraz.set_data(image)
        fig.canvas.draw()
        plt.pause(1)
        # image = []
        # for i in range(0, 296):
        #     image.append(ser.read(400))
        #     print(f"Read line {i}")
        # # print("image read!")

plt.ioff()
plt.show()