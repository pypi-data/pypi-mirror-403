from tabulate import tabulate
from os import environ
from typing import Dict, List, Any, Union
from .types import Bool as types_bool
from dotenv import load_dotenv
from os.path import basename
from sys import argv, stderr, exit
import re
from textwrap import wrap



def camel_to_words(s: str) -> str:
    words = re.sub(r'(?<!^)(?=[A-Z])', ' ', s)
    return words


class TypeBase():

    def __call__(self, value):
        ...
        answer = None
        ...
        return answer
    
    def __str__(self):
        return camel_to_words(str(self.__class__.__name__))


class Bool(TypeBase):

    def __call__(self, value):
        return bool(types_bool.from_string(value))


class PositiveIntegerAndZero(TypeBase):

    def __call__(self, value):
        try:
            answer = int(value)
        except ValueError:
            raise ValueError(f"{repr(value)} must be an integer")
        if answer >= 0:
            return answer
        else:
            raise ValueError(f"value can't be negative")
            
    def __str__(self):
        return "Integer>=0"


class PositiveInteger(PositiveIntegerAndZero):

    def __call__(self, value):
        answer = PositiveIntegerAndZero.__call__(self, value)
        if not answer:
            raise ValueError(f"value can't be zero")
        return answer
            
    def __str__(self):
        return "Integer>0"


class Options(TypeBase):

    def __init__(self, options: Union[List, dict]):
        if not isinstance(options, (list, dict)):
            raise ValueError('options must be a dict or list')
        if not options:
            raise ValueError('options cannot be empty')
        if len(options)<2:
            raise ValueError('options must be two or more')
        self._options = options
    
    @property
    def options(self):
        return self._options

    @property
    def options_as_string(self):
        options = [repr(opt) for opt in self.options]
        return f"{', '.join(options[:-1])} or {options[-1]}"

    def __call__(self, value):
        
        if isinstance(self.options, dict):
            options = [ (str(key).lower().strip(), opt_value)
                       for key, opt_value in self.options.items()]
        else: # list
            options = [ (str(opt).lower().strip(), opt)
                       for opt in self.options]
        translator = dict(options)
        
        key = str(value).lower().strip()
        
        if key not in translator:
            raise ValueError(f"{repr(value)} is not {self.options_as_string}")
        answer = translator.get(key)

        return answer


class EnvsTypes():
    bool = staticmethod(Bool())
    positive_integer = staticmethod(PositiveInteger())
    positive_integer_and_zero = staticmethod(PositiveIntegerAndZero())
    Options = Options


