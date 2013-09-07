import copy, re

class PyConf():
	"""Configuration file parser similar to the built in configparser.py"""
	
	def __init__(self, defaults=None, files=[], section_matters=True,
				 file_matters=False, explicit_load=True, silent_errors=True):
		"""Inialize your PyConf object
        
        Args:
            defaults (dict): Dictionary that PyConf will reference whenever
            Default: None	 it can't find a certain config item. Should be
                             setup depending on how your file_matters and
                             section_matters arguments are passed. Example
                             with both being True:
                             {
                                'file_name':
                                {
                                    'section_name':
                                    {
                                        'item_name':'item_value'
                                    }
                                }
                            }
            
            files (list(str), list(file)): All the files you want PyConf to
            Default: []                    auto-load upon initialization.
                                           By default if it can't load a
                                           file it will just skip it.
            
            section_matters (bool): Whether or not sections will be tracked
            Default: True           when loading files or config items. If
                                    they are tracked you must supply the
                                    section name you wish to load your item
                                    from everytime you call get_item().
            
            file_matters (bool): Same as section_matters but for the actual
            Default: False       file that you parse from. (like "config.ini")
                                 
            explicit_load (bool): If False, PyConf will attempt to load files
            Default: False        that haven't been loaded yet when calling
                                  get_item(). It is potentially dangerous to
                                  enable this feature, as you could be loading
                                  arbitrary files upon each get_item() call.
            
            silent_errors (bool): Whether or not to ignore errors thrown when
            Default: True         loading files. Having this set to True is
                                  preferable as you can just fall back to your
                                  set default values.
		"""
		self.defaults = defaults
		self.section_matters = section_matters
		self.file_matters = file_matters
		self.explicit_load = explicit_load
		self.silent_errors = silent_errors
		
		self._item_tree = {}
		
		for f in files:
			self.load(f)
	
	def load(self, config_file, silent=None):
		"""Load your config file for reading and writing values
        
        Args:
            config_file (str, file): Config file you wish to parse and grab
                                     values from.
            
            silent (bool): If silent is False parsing/loading errors will be
                           thrown. It's preferable to set silent to True
                           and rely on your default values in case of errors.
                           Default: self.silent_errors
        Raises:
            TypeError: config_file is not file or str
            IOError: Cannot load given file name
            ParsingError: Given config file has invalid syntax
		"""
		if type(silent) is not bool:
			silent = self.silent_errors

		try:
			if type(config_file) == str:
				with open(config_file) as f:
					self._parse_file(f)
			elif type(config_file) == file:
				self._parse_file(f)
			else:
				raise TypeError('load function must be either a file name or file object, got %s' %
								type(config_file))
		except (IOError, ParsingError), e:
			if not silent:
				raise e

	def get_item(self, item, section=None, conf_file=None):
		"""Get value of a config item
        
        If the specified item, section, and config file match cannot be found,
        the function will check the provided default values and return that
        item value if found.
        
        Whether file or section are required depend on 
        if self.section_matters or self.file_matters are set to True
        
        Args:
            item (str): Name of the config file itme you wish to load
            
            section (str): Name of the section to search for the config item.
            Default: None  Ignored if self.section_matters is False.
            
            conf_file (str): Name of the physical config file to search for the
            Default: None    config item. Ignored if self.file_matters is False.
                             
        Returns:
            A string of the value matched.

        Raises:
            FileLoadError: The class cannot find the provided config file
            SectionLoadError: The class cannot find the provided section
            ItemLoadError: The class cannot find the provided item name
            TypeError: Any of the arguments provided are not type str
		"""
		#Validate arguments
		if type(section) is not str and self.section_matters:
			raise TypeError('Expected type str for "section" got %s' % type(section))
		if type(conf_file) is not str and self.file_matters:
			raise TypeError('Expected type str for "file" got %s' % type(conf_file))
		if type(item) is not str:
			raise TypeError('Expected type str for "item" got %s' % type(item))
		
		try:
			working_tree = self._item_tree
		
			#Validate file identifier, make sure file is loaded
			if self.file_matters and conf_file is not None:
				if not working_tree.has_key(conf_file): 
					if not self.explicit_load:
						self.load(conf_file, silent=False)
						working_tree = working_tree[conf_file]
					else:
						raise FileLoadError(conf_file)
				else:
					working_tree = working_tree[conf_file]
			
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
				for i in filter(lambda x: x is not None, (conf_file, section, item)):
					default_item_tree_key = default_item_tree_key[i]
				return default_item_tree_key
			except KeyError:
				raise orig_error
	
	#TODO: Include default values
	def get_items(self, section=None, conf_file=None):
		"""Get all items within a section or file combination

        If both section and conf_file are None then the entire config item
        tree will be return.
        
        Args:
            section (str): Name of the section to search for.
            Default: None  Ignored if self.section_matters is False.
            
            conf_file (str): Name of the physical config file to search for.
            Default: None    config item. Ignored if self.file_matters is False.
                             
        Returns:
            Dictionary of item values in a format such as:
            {
                'file_name':
                {
                    'section_name':
                    {
                        'item_name':'item_value'
                    }
                }
            }

        Raises:
            FileLoadError: The class cannot find the provided config file
            SectionLoadError: The class cannot find the provided section
            ItemLoadError: The class cannot find the provided item name
            TypeError: Any of the arguments provided are not type str
		"""
		if not conf_file and not section:
			return None
		if conf_file is not None and type(conf_file) is not str:
			raise TypeError('file must be of type str, got %s' % type(conf_file))
		if section is not None and type(section) is not str:
			raise TypeError('section must be of type section, got %s' % type(section))
		
		matched_items = copy.deepcopy(self._item_tree)
		
		raise StandardError('Reimplement')
		
		if conf_file and self.file_matters:
			try:
				matched_file = matched_items[conf_file]
			except KeyError:
				pass
		
		if section and self.section_matters:
				if matched_file:
					matched_items = matched_items[section]
				else:
					search_list = matched_items
					matched_items
					for temp_file in matched_items:
						try:
							matched_items = temp_file[section]
						except KeyError:
							pass
			
		return matched_items
	
	_section_regex = re.compile(
		r'^'
		r'[\s]*'						#Leading whitespace
		
		r'\['
		r'(?P<section_name>[^[\]#]+)'	#[Section name] (no ] or [ or #)
		r'\]'
		
		r'[\s]*'						#Trailing whitespace
		r'(#.*)?'						#Trailing comments
		r'$'
	)
	
	_item_regex = re.compile(
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
	
	def _parse_file(self, conf_file):
		found_items = {}
		current_section = None
		for line_num, line in enumerate(conf_file):
			line_num += 1 #Line 0 doesn't make sense
		
			#Comment found or whitespace line
			if len(line.strip()) == 0 or line.strip()[0] == '#':
				continue
			
			match = self._section_regex.match(line.strip())
			#is section
			if match:
				if self.section_matters:
					current_section = match.group('section_name')
					found_items[current_section] = {}
				continue
			
			match = self._item_regex.match(line.strip())
			#is item
			if match:
				#Item is found outside of section
				if self.section_matters and current_section is None:
					raise ParsingError(conf_file.name, line, line_num)
					
				if self.section_matters:
					found_items[current_section][match.group('item_name')] = match.group('item_val')
				else:
					found_items[match.group('item_name')] = match.group('item_val')
			else:
				raise ParsingError(conf_file.name, line, line_num)
			
		if self.file_matters:
			self._item_tree[conf_file.name] = found_items
		else:
			self._item_tree.update(found_items)
			

class ConfigError(Exception):
	"""Base Exception class"""
	
	def __init__(self, msg=''):
		self.msg = msg

	def __str__(self):
		return self.msg

class IdentifierError(ConfigError):
	"""Thrown when an identifier is not specific enough for given options"""
	
	def __init__(self, identifier, file_matters, section_matters):
		ConfigError.__init__(self,
		'Invalid identfier "%s" given options file_matters=%s and section_matters=%s' %
		(identifier, file_matters, section_matters))

class ItemLoadError(ConfigError):
	"""Thrown when trying to access a config item that can't be found"""

	def __init__(self, item):
		ConfigError.__init__(self, 'Cannot load item "%s"' %
							(item))
							
		self.item = item

class SectionLoadError(ConfigError):
	"""Thrown when trying to access a section that can't be found"""

	def __init__(self, section):
		ConfigError.__init__(self, 'Cannot load section "%s"' %
							(section))
							
		self.section = section	

class FileLoadError(ConfigError):
	"""Thrown when trying to access a file that can't be found"""
	
	def __init__(self, conf_file):
		ConfigError.__init__(self, 'Cannot load file "%s"' %
							(conf_file))
							
		self.conf_file = conf_file

class ParsingError(ConfigError):
	"""Thrown when a line has a syntax error within a file"""

	def __init__(self, conf_file, line, line_num):
		ConfigError.__init__(self, 'Error on line #%s in file "%s". Given line:\n%s' %
							(line_num, conf_file, line.strip()))
							
		self.conf_file = conf_file
		self.line = line