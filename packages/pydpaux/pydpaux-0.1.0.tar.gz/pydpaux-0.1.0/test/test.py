import pydpaux
import sys

name = sys.argv[1] if len(sys.argv) > 1 else ""

if name:
    display = pydpaux.find_display_by_name(name)
    if not display:
        print (f"No display named {name}")
        exit()
else:
    displays = pydpaux.get_displays()
    if not displays:
        print (f"No display found")
        exit()
    
    display = displays[0]

print (f"Found display: {display.name}")

# Copied from Intel document:
#
# I2C WRITE : 82 01 10 AC at adddress 6E and subaddress 51
# If we write these BYTEs ( 82 01 10  AC) to adddress 6E and
# subaddress 51, it should update the current brightness to the 10th
# byte at adddress 6E and subaddress 51. One can verify by changing
# panel brightness from panel buttons and the writing to adddress 6E
# and subaddress 51 ( 82 01 10  AC), and then reading 10th byte at
# adddress 6E and subaddress 51. For Example : The following 11 byte
# values should be shown by the I2C Read post I2C write. Values are
# 6E 88 02 00 10 00 00 64 00 19 D9.  (If HDMI panel brightness is set
# to 25%) 10th byte value is current  brightness value of the
# panel.To confirm that value is correct or not, convert the Hex
# value to Decimal.

#Seems not working -->
#code = display.i2c_write(0x6e, 0x51, [0x82, 0x01, 0x10, 0xac])
#if (code):
#    print (f'Error on write: 0x{code:08x}')
#else:
#    print (f"read 11 bytes: {display.i2c_read(0x6e, 0x51, 11)}")

print ("\nTest EDID read with i2c_read():")
print ( ", ".join(map(lambda x : f'0x{x:02x}', display.i2c_read(0xa0, 0x00, 8))))
print ("\n")

print ("Test DPCD read with aux_read():")
for addr in [0x00, 0x01, 0x02, 0x03, 0x0C, 0x22, 0x101]:
    print (f"0x{addr:04x}: 0x{display.aux_read(addr, 1)[0]:02x}")

print ("Test result OK.")
