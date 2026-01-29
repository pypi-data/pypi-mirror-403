# WinRAM
## The honest Python-to-Windows interface
## Introduction
**WinRAM** is a Python library dedicated to exposing raw access to the user-mode memory on Windows. Before you ask, no, i will **not** support backwards compatibility. It will be in line with bleeding edge standards. Follow or be left behind.

## Features
- Virtual Memory: No more of that kiddy Unix-inspired stuff from `mmap`, instead you call `vm = VirtualMemory(addr, size, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE)` and watch as virtual memory gets handed down on a silver platter, wrapped in a buffer-supported `memoryview`. 
- Constants: Yes. Constants are supported, so you can do `MEM_COMMIT` instead of fiddling with bitflags.
- Executable Memory: Yes, the widely recognisable **RWX** is supported. **JIT** developers would be happy, even though Python is slower than eight `C++` hot loops.
- Security: For security-obessesed people, **W^X** is supported (even though you have to flip flags like a maniac).

## Comparison with `mmap`:
**Scale is 0.4**, because i said so.
- Can allocate and free memory: Both support it. Boring, but useful.
- Mark down specific regions of memory with flags: WinRAM supports it. `mmap` does not.
- Query full regions: Another point to **WinRAM**.
- Commit and decommit?: WinRAM again. `mmap` dropping the ball here.


Result:

WinRAM: 1.6

`mmap`: 0.4

## Call for Action
CPython devs... Show love for **NT**. POSIX is too overrepresented.

## Conclusion
Get this library if you are sick and tired of constant-less ctypes binding, sick of baby abstractions, and sick of `mmap` and `POSIX` culture as a whole.