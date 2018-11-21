# About this project
This is a final year project on investigating deep learning models for [Hong Kong Mahjong](https://en.wikipedia.org/wiki/Mahjong). 

The project consists of 2 stages.

In the 1st stage, various models were implemented. These include heuristics based, Monte-Carlo tree search based, Deep Q learning based and Deep policy gradient based models.

In the 2nd stage, the models were benchmarked by making them compete with each other. A Telegram bot was also built to benchmarking against human players.

The reports of the project could be downloaded here:
- [Term 1 report](https://docs.google.com/document/d/e/2PACX-1vSTvJQ6Etw1z37dGPn7J283G-l2Runh3m3tXmqhlx88lb8rxleFFmlDLCsIqI8vXaozkoT-lyhguLll/pub)
- [Term 2 final report](https://docs.google.com/document/d/e/2PACX-1vTnkGsftaZSHcjzMP5BVlx5bEgJx4J9c-NApYddfOebobWguQGlNaqrS2M8PX853BoodR17P-FrFBay/pub)

## Dependencies (main module)
- C++ 11 compiler
- cython
- tensorflow (1.8)
- (optional) pillow

## Dependencies (Telegram bot server module)
- all libraries required in the main module
- python-telegram-bot
- pymongo

## Environment Setup
- Install C++ 11 compiler.
- Install Python dependencies by `pip3 install cython tensorflow==1.8 pillow python-telegram-bot pymongo`.
- Issue the command `make` to compile the C++ scripts for the Monte Carlo Tree Search model.

## List of Test Scripts
During the project, different test scripts were coded for experiments. The scripts are located under `/test_cases`. 

In general, to invoke a test script, issue the command `python3 test.py [script_name] [..args for the script]`. 

The use of each script could be found [here](https://github.com/clarkwkw/mahjong-ai/wiki/List-of-Test-Scripts).

## Setting Up the Telegram Bot
1. Retrieve a Telegram Bot token by talking to [BotFather](https://telegram.me/botfather) in Telegram.
2. Set up a [MongoDB](https://docs.mongodb.com/manual/installation/).
3. Edit `/resources/server_settings.json`. 

　Change `mongo_uri` according to the host, username and password of the MongoDB. 
 
　Replace the value of `tg_bot_token` by the token you retrieved from BotFather.
  
　(Ignore `tg_server_address` and `tg_server_port` since by default the bot is in [polling mode](https://python-telegram-bot.readthedocs.io/en/stable/telegram.ext.updater.html#telegram.ext.Updater.start_polling).)
  
4. Start the bot by `python3 start_server.py`.

## Development Documentation
These are the functions of the modules:

|Module Name|Functions|
|---|---|
|Game|Implements the Hong Kong Mahjong main game logic, such as turn taking and victory condition checking, etc. The module consists of the `Game` class and the `TGGame` class. `TGGame` is rewritten from `Game` to facilitate pausing and resuming a game.|
|MLUtils|Implements different machine learning models, mainly deep learning models implemented in Tensorflow.|
|MoveGenerator|Acts as an interface between the `Player` class and the corresponding AI model in `MLUtils`.|
|Player|Encapsulate the information of a player, including tiles held and discaded tile history.|
|ScoringRules|Implements the score calculation and victory hand detection mechanism.|
|TGBotServer|Implements the communication with Telegram bot users and game state storing.|
|TGLanguage|Wraps the lamguage pack as Python functions for the Telegram bot.|
|Tile|Encapsulates the information of a tile, such as tile symbol and name.|

[Outdated, for reference only] For the detail API documentation, please refer to [here](https://docs.google.com/document/d/e/2PACX-1vTTcfwVCwFeHgwfVt7G1eyD5sLF7NmlHHANPOIU1pDlPldczfIi-PdrePyeFU0MXXaL6Qi98JVZlSNX/pub).
