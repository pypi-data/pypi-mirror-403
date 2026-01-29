from collections.abc import Sequence, Set
import datetime
import enum
import os
from typing import Optional, overload

from . import logging as logging, wormhole as wormhole


class NocId(enum.Enum):
    DEFAULT_NOC = 0

    NOC0 = 0

    NOC1 = 1

    SYSTEM_NOC = 2

    def __int__(self) -> int: ...

def set_thread_noc_id(noc_id: NocId) -> None: ...

class EthCoord:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, cluster_id: int, x: int, y: int, rack: int, shelf: int) -> None: ...

    @property
    def cluster_id(self) -> int: ...

    @cluster_id.setter
    def cluster_id(self, arg: int, /) -> None: ...

    @property
    def x(self) -> int: ...

    @x.setter
    def x(self, arg: int, /) -> None: ...

    @property
    def y(self) -> int: ...

    @y.setter
    def y(self, arg: int, /) -> None: ...

    @property
    def rack(self) -> int: ...

    @rack.setter
    def rack(self, arg: int, /) -> None: ...

    @property
    def shelf(self) -> int: ...

    @shelf.setter
    def shelf(self, arg: int, /) -> None: ...

class tt_xy_pair:
    def __init__(self, x: int, y: int) -> None: ...

    @property
    def x(self) -> int: ...

    @property
    def y(self) -> int: ...

    def __str__(self) -> str: ...

class ARCH(enum.Enum):
    def __str__(self) -> str: ...

    WORMHOLE_B0 = 2

    BLACKHOLE = 3

    QUASAR = 4

    Invalid = 255

    def __int__(self) -> int: ...

    @staticmethod
    def from_str(arch_str: str) -> ARCH: ...

class BoardType(enum.Enum):
    def __str__(self) -> str: ...

    E75 = 0

    E150 = 1

    E300 = 2

    N150 = 3

    N300 = 4

    P100 = 5

    P150 = 6

    P300 = 7

    GALAXY = 8

    UBB = 9

    UBB_WORMHOLE = 9

    UBB_BLACKHOLE = 10

    QUASAR = 11

    UNKNOWN = 12

    def __int__(self) -> int: ...

class semver_t:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, major: int, minor: int, patch: int) -> None: ...

    @overload
    def __init__(self, version_str: str) -> None: ...

    @property
    def major(self) -> int: ...

    @major.setter
    def major(self, arg: int, /) -> None: ...

    @property
    def minor(self) -> int: ...

    @minor.setter
    def minor(self, arg: int, /) -> None: ...

    @property
    def patch(self) -> int: ...

    @patch.setter
    def patch(self, arg: int, /) -> None: ...

    def to_string(self) -> str: ...

    def __str__(self) -> str: ...

    def __lt__(self, arg: semver_t, /) -> bool: ...

    def __le__(self, arg: semver_t, /) -> bool: ...

    def __gt__(self, arg: semver_t, /) -> bool: ...

    def __ge__(self, arg: semver_t, /) -> bool: ...

    def __eq__(self, arg: semver_t, /) -> bool: ...

    def __ne__(self, arg: semver_t, /) -> bool: ...

class ChipInfo:
    def __init__(self) -> None: ...

    @property
    def noc_translation_enabled(self) -> bool: ...

    @noc_translation_enabled.setter
    def noc_translation_enabled(self, arg: bool, /) -> None: ...

    @property
    def harvesting_masks(self) -> HarvestingMasks: ...

    @harvesting_masks.setter
    def harvesting_masks(self, arg: HarvestingMasks, /) -> None: ...

    @property
    def board_type(self) -> BoardType: ...

    @board_type.setter
    def board_type(self, arg: BoardType, /) -> None: ...

    @property
    def board_id(self) -> int: ...

    @board_id.setter
    def board_id(self, arg: int, /) -> None: ...

    @property
    def asic_location(self) -> int: ...

    @asic_location.setter
    def asic_location(self, arg: int, /) -> None: ...

