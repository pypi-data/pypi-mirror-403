import random

import pyfiglet

print(pyfiglet.figlet_format("CONSOLE GAMES"))


def rock_paper_scissors():
    options = ["rock", "paper", "scissors"]
    graphics = {"rock": '🌑', "paper": '📝', "scissors": '✂️'}
    print("Welcome to Rock, Paper, Scissors!")
    print("\033[94mType 'exit' to quit the game.\033[0m")

    while True:
        user_choice = input("\nEnter your choice (rock, paper, scissors): ").lower()

        if user_choice == 'exit':
            print("Thanks for playing! Goodbye!")
            break

        if user_choice not in options:
            print("\033[91mInvalid choice! Please choose rock, paper, or scissors.\033[0m")
            continue

        computer_choice = random.choice(options)
        print(f"Computer chose: \033[36m{computer_choice}\033[0m")

        if user_choice == computer_choice:
            print(f'{graphics[computer_choice]}')
            print("\033[93mIt's a tie!\033[0m")
        elif (user_choice == "rock" and computer_choice == "scissors") or \
                (user_choice == "paper" and computer_choice == "rock") or \
                (user_choice == "scissors" and computer_choice == "paper"):
            print(f'{graphics[user_choice]} xxxxxxxx {graphics[computer_choice]}')
            print("\033[92mYou win!\033[0m")
        else:
            print(f'{graphics[computer_choice]} xxxxxxxx {graphics[user_choice]}')
            print("\033[91mYou lose!\033[0m")


