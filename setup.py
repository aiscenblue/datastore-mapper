from distutils.core import setup

setup(
    name='datastore_mapper',
    version='0.0.3',
    description='Object Mapper for google datastore withour using appengine',
    author='Jeffrey Marvin Forones',
    author_email='aiscenblue@gmail.com',
    license='MIT',
    url='https://github.com/aiscenblue/datastore-mapper',
    packages=['datastore_mapper'],
    keywords=['datastore', 'google datastore', 'datastore mapper'],  # arbitrary keywords
    install_requires=['google-cloud-datastore', 'sanic'],
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5'
    ]
)
