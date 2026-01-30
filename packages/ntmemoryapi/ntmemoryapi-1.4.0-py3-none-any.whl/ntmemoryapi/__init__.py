# +-------------------------------------+
# |         ~ Author : Xenely ~         |
# +=====================================+
# | GitHub: https://github.com/Xenely14 |
# | Discord: xenely                     |
# +-------------------------------------+

import os
import ctypes
import psutil

# Local imports
from .misc import *
from .embed import *

# ==-------------------------------------------------------------------== #
# C-consts                                                                #
# ==-------------------------------------------------------------------== #

# Process access flags
PROCESS_ALL_ACCESS = 0x1F0FFF
PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
PROCESS_VM_OPERATION = 0x0008
PROCESS_QUERY_INFORMATION = 0x0400

# Memory protection constants
PAGE_NOACCESS = 0x01
PAGE_READONLY = 0x02
PAGE_READWRITE = 0x04
PAGE_WRITECOPY = 0x08
PAGE_EXECUTE = 0x10
PAGE_EXECUTE_READ = 0x20
PAGE_EXECUTE_READWRITE = 0x40
PAGE_EXECUTE_WRITECOPY = 0x80
PAGE_GUARD = 0x100
PAGE_NOCACHE = 0x200
PAGE_WRITECOMBINE = 0x400

# Memory state constants
MEM_COMMIT = 0x1000
MEM_RESERVE = 0x2000
MEM_FREE = 0x10000
MEM_PRIVATE = 0x20000
MEM_MAPPED = 0x40000
MEM_IMAGE = 0x1000000

# Memory type constants
MEM_IMAGE = 0x1000000
MEM_MAPPED = 0x40000
MEM_PRIVATE = 0x20000

# Memory free types
MEM_DECOMMIT = 0x4000
MEM_RELEASE = 0x8000

# ToolHelp32 constants
TH32CS_SNAPPROCESS = 0x00000002
TH32CS_SNAPMODULE = 0x00000008


# ==-------------------------------------------------------------------== #
# C-structs                                                               #
# ==-------------------------------------------------------------------== #
class CLIENT_ID(ctypes.Structure):
    """Client-ID structure that required to open process."""

    _fields_ = [
        ("unique_process", ctypes.c_void_p),
        ("unique_thread", ctypes.c_void_p)
    ]


class OBJECT_ATTRIBUTES(ctypes.Structure):
    """Object attributes structure that can be applied to objects or object handles."""

    _fields_ = [
        ("length", ctypes.c_ulong),
        ("root_directory", ctypes.c_void_p),
        ("object_name", ctypes.c_void_p),
        ("attributes", ctypes.c_ulong),
        ("security_descriptor", ctypes.c_void_p),
        ("security_quality_of_service", ctypes.c_void_p)
    ]


class MODULEENTRY32(ctypes.Structure):
    """Module entry structure, describes an entry from a list of the modules belonging to the specified process."""

    _fields_ = [
        ("dw_size", ctypes.c_ulong),
        ("module_id", ctypes.c_ulong),
        ("process_id", ctypes.c_ulong),
        ("glbl_cnt_usage", ctypes.c_ulong),
        ("proc_cnt_usage", ctypes.c_ulong),
        ("mod_base_addr", ctypes.c_void_p),
        ("mod_base_size", ctypes.c_ulong),
        ("h_module", ctypes.c_void_p),
        ("sz_module", ctypes.c_char * 256),
        ("sz_exe_path", ctypes.c_char * 260)
    ]

    @property
    def name(self) -> str:
        """Process module name."""

        return self.sz_module.decode()

    @property
    def base(self) -> int:
        """Process module base address."""

        return self.mod_base_addr or 0

    @property
    def size(self) -> int:
        """Process module base address."""

        return self.mod_base_size