class HarvestingMasks:
    def __init__(self) -> None: ...

    @property
    def tensix_harvesting_mask(self) -> int: ...

    @tensix_harvesting_mask.setter
    def tensix_harvesting_mask(self, arg: int, /) -> None: ...

    @property
    def dram_harvesting_mask(self) -> int: ...

    @dram_harvesting_mask.setter
    def dram_harvesting_mask(self, arg: int, /) -> None: ...

    @property
    def eth_harvesting_mask(self) -> int: ...

    @eth_harvesting_mask.setter
    def eth_harvesting_mask(self, arg: int, /) -> None: ...

    @property
    def pcie_harvesting_mask(self) -> int: ...

    @pcie_harvesting_mask.setter
    def pcie_harvesting_mask(self, arg: int, /) -> None: ...

    @property
    def l2cpu_harvesting_mask(self) -> int: ...

    @l2cpu_harvesting_mask.setter
    def l2cpu_harvesting_mask(self, arg: int, /) -> None: ...

def board_type_to_string(board_type: BoardType) -> str:
    """Convert BoardType to string"""

def board_type_from_string(board_type_str: str) -> BoardType:
    """Convert string to BoardType"""

class Cluster:
    def __init__(self) -> None: ...

    def get_target_device_ids(self) -> set[int]: ...

    def get_clocks(self) -> dict[int, int]: ...

class IODeviceType(enum.Enum):
    PCIe = 0

    JTAG = 1

    Undefined = 2

class PciDeviceInfo:
    @property
    def vendor_id(self) -> int: ...

    @property
    def device_id(self) -> int: ...

    @property
    def subsystem_vendor_id(self) -> int: ...

    @property
    def subsystem_id(self) -> int: ...

    @property
    def pci_domain(self) -> int: ...

    @property
    def pci_bus(self) -> int: ...

    @property
    def pci_device(self) -> int: ...

    @property
    def pci_function(self) -> int: ...

    @property
    def pci_bdf(self) -> str: ...

    def get_arch(self) -> ARCH: ...

class PCIDevice:
    def __init__(self, arg: int, /) -> None: ...

    @staticmethod
    def enumerate_devices(pci_target_devices: Set[int] = ...) -> list[int]:
        """Enumerates PCI devices, optionally filtering by target devices."""

    @staticmethod
    def enumerate_devices_info(pci_target_devices: Set[int] = ...) -> dict[int, PciDeviceInfo]:
        """
        Enumerates PCI device information, optionally filtering by target devices.
        """

    def get_device_info(self) -> PciDeviceInfo: ...

    def get_device_num(self) -> int: ...

    @staticmethod
    def read_kmd_version() -> semver_t:
        """Read KMD version installed on the system."""

    @staticmethod
    def read_device_info(fd: int) -> PciDeviceInfo:
        """Read PCI device information."""

    @staticmethod
    def is_arch_agnostic_reset_supported() -> bool:
        """Check if KMD supports arch agnostic reset."""

class RemoteCommunication:
    def set_remote_transfer_ethernet_cores(self, cores: Sequence[tuple[int, int]]) -> None: ...

    def get_local_device(self) -> TTDevice: ...

    def get_remote_transfer_ethernet_core(self) -> tuple[int, int]: ...

