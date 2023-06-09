#! /usr/bin/env python3

import asyncio
import os
import sys
import re
from random_word import RandomWords

# Constants

HOST = 'chat.ndlug.org'
PORT = 6697
NICK = f'hangmanbot'

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
    writer.write(f'PRIVMSG #bots : Hello, hangman dude has arrived\r\n'.encode())
    #writer.write(f"PRIVMSG #bots :I've fallen and I can't get up!\r\n".encode())
    await writer.drain()

    # Read and display
    string = []
    while True:
        message = (await reader.readline()).decode().strip()
        if message.startswith('PING'):
            message = re.findall(r"PING (.*)", message)
            writer.write(f"PONG {message[0]}\r\n".encode())
            await writer.drain()
            continue

        message = re.findall(r'PRIVMSG #bots :(.*)', message)
        if message and message[0].startswith('!hangman'): #start game
            string, word, tries = await hangman(reader, writer)
        
        if message and message[0].startswith('!guessword'): #guess word
            if not string:
                writer.write(f"PRIVMSG #bots :Start a game first\r\n".encode())
                await writer.drain()
            else:
                message = message[0].split()
                await guess_word(writer, word, message[1], string)
                string = []

        elif message and message[0].startswith('!guess'): #guess
            message = message[0].split()
            if len(message) == 1: #check to see if there is a guess
                writer.write(f"PRIVMSG #bots :Please enter a character\r\n".encode())
                await writer.drain()
            else:
                if not string:
                    writer.write(f"PRIVMSG #bots :Start a game first\r\n".encode())
                    await writer.drain()
                else:
                    if len(message[1]) == 1 and message[1].isalpha():
                        tries = await play_hangman(writer, word, message[1].lower(), string, tries)
                        if not tries:
                            string = []
                    else:
                        writer.write(f"PRIVMSG #bots :bad boy, one letter guess only\r\n".encode())
                        await writer.drain()


# Main execution
async def hangman(reader, writer):
    r = RandomWords()
    word = r.get_random_word()
    print(word)
    
    string = ['_'] * len(word)
    letter_count = len(word) #7
    writer.write(f"PRIVMSG #bots :LETS PLAY HANGMAN!\r\n".encode())
    writer.write(f"PRIVMSG #bots :{' '.join(string)} | Tries left: {len(word)}\r\n".encode())
    await writer.drain()
    return string, word, len(word) #returns array with _'s as place holder and word to guess

async def play_hangman(writer, word, letter, string_arr, tries): #writer to write, word to guess, letter guessed, current guesses
    match_index = []
    for index, char in enumerate(word):
        if char == letter:
            match_index.append(index)
    
    if not match_index:
        tries -= 1
        if tries == 0:
            writer.write(f"PRIVMSG #bots :rekt, start new game\r\n".encode())
            writer.write(f"PRIVMSG #bots :The word was {word}\r\n".encode())
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
    
async def guess_word(writer, word, guess, string_arr):
    if word == guess:
        writer.write(f"PRIVMSG #bots :Nice!\r\n".encode())
        await writer.drain()
    
        string_arr = [char for char in word]
        writer.write(f"PRIVMSG #bots :{' '.join(string_arr)}\r\n".encode())
        await writer.drain()

    else:
        writer.write(f"PRIVMSG #bots :Nope, INCORRECT. Start new game\r\n".encode())
        writer.write(f"PRIVMSG #bots :The word was {word}\r\n".encode())
        await writer.drain()
    
def main():
    asyncio.run(ircle())

if __name__ == '__main__':
    main()