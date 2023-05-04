#! /usr/bin/env python3

import asyncio
import os
import sys
import re
from random_word import RandomWords

# Constants

HOST = 'chat.ndlug.org'
PORT = 6697
NICK = f'ircle-{os.environ["USER"]}'

# Functions

async def ircle():
    # Connect to IRC server
    reader, writer = await asyncio.open_connection(HOST, PORT, ssl=True)

    # Identify ourselves
    writer.write(f'USER {NICK} 0 * :{NICK}\r\n'.encode())
    writer.write(f'NICK {NICK}\r\n'.encode())
    await writer.drain()

    # Join #bots channel
    writer.write(f'JOIN #bots\r\n'.encode())
    #writer.write(f'JOIN #lug\r\n'.encode())
    await writer.drain()

    # Write message to channel
    writer.write(f'PRIVMSG #bots : wow\r\n'.encode())
    #writer.write(f"PRIVMSG #bots :I've fallen and I can't get up!\r\n".encode())
    await writer.drain()

    # Read and display
    string = []
    tries = 5
    while True:
        message = (await reader.readline()).decode().strip()
        print(message)
        if message.startswith('PING'):
            message = re.findall(r"PING (.*)", message)
            writer.write(f"PONG {message[0]}\r\n".encode())
            await writer.drain()

        message = re.findall(r'PRIVMSG #bots :(.*)', message)
        if message and message[0].startswith('!hangman'):
            string, word = await hangman(reader, writer, tries)
        

        if message and message[0] == '!guess':
            if not string:
                writer.write(f"PRIVMSG #bots :Start a game first\r\n".encode())
                await writer.drain()
            else:
                message = message[0].split()
                if len(message[1]) == 1 and message[1].isalpha():
                    tries = await play_hangman(writer, word, message[1], string, tries)
                    if not tries:
                        string = []
                        tries = 5
                else:
                    writer.write(f"PRIVMSG #bots :bad boy\r\n".encode())
                    await writer.drain()

                


# Main execution
async def hangman(reader, writer, tries):
    r = RandomWords()
    word = r.get_random_word()
    print(word)
    
    string = ['_'] * len(word)
    letter_count = len(word) #7
    writer.write(f"PRIVMSG #bots :LETS PLAY HANGMAN!\r\n".encode())
    writer.write(f"PRIVMSG #bots :{' '.join(string)} | Tries left: {tries}\r\n".encode())
    await writer.drain()
    return string, word #returns array with _'s as place holder and word to guess

async def play_hangman(writer, word, letter, string_arr, tries): #writer to write, word to guess, letter guessed, current guesses
    match_index = []
    for index, char in enumerate(word):
        if char == letter:
            match_index.append(index)
    
    if not match_index:
        tries -= 1
        if tries == 0:
            writer.write(f"PRIVMSG #bots :rekt, start new game\r\n".encode())
            await writer.drain()
            return tries
        writer.write(f"PRIVMSG #bots :Nope, try again\r\n".encode())
        writer.write(f"PRIVMSG #bots :{' '.join(string_arr)} | Tries left: {tries}\r\n".encode())
        await writer.drain()
    else: #match found
        writer.write(f"PRIVMSG #bots :Match found!\r\n".encode())
        for match in match_index:
            string_arr[match] = letter
        writer.write(f"PRIVMSG #bots :{' '.join(string_arr)} | Tries left: {tries}\r\n".encode())
        await writer.drain()
    
    #end of game
    if '_' not in string_arr:
        writer.write(f"PRIVMSG #bots :POG ez dub\r\n".encode())
        tries = 0
        await writer.drain()
    
    return tries
    

    
def main():
    asyncio.run(ircle())

if __name__ == '__main__':
    main()