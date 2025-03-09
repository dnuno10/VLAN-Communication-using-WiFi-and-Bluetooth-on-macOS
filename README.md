# VLAN Communication using WiFi and Bluetooth on macOS

This repository contains scripts for implementing VLAN communication between macOS devices using both WiFi and Bluetooth technologies. The implementation allows for file listing, file uploads, and file downloads through both protocols.

## Repository Structure

The repository is organized into four main folders:

- **WiFi Client**: Contains `clientWifi.py` for WiFi-based client operations
- **WiFi Server**: Contains `serverWifi.py` for WiFi-based server operations
- **Bluetooth Client**: Contains `clientBluetooth.py` for Bluetooth-based client operations
- **Bluetooth Server**: Contains `serverBluetooth.swift` for Bluetooth-based server operations
- **Utilities**: Contains `scan.py` for scanning Bluetooth devices

## Installation and Setup

### Prerequisites

- macOS operating system
- Python 3.8 or later
- Swift 5.0 or later
- Miniforge or Conda for virtual environment management

### Environment Setup

1. **Install Miniforge/Conda**:
   - Download Miniforge from [GitHub](https://github.com/conda-forge/miniforge)
   - Run the installer and follow the on-screen instructions
   - Verify installation by running: `conda --version`

2. **Create Virtual Environment**:
   ```bash
   conda create -n socket python=3.8
   conda activate socket
   ```

3. **Install Required Python Packages**:
   ```bash
   # For WiFi communication (both client and server)
   conda install -c conda-forge numpy
   
   # For Bluetooth client
   conda install -c conda-forge bleak
   ```

4. **Setup for Bluetooth Server**:
   - Ensure Xcode Command Line Tools are installed:
   ```bash
   xcode-select --install
   ```
   - Verify Swift installation:
   ```bash
   swift --version
   ```

### Clone the Repository

```bash
git clone https://github.com/yourusername/VLAN-Communication-using-WiFi-and-Bluetooth-on-macOS.git
cd VLAN-Communication-using-WiFi-and-Bluetooth-on-macOS
```

### Configuration

1. **WiFi Setup**:
   - Edit `clientWifi.py` to specify the server's IP address:
   ```python
   # Change this to your server's IP address
   SERVER_HOST = "192.168.x.x"
   ```

2. **Bluetooth Setup**:
   - Run the scan utility to find your Bluetooth server:
   ```bash
   conda activate socket
   python scan.py
   ```
   - Note the server address and update `clientBluetooth.py` if needed:
   ```python
   # Update with your server's address from scan results
   SERVER_ADDRESS = "XX:XX:XX:XX:XX:XX"
   ```

## Technologies Used

- **WiFi Communication**: Implemented using Python's socket library
- **Bluetooth Communication**: Implemented using CoreBluetooth (Swift) for the server and Bleak (Python) for the client
- **Development Environment**: macOS, Miniforge (Conda Virtual Environment)

## WiFi Communication

The WiFi implementation establishes a client-server communication channel using Python sockets.

### Server (serverWifi.py)

The server script:
- Creates a socket and binds it to a specified IP and port
- Listens for incoming client connections
- Handles client requests for file listing, uploads, and downloads
- Processes data transfers and confirms successful operations

### Client (clientWifi.py)

The client script:
- Connects to the server using the server's IP address
- Provides a menu of operations (list files, download, upload)
- Handles file transfers between client and server
- Displays confirmations of successful operations

## Bluetooth Communication

The Bluetooth implementation leverages BLE (Bluetooth Low Energy) for data transfer between devices.

### Server (serverBluetooth.swift)

The Swift-based server:
- Utilizes Apple's CoreBluetooth framework
- Broadcasts BLE services with specific characteristics
- Handles client requests for file operations
- Processes chunk-based file transfers due to BLE limitations

### Client (clientBluetooth.py)

The Python-based client:
- Uses the Bleak library for BLE communication
- Scans for available BLE devices
- Connects to the server's BLE service
- Implements chunk-based file transfer functionality

### Scan Utility (scan.py)

This utility script:
- Scans for available BLE devices in the vicinity
- Displays device information including addresses
- Helps in identifying the correct Bluetooth server

## Usage Instructions

### WiFi Communication

#### Server Setup:
1. Navigate to the WiFi Server directory
2. Activate the virtual environment: `conda activate socket`
3. Run the server: `python serverWifi.py`
4. The server will display a message indicating it's waiting for client connections

#### Client Setup:
1. Navigate to the WiFi Client directory
2. Ensure the script contains the correct server IP
3. Activate the virtual environment: `conda activate socket`
4. Run the client: `python clientWifi.py`
5. Choose from available operations (list, download, upload)

### Bluetooth Communication

#### Server Setup:
1. Navigate to the Bluetooth Server directory
2. Run the Swift script: `swift serverBluetooth.swift`
3. Grant necessary Bluetooth permissions when prompted
4. Confirm the server is broadcasting its BLE services

#### Client Setup:
1. Navigate to the Bluetooth Client directory
2. Run the scan utility to find the server: `python scan.py`
3. Note the server address and update the client script if needed
4. Run the client: `python clientBluetooth.py`
5. Choose from available operations (list, download, upload)

## Troubleshooting

### WiFi Connection Issues
- Ensure both devices are on the same network
- Verify firewall settings to allow Python to access the network
- Check if the specified port is available and not blocked

### Bluetooth Connection Issues
- Ensure Bluetooth is enabled on both devices
- Verify that your macOS device has granted Bluetooth permissions to the application
- Make sure devices are within range (typically 10 meters for Bluetooth)
- Restart the Bluetooth service if connection problems persist

## Performance Comparison

- **WiFi**: Offers high-speed connectivity, supporting large file transfers with minimal latency
- **Bluetooth**: Requires chunk-based transfers due to lower bandwidth but proves effective for small to medium-sized file transfers

## Technical Details

### WiFi Implementation
- Uses TCP sockets for reliable data transfer
- Implements a simple command protocol for operations
- Handles binary file transfers efficiently

### Bluetooth Implementation
- Uses GATT protocol for BLE communication
- Implements chunked data transfer to overcome BLE data limitations
- Manages reconnection for multi-chunk transfers

## System Requirements

- macOS operating system (tested on macOS Ventura)
- Python 3.8 or later
- Swift 5.0 or later
- Conda or Miniforge for virtual environment management
- Bleak library for Python (BLE client)
- Core Bluetooth framework (built into macOS)

## Future Improvements

Potential enhancements include:
- Implementing encryption for secure transfers
- Optimizing Bluetooth chunk transmission to reduce latency
- Adding support for more file operations
- Extending the solution to support additional communication protocols

## Citation

If you use this code for academic purposes, please cite:
```
Nuño, D., Hernandez, K., & Sanchez Adame, M. (2025). Implementation of VLAN Communication using WiFi and Bluetooth on macOS. CETYS University.
```
