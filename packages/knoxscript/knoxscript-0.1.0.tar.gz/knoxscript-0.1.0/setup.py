from setuptools import setup

setup(
    name='knoxscript',
    version='0.1.0',
    py_modules=['knox_engine'],
    install_requires=['opencv-python', 'numpy'],
    entry_points={
        'console_scripts': [
            'knox=knox_engine:main',
        ],
    },
)
