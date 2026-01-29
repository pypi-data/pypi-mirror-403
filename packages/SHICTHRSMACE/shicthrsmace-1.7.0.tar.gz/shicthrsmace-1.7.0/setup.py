from setuptools import setup, find_packages

setup(name='SHICTHRSMACE',
      version='1.7.0',
      description='SHICTHRS MACE machine identity system',
      url='https://github.com/JNTMTMTM/SHICTHRS_MACE',
      author='SHICTHRS',
      author_email='contact@shicthrs.com',
      license='GPL-3.0',
      packages=find_packages(),
      include_package_data=True,
      install_requires=['colorama==0.4.6' , 'pywin32==311' , 'WMI==1.5.1'],
      zip_safe=False)
