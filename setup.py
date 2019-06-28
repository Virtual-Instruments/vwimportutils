from setuptools import setup, find_packages

setup(
    name='vwimporttools',
    version='1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'click',
        'requests'
    ],
    entry_points='''
        [console_scripts]
        vw_csv_nicknames_to_json=vwimporttools.vw_csv_nicknames_to_json:main
        vw_csv_relations_to_json=vwimporttools.vw_csv_relations_to_json:main
        vw_import_entities=vwimporttools.vw_import_entities:main
    '''
)
