# subnewsbot

subnewsbot is a Python bot aimed for subreddits, where you can send out a customised newsletter to all those who've subscribed to the newsletter. It has simple commands users can use to interact with it.

## Configuration

Example of a configuration file with explanations

    [config]
    username = subnewsbot #bot username
    password = password123 #bot password
    useragent = /u/subnewsbot by /u/zeokila #bot useragent
    sub = subnewsbot #aimed subreddit
    signature = ^[subnewsbot](https://github.com/zeokila/subnewsbot) #message signature
    date_format = %H:%M %d/%m/%Y #format to read dates in
    
    [data]
    subscribed = zeokila

## User commands

User commands sent though messages to the bot, the command is in the subject, the parameters are in the body

Command       | Parameters          | Action
------------- | ------------------- | ------
`subscribe`   | none                | Subscribes the message sender to future newsletters
`unsubscribe` | none                | Unsubscribes the message sender from future newsletters
`list`        | none                | Lists all sent issues names seperated by commas
`get`         | `issue[,issue ...]` | Sends the user all found issues from specified issues

## Console commands

These commands are entered on the script's host's input

Command       | Parameters        | Action
------------- | ----------------- | ------
`help`        | `[command]`       | Lists all console commands and their description, or lists help and usage to specific command
`reload`      | none              | Reload configuration
`list`        | none              | Lists all sent issues
`kill`        | none              | Safely kill the bot
`subscribed`  | none              | List all subscribers
`subscribe`   | `user[,user ...]` | Subscribe user(s)
`unsubscribe` | `user[,user ...]` | Unubscribe user(s)

## Message files

Example message with explanations (in real messages, there are *no* comments!). Messages have a `.msg` extension. All messages in `messages/queue/` should have a date, to be sent off on that date. All messages in `messages/sent/` are acessable to all.

    %H:%M %d/%m/%Y (optional line, if no date, move everything up one line, depends on time format from settings!)
    This is the messages subject
    Hi %user% this is the message body!
    #Header
    
    * Has reddit markup syntax stuff, write under the subject like you would write any other reddit message
    
    Love this %sub%

### Replaceable variables

Variable               | Replaced by
---------------------- | -----------
`%sub%`, `%subreddit%` | Newsletter's subreddit, from settings
`%user%`, `%username%` | Message receivers username
`%sig%`, `%signature%` | Bot's signature from settings
`%list%`               | List of sent messages (when available)
