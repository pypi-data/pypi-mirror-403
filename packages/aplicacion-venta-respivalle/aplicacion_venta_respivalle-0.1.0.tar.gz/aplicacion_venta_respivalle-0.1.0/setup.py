from setuptools import setup, find_packages

setup(
    name='aplicacion_venta_respivalle',
    version='0.1.0',
    # user='',
    author='Roger Espinoza',
    author_email='oespinozavalle@gmail.com',
    description='Paquete para gestionar ventas, precios, impuestos y descuentos.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com',
    packages=find_packages(),
    install_requires=[],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',   # Cambia esto según sea necesario
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
)