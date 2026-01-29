from setuptools import setup, find_packages

setup(name='aplicacion_ventas_beto', version='0.1.0', author='Beto', author_email='albermontesbre@gmail.com',
      description='Aplicacion de ventas, impuestos y descuentos', long_description=open('README.md').read(),
      longdescription_content_type="text/markdown", url='https://github.com/usuario/gestor_ventas',
      packages=find_packages(), install_requires=[],
      classifiers=[
          'Programming Language :: Python :: 3',
          'License :: OSI Approved :: MIT License',
          'Operating System :: OS Independent',
      ], python_requires='>=3.6')
