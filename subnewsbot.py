import praw, time, ConfigParser, re, readline, thread, sys, os, glob, shutil

run = True

def output(string):
	"""write the string to start of line then clear out the rest of the line, only if string is set"""
	if string:
		sys.stdout.write('\r%s\x1b7\x1b[K\n>' % string + readline.get_line_buffer())
		sys.stdout.flush()

class Config():
	"""creates a Config """

	def save(self):
		"""save all config to file"""
		self.config.set('config', 'username', self.username)
		self.config.set('config', 'password', self.password)
		self.config.set('config', 'useragent', self.useragent)
		self.config.set('config', 'sub', self.sub)
		self.config.set('config', 'signature', self.signature)
		self.config.set('config', 'log', str(self.log))
		self.config.set('config', 'date_format', self.date_format)
		self.config.set('data', 'allowed', self.allowed)
		self.config.set('data', 'subscribed', self.subscribed)
		self.config.set('data', 'admins', self.admins)
		config = open('subnewsbot.cfg', 'w')
		self.config.write(config)
		config.close()

	def load(self):
		"""load all config from file"""
		self.username = self.config.get('config', 'username')
		self.password = self.config.get('config', 'password')
		self.useragent = self.config.get('config', 'useragent')
		self.sub = self.config.get('config', 'sub')
		self.signature = self.config.get('config', 'signature')
		self.log = self.config.getboolean('config', 'log')
		self.date_format = self.config.get('config', 'date_format')
		self.allowed = self.config.get('data', 'allowed')
		self.subscribed = self.config.get('data', 'subscribed')
		self.admins = self.config.get('data', 'admins')

	def __init__(self):
		self.config = ConfigParser.ConfigParser()
		self.config.read('subnewsbot.cfg')
		self.load()

config = Config()

class Users():
	"""everything you need to handle users"""

	def get_subscribers(self): # return list of subscribers usernames
		return config.subscribed.split(',')

	def get_admins(self):
		return config.admins.split(',')

	def subscribe_user(self, username):
		subscribed = self.get_subscribers()
		added = False
		try:
			subscribed.index(username)
		except ValueError: # only append the username if not found (aka. throws error)
			subscribed.append(username)
			config.subscribed = ','.join(subscribed)
			if config.subscribed[0:1] == ',': # stop single comma problem
				config.subscribed = config.subscribed[1:]
			added = True
			output('subscribed %s' % username)
		if not added:
			output('%s already subscribed' % username)

	def unsubscribe_user(self, username):
		subscribed = self.get_subscribers()
		try:
			del subscribed[subscribed.index(username)]
			config.subscribed = ','.join(subscribed)
			if config.subscribed[0:1] == ',': # stop single comma problem
				config.subscribed = config.subscribed[1:]
			output('unsubscribed %s' % username)
		except ValueError: # if username not found, ignore
			output('%s not found in subscribed' % username)

	def adminify_user(self, username):
		admins = self.get_admins()
		added = False
		try:
			admins.index(username)
		except ValueError: # only append the username if not found (aka. throws error)
			admins.append(username)
			config.admins = ','.join(admins)
			if config.admins[0:1] == ',': # stop single comma problem
				config.admins = config.admins[1:]
			added = True
			output('%s added to admins' % username)
		if not added:
			output('%s already an admin' % username)

	def unadminify_user(self, username):
		admins = self.get_admins()
		try:
			del admins[admins.index(username)]
			config.admins = ','.join(admins)
			if config.admins[0:1] == ',': # stop single comma problem
				config.admins = config.admins[1:]
			output('%s is no longer an admin' % username)
		except ValueError: # if username not found, ignore
			output('%s not found in admins' % username)

	def __init__(self):
		pass

users = Users()