class Envs():

    def __init__(self,
                 envfile_var_name: str = None,
                 envfile_var_description: str = 'Environment file overwrite',
                 envfile_default: str = '.env',
                 envfile_hide = False,
                 load_envfile_on_init = False,
                 load_envfile_on_first_get = True,
                 load_env_file_on_any_get = False):
        self._envfile_var_name = envfile_var_name
        self._envfile_var_description = envfile_var_description
        self._envfile_default = envfile_default
        self._envfile_hide = envfile_hide
        self._list: List[Dict] = []
        if load_envfile_on_init:
            self._load_dotenv()
        self._load_envfile_on_first_get = load_envfile_on_first_get
        self._load_env_file_on_any_get = load_env_file_on_any_get
        self._types = EnvsTypes()

    @property
    def types(self):
        return self._types
    
    def load_dotenv(self,
                     var_name: str = None,
                     var_description: str = 'Environment file overwrite',
                     default_file: str = '.env',
                     hide = False
                     ) -> None:
        
        if var_name is None:
            var_name = basename(argv[0])
            if var_name.endswith('.py'):
                var_name = var_name[:-3]
            var_name = f"{var_name}_env_file"
        
        envfile = self(var_name, default_file, str,
                       description = var_description,
                       hide = hide,
                       use_load_dotenv = False)
        
        load_dotenv(envfile)

    def _load_dotenv(self) -> None:
        self.load_dotenv(
            var_name = self._envfile_var_name,
            var_description = self._envfile_var_description,
            default_file = self._envfile_default,
            hide = self._envfile_hide
        )

    @staticmethod
    def _normalize_name(name:str) -> str:
        name = '_'.join(str(name).strip().upper().split()) if name else None
        if name is None:
            raise ValueError("Environment variable name cannot be empty")
        return name
   
    def __call__(self,
            name: str,
            default: Any = None,
            cast: callable = None,
            alias: dict = {},
            on_error_exit: bool = True,
            description = None,
            use_load_dotenv = None,
            hide = False
        ) -> Any:

        # Load envfile
        if use_load_dotenv is not False: # avoid max recursion depth exceeded
            if use_load_dotenv or self._load_env_file_on_any_get or (
                               not(self) and self._load_envfile_on_first_get):
                self._load_dotenv()

        # Normalize name
        name = self._normalize_name(name)

        # Normalize alias
        if alias:
            alias = dict(
                [(str(k).strip().lower(),
                str(v).strip()) for (k, v) in alias.items()])
            new_alias = {}
            for (key, alias_value) in alias.items():
                available_keys = [k for k in alias.keys() if k!=key ]
                while alias_value in available_keys:
                    available_keys.remove(alias_value)
                    alias_value = alias[alias_value]
                new_alias[key] = alias_value
            alias = new_alias

        # Try to obtain previously recorded data
        prev_description = None
        if self:
            prev_data = envs[name]
            if len(prev_data)==1:
                prev_data = prev_data[0]
                prev_cast = prev_data['cast']
                prev_default = prev_data['default']
                prev_alias = prev_data['alias']
                prev_description = prev_data['description']
                if cast is None:
                    cast = prev_cast
                if default is None:
                    default = prev_default
                if alias=={}:
                    alias = prev_alias
                if description is not None:
                    prev_description = None

        # Normalize cast
        denormalize_cast = None
        if cast is None:
            cast = str
        elif cast is bool:
            denormalize_cast = bool
            cast = self.types.bool
        elif isinstance(cast, (list, dict)):
            denormalize_cast = cast
            cast = self.types.Options(cast)

        # Intervene the description
        if isinstance(cast, self.types.Options):
            if description:
                description = f"{description} (use: {cast.options_as_string})"
            else:
                description = f"Use: {cast.options_as_string}"
        if prev_description is not None:
            description = prev_description

        # Get value from environment
        try:
            value = environ[name]
        except KeyError:
            value = default

        # Apply aliasing
        if alias:
            alias_key = str(value).strip().lower()
            if alias_key in alias:
                value = alias[alias_key]

        # Options
        options = set([str(default)]) if default is not None else set()
        for key, option_value in alias.items():
            options.add(key)
            options.add(option_value)
        options = list(options)
        options.sort()

        # Cast value
        if value!=default:
            try:
                value = cast(str(value))
            except Exception as e:
                if on_error_exit: # Show errors
                    msg = ("ERROR: invalid value for env var "
                           f"{name}: {value!r}\n{e}")
                    print(msg, file=stderr)
                    exit(1)
                else:
                    value = default

        # (De)normalize cast
        if denormalize_cast is not None:
            cast = denormalize_cast
        
        # Registry
        if not hide:
            registry = {
                'name': name,
                'cast': cast,
                'value': value,
                'default': default,
                'options': options,
                'description': description,
                'alias': alias}
            if not registry in self._list:
                self._list.append(registry)
                self._list.sort(key=lambda d: d["name"])
        
        # Return value
        return value
    
    def __iter__(self):
        return iter(self._list)

    def __len__(self):
        return len(self._list)

    def __bool__(self):
        return len(self._list)>0

    def __getitem__(self, i):
        if isinstance(i, str):
            name = self._normalize_name(i)
            return list(filter(lambda x: x['name']==name, self._list))
        return self._list[i]
    
    def __str__(self):
        if not self:
            return ''
        fields = ['name','value', 'default', 'cast', 'description']
        titles = {'cast': 'Type'}
        headers = [titles.get(f, str(f).capitalize()) for f in fields]
        def format(obj, name):
            if obj is None:
                return ''
            if obj is int:
                return 'Integer'
            if obj is float:
                return 'Float'
            if obj is str:
                return 'String'
            if obj is bool:
                return 'Bool'
            if callable(obj):
                if hasattr(obj, '__name__'):
                    return ' '.join(map(lambda w: w.capitalize(),
                        str(obj.__name__).replace('_', ' ').split()))
                return str(obj)
            if isinstance(obj, (list, dict)):
                if name=='cast':
                    return 'Options'
                return ', '.join([str(x) for x in obj])
            if name=='description':
                return '\n'.join(wrap(str(obj),
                                      width = 30,
                                      break_long_words = True,
                                      break_on_hyphens = False))
            if hasattr(obj, 'abbreviation'): #Address
                return obj.abbreviation
            return f"{obj}"
        table = [[format(r[f], f) for f in fields] for r in self]
        str_table = tabulate(table, headers=headers, tablefmt='grid')
        return f"\n{str_table}\n"

    def _data_of(self, name, key) -> Any:
        data = envs[name]
        if len(data)>1:
            raise KeyError('more than one env with that name')
        if len(data)<1:
            raise KeyError('no env with that name')
        data = data[0]
        return data[key]

    def cast_of(self, name) -> Any:
        return self._data_of(name, 'cast')
    
    def value_of(self, name) -> Any:
        return self._data_of(name, 'value')
    
    def default_of(self, name) -> Any:
        return self._data_of(name, 'default')
    
    def options_of(self, name) -> List:
        return self._data_of(name, 'options')
    
    def description_of(self, name) -> str:
        return self._data_of(name, 'description')
    
    def alias_of(self, name) -> Dict:
        return self._data_of(name, 'alias')

    @property
    def names(self) -> List:
        names = list(set([x['name'] for x in list(self)]))
        names.sort()
        return names


envs = Envs()
