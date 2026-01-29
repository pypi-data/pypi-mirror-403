from .._raw.dll import kernel32
from ctypes.wintypes import BOOL, DWORD, LPCVOID, LPVOID, PDWORD, WORD
from ctypes import POINTER, Structure, c_size_t

kernel32.VirtualAlloc.argtypes = [LPVOID, c_size_t, DWORD, DWORD]
kernel32.VirtualAlloc.restype = LPVOID
VirtualAlloc = kernel32.VirtualAlloc
kernel32.VirtualFree.argtypes = [LPVOID, c_size_t, DWORD]
kernel32.VirtualFree.restype = BOOL
VirtualFree = kernel32.VirtualFree
kernel32.VirtualProtect.argtypes = [LPVOID, c_size_t, DWORD, PDWORD]
kernel32.VirtualProtect.restype = BOOL
VirtualProtect = kernel32.VirtualProtect

class MEMORY_BASIC_INFORMATION(Structure):
	'''Contains information about a range of pages in the virtual address space of a process. The VirtualQuery and VirtualQueryEx functions use this structure.'''
	_fields_ = [('BaseAddress', LPVOID),('AllocationBase', LPVOID),('AllocationProtect', DWORD),('PartitionId', WORD),('RegionSize', c_size_t),('State', DWORD),('Protect', DWORD),('Type', DWORD)]

PMEMORY_BASIC_INFORMATION = POINTER(MEMORY_BASIC_INFORMATION)

kernel32.VirtualQuery.argtypes = [LPCVOID, PMEMORY_BASIC_INFORMATION, c_size_t]
kernel32.VirtualQuery.restype = c_size_t
VirtualQuery = kernel32.VirtualQuery