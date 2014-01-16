import praw, time, ConfigParser, re, readline, thread, sys, os, glob

run = True

def output(string):
	"""write the string to start of line then clear out the rest of the line, only if string is set"""
	if string:
		sys.stdout.write('\r%s\x1b7\x1b[K\n>' % string + readline.get_line_buffer())
		sys.stdout.flush()

class Config():
	"""creates a Config """

	def save(self):
		"""save the config file"""
		config = open('subnewsbot.cfg', 'w')
		self.config.write(config)
		config.close()

	def load(self):
		"""load all config from file"""
		self.username = self.config.get('config', 'username')
		self.password = self.config.get('config', 'password')
		self.useragent = self.config.get('config', 'useragent')
		self.sub = self.config.get('config', 'sub')
		self.signature_show = self.config.getboolean('config', 'signature_show')
		self.signature = self.config.get('config', 'signature')
		self.log = self.config.getboolean('config', 'log')
		self.date_format = self.config.get('config', 'date_format')
		self.next_issue = self.config.get('data', 'next_issue')
		self.next = self.config.get('data', 'next')
		self.subscribed = self.config.get('data', 'subscribed')

	def __init__(self):
		self.config = ConfigParser.ConfigParser()
		self.config.read('subnewsbot.cfg')
		self.load()

config = Config()

class Message:
	"""creates a Message, with issue name to get all the message's elements"""

	def get_messages(self):
		"""return all messages"""
		messages = queue = sent = {}
		for message in glob.glob('messages/*.msg'):
			messages[message.split('/')[-1:][0]] = Message(message).data
		for message in glob.glob('messages/queue/*.msg'):
			queue[message.split('/')[-1:][0]] = Message(message).data
		for message in glob.glob('messages/queue/*.msg'):
			sent[message.split('/')[-1:][0]] = Message(message).data
		return (messages, queue, sent)

	def get_date(self):
		"""returns send date"""
		try:
			return time.strptime(self.data['raw'].splitlines()[0], config.date_format)
		except ValueError:
			return None


	def get_subject(self):
		"""returns message subject"""
		if self.data['date']:
			return self.data['raw'].splitlines()[1]
		else:
			return self.data['raw'].splitlines()[0]

	def get_body(self):
		"""returns message body"""
		if self.data['date']:
			return self.data['raw'].splitlines()[2:]
		else:
			return self.data['raw'].splitlines()[1:]

	def __init__(self, message = None):
		if message:
			self.data = {}
			with open(message) as f:
				self.data['raw'] = f.read()
			self.data['date'] = self.get_date()
			self.data['subject'] = self.get_subject()
			self.data['body'] = self.get_body()

(messages, queue, sent) = Message().get_messages()

class Commands():
	"""creates a Commands initialised with the commands, their help and their respective function"""

	def help(self, arguments):
		output('subnewsbot by /u/zeokila - github.com/zeokila/subnewsbot')
		found = False
		for command in commands:
			if not arguments:
				output('  %s: %s' % (command[0], command[1]))
			elif command[0] == arguments[0]:
				output('  description: %s' % command[1])
				found = True
				if command[2]:
					output('  usage: %s %s' % (command[0], command[2]))
		if not found and arguments:
			output('  command not found')

	def reload(self, arguments):
		output('reloading data and config')
		global config
		config.load()

	def kill(self, arguments):
		output('killing the bot')
		global run
		run = False

	def add(self, arguments):
		"""add message to queue"""
		pass

	def remove(self, arguments):
		"""remove message from queue"""
		pass

	def subscribe(self, arguments):
		if arguments:
			output('subscribing %s' % arguments[0])
		else:
			output('incorrect arguments')
			self.help(['subscribe'])

	def unsubscribe(self, arguments):
		if arguments:
			output('unsubscribing %s' % arguments[0])
		else:
			output('incorrect arguments')
			self.help(['unsubscribe'])

	def __init__(self):
		self.commands = [
			('help', 'display command help', '[command]', self.help),
			('reload', 'reloads the data and config', None, self.reload),
			('kill', 'safely kill the bot', None, self.kill),
			('add', 'add message to queue', '[date,]issue,subject,body', self.add),
			('remove', 'remove message from queue (forever!)', 'issue', self.remove),
			('subscribe', 'subscribe user to newsletter', 'username', self.subscribe),
			('unsubscribe', 'unsubscribe user from newsletter', 'username', self.subscribe)
		]

commands = Commands().commands

while run:
	i = raw_input('\r>').split(' ') # split to gather arguments

	found = False
	for command in commands:   # go through all stored commands
		if i[0] == command[0]: # if first word matches stored commands
			command[3](i[1:])  # run stored command's function, pass the arguments
			found = True
	if not found:
		output('invalid command')
		output('  command not found, try "help"')
