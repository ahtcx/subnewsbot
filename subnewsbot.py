import praw, time, ConfigParser, readline, thread, sys, glob, shutil

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
		# TODO self.config.set('config', 'log', str(self.log))
		self.config.set('config', 'date_format', self.date_format)
		self.config.set('data', 'subscribed', self.subscribed)
		# TODO self.config.set('data', 'admins', self.admins)
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
		# TODO self.log = self.config.getboolean('config', 'log')
		self.date_format = self.config.get('config', 'date_format')
		self.subscribed = self.config.get('data', 'subscribed')
		# TODO self.admins = self.config.get('data', 'admins')

	def __init__(self):
		self.config = ConfigParser.ConfigParser()
		self.config.read('subnewsbot.cfg')
		self.load()

config = Config()

class Users():
	"""everything you need to handle users"""

	def is_admin(self):
		"""returns if user is an admin"""
		try:
			self.get_admins().index[username]
			return True
		except ValueError:
			return False

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
			return True
		if not added:
			output('%s already subscribed' % username)
			return False

	def unsubscribe_user(self, username):
		subscribed = self.get_subscribers()
		try:
			del subscribed[subscribed.index(username)]
			config.subscribed = ','.join(subscribed)
			if config.subscribed[0:1] == ',': # stop single comma problem
				config.subscribed = config.subscribed[1:]
			output('unsubscribed %s' % username)
			return True
		except ValueError: # if username not found, ignore
			output('%s not found in subscribed' % username)
			return False

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

class Message():
	"""Message instance (w/ date, subject, body, file)"""

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

	def __init__(self, message):
		self.data = {}
		self.data['file'] = message
		with open(message) as f:
			self.data['raw'] = f.read()
		self.data['date'] = self.get_date()
		self.data['subject'] = self.get_subject()
		self.data['body'] = self.get_body()

class Messages():
	"""Message handling here"""

	def set_messages(self):
		"""updates messages, queue and sent"""
		for message in glob.glob('messages/*.msg'):
			self.messages[message.split('/')[-1]] = Message(message)
		for message in glob.glob('messages/queue/*.msg'):
			self.queue[message.split('/')[-1]] = Message(message)
		for message in glob.glob('messages/sent/*.msg'):
			self.sent[message.split('/')[-1]] = Message(message)

	def set_content(self, message, username, listed = None):
		"""set message with info/content"""
		replacements = {
			'sub': config.sub,
			'subreddit': config.sub,
			'user': username,
			'username': username,
			'signature': config.signature,
		}
		if listed:
			replacements += {
				'list': listed
			}
		for keys in replacements.keys():
			message.data['subject'] = message.data['subject'].replace('%%%s%%' % keys, replacements[keys])
			message.data['body'] = message.data['body'].replace('%%%s%%' % keys, replacements[keys])

	def send(self, message, receivers, listed = None):
		"""move to sent then send issue to all subscribers"""
		if  message.data['file'].split('/')[1] == 'queue': # if it was queued, move to sent
			shutil.move(message.data['file'], 'messages/sent/%s' % message.data['file'].split('/')[-1])
			self.set_messages()
		for user in receivers:
			self.set_content(message, user, listed)
			r.send_message(user, message.data['subject'], message.data['body'])
		output('sent %s to %i users' % (message.data['file'], len(receivers)))

	def parse(self, message):
		"""parse user command from message"""
		if message.subject == 'subscribe':
			users.subscribe_user(message.author.name)
			self.send(self.messages['subscribed.msg'], [message.author.name])
		elif message.subject == 'unsubscribe':
			users.unsubscribe_user(message.author.name)
			self.send(self.messages['unsubscribed.msg'], [message.author.name])
		elif message.subject == 'get':
			for m in message.body.split(','):
				try:
					self.send(self.sent['%s.msg' % m], [message.author.name])
				except:
					pass
		elif message.subject == 'list':
			listed = ''
			for m in self.sent:
				listed += ',%s' % self.sent[m].data['file'].split('/')[-1:][0].split('.')[0]
			self.send(self.messages['list.msg'], [message.author.name], listed[1:])
		else:
			pass

	def __init__(self):
		(self.messages, self.queue, self.sent) = ({}, {}, {})
		self.set_messages()

messages = Messages()

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
		output('reloading config')
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
		for message in messages.sent:
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
			('reload', 'reloads config', None, self.reload),
			('kill', 'safely kill the bot', None, self.kill),
			('list', 'list all issues', None, self.list),
			# TODO ('admins', 'list admins', None, self.admins),
			# TODO ('adminify', 'add user(s) to admins', 'username[,username ...]', self.adminify),
			# TODO ('unadminify', 'remove user(s) from admins', 'username[,username ...]', self.unadminify),
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
	for message in r.get_unread(limit = None):
		Messages().parse(message)
		message.mark_as_read()
	for message in messages.queue:
		if time.mktime(messages.queue[message].get_date()) <= time.time():
			messages.queue[message].send_issue(users.get_subscribers()) # the issues receiver is all the subscribers
	time.sleep(10)
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
