from setuptools import setup, find_packages, Extension

setup(
    name = 'virgo-pycdm',
    packages = find_packages(),
    platforms=['any'],
    entry_points = {
        'console_scripts': ['cdm_gui=cdm_gui.widget:main'],
    },
    version = '0.4.3',
    author = 'David Roman',
    author_email = 'droman@ifae.es',
    url = 'https://gitlab.pic.es/virgo-sw/cdm-python-frontend',
    license = 'BSD-3',
    include_package_data=True,
    package_data={"pycdm": ["py.typed"]},
    install_requires=[
            'appdirs',
            'PyQt5',
            'pybind11',
            'pyqt_tools',
            'pyzmq',
            'tomli',
        ],
	classifiers=[
		'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
		'Programming Language :: Python :: 3'
	],
    ext_modules=[
        Extension(
            name="cdm_bindings",  # as it would be imported
            sources=["common-cdm/cdm_bindings.cpp", "common-cdm/frame_decoding.cpp"], # all sources are compiled into a single binary file
            extra_link_args=["-lfmt"],
            extra_compile_args=["-std=c++20"],
        ),
    ]
)
