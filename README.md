# discordpy-bot

This is a discord music bot made using discord.py. This music bot utilizes slash commands, so every command begins with a slash. These commands should autocomplete within discord.

```
/<COMMANDNAME> <PARAMETERS>
```

Steps to Use:

1. Create Discord application and obtain application/bot secret. [Docs Link](https://discordpy.readthedocs.io/en/stable/discord.html)
2. Create .env in root of project.
3. Add Params to a .env file (Use the example).
4. execute "pip install -r requirements.txt"
5. Run main.py
6. Invite bot to your server(s).
7. Run main.py and allow the program to import commands.

## Cogs

### Admin

**Shutdown**: Shuts down the bot.

**Announce**: Sends an announcement to the selected channel.

**Kick**: Kicks a user

**Ban**: Bans a user

**Timeout**: Times out a user for a user-defined number of seconds.

### Music

**Play**: Plays music from a youtube link (Query string to be implemented).

**Pause**: Pauses the playing song.

**Stop**: Stops the playing song.

**Resume**: Resumes a song if it was previously paused.

**Join**: Joins the voice channel of the user that issued the command.

**Leave**: Leaves the voice channel in the current server/guild.

### Utility

**Coinflip**: Flips a coin and returns heads or tails.

**Roll**: Rolls a number between one and the number specified in the command. If no number is specified, then six is the default.

**Pick**: Randomly picks between a list of space delimited user-specified items.

**Math**: Evaluates simple math expressions.

**UserInfo**: Gives information about a user. If a user is not specified, then it will send information on user who issued the command.

**ServerInfo**: Gives information about the current server/guild.

**Reminder**: Will remind the user about something given time. (Accepts: Number + d -> day, h-> hour, m -> minute, s -> second)

**Weather**: Will return an embed with the weather for a specified city name.
NOTE: Requires an openweathermap API Key in .env called WEATHER_API_KEY

### Economy

**Balance**: Retrieves the balance for the user who initiated the command

**Gamble**: Allows the user to gamble a user-defined amount of money.

**Pay**: Allows the user to gift or send some of their money to another user in the guild.

**Daily**: Claim Daily Coin Reward

**Leaderboard**: Displays the top 10 richest members in the guild.

### Levels

**Level**: Retrieves and displays the user's current level

**Lvlboard**: Displays the 10 members with the highest levels on the guild.

## Technologies Used

1. Discord.py - [GitHub](https://github.com/Rapptz/discord.py) - [Docs](https://discordpy.readthedocs.io/)
2. yt-dlp - [GitHub](https://github.com/yt-dlp/yt-dlp)
3. python-dotenv - [GitHub](https://github.com/yt-dlp/yt-dlp)
4. OpenWeatherMap API - [Site](https://openweathermap.org/api)

## Todo

- Youtube Playlists.
- Youtube Query Strings (Fetch links using string).
- Look into Lavalink.
- Add Features and Improve Economy Commands.
- Add additional utility commands.
