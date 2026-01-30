# CDM Python frontend

Python frontend to communicate with the CDM. This library implements the 0mq API

## Build & install

To build the project run: `python3 setup.py build` which will also build the cdm_bindings module.

To install it: `python3 setup.py install --user`

### Manual build

To compile the tiny cdm_bindings module manually run: `bash -c "cd common-cdm && g++ -O3 -shared -std=c++17 -fPIC $(python3 -m pybind11 --includes) cdm_bindings.cpp -o ../cdm_bindings$(python3-config --extension-suffix)"`
Note that the module depends on pybind11.

In mac:
```
bash -c "cd common-cdm && g++ -O3 -shared -std=c++17 -fPIC -Wl,-undefined,dynamic_lookup $(python3 -m pybind11 --includes) $(python3-config --ldflags) cdm_bindings.cpp -o ../cdm_bindings$(python3-config --extension-suffix)"
```

## GUI

Once the project is installed the GUI can be executed running "cdm_gui" command. 

To run the gui without installing the project `python3 -m cdm_gui.widget` can be used. 

## Pushing new version to PyPi

Build dist: `python3 setup.py build bdist sdist`
Push example: `twine upload --repository pypi --verbose dist/virgo_pycdm-X.Y.Z.tar.gz`

TODO: Would be nice to have this done at CI/CD at merge time in Gitlab

## Integration tests

Before running intergration tests we must run `export PYTHONPATH="$PWD"` in order to detect the test coverage. Then we can proceed by executing `pytest -x -rx -rP -vvv --cov=$PWD/pycdm --cov-report html integration_tests`
