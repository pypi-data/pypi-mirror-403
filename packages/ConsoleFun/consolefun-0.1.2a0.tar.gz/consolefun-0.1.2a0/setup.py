from setuptools import setup, find_packages

setup(
    name='ConsoleFun',
    version='0.1.2a',
    packages=find_packages(),
    install_requires=[
        'tabulate',
        'prettytable',
        'colorama',
        'pyfiglet'
    ],
    entry_points={
        'console_scripts': [
            'list_games=ConsoleFun.list_games:list_games',
            'play-guessing-game=ConsoleFun.guessing_game:start_game',
            'play-rock-paper=ConsoleFun.rps:rock_paper_scissors',
            'play-chess=ConsoleFun.chess:play',

        ],
    },
    author='Manoj Shetty K',
    author_email='shettykmanojmask@gmail.com',
    description='Developed primarily for fun and learning purposes, this collection serves as a playground for '
                'budding developers and gamers alike. As such, you might encounter a few bugs along the way—consider '
                'them part of the adventure!',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/memanja/ConsoleGames',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
