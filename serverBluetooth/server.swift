import Foundation
import CoreBluetooth

class BLEServer: NSObject, CBPeripheralManagerDelegate {
    var peripheralManager: CBPeripheralManager?
    var characteristic: CBMutableCharacteristic?
    
    var fileBase64CacheDownload: [String: String] = [:]
    
    var fileBase64CacheUpload: [String: String] = [:]

    let chunkSize = 300
    
    let currentDirectory = FileManager.default.currentDirectoryPath

    var lastValue: Data = Data()

    override init() {
        super.init()
        peripheralManager = CBPeripheralManager(delegate: self, queue: nil)
    }

    func peripheralManagerDidUpdateState(_ peripheral: CBPeripheralManager) {
        if peripheral.state == .poweredOn {
            print("BLE Server is Running on macOS")
            
            let serviceUUID = CBUUID(string: "12345678-1234-5678-1234-56789abcdef0")
            let charUUID    = CBUUID(string: "12345678-1234-5678-1234-56789abcdef1")

            characteristic = CBMutableCharacteristic(
                type: charUUID,
                properties: [.read, .write, .notify],
                value: nil,
                permissions: [.readable, .writeable]
            )

            let service = CBMutableService(type: serviceUUID, primary: true)
            service.characteristics = [characteristic!]
            peripheralManager?.add(service)

            peripheralManager?.startAdvertising([CBAdvertisementDataServiceUUIDsKey: [serviceUUID]])
            print("Advertising BLE Service... in directory:", currentDirectory)
        } else {
            print("Bluetooth is OFF or Unavailable (state: \(peripheral.state.rawValue))")
        }
    }

    func peripheralManager(_ peripheral: CBPeripheralManager, didReceiveWrite requests: [CBATTRequest]) {
        for request in requests {
            if request.characteristic.uuid == characteristic?.uuid,
               let value = request.value {
                
                let commandString = String(data: value, encoding: .utf8) ?? ""
                print("Received command from client: \(commandString)")
                
                let responseString = self.processCommand(commandString)

                if let data = responseString.data(using: .utf8) {
                    self.lastValue = data
                } else {
                    self.lastValue = Data()
                }
                
                peripheralManager?.respond(to: request, withResult: .success)
            }
        }
    }

    func peripheralManager(_ peripheral: CBPeripheralManager, didReceiveRead request: CBATTRequest) {
        if request.characteristic.uuid == characteristic?.uuid {
            request.value = self.lastValue
            peripheralManager?.respond(to: request, withResult: .success)

            let debugString = String(data: self.lastValue, encoding: .utf8) ?? "nil"
            print("Client read request, returning: \(debugString.prefix(80))...")
        }
    }

    private func processCommand(_ cmd: String) -> String {

        let trimmed = cmd.trimmingCharacters(in: .whitespacesAndNewlines)
        let upper = trimmed.uppercased()

        if upper == "LIST" {
            return listFiles()
        }
        else if upper.hasPrefix("DOWNLOAD ") {
            return handleDownload(trimmed)
        }
        else if upper.hasPrefix("UPLOADCHUNK:") {
            return handleUploadChunk(trimmed)
        }
        else if upper.hasPrefix("COMMENT ") {
            let comment = String(trimmed.dropFirst("COMMENT ".count))
            return storeComment(comment)
        }
        else {
            return "ERROR: Unrecognized command."
        }
    }

    private func listFiles() -> String {
        do {
            let files = try FileManager.default.contentsOfDirectory(atPath: currentDirectory)
            let fileList = files.joined(separator: ", ")
            return "FILES: \(fileList)"
        } catch {
            return "ERROR: Failed to list files → \(error)"
        }
    }

