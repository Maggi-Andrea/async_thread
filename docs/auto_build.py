'''
Created on 6 dic 2019

@author: Andrea
'''
import sphinx_autobuild

import sys
import os


def main():
  _this_path = os.path.dirname(__file__)
  python_path = os.path.dirname(sys.executable)
  python_script_path = os.path.join(python_path, r'Scripts')
  env_path = os.environ.get('PATH')
  if python_script_path not in env_path:
    print("Adding Python script path")
    os.environ['PATH'] = env_path + f";{python_script_path}"
  sys.argv = [
    'sphinx-autobuild', './source', './build/html_live',
    '--port', '8000',
    '--watch', '..',
  ]
  sphinx_autobuild.main()

if __name__ == '__main__':
  main()