class TTDevice:
    @staticmethod
    def create(device_number: int, device_type: IODeviceType = IODeviceType.PCIe) -> TTDevice: ...

    def init_tt_device(self, timeout_ms: datetime.timedelta | float = ...) -> None: ...

    def get_chip_info(self) -> ChipInfo: ...

    def get_arc_telemetry_reader(self) -> ArcTelemetryReader: ...

    def get_arch(self) -> ARCH: ...

    def get_board_id(self) -> int: ...

    def board_id(self) -> int: ...

    def get_board_type(self) -> BoardType: ...

    def get_communication_device_type(self) -> IODeviceType: ...

    def get_pci_device(self) -> PCIDevice: ...

    def get_noc_translation_enabled(self) -> bool: ...

    def is_remote(self) -> bool:
        """Returns true if this is a remote TTDevice"""

    def get_remote_communication(self) -> RemoteCommunication: ...

    def get_firmware_info_provider(self) -> FirmwareInfoProvider: ...

    def as_wh(self) -> TTDevice:
        """Return self - for compatibility with luwen's API"""

    def as_bh(self) -> TTDevice:
        """Return self - for compatibility with luwen's API"""

    def noc_read32(self, core_x: int, core_y: int, addr: int) -> int:
        """Read a 32-bit value from a core at the specified address"""

    def noc_write32(self, core_x: int, core_y: int, addr: int, value: int) -> None:
        """Write a 32-bit value to a core at the specified address"""

    @overload
    def noc_read(self, core_x: int, core_y: int, addr: int, size: int) -> bytes:
        """Read arbitrary-length data from a core at the specified address"""

    @overload
    def noc_read(self, noc_id: int, core_x: int, core_y: int, addr: int, buffer: bytearray) -> None:
        """
        Read data into the provided buffer from a core at the specified address. noc_id must be 0 for now.
        """

    def noc_write(self, core_x: int, core_y: int, addr: int, data: bytes) -> None:
        """Write arbitrary-length data to a core at the specified address"""

    def bar_read32(self, addr: int) -> int:
        """Read a 32-bit value from the specified address on bar0"""

    def bar_write32(self, addr: int, data: int) -> None:
        """Write a 32-bit value to the specified address on bar0"""

    @overload
    def dma_read_from_device(self, core_x: int, core_y: int, addr: int, size: int) -> bytes:
        """Read arbitrary-length data from a core at the specified address"""

    @overload
    def dma_read_from_device(self, noc_id: int, core_x: int, core_y: int, addr: int, buffer: bytearray) -> None:
        """
        Read data into the provided buffer from a core at the specified address. noc_id must be 0 for now.
        """

    def dma_write_to_device(self, core_x: int, core_y: int, addr: int, data: bytes) -> None:
        """Write arbitrary-length data to a core at the specified address"""

    @overload
    def arc_msg(self, msg_code: int, wait_for_done: bool = True, args: Sequence[int] = [], timeout_ms: int = 1000) -> tuple[int, int, int]:
        """
        Send ARC message and return (exit_code, return_3, return_4). Args is a list of uint32_t arguments. For Wormhole, max 2 args (each <= 0xFFFF). For Blackhole, max 7 args. Timeout is in milliseconds.
        """

    @overload
    def arc_msg(self, msg_code: int, wait_for_done: bool, arg0: int, arg1: int, timeout_ms: int = 1000) -> tuple[int, int, int]:
        """
        Send ARC message with two arguments and return (exit_code, return_3, return_4). Timeout is in milliseconds.
        """

    @overload
    def arc_msg(self, msg_code: int, wait_for_done: bool, arg0: int, arg1: int, timeout: int = 1) -> tuple[int, int, int]:
        """
        Send ARC message with two arguments and return (exit_code, return_3, return_4). Timeout is in seconds.
        """

class RemoteWormholeTTDevice(TTDevice):
    pass

class RtlSimulationTTDevice(TTDevice):
    @staticmethod
    def create(simulator_directory: str | os.PathLike) -> RtlSimulationTTDevice:
        """Creates an RtlSimulationTTDevice for RTL simulation communication."""

    def send_tensix_risc_reset(self, translated_core: tt_xy_pair, deassert: bool) -> None:
        """Send a Tensix RISC reset signal to the RTL simulation device."""

    def get_soc_descriptor(self) -> SocDescriptor:
        """Get the SocDescriptor associated with this RTL simulation device."""

def create_remote_wormhole_tt_device(local_chip: TTDevice, cluster_descriptor: ClusterDescriptor, remote_chip_id: int) -> TTDevice:
    """Creates a RemoteWormholeTTDevice for communication with a remote chip."""

class TelemetryTag(enum.Enum):
    BOARD_ID_HIGH = 1

    BOARD_ID_LOW = 2

    ASIC_ID = 3

    HARVESTING_STATE = 4

    UPDATE_TELEM_SPEED = 5

    VCORE = 6

    TDP = 7

    TDC = 8

    VDD_LIMITS = 9

    THM_LIMITS = 10

    ASIC_TEMPERATURE = 11

    VREG_TEMPERATURE = 12

    BOARD_TEMPERATURE = 13

    AICLK = 14

    AXICLK = 15

    ARCCLK = 16

    L2CPUCLK0 = 17

    L2CPUCLK1 = 18

    L2CPUCLK2 = 19

    L2CPUCLK3 = 20

    ETH_LIVE_STATUS = 21

    DDR_STATUS = 22

    DDR_SPEED = 23

    ETH_FW_VERSION = 24

    GDDR_FW_VERSION = 25

    DM_APP_FW_VERSION = 26

    DM_BL_FW_VERSION = 27

    FLASH_BUNDLE_VERSION = 28

    CM_FW_VERSION = 29

    L2CPU_FW_VERSION = 30

    FAN_SPEED = 31

    TIMER_HEARTBEAT = 32

    TELEMETRY_ENUM_COUNT = 33

    ENABLED_TENSIX_COL = 34

    ENABLED_ETH = 35

    ENABLED_GDDR = 36

    ENABLED_L2CPU = 37

    PCIE_USAGE = 38

    NOC_TRANSLATION = 40

    FAN_RPM = 41

    ASIC_LOCATION = 52

    TDC_LIMIT_MAX = 55

    TT_FLASH_VERSION = 58

    ASIC_ID_HIGH = 61

    ASIC_ID_LOW = 62

    AICLK_LIMIT_MAX = 63

    TDP_LIMIT_MAX = 64

    NUMBER_OF_TAGS = 65

    def __int__(self) -> int: ...

