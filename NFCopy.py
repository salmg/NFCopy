#!/usr/bin/python

#
# Modified by Salvador Mendoza (salmg.net)
# Visa MSD Beta version with APDU delay tracker
# Requieres RFIDIOt Library: https://github.com/AdamLaurie/RFIDIOt
# Original Code: https://github.com/AdamLaurie/RFIDIOt/blob/master/pn532emulate.py
#
# This code modification follows the original disclaimer:
# ----
#
#  pn532emulate.py - switch NXP PN532 reader chip into TAG emulation mode
# 
#  Adam Laurie <adam@algroup.co.uk>
#  http://rfidiot.org/
# 
#  This code is copyright (c) Adam Laurie, 2009, All rights reserved.
#  For non-commercial use only, the following terms apply - for all other
#  uses, please contact the author:
#
#    This code is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This code is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
import rfidiot
from rfidiot.pn532 import *
import sys
import os
from time import sleep, time


try:
	card= rfidiot.card
except:
	os._exit(True)

card.info('pn532emulate v0.1d')
if not card.readersubtype == card.READER_ACS:
	print '  Reader type not supported!'
	os._exit(True)

# switch off auto-polling (for ACS v1 firmware only) (doesn't seem to help anyway!)
#if not card.acs_send_apdu(card.PCSC_APDU['ACS_DISABLE_AUTO_POLL']):
#	print '  Could not disable auto-polling'
#	os._exit(True)

if card.acs_send_apdu(PN532_APDU['GET_PN532_FIRMWARE']):
	#print '  NXP PN532 Firmware:'
	pn532_print_firmware(card.data)

if card.acs_send_apdu(PN532_APDU['GET_GENERAL_STATUS']):
	pn532_print_status(card.data)

mode = '00'
sens_res = '0800'
uid = 'dc4420'
sel_res = '60'
felica = '01fea2a3a4a5a6a7c0c1c2c3c4c5c6c7ffff'
nfcid =  'aa998877665544332211'
last6 = '00'
last7 = '52464944494f7420504e353332'
MSDdata = '4006884501025442d24092010339000037556f'

try:
	lengt= ['%02x' % (len(last6) / 2)]
	gt= [last6]
except:
	lengt= ['00']
	gt= ['']
try:
	lentk= ['%02x' % (len(last7) / 2)]
	tk= [last7]
except:
	lentk= ['00']
	tk= ['']

#print '  Waiting for activation...'
card.acs_send_apdu(card.PCSC_APDU['ACS_LED_RED'])
status= card.acs_send_apdu(PN532_APDU['TG_INIT_AS_TARGET']+[mode]+[sens_res]+[uid]+[sel_res]+[felica]+[nfcid]+lengt+gt+lentk+tk)
#print status

if not status or not card.data[:4] == 'D58D':
		#print 'Target Init failed:', card.errorcode
		os._exit(True)
mode= int(card.data[4:6],16)
baudrate= mode & 0x70
class color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'
"""print '  Emulator activated:'
print '         UID: 08%s' % uid[0]
print '    Baudrate:', PN532_BAUDRATES[baudrate]
print '        Mode:',
if mode & 0x08:
	print 'ISO/IEC 14443-4 PICC'
if mode & 0x04:
	print 'DEP'
framing= mode & 0x03
print '     Framing:', PN532_FRAMING[framing]
print '   Initiator:', card.data[6:]
print
"""

print ' Waiting for a PoS/Terminal/ or something to make a payment...'
status= card.acs_send_apdu(PN532_APDU['TG_GET_DATA'])
if not status or not card.data[:4] == 'D587':
		print 'Target Get Data failed:', card.errorcode
		print 'Data:',card.data
		os._exit(True)
errorcode= int(card.data[4:6],16)
if not errorcode == 0x00:
	print 'Error:',PN532_ERRORS[errorcode]
	os._exit(True)


VISAMSD= [
	'6F23840E325041592E5359532E4444463031A511BF0C0E610C4F07A00000000310108701019000',
	'6F1E8407A0000000031010A513500B56495341204352454449549F38039F66029000',
    '80060080080101009000',
	'70155713' + MSDdata +'9000'
]

start_time = time()
after_apdu = 0
a = 0
while(a<7):
	terminal = card.data[6:]
	print 'Terminal: ', terminal
	if terminal == '00A404000E325041592E5359532E444446303100':
		sendd = VISAMSD[0]
	elif terminal == '00A4040007A000000003101000':
		sendd = VISAMSD[1]
	elif '80A80000048' in terminal:
		sendd = VISAMSD[2]
	elif '00B2' in terminal:
		sendd = VISAMSD[3]
	else:
		sendd = '6f00'

	print 'Card:', sendd, '\n----------'
	status= card.acs_send_apdu(PN532_APDU['TG_SET_DATA']+[sendd])
	status2= card.acs_send_apdu(PN532_APDU['TG_GET_DATA'])
	if after_apdu == 0:
		after_apdu = (time() - start_time) 
	else:
		after_apdu += (time() - (after_apdu+start_time))
    print color.RED + "Delay since last APDU: " + color.END + color.BOLD,
    print("%s" % (after_apdu))      
    print color.END
	a+=1


sleep(0.2)
if not status:
	os._exit(True)
else:
	os._exit(False)