class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    """Memory basic information structure that containg information about a range of pages in the virtual address space of a proces"""

    _fields_ = [
        ("m_base_address", ctypes.c_void_p),
        ("m_allocation_base", ctypes.c_void_p),
        ("m_allocation_protect", ctypes.c_ulong),
        ("m_partition_id", ctypes.c_ushort),
        ("m_region_size", ctypes.c_size_t),
        ("m_state", ctypes.c_ulong),
        ("m_protect", ctypes.c_ulong),
        ("m_type", ctypes.c_ulong)
    ]

    @property
    def base_address(self) -> int:
        """Memory region base address."""

        return self.m_base_address or 0

    @property
    def allocation_base(self) -> int:
        """Memory region allocation base."""

        return self.m_allocation_base or 0

    @property
    def allocation_protect(self) -> int:
        """Memory region allocation protect."""

        return self.m_allocation_protect

    @property
    def partition_id(self) -> int:
        """Memory region partition ID."""

        return self.m_partition_id

    @property
    def region_size(self) -> int:
        """Memory region size."""

        return self.m_region_size

    @property
    def state(self) -> int:
        """Memory region state."""

        return self.m_state

    @property
    def protect(self) -> int:
        """Memory region protect."""

        return self.m_protect

    @property
    def type(self) -> int:
        """Memory region type."""

        return self.m_type


class PatternScanBuffer(ctypes.Structure):
    """Structure that containing pointer to array received from SIMD KMP after call of `scanAOB` function."""

    _fields_ = [
        ("pointer", ctypes.c_void_p),
        ("size", ctypes.c_size_t),
    ]

    def read(self) -> list:
        """Read all of the values located at buffer array."""

        return list((ctypes.c_size_t * self.size).from_address(self.pointer))

    def free(self, library: ctypes.WinDLL) -> None:
        """Free memory allocated on `scanAOB` function call."""

        # If pointer is not defined
        if self.pointer is None:
            return

        # Free memory
        library.freeScanAOB(ctypes.byref(self))


# ==-------------------------------------------------------------------== #
# Syscalls                                                                #
# ==-------------------------------------------------------------------== #
_nt_close = syscall("NtClose", result_type=ctypes.c_ulong, arguments_types=[ctypes.c_void_p])
_nt_open_process = syscall("NtOpenProcess", result_type=ctypes.c_ulong, arguments_types=[ctypes.c_void_p, ctypes.c_ulong, ctypes.POINTER(OBJECT_ATTRIBUTES), ctypes.POINTER(CLIENT_ID)])

_nt_read_virtual_memory = syscall("NtReadVirtualMemory", result_type=ctypes.c_ulong, arguments_types=[ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong, ctypes.POINTER(ctypes.c_ulong)])
_nt_write_virtual_memory = syscall("NtWriteVirtualMemory", result_type=ctypes.c_ulong, arguments_types=[ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong, ctypes.POINTER(ctypes.c_ulong)])

_nt_virtual_query_memory = syscall("NtQueryVirtualMemory", result_type=ctypes.c_ulong, arguments_types=[ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)])
_nt_query_information_process = syscall("NtQueryInformationProcess", result_type=ctypes.c_ulong, arguments_types=[ctypes.c_void_p, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_ulong, ctypes.POINTER(ctypes.c_ulong)])

_nt_free_virtual_memory = syscall("NtFreeVirtualMemory", result_type=ctypes.c_ulong, arguments_types=[ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_ulong), ctypes.c_ulong])
_nt_allocate_virtual_memory = syscall("NtAllocateVirtualMemory", result_type=ctypes.c_ulong, arguments_types=[ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p), ctypes.c_ulong, ctypes.POINTER(ctypes.c_ulong), ctypes.c_ulong, ctypes.c_ulong])
_nt_protect_virtual_memory = syscall("NtProtectVirtualMemory", result_type=ctypes.c_ulong, arguments_types=[ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_ulong), ctypes.c_ulong, ctypes.POINTER(ctypes.c_ulong)])


# ==-------------------------------------------------------------------== #
# Functions                                                               #
# ==-------------------------------------------------------------------== #
def list_processes(include_id: bool = True, include_name: bool = True, include_username: bool = True, current_username_only: bool = True) -> list[dict[str, int | str]]:
    """List all of the currently active system processes."""

    # If `include_id` and `include_name` disabled both
    if not include_id and not include_name:
        raise Exception("Unable to disable ID and name including at once")

    # Current process username
    current_username = psutil.Process().username()

    # Result list of processes
    processes = list()

    # Process iteration
    for process in psutil.process_iter():

        # If process started not from current username
        if current_username_only and process.username() != current_username:
            continue

        # Save process to list
        process_dict = dict()

        # If process ID including required
        if include_id:
            process_dict |= {"id": process.pid}

        # If process ID including required
        if include_name:
            process_dict |= {"name": process.name()}

        # If process username including required
        if include_username:
            process_dict |= {"username": process.username()}

        # Save process information to list
        processes.append(process_dict)

    return processes


