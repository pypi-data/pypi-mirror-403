from setuptools import setup

setup(
    name='knoxscript',
    version='0.1.3',
    py_modules=['knox_engine'],
    install_requires=['opencv-python', 'numpy'],
    entry_points={
        'console_scripts': [
            'knox=knox_engine:main',
        ],
    },
)