class ArcTelemetryReader:
    def read_entry(self, telemetry_tag: int) -> int: ...

    def is_entry_available(self, telemetry_tag: int) -> bool: ...

class SmBusArcTelemetryReader(ArcTelemetryReader):
    def __init__(self, tt_device: TTDevice) -> None: ...

    def read_entry(self, telemetry_tag: int) -> int: ...

    def is_entry_available(self, telemetry_tag: int) -> bool: ...

class DramTrainingStatus(enum.Enum):
    IN_PROGRESS = 0

    FAIL = 1

    SUCCESS = 2

    def __int__(self) -> int: ...

class FirmwareInfoProvider:
    def get_firmware_version(self) -> semver_t: ...

    def get_board_id(self) -> int: ...

    def get_eth_fw_version(self) -> int: ...

    @overload
    def get_asic_location(self) -> int: ...

    @overload
    def get_asic_location(self) -> int: ...

    def get_aiclk(self) -> Optional[int]: ...

    def get_axiclk(self) -> Optional[int]: ...

    def get_arcclk(self) -> Optional[int]: ...

    def get_fan_speed(self) -> Optional[int]: ...

    def get_tdp(self) -> Optional[int]: ...

    def get_tdc(self) -> Optional[int]: ...

    def get_vcore(self) -> Optional[int]: ...

    def get_board_temperature(self) -> Optional[float]: ...

    def get_dram_training_status(self, num_dram_channels: int) -> list[DramTrainingStatus]: ...

    def get_max_clock_freq(self) -> int: ...

    def get_heartbeat(self) -> int: ...

    @staticmethod
    def get_minimum_compatible_firmware_version(arch: ARCH) -> semver_t: ...

    @staticmethod
    def get_latest_supported_firmware_version(arch: ARCH) -> semver_t: ...

    @staticmethod
    def create_firmware_info_provider(tt_device: TTDevice) -> FirmwareInfoProvider: ...

class ClusterDescriptor:
    @staticmethod
    def create_from_yaml_content(yaml_content: str) -> ClusterDescriptor: ...

    def get_all_chips(self) -> set[int]: ...

    def is_chip_mmio_capable(self, chip_id: int) -> bool: ...

    def is_chip_remote(self, chip_id: int) -> bool: ...

    def get_closest_mmio_capable_chip(self, chip: int) -> int: ...

    def get_chips_local_first(self, chips: Set[int]) -> list[int]: ...

    def get_chip_locations(self) -> dict[int, EthCoord]: ...

    def get_chips_with_mmio(self) -> dict[int, int]: ...

    def get_active_eth_channels(self, chip_id: int) -> set[int]: ...

    def get_ethernet_connections(self) -> dict[int, dict[int, tuple[int, int]]]: ...

    def get_chip_unique_ids(self) -> dict[int, int]: ...

    def get_io_device_type(self) -> IODeviceType: ...

    def serialize_to_file(self, dest_file: str = '') -> str: ...

    def get_arch(self, chip_id: int) -> ARCH: ...

    def get_board_type(self, chip_id: int) -> BoardType:
        """Get board type for a chip"""

    def get_board_id_for_chip(self, chip: int) -> int:
        """Get board ID for a chip"""

class TopologyDiscoveryOptions:
    def __init__(self) -> None: ...

    @property
    def soc_descriptor_path(self) -> str: ...

    @soc_descriptor_path.setter
    def soc_descriptor_path(self, arg: str, /) -> None: ...

    @property
    def io_device_type(self) -> IODeviceType: ...

    @io_device_type.setter
    def io_device_type(self, arg: IODeviceType, /) -> None: ...

    @property
    def no_remote_discovery(self) -> bool: ...

    @no_remote_discovery.setter
    def no_remote_discovery(self, arg: bool, /) -> None: ...

    @property
    def no_wait_for_eth_training(self) -> bool: ...

    @no_wait_for_eth_training.setter
    def no_wait_for_eth_training(self, arg: bool, /) -> None: ...

    @property
    def predict_eth_fw_version(self) -> bool: ...

    @predict_eth_fw_version.setter
    def predict_eth_fw_version(self, arg: bool, /) -> None: ...

    @property
    def no_eth_firmware_strictness(self) -> bool: ...

    @no_eth_firmware_strictness.setter
    def no_eth_firmware_strictness(self, arg: bool, /) -> None: ...

