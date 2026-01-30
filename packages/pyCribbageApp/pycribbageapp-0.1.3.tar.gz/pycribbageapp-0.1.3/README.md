# pyCribbageApp

Source code: [GitHub](https://github.com/KevinRGeurts/pyCribbageApp)
---
pyCribbageApp is a python package that provides a tkinter based GUI for playing cribbage games using the CribbageSim package.

## Requirements

- tkAppFramework>=0.9.2: [GitHub](https://github.com/KevinRGeurts/tkAppFramework), [PyPi](https://pypi.org/project/tkAppFramework/)
- CribbageSim>=1.0.1: [GitHub](https://github.com/KevinRGeurts/CribbageSim), [PyPi](https://pypi.org/project/CribbageSim/)

## Basic usage

The simplest way to run the app is:

```
python -m pyCribbageApp.CribbageApp 
```

This assumes that the required packages are installed. To learn how to use the app, select Help | View Help... from the menu bar.

## Unittests

Unittests for the pyCribbageApp package are in the tests directory, with filenames starting with test_. To run the unittests,
type ```python -m unittest discover -s ..\..\tests -v``` in a terminal window in the src\pyCribbageApp directory.

## License

MIT License. See the LICENSE file for details