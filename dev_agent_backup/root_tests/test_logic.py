import pytest
import sys
from unittest import mock
import os

# Custom mock for Streamlit to handle layout and form submissions on import
class StreamlitMock(mock.MagicMock):
    def columns(self, spec):
        if isinstance(spec, int):
            return [mock.MagicMock() for _ in range(spec)]
        return [mock.MagicMock() for _ in spec]
    
    def tabs(self, tabs_list):
        return [mock.MagicMock() for _ in tabs_list]
        
    def selectbox(self, label, options=None, **kwargs):
        if options:
            return options[0]
        return ""
        
    def form_submit_button(self, label, **kwargs):
        return False
        
    def button(self, label, **kwargs):
        return False

    def file_uploader(self, *args, **kwargs):
        return None

# Mock get_connection to avoid hitting the SQLite file on disk
database_mock = mock.MagicMock()
database_mock.get_connection.return_value = mock.MagicMock()

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

import importlib

def test_imports():
    # Save original modules
    orig_pandas = sys.modules.get('pandas')
    orig_streamlit = sys.modules.get('streamlit')
    orig_database = sys.modules.get('database')
    orig_auth = sys.modules.get('auth')
    orig_components = sys.modules.get('components')
    
    # Mock them
    sys.modules['pandas'] = mock.MagicMock()
    sys.modules['streamlit'] = StreamlitMock()
    sys.modules['database'] = database_mock
    auth_mock = mock.MagicMock()
    auth_mock.get_department_by_code.return_value = None
    sys.modules['auth'] = auth_mock
    sys.modules['components'] = mock.MagicMock()
    
    try:
        if 'src.pages.2_QuanLyCanBo' in sys.modules:
            del sys.modules['src.pages.2_QuanLyCanBo']
        if 'src.pages.4_CaiDatHeThong' in sys.modules:
            del sys.modules['src.pages.4_CaiDatHeThong']
            
        importlib.import_module("src.pages.2_QuanLyCanBo")
        importlib.import_module("src.pages.4_CaiDatHeThong")
    finally:
        # Remove imported pages from cache so they don't persist with mocked imports
        sys.modules.pop('src.pages.2_QuanLyCanBo', None)
        sys.modules.pop('src.pages.4_CaiDatHeThong', None)
        
        # Restore original modules
        if orig_pandas is not None:
            sys.modules['pandas'] = orig_pandas
        else:
            sys.modules.pop('pandas', None)
            
        if orig_streamlit is not None:
            sys.modules['streamlit'] = orig_streamlit
        else:
            sys.modules.pop('streamlit', None)
            
        if orig_database is not None:
            sys.modules['database'] = orig_database
        else:
            sys.modules.pop('database', None)

        if orig_auth is not None:
            sys.modules['auth'] = orig_auth
        else:
            sys.modules.pop('auth', None)

        if orig_components is not None:
            sys.modules['components'] = orig_components
        else:
            sys.modules.pop('components', None)
