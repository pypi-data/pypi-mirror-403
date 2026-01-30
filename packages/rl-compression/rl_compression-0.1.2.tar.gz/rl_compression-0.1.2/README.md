# Run-Length Encoding / Decoding

This module contains a simple implementation of **run-length encoding (RLE)**
and **run-length decoding (RLD)**.

---

## What the run-length encoder does

Run-length encoding is a basic compression technique.

If you have repeated values next to each other, you store:
- how many times they repeat
- and the value itself

Ex: ('a', 'a', 'a', 'b', 'b', 'c') --> (3, 'a', 2, 'b', 1, 'c')

---

## What the run-length decoder does

This run-lenght decoder iterates through ever 2nd index of the outputed list from RLE
and it runs a while loop which appends the decoded output for every count value pair in the
encoded list.

Ex: (3, 'a', 2, 'b', 1, 'c') --> ('a', 'a', 'a', 'b', 'b', 'c') 

---

## How to use this module

This module is made up of two main methods. RLE.py contains the RLE method which is the Run-Length Encoder. RLD.py contains the RLD method which is the Run-Length Decoder.

- RLE specifically accepts sequenced iterable types. So only Strings, Lists, and Bytes.
- RLD specifically accepts only the outputed list from RLE.

They can be called as such:

```python
from rl_compression import RLE, RLD

data = ['a', 'a', 'a', 'b', 'b', 'c']
encoded = RLE(data)
# can also pass data directly RLE('aaabbc')

decoded = RLD(encoded)
```
