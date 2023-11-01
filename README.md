# discordpy-bot

This is a discord music bot made using discord.py. This music bot utilizes slash commands, so every command begins with a slash. These commands should autocomplete within discord.

```
/<COMMANDNAME> <PARAMETERS>
```

## Cogs

### Admin

**UserInfo**: Gives information about a user. If a user is not specified, then it will send information on user who issued the command.

**ServerInfo**: Gives information about the current server/guild.

**Shutdown**: Shuts down the bot.

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