    private func handleDownload(_ fullCmd: String) -> String {
        let noPrefix = String(fullCmd.dropFirst("DOWNLOAD ".count)).trimmingCharacters(in: .whitespaces)
        guard let colonIndex = noPrefix.firstIndex(of: ":") else {
            return "ERROR: Use DOWNLOAD <filename>:<offset>"
        }

        let filename = String(noPrefix[..<colonIndex]).trimmingCharacters(in: .whitespaces)
        let offsetStr = String(noPrefix[noPrefix.index(after: colonIndex)...]).trimmingCharacters(in: .whitespaces)

        guard let offset = Int(offsetStr) else {
            return "ERROR: Invalid offset \(offsetStr)."
        }

        return downloadChunk(filename: filename, offset: offset)
    }

    private func downloadChunk(filename: String, offset: Int) -> String {
        if offset == 0 {
            let filePath = URL(fileURLWithPath: currentDirectory).appendingPathComponent(filename).path
            guard FileManager.default.fileExists(atPath: filePath) else {
                return "ERROR: File '\(filename)' does not exist."
            }
            do {
                let fileData = try Data(contentsOf: URL(fileURLWithPath: filePath))
                let base64 = fileData.base64EncodedString()
                fileBase64CacheDownload[filename] = base64
            } catch {
                return "ERROR: Failed to read file '\(filename)': \(error)"
            }
        }

        guard let b64 = fileBase64CacheDownload[filename], !b64.isEmpty else {
            return "ERROR: No base64 cached for '\(filename)'."
        }

        let startIndex = offset
        let endIndex   = min(offset + chunkSize, b64.count)

        if startIndex >= b64.count {
            fileBase64CacheDownload.removeValue(forKey: filename)
            return "CHUNK:\(filename):\(offset)-\(offset)::DONE"
        }

        let range = b64.index(b64.startIndex, offsetBy: startIndex)..<b64.index(b64.startIndex, offsetBy: endIndex)
        let chunk = String(b64[range])
        let nextOffset = endIndex
        let status = (endIndex >= b64.count) ? "DONE" : "CONT"

        if status == "DONE" {
            fileBase64CacheDownload.removeValue(forKey: filename)
        }

        return "CHUNK:\(filename):\(startIndex)-\(endIndex):\(chunk):\(status)"
    }

    private func handleUploadChunk(_ fullCmd: String) -> String {
        let noPrefix = String(fullCmd.dropFirst("UPLOADCHUNK:".count))
        let parts = noPrefix.split(separator: ":", maxSplits: 3, omittingEmptySubsequences: false)
        guard parts.count == 4 else {
            return "ERROR: Invalid UPLOADCHUNK format."
        }

        let filename = String(parts[0])
        let rangeStr = String(parts[1])
        let base64chunk = String(parts[2])
        let status = String(parts[3])

        if fileBase64CacheUpload[filename] == nil, rangeStr.hasPrefix("0-") {
            fileBase64CacheUpload[filename] = ""
        }

        if var existingB64 = fileBase64CacheUpload[filename] {
            existingB64 += base64chunk
            fileBase64CacheUpload[filename] = existingB64

            if status.uppercased() == "DONE" {
                let result = finalizeUpload(filename: filename)
                fileBase64CacheUpload.removeValue(forKey: filename)
                return result
            } else {
                return "UPLOADCHUNK CONT: \(filename)"
            }
        } else {
            return "ERROR: No upload cache for \(filename). Did you start from offset 0?"
        }
    }

    private func finalizeUpload(filename: String) -> String {
        guard let base64 = fileBase64CacheUpload[filename] else {
            return "ERROR: No base64 data for \(filename)."
        }
        guard let rawData = Data(base64Encoded: base64) else {
            return "ERROR: Could not decode base64 for \(filename)."
        }
        let fileURL = URL(fileURLWithPath: currentDirectory).appendingPathComponent(filename)
        do {
            try rawData.write(to: fileURL)
            print("Uploaded file saved as \(fileURL.lastPathComponent)")
            return "UPLOAD SUCCESS: \(filename) saved on server."
        } catch {
            return "ERROR: Failed writing \(filename): \(error)"
        }
    }

    private func storeComment(_ comment: String) -> String {
        print("Client Comment: \(comment)")
        return "Comment Received: \(comment)"
    }
}

let bleServer = BLEServer()
RunLoop.main.run()
