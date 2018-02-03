from memories import CardReader, Screen, Memories

# Initiate card reader
card_reader = CardReader('ABCDEF0123')
screen = Screen()
memory = Memories(card_reader, screen)
memory.setup()

while 1:
    memory.run()
