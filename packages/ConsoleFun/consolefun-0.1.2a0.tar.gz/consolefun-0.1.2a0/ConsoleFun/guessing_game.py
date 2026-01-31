import random
import pyfiglet
from prettytable import PrettyTable
from colorama import Fore, Style, init


# Initialize colorama


def start_game():
    init(autoreset=True)
    print(pyfiglet.figlet_format("CONSOLE GAMES"))
    print("Welcome Guessing Game!")
    print("\033[94mType 'exit' to quit the game.\033[0m\n")
    play = True
    digits = list(range(10))
    random.shuffle(digits)
    target = "".join(map(str, digits[:4]))
    while play:
        correct_place = 0
        correct_number = 0
        my_guess = input('Guess Your Number ').strip()
        if my_guess == 'exit':
            print("Thanks for playing! Goodbye!")
            break

        if my_guess == target:
            print(pyfiglet.figlet_format("CONGRATZZ!!\n"))
            break

        used_chars = [False] * len(target)
        for i in range(len(my_guess)):
            if i < len(target) and my_guess[i] == target[i]:
                correct_place += 1
                used_chars[i] = True
        for i in range(len(my_guess)):
            if i < len(target) and my_guess[i] != target[i] and my_guess[i] in target:
                for j in range(len(target)):
                    if not used_chars[j] and my_guess[i] == target[j]:
                        correct_number += 1
                        used_chars[j] = True
                        break
        table = PrettyTable()
        table.field_names = [Fore.GREEN + "Correct Place and number" + Style.RESET_ALL,
                             Fore.RED + "Correct Number but not in place" + Style.RESET_ALL]

        table.add_row([Fore.YELLOW + str(correct_place) + Style.RESET_ALL,
                       Fore.YELLOW + str(correct_number) + Style.RESET_ALL])
        print(table)
