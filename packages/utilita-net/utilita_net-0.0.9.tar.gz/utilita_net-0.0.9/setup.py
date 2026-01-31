from setuptools import setup, find_namespace_packages
setup(
  name = 'utilita-net', # How you named your package folder (MyLib)
  version = '0.0.9', # Start with a small number and increase it with every change you make
  packages=find_namespace_packages(include=['utilita.*']),
  license= 'MIT', # Chose a license from here: https://help.github.com/articles/licensing-a-repository
  description = 'utilita but with helpers for web services', # Give a short description about your library
  author = 'Tommy Rojo',
  author_email = 'tr.trojo@gmail.com',
  url = 'https://github.com/trtrojo', # Provide either the link to your github or to your website
  download_url = 'https://github.com/trtrojo',
  keywords = [], # Keywords that define your package best
  install_requires= ['msal>=1.24.1', 'requests>=2.25.0', 'google-cloud-pubsub>=2.7.0', 'google-cloud-storage>=1.41.1', 'google-auth'],
  classifiers=[
    'Development Status :: 3 - Alpha', # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
    'Intended Audience :: Developers', # Define your audience
    'Topic :: Utilities',
    'License :: OSI Approved :: MIT License', # Again, pick a license
    'Programming Language :: Python :: 3.8'
  ],
    entry_points={
        'console_scripts': [
            'init-microsofthelper=utilita.net.scripts.init_microsofthelper:cli',
        ],
    },
)