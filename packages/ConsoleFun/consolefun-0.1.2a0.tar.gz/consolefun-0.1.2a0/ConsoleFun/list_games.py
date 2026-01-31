import pyfiglet
def list_games():
    print(pyfiglet.figlet_format("CONSOLE GAMES"))

    games = {'Guessing Game':'play-guessing-game',
             'Rock-Paper-Scissors':'play-rock-paper',
             'Chess':'play-chess'}
    print("\033[4m\033[91mAvailable games:\033[0m")
    for key,val in games.items():
        print(f'-{key}, command: \033[92m\033[1m\x1B[3m{val}\x1B[0m\033[0m')

