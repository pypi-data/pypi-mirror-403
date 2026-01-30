import setuptools

with open('README.md', 'r', encoding='utf-8') as fh:
	long_description = fh.read()

setuptools.setup(
	name='debugaid',
	version='1.0.0',
	author='FelineFantasy',
	author_email='mailsalavata5@gmail.com',
	description='A lightweight Python toolkit for debugging and performance analysis',
	long_description=long_description,
	long_description_content_type='text/markdown',
	packages=['debugaid'],
	include_package_data=True,
	classifiers=[
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
	],
	python_requires='>=3.6',
)