#!/usr/bin/env python3
#
# Documentation for the streamdeck library
# https://python-elgato-streamdeck.readthedocs.io/en/stable/index.html
# 
# Needed:
# - Python 3.9
# - Python-Elgato-Streamdeck library
# - Pillow
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
deckid = r"\\?\hid#vid_0fd9&pid_0060#7&2733624f&0&0000#{4d1e55b2-f16f-11cf-88cb-001111000030}"




# Generates the key images
def render_key_image(deck, icon_filename, font_filename, label_text, key):

    icon = Image.open(icon_filename)

    # Resize the image to the key size without a label
    if key in stat_key_index:
        image = PILHelper.create_scaled_image(deck, icon, margins=[0, 0, 0, 0])

    # Resive the image to the key size with a label beneath
    else:
        image = PILHelper.create_scaled_image(deck, icon, margins=[0, 0, 20, 0])

        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()
        label_w, label_h = draw.textsize(label_text, font=font)
        label_pos = ((image.width - label_w) // 2, image.height - 20)
        draw.text(label_pos, text=label_text, font=font, fill="white")

    return PILHelper.to_native_format(deck, image)


# Style info for image generator for keys
def get_key_style(deck, key, state):

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
        resp1 = requests.get('http://10.201.37.151:8000/session_status')
        json1 = resp1.json()
        name = "CC1 Status"
        icon = "{}.png".format("SqGreen" if json1["session_status"] == "1" else "SqRed")
        font = "Roboto-Regular.ttf"
        label = "CC1 Status"
    elif key in cc2_key_index: 
        resp2 = requests.get('http://10.201.37.150:8000/session_status')
        json2 = resp2.json()
        name = "CC2 Status"
        icon = "{}.png".format("SqGreen" if json2["session_status"] == "1" else "SqRed")
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
def update_key_image(deck, key, state):
    key_style = get_key_style(deck, key, state)
    image = render_key_image(deck, key_style["icon"], key_style["font"], key_style["label"], key)

    # Ensure nothing else using deck, then update the image
    with deck:
        deck.set_key_image(key, image)


# Prints key state change information, updates the key image and performs any
# associated actions when a key is pressed.
def key_change_callback(deck, key, state):
    # Logging keypresses
    print("Deck {} Key {} = {}".format(deck.id(), key, state), flush=True)

    update_key_image(deck, key, state)

    # Actions to run if key is pressed
    if state:
        key_style = get_key_style(deck, key, state)
        if key == cc1on_key_index:
            tel2 = telnetlib.Telnet(b"wgme-ibm-cc1", 5000)
            tel2.write(b"START\n")
            tel2.write(b"exit\n")
        if key == cc1off_key_index:
            tel2 = telnetlib.Telnet(b"wgme-ibm-cc1", 5000)
            tel2.write(b"STOP\n")
            tel2.write(b"exit\n")
        if key == cc2on_key_index:
            tel2 = telnetlib.Telnet(b"wgme-ibm-cc2", 5000)
            tel2.write(b"START\n")
            tel2.write(b"exit\n")
        if key == cc2off_key_index:
            tel2 = telnetlib.Telnet(b"wgme-ibm-cc2", 5000)
            tel2.write(b"STOP\n")
            tel2.write(b"exit\n")
        if key_style["name"] == "exit":
            # Ensure nothing else using deck
            with deck:
                deck.reset()
                # Update deck to show the CC launch image after resetting
                update_key_image(deck, launch_key, False)
                deck.close()


if __name__ == "__main__":
    streamdecks = DeviceManager().enumerate()
    print("Found {} Stream Deck(s).\n".format(len(streamdecks)))
    for index, deck in enumerate(streamdecks):
        print (deck.id())
        if deck.id() == deckid:
            deck.open()
            deck.reset()

            print("Opened '{}' device (serial number: '{}')".format(deck.deck_type(), deck.get_serial_number()))

            # Screen brightness and image initialization
            deck.set_brightness(brightness)
            for key in range(deck.key_count()):
                update_key_image(deck, key, False)

            # Function to run on key press
            deck.set_key_callback(key_change_callback)

            while True:
                for i in cc1_key_index:
                    update_key_image(deck, i, False)
                for i in cc2_key_index:
                    update_key_image(deck, i, False)
                time.sleep(1)

            # Wait until all application threads have terminated (for this example,
            # this is when all deck handles are closed).
            for t in threading.enumerate():
                if t is threading.currentThread():
                    continue

                if t.is_alive():
                    t.join()