# ==-------------------------------------------------------------------== #
# Classes                                                                 #
# ==-------------------------------------------------------------------== #
class Process:
    """Basic class of process, have methods to manipulate it."""

    # ==-------------------------------------------------------------------== #
    # Methods                                                                 #
    # ==-------------------------------------------------------------------== #

    def __init__(self, pid_or_name: int | str, access: int = PROCESS_ALL_ACCESS, current_username_only: bool = True) -> None:
        """Initialize instance to manipulate process."""

        # Open process by it's ID or it's name
        match pid_or_name:

            case pid if type(pid_or_name) is int:
                self.handle, self.name, self.pid = self.__init_with_pid(pid, access, current_username_only)

            case name if type(pid_or_name) is str:
                self.handle, self.name, self.pid = self.__init_with_name(name, access, current_username_only)

            case _:
                raise Exception("Invalid `pid_or_name` argument value, have to be `int` or `str` type")

        # Try create file at temp directory to load SIMD KMP .dll (Module to blazingly fast pattern scaning)
        try:

            # Write library bytes directry from python list
            with open("%s\\simdkmp.dll" % (appdata := os.getenv("APPDATA")), "wb") as file:
                file.write(bytes(embed.kmp))

        except Exception:
            pass

        # Load library
        self.__kmp = ctypes.WinDLL(appdata + "\\simdkmp.dll")

    def list_modules(self) -> list[MODULEENTRY32]:
        """List all of the modules loaded to process."""

        # Modules snapshot functions
        close_handle = ctypes.windll.kernel32.CloseHandle
        module32_next = ctypes.windll.kernel32.Module32Next
        module32_first = ctypes.windll.kernel32.Module32First
        create_tool_help32_snapshot = ctypes.windll.kernel32.CreateToolhelp32Snapshot

        # Create snapshot to iterate process modules
        if (snapshot := create_tool_help32_snapshot(TH32CS_SNAPMODULE, self.pid)) == -1:
            raise Exception("Unable to create snapshot to iterate process modules")

        # Result list of process modules
        process_modules = list()

        # Process modules enumeration
        try:

            # Modules entry to iterate process modules
            modules_entry = MODULEENTRY32()
            modules_entry.dw_size = ctypes.sizeof(MODULEENTRY32)

            # Retrieve first process module snapshot
            if not module32_first(snapshot, ctypes.byref(modules_entry)):
                raise Exception("Unable to get first process module to save to snapshot")

            # Iterate all of the process modules using snapshot
            while True:

                # Create copy of module entry
                ctypes.memmove(ctypes.byref(module_entry_copy := MODULEENTRY32()), ctypes.byref(modules_entry), ctypes.sizeof(MODULEENTRY32))

                # Save process module to list
                process_modules.append(module_entry_copy)

                # snapshot is over
                if not module32_next(snapshot, ctypes.byref(modules_entry)):
                    break

        finally:

            # Close snapshot handle
            close_handle(snapshot)

        return process_modules

    def list_memory_regions(self, allowed_states: list[int] = list(), allowed_protects: list[int] = list(), allowed_types: list[int] = list(), memory_regions_filter: typing.Callable[[MEMORY_BASIC_INFORMATION], bool] | None = None) -> list[MEMORY_BASIC_INFORMATION]:
        """List all of the aviable process memory regions."""

        # Result list of memory regions
        memory_regions = list()

        # Iterate all of the process memory regions
        current_address = 0
        while True:

            # Prepare arguments
            memory_basic_information = MEMORY_BASIC_INFORMATION()

            # Try to get memory region information using it's address
            if (result := _nt_virtual_query_memory(self.handle, current_address, 0, ctypes.byref(memory_basic_information), ctypes.sizeof(memory_basic_information), None)):

                # If result failed due out of process memory space bounds
                if result == 0xC000000D:
                    break

                else:
                    raise Exception("NtVirtualQueryMemory failed with status: 0x%s" % hex(result)[2:].upper())

            # Move to next memory region
            if (next_address := current_address + memory_basic_information.region_size) <= current_address:
                break

            # Overriding current address
            current_address = next_address

            # Save memory regions after filtering it
            if allowed_states and memory_basic_information.state not in allowed_states:
                continue

            if allowed_protects and memory_basic_information.protect not in allowed_protects:
                continue

            if allowed_types and memory_basic_information.type not in allowed_types:
                continue

            if memory_regions_filter and not memory_regions_filter(memory_basic_information):
                continue

            # Save memory region information if filter passed
            memory_regions.append(memory_basic_information)

        return memory_regions

    def get_module(self, name: str) -> MODULEENTRY32:
        """Get process module information."""

        # Process modules enumeration
        for module in self.list_modules():

            # If module have a required name
            if module.name.lower() == name.strip().lower():
                return module

        raise Exception("Module with `%s` name not found" % name)

    def get_memory_region(self, address: int) -> MEMORY_BASIC_INFORMATION:
        """Get memory region information located at given address."""

        # Prepare arguments
        memory_basic_information = MEMORY_BASIC_INFORMATION()

        # Try to get memory region information using it's address
        if (result := _nt_virtual_query_memory(self.handle, address, 0, ctypes.byref(memory_basic_information), ctypes.sizeof(memory_basic_information), None)):
            raise Exception("NtVirtualQueryMemory failed with status: 0x%s" % hex(result)[2:].upper())

        return memory_basic_information

    def is_64bit(self) -> bool:
        """Check if process is 64 bit."""

        # Prepare arguments
        wow64_info = ctypes.c_void_p()

        # Try to query process information
        if (result := _nt_query_information_process(self.handle, 26, ctypes.byref(wow64_info), ctypes.sizeof(wow64_info), ctypes.byref(ctypes.c_ulong()))):
            raise Exception("NtQueryInformationProcess failed with status: 0x%s" % hex(result)[2:].upper())

        return wow64_info.value is None

    def allocate_memory(self, address: int = 0, size: int = 4096, memory_type: int = MEM_COMMIT, memory_protect: int = PAGE_READWRITE) -> tuple[int, int]:
        """Allocate process memory."""

        # Prepare arguments
        allocation_address = ctypes.c_void_p(address)
        allocation_size = ctypes.c_ulong(size)

        # Try to allocate process memory
        if (result := _nt_allocate_virtual_memory(self.handle, ctypes.byref(allocation_address), 0, ctypes.byref(allocation_size), memory_type, memory_protect)):
            raise Exception("NtAllocateVirtualMemory failed with status: 0x%s" % hex(result)[2:].upper())

        return allocation_address.value or 0, allocation_size.value or 0

    def free_memory(self, address: int, size: int = 0, memory_type: int = MEM_RELEASE) -> int:
        """Deallocate process memory."""

        # Prepare arguments
        allocation_address = ctypes.c_void_p(address)
        allocation_size = ctypes.c_ulong(size)

        # Try to deallocate process memory
        if (result := _nt_free_virtual_memory(self.handle, ctypes.byref(allocation_address), ctypes.byref(allocation_size), memory_type)):
            raise Exception("NtFreeVirtualMemory failed with status: 0x%s" % hex(result)[2:].upper())

        return allocation_size.value or 0

    def protect_memory(self, address: int, size: int, memory_protect: int) -> int:
        """Change process memory protection."""

        # Prepare arguments
        protect_address = ctypes.c_void_p(address)
        protect_size = ctypes.c_ulong(size)

        # Try to change memory protection
        if (result := _nt_protect_virtual_memory(self.handle, ctypes.byref(protect_address), ctypes.byref(protect_size), memory_protect, ctypes.byref(memory_old_protect := ctypes.c_ulong()))):
            raise Exception("NtProtectVirtualMemory failed with status: 0x%s" % hex(result)[2:].upper())

        return memory_old_protect.value or 0

    def pattern_scan(self, pattern: str, allowed_states: list[int] = [MEM_COMMIT], allowed_protects: list[int] = [PAGE_READWRITE], allowed_types: list[int] = list(), start_address: int | None = None, end_address: int | None = None, return_first: int | None = None, memory_regions_filter: typing.Callable[[MEMORY_BASIC_INFORMATION], bool] | None = None) -> list[int]:
        """Scan process and return address that validates given pattern hex byte mask, use `??` to wildcard byte, for example - "14 00 00 00 DB FF ?? ?? FF FF 00 00"."""

        # Validate given pattern
        for byte in pattern.strip().split():

            # If pattern byte is digit or wildcard
            if len(byte) == 2 and [item in "0123456789ABCDEFabcdef" for item in byte].count(True) == 2:
                continue

            # If pattern byte is wildcard
            if byte == "??":
                continue

            raise Exception("Invalid pattern: `%s`" % pattern)

        # Result list of found addresses
        found_addresses = list()

        # iterate memory regions and finding addresses at them
        for region in self.list_memory_regions(allowed_states, allowed_protects, allowed_types, memory_regions_filter):

            # If required amount of addresses found
            if return_first is not None and return_first <= 0:
                break

            # Region bounds
            region_start = region.base_address
            region_end = region.base_address + region.region_size

            # If start address is defined
            if start_address is not None and region_end <= start_address:
                continue

            # If end address is defined
            if end_address is not None and region_start >= end_address:
                continue

            # Scan params
            scan_start = max(region_start, start_address) if start_address is not None else region_start
            scan_size = min(region_end, end_address) - scan_start if end_address is not None else region_end - scan_start

            # Read region as bytes
            try:
                read_region_bytes = self.read_bytes(scan_start, scan_size)

            except Exception:
                continue

            # Pattern scan region using SIMD KMP algorithm
            self.__kmp.scanAOB(read_region_bytes, scan_size, pattern.strip().encode(), ctypes.c_uint64(scan_start), ctypes.c_uint64(return_first if return_first is not None else 0), ctypes.byref(scan_result := PatternScanBuffer()))

            # Read result addresses
            addresses = scan_result.read()

            # Free scan result memory
            scan_result.free(self.__kmp)

            # If return first is defined
            if return_first is not None and addresses:
                return_first -= len(addresses)

            # Save found addresses
            if addresses:
                found_addresses.extend(addresses)

        return found_addresses

    def read_int8(self, address: int) -> int:
        """Read 1 byte signed integer value located at given address."""

        if (result := _nt_read_virtual_memory(self.handle, address, ctypes.byref(buffer := ctypes.c_int8()), ctypes.sizeof(buffer), None)):

            # If result failed due memory protection
            if result == 0x8000000D:
                raise Exception("Unable to read value located at `0x%s` address due memory protection" % hex(address)[2:].upper())

            else:
                raise Exception("NtReadVirtualMemory failed with status: 0x%s" % hex(result)[2:].upper())

        return buffer.value

    def read_int16(self, address: int) -> int:
        """Read 2 byte signed integer value located at given address."""

        if (result := _nt_read_virtual_memory(self.handle, address, ctypes.byref(buffer := ctypes.c_int16()), ctypes.sizeof(buffer), None)):

            # If result failed due memory protection
            if result == 0x8000000D:
                raise Exception("Unable to read value located at `0x%s` address due memory protection" % hex(address)[2:].upper())

            else:
                raise Exception("NtReadVirtualMemory failed with status: 0x%s" % hex(result)[2:].upper())

        return buffer.value

    def read_int32(self, address: int) -> int:
        """Read 4 byte signed integer value located at given address."""

        if (result := _nt_read_virtual_memory(self.handle, address, ctypes.byref(buffer := ctypes.c_int32()), ctypes.sizeof(buffer), None)):

            # If result failed due memory protection
            if result == 0x8000000D:
                raise Exception("Unable to read value located at `0x%s` address due memory protection" % hex(address)[2:].upper())

            else:
                raise Exception("NtReadVirtualMemory failed with status: 0x%s" % hex(result)[2:].upper())

        return buffer.value

    def read_int64(self, address: int) -> int:
        """Read 8 byte signed integer value located at given address."""

        if (result := _nt_read_virtual_memory(self.handle, address, ctypes.byref(buffer := ctypes.c_int64()), ctypes.sizeof(buffer), None)):

            # If result failed due memory protection
            if result == 0x8000000D:
                raise Exception("Unable to read value located at `0x%s` address due memory protection" % hex(address)[2:].upper())

            else:
                raise Exception("NtReadVirtualMemory failed with status: 0x%s" % hex(result)[2:].upper())

        return buffer.value

    def read_uint8(self, address: int) -> int:
        """Read 1 byte unsigned integer value located at given address."""

        if (result := _nt_read_virtual_memory(self.handle, address, ctypes.byref(buffer := ctypes.c_uint8()), ctypes.sizeof(buffer), None)):

            # If result failed due memory protection
            if result == 0x8000000D:
                raise Exception("Unable to read value located at `0x%s` address due memory protection" % hex(address)[2:].upper())

            else:
                raise Exception("NtReadVirtualMemory failed with status: 0x%s" % hex(result)[2:].upper())

        return buffer.value

    def read_uint16(self, address: int) -> int:
        """Read 2 byte unsigned integer value located at given address."""

        if (result := _nt_read_virtual_memory(self.handle, address, ctypes.byref(buffer := ctypes.c_uint16()), ctypes.sizeof(buffer), None)):

            # If result failed due memory protection
            if result == 0x8000000D:
                raise Exception("Unable to read value located at `0x%s` address due memory protection" % hex(address)[2:].upper())

            else:
                raise Exception("NtReadVirtualMemory failed with status: 0x%s" % hex(result)[2:].upper())

        return buffer.value

    def read_uint32(self, address: int) -> int:
        """Read 4 byte unsigned integer value located at given address."""

        if (result := _nt_read_virtual_memory(self.handle, address, ctypes.byref(buffer := ctypes.c_uint32()), ctypes.sizeof(buffer), None)):

            # If result failed due memory protection
            if result == 0x8000000D:
                raise Exception("Unable to read value located at `0x%s` address due memory protection" % hex(address)[2:].upper())

            else:
                raise Exception("NtReadVirtualMemory failed with status: 0x%s" % hex(result)[2:].upper())

        return buffer.value

    def read_uint64(self, address: int) -> int:
        """Read 8 byte unsigned integer value located at given address."""

        if (result := _nt_read_virtual_memory(self.handle, address, ctypes.byref(buffer := ctypes.c_uint64()), ctypes.sizeof(buffer), None)):

            # If result failed due memory protection
            if result == 0x8000000D:
                raise Exception("Unable to read value located at `0x%s` address due memory protection" % hex(address)[2:].upper())

            else:
                raise Exception("NtReadVirtualMemory failed with status: 0x%s" % hex(result)[2:].upper())

        return buffer.value

    def read_float32(self, address: int) -> int:
        """Read 4 byte floating-point digit value located at given address."""

        if (result := _nt_read_virtual_memory(self.handle, address, ctypes.byref(buffer := ctypes.c_float()), ctypes.sizeof(buffer), None)):

            # If result failed due memory protection
            if result == 0x8000000D:
                raise Exception("Unable to read value located at `0x%s` address due memory protection" % hex(address)[2:].upper())

            else:
                raise Exception("NtReadVirtualMemory failed with status: 0x%s" % hex(result)[2:].upper())

        return buffer.value

    def read_float64(self, address: int) -> int:
        """Read 8 byte floating-point digit value located at given address."""

        if (result := _nt_read_virtual_memory(self.handle, address, ctypes.byref(buffer := ctypes.c_double()), ctypes.sizeof(buffer), None)):

            # If result failed due memory protection
            if result == 0x8000000D:
                raise Exception("Unable to read value located at `0x%s` address due memory protection" % hex(address)[2:].upper())

            else:
                raise Exception("NtReadVirtualMemory failed with status: 0x%s" % hex(result)[2:].upper())

        return buffer.value

    def read_bytes(self, address: int, size: int) -> bytes:
        """Read bytes array of variadic size located at given address."""

        if (result := _nt_read_virtual_memory(self.handle, address, ctypes.byref(buffer := (ctypes.c_int8 * size)()), ctypes.sizeof(buffer), None)):

            # If result failed due memory protection
            if result == 0x8000000D:
                raise Exception("Unable to read value located at `0x%s` address due memory protection" % hex(address)[2:].upper())

            else:
                raise Exception("NtReadVirtualMemory failed with status: 0x%s" % hex(result)[2:].upper())

        return bytes(buffer)

    def read_buffer[T](self, address: int, buffer: T) -> T:
        """Read size of buffer byte value located at given address to buffer. Buffer have to be able passed at `ctypes.byref` and `ctype.sizeof`."""

        if (result := _nt_read_virtual_memory(self.handle, address, ctypes.byref(buffer), ctypes.sizeof(buffer), None)):

            # If result failed due memory protection
            if result == 0x8000000D:
                raise Exception("Unable to read value located at `0x%s` address due memory protection" % hex(address)[2:].upper())

            else:
                raise Exception("NtReadVirtualMemory failed with status: 0x%s" % hex(result)[2:].upper())

        return buffer

    def write_int8(self, address: int, value: int) -> None:
        """Write 1 byte signed integer value at given address."""

        if (result := _nt_write_virtual_memory(self.handle, address, ctypes.byref(buffer := ctypes.c_int8(value)), ctypes.sizeof(buffer), None)):

            # If result failed due memory protection
            if result == 0x8000000D:
                raise Exception("Unable to write value at `0x%s` address due memory protection" % hex(address)[2:].upper())

            else:
                raise Exception("NtWriteVirtualMemory failed with status: 0x%s" % hex(result)[2:].upper())

    def write_int16(self, address: int, value: int) -> None:
        """Write 2 byte signed integer value at given address."""

        if (result := _nt_write_virtual_memory(self.handle, address, ctypes.byref(buffer := ctypes.c_int16(value)), ctypes.sizeof(buffer), None)):

            # If result failed due memory protection
            if result == 0x8000000D:
                raise Exception("Unable to write value at `0x%s` address due memory protection" % hex(address)[2:].upper())

            else:
                raise Exception("NtWriteVirtualMemory failed with status: 0x%s" % hex(result)[2:].upper())

    def write_int32(self, address: int, value: int) -> None:
        """Write 4 byte signed integer value at given address."""

        if (result := _nt_write_virtual_memory(self.handle, address, ctypes.byref(buffer := ctypes.c_int32(value)), ctypes.sizeof(buffer), None)):

            # If result failed due memory protection
            if result == 0x8000000D:
                raise Exception("Unable to write value at `0x%s` address due memory protection" % hex(address)[2:].upper())

            else:
                raise Exception("NtWriteVirtualMemory failed with status: 0x%s" % hex(result)[2:].upper())

    def write_int64(self, address: int, value: int) -> None:
        """Write 8 byte signed integer value at given address."""

        if (result := _nt_write_virtual_memory(self.handle, address, ctypes.byref(buffer := ctypes.c_int64(value)), ctypes.sizeof(buffer), None)):

            # If result failed due memory protection
            if result == 0x8000000D:
                raise Exception("Unable to write value at `0x%s` address due memory protection" % hex(address)[2:].upper())

            else:
                raise Exception("NtWriteVirtualMemory failed with status: 0x%s" % hex(result)[2:].upper())

    def write_uint8(self, address: int, value: int) -> None:
        """Write 1 byte unsigned integer value at given address."""

        if (result := _nt_write_virtual_memory(self.handle, address, ctypes.byref(buffer := ctypes.c_uint8(value)), ctypes.sizeof(buffer), None)):

            # If result failed due memory protection
            if result == 0x8000000D:
                raise Exception("Unable to write value at `0x%s` address due memory protection" % hex(address)[2:].upper())

            else:
                raise Exception("NtWriteVirtualMemory failed with status: 0x%s" % hex(result)[2:].upper())

    def write_uint16(self, address: int, value: int) -> None:
        """Write 2 byte unsigned integer value at given address."""

        if (result := _nt_write_virtual_memory(self.handle, address, ctypes.byref(buffer := ctypes.c_uint16(value)), ctypes.sizeof(buffer), None)):

            # If result failed due memory protection
            if result == 0x8000000D:
                raise Exception("Unable to write value at `0x%s` address due memory protection" % hex(address)[2:].upper())

            else:
                raise Exception("NtWriteVirtualMemory failed with status: 0x%s" % hex(result)[2:].upper())

    def write_uint32(self, address: int, value: int) -> None:
        """Write 4 byte unsigned integer value at given address."""

        if (result := _nt_write_virtual_memory(self.handle, address, ctypes.byref(buffer := ctypes.c_uint32(value)), ctypes.sizeof(buffer), None)):

            # If result failed due memory protection
            if result == 0x8000000D:
                raise Exception("Unable to write value at `0x%s` address due memory protection" % hex(address)[2:].upper())

            else:
                raise Exception("NtWriteVirtualMemory failed with status: 0x%s" % hex(result)[2:].upper())

    def write_uint64(self, address: int, value: int) -> None:
        """Write 8 byte unsigned integer value at given address."""

        if (result := _nt_write_virtual_memory(self.handle, address, ctypes.byref(buffer := ctypes.c_uint64(value)), ctypes.sizeof(buffer), None)):

            # If result failed due memory protection
            if result == 0x8000000D:
                raise Exception("Unable to write value at `0x%s` address due memory protection" % hex(address)[2:].upper())

            else:
                raise Exception("NtWriteVirtualMemory failed with status: 0x%s" % hex(result)[2:].upper())

    def write_bytes(self, address: int, value: bytes) -> None:
        """Write bytes array of variadic size at given address."""

        if (result := _nt_write_virtual_memory(self.handle, address, value, len(value), None)):

            # If result failed due memory protection
            if result == 0x8000000D:
                raise Exception("Unable to write value at `0x%s` address due memory protection" % hex(address)[2:].upper())

            else:
                raise Exception("NtReadVirtualMemory failed with status: 0x%s" % hex(result)[2:].upper())

    def write_buffer(self, address: int, buffer: typing.Any) -> None:
        """Write size of buffer byte value at given address. Buffer have to be able passed at `ctypes.byref` and `ctype.sizeof`."""

        if (result := _nt_write_virtual_memory(self.handle, address, ctypes.byref(buffer), ctypes.sizeof(buffer), None)):

            # If result failed due memory protection
            if result == 0x8000000D:
                raise Exception("Unable to write value at `0x%s` address due memory protection" % hex(address)[2:].upper())

            else:
                raise Exception("NtReadVirtualMemory failed with status: 0x%s" % hex(result)[2:].upper())

    def close(self) -> None:
        """Close opened process using it's handle, have to be called once on stop interacting with process."""

        # Close process
        _nt_close(self.handle)

    # ==-------------------------------------------------------------------== #
    # Private methods                                                         #
    # ==-------------------------------------------------------------------== #
    def __init_with_pid(self, pid: int, access: int, current_username_only: bool, process_name: str | None = None) -> int:
        """Open process handle by it's ID with desired access."""

        # Iterate all of the processes if name not defined
        for process in list_processes(current_username_only):

            # If process have a reqired name
            if process["id"] == pid:

                process_name = process["name"]
                break

        else:
            raise Exception("Process with `%s` ID not found" % pid)

        # Prepare arguments
        object_attributes = OBJECT_ATTRIBUTES()
        object_attributes.length = ctypes.sizeof(OBJECT_ATTRIBUTES)

        client_id = CLIENT_ID()
        client_id.unique_process = pid

        # Try to open process using it's ID
        if (result := _nt_open_process(ctypes.byref(handle := ctypes.c_void_p()), access, ctypes.byref(object_attributes), ctypes.byref(client_id))):

            # If result failed due process ID not found
            if result == 0xC000000B:
                raise Exception("Process with `%s` ID not found" % pid)

            else:
                raise Exception("NtOpenProcess failed with status: 0x%s" % hex(result)[2:].upper())

        return handle.value, process_name, pid

    def __init_with_name(self, name: str, access: int, current_username_only: bool) -> int:
        """Open process hanle by it's name with desired access."""

        # Iterate all of the processes using snapshot
        for process in list_processes(current_username_only):

            # If process have a reqired name
            if process["name"].lower() == name.strip().lower():
                return self.__init_with_pid(process["id"], access, current_username_only, process["name"])

        raise Exception("Process with `%s` name not found" % name)
