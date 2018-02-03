from memories import CardReader, Screen, Memories

# Initiate card reader
# I don't know if 'ABCDEF0123' is just a placeholder or will change,
# you could add it as a sysarg, or an optional sysarg with a fallback
card_reader = CardReader('ABCDEF0123')
screen = Screen()
memory = Memories(card_reader, screen)
memory.setup()

while 1:
    memory.run()
