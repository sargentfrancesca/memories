import ConfigParser
import time
import threading
import sys
import signal
import RPi.GPIO as GPIO
import pygame
import os

from library import MFRC522, omxplayer
from pygame.locals import *

from utils import uid_to_hex_string

CONFIG = 'config.ini'
# media dir is a constant, as convention we use caps
MEDIA_DIR = '/media/pi/PI/'
# create an instance of the MFRC522 class
READER = MFRC522.MFRC522()


class CardReader():
    def __init__(self, card_id):
        self.card_id = None

    # global vars for card status, manipulated by card_check_thread
    card_present = False
    card_insert_time = 0.0
    card_present = False
    # set to true upon finding MEDIA_DIR
    usb_present = False
    t = None

    # checks for presence of video folder (i.e. usb drive is mounted)
    def check_for_usb(self):
        if os.path.isdir(MEDIA_DIR):
            return True
        else:
            return False

    # uses the MFRC522 library to poll the RFID card reader
    # returns False if no card present or a string containing the card ID
    # if a card is readable
    def read_card(self):
        # tag_read = False {This doesn't seem to be used?}
        (status, TagType) = READER.MFRC522_Request(READER.PICC_REQIDL)
        if status != READER.MI_OK:
            return False
        (status, uid) = READER.MFRC522_Anticoll()
        if status != READER.MI_OK:
            return False
        status = READER.MFRC522_Auth(READER.PICC_AUTHENT1A, 11, [0xFF,0xFF,0xFF,0xFF,0xFF,0xFF], uid)
        READER.MFRC522_StopCrypto1()
        return uid_to_hex_string(uid)

    # run in the background as a daemon thread, calls read_card and updates
    # status globals
    def card_check_thread(self):
        while 1:
            card = self.read_card()
            if card and not self.card_present:
                # this is a new card
                self.card_present = True
                # update the number here
                self.card_insert_time = time.time()
                # get the id
                self.card_id = card
            if not card and self.card_present:
                # no card present
                self.card_present = False
            time.sleep(0.2)

    # finds media associated with a card id
    # returns full file path if media is found, or False if not
    def validate_card(id):
        file = MEDIA_DIR + id + ".mp4"
        print(file)
        if os.path.isfile(file):
            return file
        else:
            return False

    def start_thread(self):
        # begins running the card checking thread
        t = threading.Thread(target=self.card_check_thread())
        t.daemon = True
        t.start()


class Screen():
    player = None
    # will be set to true when video is playing
    playing = False

    def configure_player(self):
        # load configuration options for the video player from config.ini
        config = ConfigParser.SafeConfigParser()
        config.read(CONFIG)
        return

    def setup_player(self):
        # set up GPIO
        GPIO.setmode(GPIO.BCM)
        # set up a button connected between P4 and GND
        # was used for testing but might come in handy for something
        # GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        config = self.configure()
        # create an instance of the video player class
        self.player = omxplayer.create_player(config)
        if self.player:
            return True
        else:
            return False

    # quit function, tidies up and exits cleanly
    # called by system interrupts and pygame when esc key is pressed
    def quit(self):
        pygame.quit()
        GPIO.cleanup()
        if self.player.is_playing():
            self.player.stop()
        print('\nBye!')
        sys.exit(0)

    # called by signal, executes on SIGINT or SIGTERM (ctrl-c)
    def exit_handler(self, signal, frame):
        quit()

    # utility function to blank the screen using pygame
    def blank_screen(self):
        screen.fill((0, 0, 0))
        pygame.display.update()

    # displays a welcome screen
    def welcome_screen(self):
        blank_screen()
        text = big_font.render("Insert A Card To Begin", True, (255, 255, 255))
        screen.blit(text, (size[0] // 2 - text.get_width() // 2, size[1] // 2 - text.get_height() // 2))
        pygame.display.flip()

    # error screen - used when no media matches the inserted card ID 
    def error_no_content(self):
        blank_screen()
        text_a = big_font.render("Content Not Found", True, (255,255,255))
        text_b = small_font.render("Card ID: %s"%card_id, True, (255,255,255))
        screen.blit(text_a, (size[0] // 2 - text_a.get_width() // 2, size[1] // 2 - text_a.get_height() // 2))
        screen.blit(text_b, (size[0] // 2 - text_b.get_width() // 2, size[1] // 2 + 150 - text_b.get_height() // 2))
        pygame.display.flip()

    # error screen - media folder not found (no USB inserted)
    def error_no_usb(self):
        blank_screen()
        text_a = big_font.render("No Media Drive Found", True, (255,255,255))
        text_b = small_font.render("Insert a USB drive with the volume label 'PI' and restart.", True, (255,255,255))
        screen.blit(text_a, (size[0] // 2 - text_a.get_width() // 2, size[1] // 2 - text_a.get_height() // 2))
        screen.blit(text_b, (size[0] // 2 - text_b.get_width() // 2, size[1] // 2 + 150 - text_b.get_height() // 2))
        pygame.display.flip()

    # initialises pygame for GUI
    def initiate_pygame(self):
        pygame.display.init()
        pygame.font.init()
        pygame.mouse.set_visible(False)
        size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
        screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
        small_font = pygame.font.Font(None, 50)
        big_font = pygame.font.Font(None, 200)


class Memories():
    def __init__(self, card_reader, screen):
        self.card_reader = card_reader
        self.screen = screen

    def initiate_startup_checks(self):
        # Make sure card reader is attached
        assertTrue(self.card_reader.t, "Thread is not running")
        # Make sure screen is attached
        assertTrue(self.screen.setup_player, "Player is not set up")

    def start_signal(self):
        # attaches handler function to interrupts
        signal.signal(signal.SIGINT, exit_handler)
        signal.signal(signal.SIGTERM, exit_handler)

    def setup(self):
        card.start_thread()

        # check card thread is running, player is set up,
        self.initiate_checks()
        self.start_signal()

        # Initiate Pygame
        player.initiate_pygame()
        # display the welcome screen
        player.welcome_screen()

    def run(self):
        # check for usb drive
        if not card.usb_present and card.check_for_usb():
            card.usb_present = True
        else:
            player.error_no_usb()

        # check if card present/not present ((player playing?))
        if card.usb_present and card.card_present and not player.playing:
            card.playing = True
            # validate the card and get the media filename
            media_file = card.validate_card(card_id)
            if media_file:
                # print some debug info to console
                print("Begin playing %d" % card.card_insert_time)
                # begin playing
                player.play(media_file, loop=1)
            else:
                # no corresponding media file found, show error message
                player.error_no_content()

        # if the card is present and we're still playing, stop playing
        if not card.card_present and player.playing:
            player.playing = False
            print("Stopped playing")
            player.stop()
            player.welcome_screen()

        # handle pygame events (quit)
        for event in pygame.event.get():
            if event.type == QUIT:
                quit()
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    quit()
        time.sleep(0.2)
