# MeT IOT Communication

## Useful Links

* [API Reference](https://github.com/Microelectronic-Technologies/MeTIOTCommunication/blob/main/docs/API_REFERENCE.md)
* [Python Library Guide](https://github.com/Microelectronic-Technologies/MeTIOTCommunication/blob/main/docs/PYTHON_LIB_GUIDE.md)
* [Example Projects](https://github.com/Microelectronic-Technologies/MeTIOTCommunication/tree/main/examples)

## Changelog `v0.1.3`

- Improved memory deallocation sequence during shutdown to reduce pointer corruption.

## Known issues

- **Exit Signal (SIGABRT/SIGSEGV):** Upon exiting the Python interpreter, a `free(): invalid pointer` error may occur.
  - **Reason:** This is a known teardown conflict between the Python Garbage Collector and the C++ Runtime (libstdc++). It occurs after all user code has executed.
  - **Impact:** None. This does not affect data transmission or device logic during the program's lifecycle.

## How To Use

### Importing the Library

#### Use pip to install the library

```sh
pip install MeTIOT
```

> [!NOTE]
> This library is not pre-compiled.
> You must have installed on your system (Other version may work but are official unsupported):
> * GCC >= 15.2.1
> * CMake >= 3.10

### Programming with the Library

#### Testing the library imported successfully

You can use this code to test you can successfully import the library into your code.

```py
import MeTIOT

client = MeTIOT.DeviceClient("0.0.0.0", 12345)

print(type(client))
print("MeTIOT import successful!")
```

#### Using the library

For further information on how to use this library refer to the [PYTHON_LIB_GUIDE.md document](https://github.com/Microelectronic-Technologies/MeTIOTCommunication/blob/main/docs/PYTHON_LIB_GUIDE.md).

## How to compile and use from this repository

Linux based systems:

1. Clone the repository
```bash
git clone https://github.com/Microelectronic-Technologies/MeTIOTCommunication.git
```
2. Navigate into repository
```bash
cd MeTIOTCommunication/
```
3. Create and navigate into build directory
```bash
mkdir build
cd build
```
4. Compile library using CMake
```bash
cmake ..
cmake --build . --config Release
```
5. Export path to python
```bash
export PYTHONPATH=./src/python_bindings:$PYTHONPATH
```
6. Now you can use and import the library in your current directory
7. *(optional)* Test the library is python
```bash
python3
```
```py
import MeTIOT
client = MeTIOT.DeviceClient("0.0.0.0", 12345)
type(client)
```

