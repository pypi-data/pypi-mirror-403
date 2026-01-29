from ctypes import WinError, byref, get_last_error, c_ubyte, sizeof
from ctypes.wintypes import DWORD
from typing import Optional
from ._raw.bindings import MEMORY_BASIC_INFORMATION, VirtualAlloc, VirtualFree, VirtualProtect, VirtualQuery
from  .constants import MEM_RELEASE

class VirtualMemory:
	def __init__(self, address: Optional[int], size: int, allocation_type: int, protect: int):
		self._mem =  VirtualMemory.allocate(address, size, allocation_type, protect)
		mem2 = memoryview((c_ubyte * size).from_address(self._mem)).cast('B')
		self.mem = mem2
	@staticmethod
	def allocate(address: Optional[int], size: int, allocation_type: int, protect: int):
		mem: int = VirtualAlloc(address, size, allocation_type, protect)
		if not mem:
			raise WinError(get_last_error())
		return mem
	@staticmethod
	def free(address: int, size: int, free_type: int):
		if not VirtualFree(address, size, free_type):
			raise WinError(get_last_error())

	def release(self):
		VirtualMemory.free(self._mem, 0, MEM_RELEASE)
		self._mem = 0
		self.mem.release()

	def __del__(self):
		'''Undeterministic. Use VirtualMemory.release whenever possible'''
		if self._mem:
			self.release()

	@staticmethod
	def protect(address: int, size: int, new_protect: int) -> int:
		old_protect = DWORD(0)
		if not VirtualProtect(address, size, new_protect, byref(old_protect)):
			raise WinError(get_last_error())
		return old_protect.value
	@staticmethod
	def query(address: Optional[int]) -> MEMORY_BASIC_INFORMATION:
		basic = MEMORY_BASIC_INFORMATION(0, 0, 0, 0, 0, 0, 0, 0)
		size = VirtualQuery(address, byref(basic), sizeof(basic))
		if size == 0:
			raise WinError(get_last_error())
		return basic
	def __enter__(self):
		return self
	def __exit__(self, *unk_args):
		if self._mem:
			self.release()