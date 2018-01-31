import random
import time
import threading
import sys
import signal
import RPi.GPIO as GPIO
import ConfigParser
import omxplayer
import pygame
from pygame.locals import *

GPIO.setmode(GPIO.BCM)
GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_UP)

card_present = False
card_insert_time = 0.0
card_id = "ABCDEF01"

playing = False

# Load the configuration.
config = ConfigParser.SafeConfigParser()
config.read('config.ini')
#print(config.get('omxplayer','sound'))

player = omxplayer.create_player(config)

def card_check_thread():
    global card_present, card_insert_time
    while 1:
        if not GPIO.input(4) and not card_present:
            #this is a new card
            card_present = True
            #update the number here
            card_insert_time = time.time()
        if GPIO.input(4) and card_present:
            #no card present
            card_present = False
        time.sleep(0.2)

def quit():
    pygame.quit()
    GPIO.cleanup()
    if player.is_playing():
        player.stop()
    print('\nBye!')
    sys.exit(0)

def exit_handler(signal, frame):
    quit()

def blank_screen():
    screen.fill((0,0,0))
    pygame.display.update()

def welcome_screen():
    blank_screen()
    text = big_font.render("Insert A Card To Begin", True, (255, 255, 255))
    screen.blit(text, (size[0] // 2 - text.get_width() // 2, size[1] // 2 - text.get_height() // 2))
    pygame.display.flip()

def error_no_content():
    blank_screen()
    text_a = big_font.render("Content Not Found", True, (255,255,255))
    text_b = small_font.render("Card ID: %s"%card_id, True, (255,255,255))
    screen.blit(text_a, (size[0] // 2 - text_a.get_width() // 2, size[1] // 2 - text_a.get_height() // 2))
    screen.blit(text_b, (size[0] // 2 - text_b.get_width() // 2, size[1] // 2 + 150 - text_b.get_height() // 2))
    pygame.display.flip()

def validate_card(id):
    #validate the card here
    return True

t = threading.Thread(target=card_check_thread)
t.daemon = True
t.start()

signal.signal(signal.SIGINT, exit_handler)
signal.signal(signal.SIGTERM, exit_handler)

#init pygame
pygame.display.init()
pygame.font.init()
pygame.mouse.set_visible(False)
size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
small_font = pygame.font.Font(None, 50)
big_font   = pygame.font.Font(None, 200)

welcome_screen()
# error_no_content()

while 1:
    # check if card present/not present
    if card_present and not playing:
        playing = True
        #validate the card
        if validate_card(card_id):
            print("Begin playing %d"%card_insert_time)
            player.play("01.mp4",loop=1)
        else:
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