import copy, re

class PyConf():
	
	
	def __init__(self, defaults=None, files=[], section_matters=True, file_matters=False, explicit_load=True):
		self.defaults = defaults
		self.section_matters = section_matters
		self.file_matters = file_matters
		self.explicit_load = explicit_load
		
		self._item_tree = {}
		
		for f in files:
			self.load(f)
	
	def load(config_file):
		if type(config_file) == str:
			with open(config_file) as f:
				self._parse_file(f)
		elif type(config_file) == file:
			self._parse_file(f)
		else:
			raise TypeError('load function must be either a file name or file object, got %s' %
							type(config_file))
		
	"""Get value of a config item given an identifier
	
	Whether file or section are required depend on 
	if self.section_matters or self.file_matters are set to True
	"""
	def get_item(self, item, section=None, file=None):
		#Validate arguments
		if type(section) is not str and self.section_matters:
			raise TypeError('Expected type str for "section" got %s' % type(section))
		if type(file) is not str and self.file_matters:
			raise TypeError('Expected type str for "file" got %s' % type(file))
		if type(item) is not str:
			raise TypeError('Expected type str for "item" got %s' % type(item))
		
		try:
			working_tree = self._item_tree
		
			#Validate file identifier, make sure file is loaded
			if self.file_matters and file is not None:
				if not working_tree.has_key(file): 
					if not self.explicit_load:
						self.load(file)
						working_tree = working_tree[file]
					else:
						raise FileLoadError(file)
				else:
					working_tree = working_tree[file]
			
			#Validate section identifier
			if self.section_matters and section is not None:
				if not working_tree.has_key(section):
					raise SectionLoadError(section)
				else:
					working_tree = working_tree[section]
			
			#Attempt to grab the actual item
			try:
				return working_tree[item]
			except KeyError:
				raise ItemLoadError(item)
	
		#Check if value is in defaults before raising error
		except (ItemLoadError, SectionLoadError, FileLoadError), orig_error:
			if self.defaults is None:
				raise orig_error
			
			default_item_tree_key = self.defaults
			try:
				for i in filter(lambda x: x is not None, (file, section, item)):
					default_item_tree_key = default_item_tree_key[i]
				return default_item_tree_key
			except KeyError:
				raise orig_error
	
	"""Get all items within a section/file"""
	def get_items(self, file=None, section=None):
		if not file and not section:
			return None
		if file is not None and type(file) is not str:
			raise TypeError('file must be of type str, got %s' % type(file))
		if section is not None and type(section) is not str:
			raise TypeError('section must be of type section, got %s' % type(section))
		
		matched_items = copy.deepcopy(self._item_tree)
		
		raise StandardError('Reimplement')
		
		if file and self.file_matters:
			try:
				matched_items = matched_items[file]
			except KeyError:
				pass
		
		if section and self.section_matters:
			try:
				matched_items = matched_items[section]
			except KeyError:
				pass
			
		return matched_items
		
	def load(self, file, raise_errors=False):
		try:
			self._parse_file(open(file))
		except (IOError, ParsingError), e:
			if raise_errors:
				raise e
	
	section_regex = re.compile(
		r'^'
		r'[\s]*'						#Leading whitespace
		
		r'\['
		r'(?P<section_name>[^[\]#]+)'	#[Section name] (no ] or [ or #)
		r'\]'
		
		r'[\s]*'						#Trailing whitespace
		r'(#.*)?'						#Trailing comments
		r'$'
	)
	
	item_regex = re.compile(
		r'^'
		r'[\s]*'						#Leading whitespace
		
		r'(?P<item_name>[^=#\s]+)'		#Name of the item (no whitespace, =, or #)
		r'[\s]*'						#Formatting whitespace between name and =
		r'='							#Equal between item name and item value
		r'[\s]*'						#Formatting whitespace = and value
		r'(?P<item_val>[^=#\s]+)'		#Item value(no whitespace, =, or #)
		
		r'[\s]*'						#Trailing whitespace
		r'(#.*)?'						#Trailing comments
		r'$'
	)
	
	def _parse_file(self, config_file):
		found_items = {}
		current_section = None
		for line_num, line in enumerate(config_file):
			line_num += 1 #Line 0 doesn't make sense
		
			#Comment found or whitespace line
			if len(line.strip()) == 0 or line.strip()[0] == '#':
				continue
			
			match = self.section_regex.match(line.strip())
			#is section
			if match:
				if self.section_matters:
					current_section = match.group('section_name')
					found_items[current_section] = {}
				continue
			
			match = self.item_regex.match(line.strip())
			#is item
			if match:
				#Item is found outside of section
				if self.section_matters and current_section is None:
					raise ParsingError(config_file.name, line, line_num)
					
				if self.section_matters:
					found_items[current_section][match.group('item_name')] = match.group('item_val')
				else:
					found_items[match.group('item_name')] = match.group('item_val')
			else:
				raise ParsingError(config_file.name, line, line_num)
			
		if self.file_matters:
			self._item_tree[config_file.name] = found_items
		else:
			self._item_tree.update(found_items)
			

"""Base Exception class"""
class ConfigError(Exception):
	
	def __init__(self, msg=''):
		self.msg = msg

	def __str__(self):
		return self.msg

"""Thrown when an identifier is not specific enough for given options"""
class IdentifierError(ConfigError):
	
	def __init__(self, identifier, file_matters, section_matters):
		ConfigError.__init__(self,
		'Invalid identfier "%s" given options file_matters=%s and section_matters=%s' %
		(identifier, file_matters, section_matters))
	
"""Thrown when trying to access a config item that can't be found"""
class ItemLoadError(ConfigError):

	def __init__(self, item):
		ConfigError.__init__(self, 'Cannot load item "%s"' %
							(item))
							
		self.item = item

"""Thrown when trying to access a section that can't be found"""
class SectionLoadError(ConfigError):

	def __init__(self, section):
		ConfigError.__init__(self, 'Cannot load section "%s"' %
							(section))
							
		self.section = section	

"""Thrown when trying to access a file that can't be found"""
class FileLoadError(ConfigError):

	def __init__(self, file):
		ConfigError.__init__(self, 'Cannot load file "%s"' %
							(file))
							
		self.file = file

"""Thrown when a line has a syntax error within a file"""
class ParsingError(ConfigError):

	def __init__(self, conf_file, line, line_num):
		ConfigError.__init__(self, 'Error on line #%s in file "%s". Given line:\n%s' %
							(line_num, conf_file, line))
							
		self.conf_file = conf_file
		self.line = line