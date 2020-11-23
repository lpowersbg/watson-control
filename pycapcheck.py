#!/usr/bin/env python3
#
# Need help? Contact:
# Liam Power
# lpower@sbgtv.com
# 207-228-7650
#
# Documentation for the streamdeck library
# https://python-elgato-streamdeck.readthedocs.io/en/stable/index.html
# 
# Needed:
# - Python 3.9 https://www.python.org/ 
# - Python-Elgato-Streamdeck library https://python-elgato-streamdeck.readthedocs.io/en/stable/index.html 
# - Pillow https://pillow.readthedocs.io/en/stable/ 
# - Requests https://requests.readthedocs.io/en/master/ 
# - hidapi: Copy download into the python folder. Ensure 64 bit used if 64 bit. https://github.com/libusb/hidapi/releases 

import os
import threading
import requests
import telnetlib
import time

from PIL import Image, ImageDraw, ImageFont
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper

# Image locations
ASSETS_PATH = os.path.join(os.path.dirname(__file__), "Assets")
# Key Location Settings
exit_key_index = 2
cc1on_key_index = 13
cc1off_key_index = 14
cc2on_key_index = 10
cc2off_key_index = 11
cc1_key_index = [3,4,8,9]
cc2_key_index = [0,1,5,6]
launch_key = 7
# Keys Without Labels
stat_key_index = [3,4,8,9,0,1,5,6,12,2]
# Deck Settings
brightness = 50
deckid = r"STREAMDECK ID BETWEEN QUOTES - SEE README"
cc1_host = "WATSON 1 HOST/IP BETWEEN QUOTES"
cc2_host = "WATSON 2 HOST/IP BETWEEN QUOTES"

#Grabs session_status from Watson API
def api_con(host):
    try:
        respwat = requests.get('http://' + host + ':8000/session_status')
        jsonwat = respwat.json()
        status = jsonwat["session_status"]
    except:
        print ("Host " + host + " failed API.")
        status = 0

    return status

#Starts/stops Watson, pass "START\n" or "STOP\n"
def tel_con(host, nogo):
    try:
        tel2 = telnetlib.Telnet(bytes(host, encoding='utf-8'), 5000, 1)
        tel2.write(bytes(nogo, encoding='utf-8'))
        tel2.write(b"exit\n")
    except:
        print ("Host " + host + " failed telnet.")