class Message:
	"""creates a Message, with issue name to get all the message's elements"""

	def send_issue(self, receivers):
		"""move to sent then send issue to all subscribers"""
		shutil.move(self.data['file'], 'messages/sent/%s' % self.data['file'].split('/')[:-1])
		for user in receivers:
			self.parse(user)
			r.send_message(user, self.data['subject'], self.data['body'])
		output('sent issue to %i users' % len(receivers))

	def parse(self, username):
		"""parse message with info"""
		replacements = {
			'sub': config.sub,
			'user': username,
			'signature': config.signature
		}
		for keys in replacements.keys():
			self.data['subject'] = self.data['subject'].replace('%%%s%%' % keys, replacements[keys])
			self.data['body'] = self.data['body'].replace('%%%s%%' % keys, replacements[keys])

	def get_messages(self):
		"""return all messages"""
		messages = {}
		queue = {}
		sent = {}
		for message in glob.glob('messages/*.msg'):
			messages[message.split('/')[-1:][0]] = Message(message)
		for message in glob.glob('messages/queue/*.msg'):
			queue[message.split('/')[-1:][0]] = Message(message)
		for message in glob.glob('messages/sent/*.msg'):
			sent[message.split('/')[-1:][0]] = Message(message)
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
			return '\n'.join(self.data['raw'].splitlines()[2:])
		else:
			return '\n'.join(self.data['raw'].splitlines()[1:])

	def __init__(self, message = None):
		if message:
			self.data = {}
			with open(message) as f:
				self.data['raw'] = f.read()
			self.data['file'] = message
			self.data['date'] = self.get_date()
			self.data['subject'] = self.get_subject()
			self.data['body'] = self.get_body()

(messages, queue, sent) = Message().get_messages()

#for message in queue:
#	output(queue[message].get_date())

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
		output('saving')
		config.save()
		output('killing the bot')
		global run
		run = False

	def list(self, arguments):
		"""list all sent issues"""
		for message in sent:
			output(message[:-4])

	def admins(self, arguments):
		"""list admins"""
		for admin in users.get_admins():
			output(admin)

	def adminify(self, arguments):
		"""adminify user(s)"""
		if arguments:
			usernames = arguments[0].split(',')
			for username in usernames:
				users.adminify_user(username)
		else:
			output('incorrect arguments')
			self.help(['adminify'])

	def unadminify(self, arguments):
		"""unadminify user(s)"""
		if arguments:
			usernames = arguments[0].split(',')
			for username in usernames:
				users.unadminify_user(username)
		else:
			output('incorrect arguments')
			self.help(['unadminify'])

	def subscribed(self, arguments):
		"""list subscribers"""
		for subscriber in users.get_subscribers():
			output(subscriber)

	def subscribe(self, arguments):
		"""subscribe user(s)"""
		if arguments:
			usernames = arguments[0].split(',')
			for username in usernames:
				users.subscribe_user(username)
		else:
			output('incorrect arguments')
			self.help(['subscribe'])

	def unsubscribe(self, arguments):
		"""unsubscribe user(s)"""
		if arguments:
			usernames = arguments[0].split(',')
			for username in usernames:
				users.unsubscribe_user(username)
		else:
			output('incorrect arguments')
			self.help(['subscribe'])

	def __init__(self):
		self.commands = [
			('help', 'display command help', '[command]', self.help),
			('reload', 'reloads the data and config', None, self.reload),
			('kill', 'safely kill the bot', None, self.kill),
			('list', 'list all issues', None, self.list),
			('admins', 'list admins', None, self.admins),
			('adminify', 'add user(s) to admins', 'username[,username ...]', self.adminify),
			('unadminify', 'remove user(s) from admins', 'username[,username ...]', self.unadminify),
			('subscribed', 'list subscribers', None, self.subscribed),
			('subscribe', 'subscribe user(s) to newsletter', 'username[,username ...]', self.subscribe),
			('unsubscribe', 'unsubscribe(s) user from newsletter', 'username[,username ...]', self.unsubscribe)
		]

commands = Commands().commands

output('subnewsbot by /u/zeokila')
r = praw.Reddit('starting bot') # praw reddit instance

def init():
	output('logging in')
	r.login(config.username, config.password)
	output('logged in')
	output('checking')
	check()

def check():
	"""runs every 2 seconds and checks for continuously updated stuff"""
	for message in queue:
		if time.mktime(queue[message].get_date()) <= time.time():
			queue[message].send_issue(users.get_subscribers()) # the issues receiver is all the subscribers
	time.sleep(2)
	thread.start_new_thread(check, ())

init()

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
