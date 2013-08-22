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
	
	Identifier syntax: [file].[section].name
	Example: user_db.user1.password
	
	Whether file or section are required depend on 
	if section_matters or file_matters are set to True
	"""
	def get_item(self, identifier):
		idents = identifier.split('.')
		
		min_idents = 1
		if self.section_matters: min_idents += 1
		if self.file_matters: min_idents += 1
		if not len(idents) >= min_idents:
			raise IdentifierError(identifier, self.file_matters, self.section_matters)
			
		#Account for item names with a "." in the name
		idents[min_idents-1:] = ['.'.join(idents[min_idents-1:])]
		
		try:
			#See if first identifier is a file, make sure file is loaded
			if self.file_matters:
				if not self._item_tree.has_key(idents[0]): 
					if not self.explicit_load:
						self.load(idents[0])
					else:
						raise FileLoadError(idents[0], identifier)
			
			#See if second identifier is a section
			if self.section_matters:
				if self.file_matters:
					if not self._item_tree[idents[0]].has_key(idents[1]):
						raise SectionLoadError(idents[1], identifier)
				else:
					if not self._item_tree.has_key(idents[1]):
						raise SectionLoadError(idents[1], identifier)
			
			#Attempt to grab the actual item
			try:
				item_tree_key = self._item_tree
				for i in idents:
					item_tree_key = item_tree_key[i]
				return item_tree_key
			except KeyError:
				raise ItemLoadError(idents[min_idents-1:], identifier)
	
		#Check if value is in defaults before raising error
		except (ItemLoadError, SectionLoadError, FileLoadError), orig_error:
			if self.defaults is None:
				raise orig_error
			
			default_item_tree_key = self.defaults
			try:
				for i in idents:
					default_item_tree_key = default_item_tree_key[i]
				return default_item_tree_key
			except KeyError:
				raise orig_error
	
	"""Get all items within a section/file"""
	def get_items(self, file=None, section=None):
		if not file and not section:
			return None
		if section is not None and type(file) is not str:
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
		
			#Comment found
			if line.strip()[0] == '#':
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

	def __init__(self, item, identifier):
		ConfigError.__init__(self, 'Cannot load item "%s", given identifier "%s"' %
							(item, identifier))
							
		self.identifier = identifier
		self.item = item

"""Thrown when trying to access a section that can't be found"""
class SectionLoadError(ConfigError):

	def __init__(self, section, identifier):
		ConfigError.__init__(self, 'Cannot load section "%s", given identifier "%s"' %
							(section, identifier))
							
		self.identifier = identifier
		self.section = section	

"""Thrown when trying to access a file that can't be found"""
class FileLoadError(ConfigError):

	def __init__(self, file, identifier):
		ConfigError.__init__(self, 'Cannot load file "%s", given identifier "%s"' %
							(file, identifier))
							
		self.identifier = identifier
		self.file = file

"""Thrown when trying to access a file that can't be found"""
class ParsingError(ConfigError):

	def __init__(self, conf_file, line, line_num):
		ConfigError.__init__(self, 'Error on line #%s in file "%s". Given line:\n%s' %
							(line_num, conf_file, line))
							
		self.conf_file = conf_file
		self.line = line