# Generates the key images
def render_key_image(deck, icon_filename, font_filename, label_text, key):

    icon = Image.open(icon_filename)

    # Resize the image to the key size without a label
    if key in stat_key_index:
        image = PILHelper.create_scaled_image(deck, icon, margins=[0, 0, 0, 0])

    # Resize the image to the key size with a label beneath
    else:
        image = PILHelper.create_scaled_image(deck, icon, margins=[0, 0, 20, 0])

        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()
        label_w, label_h = draw.textsize(label_text, font=font)
        label_pos = ((image.width - label_w) // 2, image.height - 20)
        draw.text(label_pos, text=label_text, font=font, fill="white")

    return PILHelper.to_native_format(deck, image)


# Style info for image generator for keys
def get_key_style(deck, key, state, stat1, stat2):

    if key == exit_key_index:
        name = "exit"
        icon = "{}.png".format("Exit")
        font = "Roboto-Regular.ttf"
        label = "Exit"
    elif key == cc1on_key_index: 
        name = "CC1 On"
        icon = "{}.png".format("ibm1on")
        font = "Roboto-Regular.ttf"
        label = "Start CC1"  
    elif key == cc1off_key_index: 
        name = "CC1 Off"
        icon = "{}.png".format("ibm1off")
        font = "Roboto-Regular.ttf"
        label = "Stop CC1" 
    elif key == cc2on_key_index: 
        name = "CC2 On"
        icon = "{}.png".format("ibm2on")
        font = "Roboto-Regular.ttf"
        label = "Start CC2" 
    elif key == cc2off_key_index: 
        name = "CC2 Off"
        icon = "{}.png".format("ibm2off")
        font = "Roboto-Regular.ttf"
        label = "Stop CC2"       
    elif key in cc1_key_index: 
        name = "CC1 Status"
        icon = "{}.png".format("SqGreen" if stat1 == "1" else "SqRed")
        font = "Roboto-Regular.ttf"
        label = "CC1 Status"
    elif key in cc2_key_index: 
        name = "CC2 Status"
        icon = "{}.png".format("SqGreen" if stat2 == "1" else "SqRed")
        font = "Roboto-Regular.ttf"
        label = "CC2 Status"  
    elif key == launch_key: 
        name = "CC Control"
        icon = "{}.png".format("SWCLogo")
        font = "Roboto-Regular.ttf"
        label = "CC Control" 
    else:
        name = "emoji"
        icon = "{}.png".format("logo")
        font = "Roboto-Regular.ttf"
        label = "Key {}".format(key)

    return {
        "name": name,
        "icon": os.path.join(ASSETS_PATH, icon),
        "font": os.path.join(ASSETS_PATH, font),
        "label": label
    }

# Updates the key image based on which key and whether it's pressed
def update_key_image(deck, key, state, stat1, stat2):
    key_style = get_key_style(deck, key, state, stat1, stat2)
    image = render_key_image(deck, key_style["icon"], key_style["font"], key_style["label"], key)

    # Ensure nothing else using deck, then update the image
    with deck:
        deck.set_key_image(key, image)


# Update the key image, then run any corresponding actions.
def key_change_callback(deck, key, state):
    stat1 = api_con(cc1_host)
    stat2 = api_con(cc2_host)
    update_key_image(deck, key, state, stat1, stat2)

    # Actions to run if key is pressed
    if state:
        key_style = get_key_style(deck, key, state, stat1, stat2)
        if key == cc1on_key_index:
            tel_con(cc1_host, "START\n")
        if key == cc1off_key_index:
            tel_con(cc1_host, "STOP\n")
        if key == cc2on_key_index:
            tel_con(cc2_host, "START\n")
        if key == cc2off_key_index:
            tel_con(cc2_host, "STOP\n")
        if key_style["name"] == "exit":
            # Ensure nothing else using deck
            with deck:
                deck.reset()
                # Update deck to show the CC launch image after resetting
                update_key_image(deck, launch_key, False, stat1, stat2)
                deck.close()

if __name__ == "__main__":
    streamdecks = DeviceManager().enumerate()
    print("Found {} Stream Deck(s).\n".format(len(streamdecks)))
    for index, deck in enumerate(streamdecks):
        deck.open()
        print("Located '{}' device (serial number: '{}', deck id: '{}')".format(deck.deck_type(), deck.get_serial_number(), deck.id()))
        deck.close()
        if deck.id() == deckid:
            deck.open()
            deck.reset()

            print("Opened '{}' device (serial number: '{}')".format(deck.deck_type(), deck.get_serial_number()))

            # Screen brightness and image initialization
            deck.set_brightness(brightness)
            for key in range(deck.key_count()):
                stat1 = api_con(cc1_host)
                stat2 = api_con(cc2_host)
                update_key_image(deck, key, False, stat1, stat2)

            # Function to run on key press
            deck.set_key_callback(key_change_callback)

            # Update status images every second
            while True:
                stat1 = api_con(cc1_host)
                stat2 = api_con(cc2_host)
                for i in cc1_key_index:
                    update_key_image(deck, i, False, stat1, stat2)
                for i in cc2_key_index:
                    update_key_image(deck, i, False, stat1, stat2)
                time.sleep(1)

            # Wait for all threads to end.
            for t in threading.enumerate():
                if t is threading.currentThread():
                    continue

                if t.is_alive():
                    t.join()

# Python-Elgato-Streamdeck used under MIT license:
#
# © Copyright 2020, Dean Camera
# Permission to use, copy, modify, and distribute this software
# and its documentation for any purpose is hereby granted without
# fee, provided that the above copyright notice appear in all
# copies and that both that the copyright notice and this
# permission notice and warranty disclaimer appear in supporting
# documentation, and that the name of the author not be used in
# advertising or publicity pertaining to distribution of the
# software without specific, written prior permission.
# 
# The author disclaims all warranties with regard to this
# software, including all implied warranties of merchantability
# and fitness.  In no event shall the author be liable for any
# special, indirect or consequential damages or any damages
# whatsoever resulting from loss of use, data or profits, whether
# in an action of contract, negligence or other tortious action,
# arising out of or in connection with the use or performance of
# this software.

# The Python Imaging Library (PIL) is
#
#     Copyright © 1997-2011 by Secret Labs AB
#     Copyright © 1995-2011 by Fredrik Lundh
#
# Pillow is the friendly PIL fork. It is
#
#     Copyright © 2010-2020 by Alex Clark and contributors
#
# Like PIL, Pillow is licensed under the open source HPND License:
#
# By obtaining, using, and/or copying this software and/or its associated
# documentation, you agree that you have read, understood, and will comply
# with the following terms and conditions:
#
# Permission to use, copy, modify, and distribute this software and its
# associated documentation for any purpose and without fee is hereby granted,
# provided that the above copyright notice appears in all copies, and that
# both that copyright notice and this permission notice appear in supporting
# documentation, and that the name of Secret Labs AB or the author not be
# used in advertising or publicity pertaining to distribution of the software
# without specific, written prior permission.
#
# SECRET LABS AB AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS
# SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS.
# IN NO EVENT SHALL SECRET LABS AB OR THE AUTHOR BE LIABLE FOR ANY SPECIAL, 
# INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM 
# LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE 
# OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR 
# PERFORMANCE OF THIS SOFTWARE.
