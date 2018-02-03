import random
import time
import threading
import sys
import signal
import RPi.GPIO as GPIO
import MFRC522
import ConfigParser
import omxplayer
import pygame
import os
from pygame.locals import *

#set up GPIO
GPIO.setmode(GPIO.BCM)
#set up a button connected between P4 and GND
#was used for testing but might come in handy for something
# GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_UP)

media_dir = "/home/pi/videos/"

#global vars for card status, manipulated by card_check_thread
card_present = False
card_insert_time = 0.0
card_id = "ABCDEF0123"

#will be set to true when video is playing
playing = False

#load configuration options for the video player from config.ini
config = ConfigParser.SafeConfigParser()
config.read('config.ini')

#create an instance of the video player class
player = omxplayer.create_player(config)

#create an instance of the MFRC522 class 
READER = MFRC522.MFRC522()

#utility function to convert a a 5-byte array (the mifare card UID)
#to a 10 character string of hex values - this is our 'card ID' 
#that will be referenced throughout the programme 
def uid_to_hex_string(uid):
    ret = ""
    for byte in uid:
        ret = ret+format(byte,'x')
    return ret.upper()

#uses the MFRC522 library to poll the RFID card reader
#returns False if no card present or a string containing the card ID
#if a card is readable 
def read_card():
    tag_read = False
    (status, TagType) = READER.MFRC522_Request(READER.PICC_REQIDL)
    if status != READER.MI_OK:
        return False
    (status, uid) = READER.MFRC522_Anticoll()
    if status != READER.MI_OK:
        return False
    status = READER.MFRC522_Auth(READER.PICC_AUTHENT1A, 11, [0xFF,0xFF,0xFF,0xFF,0xFF,0xFF], uid)
    READER.MFRC522_StopCrypto1()
    return uid_to_hex_string(uid)

#run in the background as a daemon thread, calls read_card and updates
#status globals 
def card_check_thread():
    global card_present, card_insert_time, card_id
    while 1:
        card = read_card()
        if card and not card_present:
            #this is a new card
            card_present = True
            #update the number here
            card_insert_time = time.time()
            #get the id 
            card_id = card
        if not card and card_present:
            #no card present
            card_present = False
        time.sleep(0.2)

#quit function, tidies up and exits cleanly 
#called by system interrupts and pygame when esc key is pressed
def quit():
    pygame.quit()
    GPIO.cleanup()
    if player.is_playing():
        player.stop()
    print('\nBye!')
    sys.exit(0)

#called by signal, executes on SIGINT or SIGTERM (ctrl-c)
def exit_handler(signal, frame):
    quit()

#utility function to blank the screen using pygame
def blank_screen():
    screen.fill((0,0,0))
    pygame.display.update()

#displays a welcome screen
def welcome_screen():
    blank_screen()
    text = big_font.render("Insert A Card To Begin", True, (255, 255, 255))
    screen.blit(text, (size[0] // 2 - text.get_width() // 2, size[1] // 2 - text.get_height() // 2))
    pygame.display.flip()

#error screen - used when no media matches the inserted card ID 
def error_no_content():
    blank_screen()
    text_a = big_font.render("Content Not Found", True, (255,255,255))
    text_b = small_font.render("Card ID: %s"%card_id, True, (255,255,255))
    screen.blit(text_a, (size[0] // 2 - text_a.get_width() // 2, size[1] // 2 - text_a.get_height() // 2))
    screen.blit(text_b, (size[0] // 2 - text_b.get_width() // 2, size[1] // 2 + 150 - text_b.get_height() // 2))
    pygame.display.flip()

#finds media associated with a card id
#returns full file path if media is found, or False if not
def validate_card(id):
    file = media_dir+id+".mp4"
    print(file)
    if os.path.isfile(file):
        return file
    else:
        return False

#begins running the card checking thread
t = threading.Thread(target=card_check_thread)
t.daemon = True
t.start()

#attaches handler function to interrupts
signal.signal(signal.SIGINT, exit_handler)
signal.signal(signal.SIGTERM, exit_handler)

#initialises pygame for GUI
pygame.display.init()
pygame.font.init()
pygame.mouse.set_visible(False)
size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
small_font = pygame.font.Font(None, 50)
big_font   = pygame.font.Font(None, 200)

#display the welcome screen
welcome_screen()

while 1:
    # check if card present/not present
    if card_present and not playing:
        playing = True
        #validate the card and get the media filename
        media_file = validate_card(card_id)
        if media_file:
            #print some debug info to console
            print("Begin playing %d"%card_insert_time)
            #begin playing
            player.play(media_file,loop=1)
        else:
            #no corresponding media file found, show error message
            error_no_content()
    if not card_present and playing:
        playing = False
        print("Stopped playing")
        player.stop()
        welcome_screen()
    
    #handle pygame events (quit)
    for event in pygame.event.get():
        if event.type == QUIT:
            quit()
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                quit()
    time.sleep(0.2)