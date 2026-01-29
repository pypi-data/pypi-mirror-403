"""
pydpaux - DisplayPort AUX Access Wrapper
========================================

A Python wrapper to access DP/eDP-connected displays via AUX lines using SoC vendor-specific APIs.

Overview
--------
This module provides a high-level interface for interacting with DisplayPort-connected displays
through the AUX protocol. Currently, Intel IGCL API on Windows is implemented, with support for
other platforms planned.

System Requirements
-------------------
- 12th generation or later Intel Core processors
- Windows 10 or later

Key Features
-----------
- Query connected displays via AUX lines
- Search displays by name
- Access display information and metadata
- Partial name matching for display discovery
"""

from ._core import Display as Display

def get_displays() -> list[Display]:
    """
    Get all connected DP/eDP displays.

    Returns
    -------
    list[Display]
        A list of Display objects representing all connected displays detected via AUX.
    """

def find_display_by_name(kwd: str) -> Display | None:
    """
    Find a display by partial name match.

    This function searches through all connected displays and returns the first one
    whose name contains the given keyword (case-sensitive).

    Parameters
    ----------
    kwd : str
        Keyword to search for in display names. Supports partial matching.

    Returns
    -------
    Display | None
        The first Display object whose name contains the keyword, or None if no match found.

    Examples
    --------
    >>> display = find_display_by_name("HDMI")
    >>> if display:
    ...     print(f"Found: {display.name}")
    """

class Display:
    """
    Represents a DP/eDP-connected display.

    This class provides access to display properties and functionality
    available through the DisplayPort AUX protocol, including EDID parsing,
    AUX and I2C communication.
    """

    @property
    def name(self) -> str:
        """Display name or identifier."""
        ...

    @property
    def serial(self) -> str:
        """Display serial number."""
        ...

    @property
    def edid_size(self) -> int:
        """Size of the EDID data in bytes."""
        ...

    @property
    def edid(self) -> bytes:
        """
        EDID (Extended Display Identification Data) as bytes.

        Returns
        -------
        bytes
            The complete EDID data for this display.
        """
        ...

    def aux_read(self, address: int, size: int) -> bytes:
        """
        Read data from DisplayPort AUX channel.

        Parameters
        ----------
        address : int
            AUX channel address to read from.
        size : int
            Number of bytes to read.

        Returns
        -------
        bytes
            The data read from the AUX channel.

        Raises
        ------
        PermissionError
            If insufficient permissions (requires elevated privileges).
        RuntimeError
            If the AUX read operation fails.
        """
        ...

    def aux_write(self, address: int, data: bytes) -> int:
        """
        Write data to DisplayPort AUX channel.

        Parameters
        ----------
        address : int
            AUX channel address to write to.
        data : bytes
            Data to write to the AUX channel.

        Returns
        -------
        int
            Result code (0 on success).

        Raises
        ------
        PermissionError
            If insufficient permissions (requires elevated privileges).
        RuntimeError
            If the AUX write operation fails.
        """
        ...

    def i2c_read(self, address: int, offset: int, size: int) -> bytes:
        """
        Read data from I2C bus.

        Parameters
        ----------
        address : int
            I2C device address.
        offset : int
            Offset within the I2C device.
        size : int
            Number of bytes to read.

        Returns
        -------
        bytes
            The data read from the I2C device.

        Raises
        ------
        PermissionError
            If insufficient permissions (requires elevated privileges).
        RuntimeError
            If the I2C read operation fails.
        """
        ...

    def i2c_write(self, address: int, offset: int, data: bytes) -> int:
        """
        Write data to I2C bus.

        Parameters
        ----------
        address : int
            I2C device address.
        offset : int
            Offset within the I2C device.
        data : bytes
            Data to write to the I2C device.

        Returns
        -------
        int
            Result code (0 on success).

        Raises
        ------
        PermissionError
            If insufficient permissions (requires elevated privileges).
        RuntimeError
            If the I2C write operation fails.
        """
        ...

    def refresh_handle(self) -> int:
        """
        Refresh the display output handle.

        This updates the internal display handle to reflect any changes
        in the display connection state.

        Returns
        -------
        int
            Result code (0 on success).

        Raises
        ------
        PermissionError
            If insufficient permissions (requires elevated privileges).
        RuntimeError
            If the refresh operation fails.
        """
        ...

__version__: str
__doc__: str

__all__ = ["Display", "get_displays", "find_display_by_name", "__version__", "__doc__"]