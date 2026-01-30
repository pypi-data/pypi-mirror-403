CC:=g++
CCFLAGS:=-Ofast -march=native -flto=auto -DNDEBUG -shared -std=c++20 -fPIC

PYTHON:=python3
PYBIND_INCLUDES:=$(strip $(shell $(PYTHON) -m pybind11 --includes))
PYEXT:=$(strip $(shell $(PYTHON)-config --extension-suffix))

tagmap$(PYEXT): tagmap_pybind.cc tagmap/tagmap.h
	$(CC) $(CCFLAGS) $(PYBIND_INCLUDES) tagmap_pybind.cc -o tagmap$(PYEXT)

clean:
	rm -f tagmap$(PYEXT)
