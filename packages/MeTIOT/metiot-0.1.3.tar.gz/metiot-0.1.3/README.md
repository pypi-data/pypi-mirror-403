# MeT IOT Communication

## Useful Links

* [API Reference](https://github.com/Microelectronic-Technologies/MeTIOTCommunication/blob/main/docs/API_REFERENCE.md)
* [Python Library Guide](https://github.com/Microelectronic-Technologies/MeTIOTCommunication/blob/main/docs/PYTHON_LIB_GUIDE.md)
* [Example Projects](https://github.com/Microelectronic-Technologies/MeTIOTCommunication/tree/main/examples)

## Changelog `v0.1.3`

```plaintext
- Fix invalid pointer error on python program exit
```

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
2. Create and navigate into build directory
```bash
mkdir build
cd build
```
3. Compile library using CMake
```bash
cmake ..
cmake --build . --config Release
```
4. Export path to python
```bash
export PYTHONPATH=./src/python_bindings:$PYTHONPATH
```
5. Now you can use and import the library in your current directory
6. *(optional)* Test the library is python
```bash
python3
```
```py
import MeTIOT
client = MeTIOT.DeviceClient("0.0.0.0", 12345)
type(client)
client.connect()
```