class TopologyDiscovery:
    @staticmethod
    def create_cluster_descriptor(options: TopologyDiscoveryOptions = ...) -> ClusterDescriptor: ...

    @staticmethod
    def discover(options: TopologyDiscoveryOptions = ...) -> tuple[ClusterDescriptor, dict[int, TTDevice]]:
        """Discover topology and return both ClusterDescriptor and TTDevices"""

class WarmReset:
    @staticmethod
    def warm_reset(pci_device_ids: Sequence[int] = [], reset_m3: bool = False, secondary_bus_reset: bool = True) -> None:
        """
        Perform a warm reset of the device. reset_m3 flag sends specific ARC message to do a M3 board level reset. secondary_bus_reset flag performs a RESET_PCIE_LINK before issuing the ASIC reset.
        """

    @staticmethod
    def ubb_warm_reset(timeout_s: datetime.timedelta | float = 100.0) -> None:
        """Perform a UBB warm reset with specified timeout in seconds."""

class CoreType(enum.Enum):
    def __str__(self) -> str: ...

    def __repr__(self) -> str: ...

    ARC = 0

    DRAM = 1

    ACTIVE_ETH = 2

    IDLE_ETH = 3

    PCIE = 4

    TENSIX = 5

    ROUTER_ONLY = 6

    SECURITY = 7

    L2CPU = 8

    HARVESTED = 9

    ETH = 10

    WORKER = 11

class CoordSystem(enum.Enum):
    def __str__(self) -> str: ...

    def __repr__(self) -> str: ...

    LOGICAL = 0

    NOC0 = 1

    TRANSLATED = 2

    NOC1 = 3

class CoreCoord:
    def __init__(self, x: int, y: int, core_type: CoreType, coord_system: CoordSystem) -> None: ...

    @property
    def x(self) -> int: ...

    @property
    def y(self) -> int: ...

    @property
    def core_type(self) -> CoreType: ...

    @property
    def coord_system(self) -> CoordSystem: ...

    def __str__(self) -> str: ...

    def __repr__(self) -> str: ...

    def __eq__(self, arg: CoreCoord, /) -> bool: ...

    def __lt__(self, arg: CoreCoord, /) -> bool: ...

class SocDescriptor:
    def __init__(self, tt_device: TTDevice) -> None:
        """Create a SocDescriptor from a TTDevice"""

    def get_cores(self, core_type: CoreType, coord_system: CoordSystem = CoordSystem.NOC0, channel: Optional[int] = None) -> list[CoreCoord]:
        """Get all cores of a specific type in the specified coordinate system"""

    def get_harvested_cores(self, core_type: CoreType, coord_system: CoordSystem = CoordSystem.NOC0) -> list[CoreCoord]:
        """
        Get all harvested cores of a specific type in the specified coordinate system
        """

    def get_all_cores(self, coord_system: CoordSystem = CoordSystem.NOC0) -> list[CoreCoord]:
        """Get all cores in the specified coordinate system"""

    def get_all_harvested_cores(self, coord_system: CoordSystem = CoordSystem.NOC0) -> list[CoreCoord]:
        """Get all harvested cores in the specified coordinate system"""

    def serialize_to_file(self, dest_file: str = '') -> str:
        """Serialize the soc descriptor to a YAML file"""

    def get_eth_cores_for_channels(self, eth_channels: Set[int], coord_system: CoordSystem = CoordSystem.NOC0) -> set[CoreCoord]:
        """
        Get ethernet cores for specified channels in the specified coordinate system
        """

    @overload
    def translate_coord_to(self, core_coord: CoreCoord, coord_system: CoordSystem) -> CoreCoord:
        """Translate a CoreCoord to the specified coordinate system"""

    @overload
    def translate_coord_to(self, core_location: tt_xy_pair, input_coord_system: CoordSystem, target_coord_system: CoordSystem) -> CoreCoord:
        """Translate a tt_xy_pair from one coordinate system to another"""
