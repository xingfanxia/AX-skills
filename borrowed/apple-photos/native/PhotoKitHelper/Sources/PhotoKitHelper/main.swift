import CryptoKit
import Darwin
import Foundation
import Photos
import PhotoKitCore

let protocolVersion = "2.0"

enum HelperError: Error {
    case invalidRequest(String)
    case permission(String)
    case notFound(String)
    case transaction(String)
    case resource(String)
    case stale(String)
    case authorizationExpired(String)
    case authorizationReplay(String)

    var code: String {
        switch self {
        case .invalidRequest: return "E_BACKEND_PROTOCOL"
        case .permission: return "E_PERMISSION_PHOTOS"
        case .notFound: return "E_NOT_FOUND"
        case .transaction: return "E_BACKEND_TRANSACTION"
        case .resource: return "E_RESOURCE_UNAVAILABLE"
        case .stale: return "E_PLAN_STALE"
        case .authorizationExpired: return "E_AUTH_EXPIRED"
        case .authorizationReplay: return "E_AUTH_REPLAY"
        }
    }

    var message: String {
        switch self {
        case let .invalidRequest(value), let .permission(value), let .notFound(value),
             let .transaction(value), let .resource(value), let .stale(value),
             let .authorizationExpired(value):
            return value
        case let .authorizationReplay(value): return value
        }
    }

    var mutationPhase: String {
        switch self {
        case .transaction: return "commit_attempted"
        default: return "not_started"
        }
    }
}

func writeResponse(ok: Bool, result: Any? = nil, error: HelperError? = nil) {
    var response: [String: Any] = ["protocol_version": protocolVersion, "ok": ok]
    if let result {
        response["result"] = result
    }
    if let error {
        response["error"] = [
            "code": error.code,
            "message": error.message,
            "detail": ["mutation_phase": error.mutationPhase]
        ]
    }
    do {
        let data = try JSONSerialization.data(withJSONObject: response, options: [.sortedKeys])
        FileHandle.standardOutput.write(data)
        FileHandle.standardOutput.write(Data("\n".utf8))
    } catch {
        FileHandle.standardError.write(Data("Could not encode helper response.\n".utf8))
        exit(7)
    }
}

func requestAuthorization() throws {
    let semaphore = DispatchSemaphore(value: 0)
    var observed = PHAuthorizationStatus.notDetermined
    PHPhotoLibrary.requestAuthorization(for: .readWrite) { status in
        observed = status
        semaphore.signal()
    }
    semaphore.wait()
    guard observed == .authorized else {
        throw HelperError.permission("PhotoKit read/write authorization is required; status=\(observed.rawValue).")
    }
}

func payloadArray(_ payload: [String: Any], _ key: String) throws -> [String] {
    guard let values = payload[key] as? [String] else {
        throw HelperError.invalidRequest("Payload field '\(key)' must be a string array.")
    }
    return values
}

func fetchAssets(_ identifiers: [String]?, includeAll: Bool = false) -> [PHAsset] {
    let result: PHFetchResult<PHAsset>
    if includeAll {
        result = PHAsset.fetchAssets(with: nil)
    } else {
        result = PHAsset.fetchAssets(withLocalIdentifiers: identifiers ?? [], options: nil)
    }
    var assets: [PHAsset] = []
    result.enumerateObjects { asset, _, _ in assets.append(asset) }
    return assets
}

func fetchAlbum(_ identifier: String) throws -> PHAssetCollection {
    let result = PHAssetCollection.fetchAssetCollections(
        withLocalIdentifiers: [identifier],
        options: nil
    )
    guard result.count == 1, let album = result.firstObject else {
        throw HelperError.notFound("Album identifier did not resolve to exactly one album.")
    }
    return album
}

func resourceRole(_ type: PHAssetResourceType) -> String {
    switch type {
    case .photo, .fullSizePhoto, .alternatePhoto: return "photo"
    case .video, .fullSizeVideo: return "video"
    case .audio: return "audio"
    case .pairedVideo, .fullSizePairedVideo: return "paired_video"
    case .adjustmentData: return "adjustment"
    case .adjustmentBasePhoto, .adjustmentBaseVideo, .adjustmentBasePairedVideo:
        return "adjustment_base"
    case .photoProxy: return "photo_proxy"
    @unknown default: return "unknown_\(type.rawValue)"
    }
}

func assetMediaType(_ type: PHAssetMediaType) -> String {
    switch type {
    case .image: return "image"
    case .video: return "video"
    case .audio: return "audio"
    case .unknown: return "unknown"
    @unknown default: return "unknown"
    }
}

let isoFormatter: ISO8601DateFormatter = {
    let formatter = ISO8601DateFormatter()
    formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
    return formatter
}()

func assetDictionary(_ asset: PHAsset) -> [String: Any] {
    let resources = PHAssetResource.assetResources(for: asset)
    let descriptors: [[String: Any]] = resources.map { resource in
        [
            "role": resourceRole(resource.type),
            "uti": resource.uniformTypeIdentifier,
            "original_filename": resource.originalFilename
        ]
    }
    return [
        "local_identifier": asset.localIdentifier,
        "media_type": assetMediaType(asset.mediaType),
        "original_filename": resources.first?.originalFilename ?? NSNull(),
        "date_taken": asset.creationDate.map(isoFormatter.string(from:)) ?? NSNull(),
        "date_modified": asset.modificationDate.map(isoFormatter.string(from:)) ?? NSNull(),
        "width": asset.pixelWidth,
        "height": asset.pixelHeight,
        "duration_ms": Int((asset.duration * 1000).rounded()),
        "favorite": asset.isFavorite,
        "hidden": asset.isHidden,
        "in_trash": false,
        "resource_descriptors": descriptors
    ]
}

func sha256File(_ url: URL) throws -> String {
    guard let stream = InputStream(url: url) else {
        throw HelperError.resource("Could not open an exported resource for hashing.")
    }
    stream.open()
    defer { stream.close() }
    var hasher = SHA256()
    let buffer = UnsafeMutablePointer<UInt8>.allocate(capacity: 1024 * 1024)
    defer { buffer.deallocate() }
    while stream.hasBytesAvailable {
        let count = stream.read(buffer, maxLength: 1024 * 1024)
        if count < 0 {
            throw HelperError.resource(stream.streamError?.localizedDescription ?? "Resource hash read failed.")
        }
        if count == 0 { break }
        hasher.update(data: Data(bytes: buffer, count: count))
    }
    return hasher.finalize().map { String(format: "%02x", $0) }.joined()
}

func safeComponent(_ value: String) -> String {
    let allowed = CharacterSet.alphanumerics.union(CharacterSet(charactersIn: "._-"))
    let filtered = value.unicodeScalars.map { allowed.contains($0) ? Character(String($0)) : "_" }
    return String(filtered).prefix(120).description
}

func writeResource(_ resource: PHAssetResource, to url: URL, network: Bool) -> Error? {
    let semaphore = DispatchSemaphore(value: 0)
    let options = PHAssetResourceRequestOptions()
    options.isNetworkAccessAllowed = network
    var observedError: Error?
    PHAssetResourceManager.default().writeData(for: resource, toFile: url, options: options) { error in
        observedError = error
        semaphore.signal()
    }
    semaphore.wait()
    return observedError
}

func probeLibrary() throws -> [String: Any] {
    try requestAuthorization()
    let allAssets = fetchAssets(nil, includeAll: true)
    let identifiers = allAssets.map(\.localIdentifier).sorted()
    var hasher = SHA256()
    for identifier in identifiers {
        hasher.update(data: Data(identifier.utf8))
        hasher.update(data: Data([0]))
    }
    let identifierDigest = hasher.finalize().map { String(format: "%02x", $0) }.joined()
    return [
        "library_snapshot": [
            "kind": "system_photo_library_snapshot",
            "canonical_path": NSNull(),
            "is_system_library": true,
            "physical_identity_verified": false,
            "sentinel_asset_ids": Array(identifiers.prefix(3)),
            "asset_ids_sha256": "sha256:\(identifierDigest)",
            "asset_count": allAssets.count,
            "observed_at": isoFormatter.string(from: Date())
        ]
    ]
}

func listAlbums() throws -> [String: Any] {
    try requestAuthorization()
    let options = PHFetchOptions()
    let result = PHAssetCollection.fetchAssetCollections(with: .album, subtype: .any, options: options)
    var albums: [[String: Any]] = []
    result.enumerateObjects { album, _, _ in
        albums.append([
            "local_identifier": album.localIdentifier,
            "title": album.localizedTitle ?? "",
            "asset_count": PHAsset.fetchAssets(in: album, options: nil).count
            ,"can_add_assets": album.canPerform(.addContent)
        ])
    }
    albums.sort {
        let left = ($0["local_identifier"] as? String) ?? ""
        let right = ($1["local_identifier"] as? String) ?? ""
        return left < right
    }
    return ["albums": albums]
}

func fetchAssetDictionaries(_ payload: [String: Any]) throws -> [String: Any] {
    try requestAuthorization()
    let includeAll = (payload["include_all"] as? Bool) ?? false
    let identifiers = try payloadArray(payload, "local_identifiers")
    return ["assets": fetchAssets(identifiers, includeAll: includeAll).map(assetDictionary)]
}

func readResources(_ payload: [String: Any]) throws -> [String: Any] {
    try requestAuthorization()
    let identifiers = try payloadArray(payload, "local_identifiers")
    let network = (payload["network_access_allowed"] as? Bool) ?? false
    let requestedOutput = payload["output_directory"] as? String
    let root: URL
    let retainFiles: Bool
    if let requestedOutput {
        root = URL(fileURLWithPath: requestedOutput, isDirectory: true)
        retainFiles = true
    } else {
        root = FileManager.default.temporaryDirectory
            .appendingPathComponent("apple-photos-helper-\(UUID().uuidString)", isDirectory: true)
        retainFiles = false
    }
    try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
    defer { if !retainFiles { try? FileManager.default.removeItem(at: root) } }
    var output: [[String: Any]] = []
    for asset in fetchAssets(identifiers) {
        for (index, resource) in PHAssetResource.assetResources(for: asset).enumerated() {
            let directory = root.appendingPathComponent(safeComponent(asset.localIdentifier), isDirectory: true)
            try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
            let name = "\(index)-\(safeComponent(resource.originalFilename))"
            let url = directory.appendingPathComponent(name)
            if let error = writeResource(resource, to: url, network: network) {
                output.append([
                    "local_identifier": asset.localIdentifier,
                    "role": resourceRole(resource.type),
                    "uti": resource.uniformTypeIdentifier,
                    "byte_count": 0,
                    "sha256": "",
                    "availability": "unavailable",
                    "path": NSNull(),
                    "backend_error": error.localizedDescription
                ])
                continue
            }
            let size = (try? url.resourceValues(forKeys: [.fileSizeKey]).fileSize) ?? 0
            output.append([
                "local_identifier": asset.localIdentifier,
                "role": resourceRole(resource.type),
                "uti": resource.uniformTypeIdentifier,
                "byte_count": size,
                "sha256": try sha256File(url),
                "availability": "available",
                "path": retainFiles ? url.path : NSNull()
            ])
            if !retainFiles { try? FileManager.default.removeItem(at: url) }
        }
    }
    return ["resources": output]
}

func importAssets(_ payload: [String: Any]) throws -> [String: Any] {
    try requestAuthorization()
    do {
        return try dispatchImportPayload(payload) { validated, albumIdentifier in
            try importValidatedAssets(validated, albumIdentifier: albumIdentifier)
        }
    } catch is ImportFieldError {
        throw HelperError.invalidRequest("Every import item must use a supported canonical UTI and role.")
    }
}

func importValidatedAssets(
    _ validated: [ValidatedImportFields], albumIdentifier: String
) throws -> [String: Any] {
    for item in validated {
        var isDirectory: ObjCBool = false
        guard FileManager.default.fileExists(atPath: item.stagedPath, isDirectory: &isDirectory),
              !isDirectory.boolValue,
              FileManager.default.isReadableFile(atPath: item.stagedPath) else {
            throw HelperError.invalidRequest("Every staged import path must be a readable regular file.")
        }
    }
    let album = try fetchAlbum(albumIdentifier)
    guard album.canPerform(.addContent) else {
        throw HelperError.invalidRequest("Target album does not allow adding assets.")
    }
    let evidence = executePerItemImport(validated) { item in
        var placeholder: PHObjectPlaceholder?
        var transactionPlanError: Error?
        try PHPhotoLibrary.shared().performChangesAndWait {
            do {
                try executeOrderedAlbumMutation(
                    acquireAlbumChange: { PHAssetCollectionChangeRequest(for: album) }
                ) { change in
                    let request = PHAssetCreationRequest.forAsset()
                    let options = PHAssetResourceCreationOptions()
                    options.uniformTypeIdentifier = item.uti
                    let type: PHAssetResourceType = item.role == "video" ? .video : .photo
                    request.addResource(
                        with: type,
                        fileURL: URL(fileURLWithPath: item.stagedPath),
                        options: options
                    )
                    placeholder = request.placeholderForCreatedAsset
                    if let placeholder {
                        change.addAssets([placeholder] as NSArray)
                    }
                }
            } catch {
                transactionPlanError = error
            }
        }
        if let transactionPlanError {
            throw transactionPlanError
        }
        return placeholder?.localIdentifier
    }
    let knownCount = evidence.filter { $0.status == .createdIdentifierKnown }.count
    let unknownCount = evidence.filter {
        $0.status == .outcomeUnknown || $0.status == .notAttemptedAfterUnknown
    }.count
    let notAttemptedCount = evidence.filter { $0.status == .notAttempted }.count
    let status = unknownCount > 0
        ? (knownCount == 0 ? "outcome_unknown" : "partial")
        : (notAttemptedCount > 0 ? "partial" : "succeeded")
    return [
        "status": status,
        "items": evidence.map { item -> [String: Any] in
            [
                "item_id": item.itemID,
                "local_identifier": item.localIdentifier.map { $0 as Any } ?? NSNull(),
                "status": item.status.rawValue,
                "evidence": item.evidence
            ]
        }
    ]
}

func addAssetsToAlbum(_ payload: [String: Any]) throws -> [String: Any] {
    try requestAuthorization()
    let identifiers = try payloadArray(payload, "local_identifiers")
    guard let albumIdentifier = payload["album_id"] as? String else {
        throw HelperError.invalidRequest("Album identifier is required.")
    }
    let assets = fetchAssets(identifiers)
    guard assets.count == identifiers.count else {
        throw HelperError.notFound("One or more assets were not found before album mutation.")
    }
    let album = try fetchAlbum(albumIdentifier)
    guard album.canPerform(.addContent) else {
        throw HelperError.invalidRequest("Target album does not allow adding assets.")
    }
    do {
        try PHPhotoLibrary.shared().performChangesAndWait {
            PHAssetCollectionChangeRequest(for: album)?.addAssets(assets as NSArray)
        }
    } catch {
        throw HelperError.transaction(error.localizedDescription)
    }
    return ["local_identifiers": identifiers]
}

func urlSafeBase64Data(_ value: String) -> Data? {
    var normalized = value.replacingOccurrences(of: "-", with: "+")
        .replacingOccurrences(of: "_", with: "/")
    normalized += String(repeating: "=", count: (4 - normalized.count % 4) % 4)
    return Data(base64Encoded: normalized)
}

func exactKeys(_ value: [String: Any], _ expected: Set<String>) -> Bool {
    Set(value.keys) == expected
}

func authorizationSecret() throws -> SymmetricKey {
    guard let account = getpwuid(getuid()) else {
        throw HelperError.invalidRequest("Current account home directory is unavailable.")
    }
    let path = URL(fileURLWithPath: String(cString: account.pointee.pw_dir), isDirectory: true)
        .appendingPathComponent("Library/Application Support/apple-photos-skill")
        .appendingPathComponent("authorization-secret").path
    guard let data = FileManager.default.contents(atPath: path), data.count == 32 else {
        throw HelperError.invalidRequest("Delete authorization secret is unavailable.")
    }
    return SymmetricKey(data: data)
}

func consumeNativeNonce(_ nonce: String, manifestDigest: String) throws {
    guard let account = getpwuid(getuid()) else {
        throw HelperError.invalidRequest("Current account home directory is unavailable.")
    }
    let root = URL(fileURLWithPath: String(cString: account.pointee.pw_dir), isDirectory: true)
        .appendingPathComponent("Library/Application Support/apple-photos-skill/native-nonces")
    let rootExisted = FileManager.default.fileExists(atPath: root.path)
    try FileManager.default.createDirectory(
        at: root, withIntermediateDirectories: true,
        attributes: [.posixPermissions: 0o700]
    )
    if !rootExisted {
        let parent = Darwin.open(root.deletingLastPathComponent().path, O_RDONLY)
        guard parent >= 0, Darwin.fsync(parent) == 0 else {
            if parent >= 0 { Darwin.close(parent) }
            throw HelperError.invalidRequest("Could not persist native replay directory.")
        }
        Darwin.close(parent)
    }
    let path = root.appendingPathComponent(nonce).path
    let descriptor = Darwin.open(path, O_WRONLY | O_CREAT | O_EXCL, 0o600)
    guard descriptor >= 0 else {
        if errno == EEXIST {
            throw HelperError.authorizationReplay("Delete authorization was already used.")
        }
        throw HelperError.invalidRequest("Could not persist native authorization replay state.")
    }
    defer { Darwin.close(descriptor) }
    let data = Data(manifestDigest.utf8)
    let written = data.withUnsafeBytes { buffer in
        Darwin.write(descriptor, buffer.baseAddress, buffer.count)
    }
    guard written == data.count, Darwin.fsync(descriptor) == 0 else {
        throw HelperError.invalidRequest("Could not persist native authorization replay state.")
    }
    let directory = Darwin.open(root.path, O_RDONLY)
    guard directory >= 0 else {
        throw HelperError.invalidRequest("Could not persist native authorization replay state.")
    }
    defer { Darwin.close(directory) }
    guard Darwin.fsync(directory) == 0 else {
        throw HelperError.invalidRequest("Could not persist native authorization replay state.")
    }
}

func verifiedSignedObject(
    encoded: Any?, signature: Any?, key: SymmetricKey
) throws -> ([String: Any], Data) {
    guard let encoded = encoded as? String,
          let signed = urlSafeBase64Data(encoded),
          let signature = signature as? String,
          let signatureData = urlSafeBase64Data(signature),
          HMAC<SHA256>.isValidAuthenticationCode(
              signatureData, authenticating: signed, using: key
          ),
          let object = try JSONSerialization.jsonObject(with: signed) as? [String: Any] else {
        throw HelperError.invalidRequest("Delete authorization signature is invalid.")
    }
    return (object, signed)
}

func verifyDeleteAuthorizationEnvelope(
    _ payload: [String: Any], items: [[String: Any]], manifestDigest: String
) throws -> Date {
    let key = try authorizationSecret()
    guard let attestation = payload["evidence_attestation"] as? [String: Any],
          exactKeys(attestation, ["algorithm", "claims_sha256", "signed_claims", "signature"]),
          attestation["algorithm"] as? String == "hmac-sha256",
          let claimsDigest = attestation["claims_sha256"] as? String else {
        throw HelperError.invalidRequest("Delete evidence attestation is malformed.")
    }
    let (evidenceClaims, signedEvidence) = try verifiedSignedObject(
        encoded: attestation["signed_claims"], signature: attestation["signature"], key: key
    )
    let observedEvidenceDigest = SHA256.hash(data: signedEvidence)
        .map { String(format: "%02x", $0) }.joined()
    let manifestFormatter = ISO8601DateFormatter()
    manifestFormatter.formatOptions = [.withInternetDateTime]
    guard claimsDigest == "sha256:\(observedEvidenceDigest)",
          evidenceClaims["purpose"] as? String == "pixel_delete_plan_v1",
          let signedManifest = evidenceClaims["manifest"] as? [String: Any],
          let signedItems = signedManifest["items"] as? [[String: Any]],
          (signedItems as NSArray).isEqual(to: items),
          let deletePolicy = signedManifest["delete_policy"] as? [String: Any],
          let signedNetwork = deletePolicy["network_access_allowed"] as? Bool,
          payload["network_access_allowed"] as? Bool == signedNetwork,
          let createdValue = signedManifest["created_at"] as? String,
          let manifestExpiresValue = signedManifest["expires_at"] as? String,
          let createdAt = manifestFormatter.date(from: createdValue),
          let manifestExpiresAt = manifestFormatter.date(from: manifestExpiresValue),
          createdAt <= Date().addingTimeInterval(5 * 60),
          manifestExpiresAt > Date(), manifestExpiresAt > createdAt,
          manifestExpiresAt.timeIntervalSince(createdAt) <= 24 * 60 * 60 else {
        throw HelperError.invalidRequest("Delete evidence does not match the requested items.")
    }

    guard let token = payload["authorization_token"] as? [String: Any],
          exactKeys(token, ["claims", "signed_claims", "signature"]),
          let claims = token["claims"] as? [String: Any],
          exactKeys(claims, [
              "schema_version", "action", "manifest_sha256", "evidence_claims_sha256",
              "library_snapshot_digest", "item_count", "issued_at", "expires_at",
              "nonce", "cli_major"
          ]) else {
        throw HelperError.invalidRequest("Delete authorization token is malformed.")
    }
    let (signedClaims, _) = try verifiedSignedObject(
        encoded: token["signed_claims"], signature: token["signature"], key: key
    )
    guard (claims as NSDictionary).isEqual(to: signedClaims),
          claims["schema_version"] as? String == "1.0",
          claims["action"] as? String == "delete_assets",
          claims["manifest_sha256"] as? String == manifestDigest,
          claims["evidence_claims_sha256"] as? String == claimsDigest,
          claims["item_count"] as? Int == items.count,
          claims["cli_major"] as? Int == 1,
          let nonce = claims["nonce"] as? String,
          nonce.count == 64,
          nonce.allSatisfy({ $0.isHexDigit && !$0.isUppercase }),
          let issuedValue = claims["issued_at"] as? String,
          let expiresValue = claims["expires_at"] as? String else {
        throw HelperError.invalidRequest("Delete authorization claims are invalid.")
    }
    let formatter = ISO8601DateFormatter()
    formatter.formatOptions = [.withInternetDateTime]
    guard let issuedAt = formatter.date(from: issuedValue),
          let expiresAt = formatter.date(from: expiresValue),
          expiresAt > issuedAt,
          expiresAt.timeIntervalSince(issuedAt) <= 15 * 60,
          issuedAt <= Date().addingTimeInterval(5 * 60),
          deleteAuthorizationIsValid(expiresAt: expiresAt),
          payload["authorization_expires_at"] as? String == expiresValue else {
        throw HelperError.authorizationExpired("Delete authorization is expired or invalid.")
    }
    try consumeNativeNonce(nonce, manifestDigest: manifestDigest)
    return expiresAt
}

func verifyDeletePixelSources(
    _ items: [[String: Any]], indexed: [String: PHAsset], network: Bool
) throws {
    var expected: [String: String] = [:]
    for item in items {
        guard let candidate = item["local_identifier"] as? String,
              let proof = item["pixel_similarity_proof"] as? [String: Any],
              let keeper = proof["keeper_local_identifier"] as? String,
              let candidateDigest = proof["candidate_source_sha256"] as? String,
              let keeperDigest = proof["keeper_source_sha256"] as? String else {
            throw HelperError.invalidRequest("Delete pixel source proof is malformed.")
        }
        for (identifier, digest) in [(candidate, candidateDigest), (keeper, keeperDigest)] {
            if let existing = expected[identifier], existing != digest {
                throw HelperError.invalidRequest("Delete pixel source proof is inconsistent.")
            }
            expected[identifier] = digest
        }
    }
    let root = FileManager.default.temporaryDirectory
        .appendingPathComponent("apple-photos-delete-\(UUID().uuidString)", isDirectory: true)
    try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
    defer { try? FileManager.default.removeItem(at: root) }
    for (identifier, digest) in expected {
        guard let asset = indexed[identifier] else { throw HelperError.notFound(identifier) }
        let resources = PHAssetResource.assetResources(for: asset)
        guard resources.count == 1, resourceRole(resources[0].type) == "photo" else {
            throw HelperError.resource(
                "Pixel deletion requires exactly one available photo resource per asset."
            )
        }
        let url = root.appendingPathComponent(UUID().uuidString)
        if let error = writeResource(resources[0], to: url, network: network) {
            throw HelperError.resource(error.localizedDescription)
        }
        guard "sha256:\(try sha256File(url))" == digest else {
            throw HelperError.stale("A pixel source resource changed before delete mutation.")
        }
        try? FileManager.default.removeItem(at: url)
    }
}

func deleteAssets(_ payload: [String: Any]) throws -> [String: Any] {
    guard let items = payload["items"] as? [[String: Any]],
          !items.isEmpty, items.count <= 50 else {
        throw HelperError.invalidRequest("Delete requires between 1 and 50 items.")
    }
    guard let manifestDigest = payload["manifest_sha256"] as? String,
          manifestDigest.hasPrefix("sha256:") else {
        throw HelperError.invalidRequest("Delete requires a bound authorization envelope.")
    }
    let expiresAt = try verifyDeleteAuthorizationEnvelope(
        payload, items: items, manifestDigest: manifestDigest
    )
    guard let network = payload["network_access_allowed"] as? Bool else {
        throw HelperError.invalidRequest("Delete resource network policy is required.")
    }
    try requestAuthorization()
    let identifiers = items.compactMap { $0["local_identifier"] as? String }
    let keeperIdentifiers = items.compactMap {
        ($0["pixel_similarity_proof"] as? [String: Any])?["keeper_local_identifier"] as? String
    }
    let assets = fetchAssets(Array(Set(identifiers + keeperIdentifiers)))
    let indexed = Dictionary(uniqueKeysWithValues: assets.map { ($0.localIdentifier, $0) })
    let actual = indexed.mapValues(assetDictionary)
    do {
        return try executeValidatedDelete(items, actualByIdentifier: actual) { validatedIdentifiers in
            try verifyDeletePixelSources(items, indexed: indexed, network: network)
            guard deleteAuthorizationIsValid(expiresAt: expiresAt) else {
                throw HelperError.authorizationExpired(
                    "Delete authorization expired during native preflight."
                )
            }
            var boundaryError: Error?
            var registeredIdentifiers: [String] = []
            try PHPhotoLibrary.shared().performChangesAndWait {
                do {
                    let refreshedAssets = fetchAssets(Array(Set(identifiers + keeperIdentifiers)))
                    let refreshed = Dictionary(
                        uniqueKeysWithValues: refreshedAssets.map { ($0.localIdentifier, $0) }
                    )
                    let refreshedActual = refreshed.mapValues(assetDictionary)
                    try executeValidatedDelete(
                        items, actualByIdentifier: refreshedActual
                    ) { boundaryIdentifiers in
                        guard deleteAuthorizationIsValid(expiresAt: expiresAt) else {
                            throw HelperError.authorizationExpired(
                                "Delete authorization expired at transaction registration."
                            )
                        }
                        let boundaryAssets = boundaryIdentifiers.compactMap { refreshed[$0] }
                        PHAssetChangeRequest.deleteAssets(boundaryAssets as NSArray)
                        registeredIdentifiers = boundaryIdentifiers
                    }
                } catch {
                    boundaryError = error
                }
            }
            if let boundaryError { throw boundaryError }
            guard registeredIdentifiers == validatedIdentifiers else {
                throw HelperError.stale("Delete registration did not match validated identifiers.")
            }
            return ["local_identifiers": validatedIdentifiers]
        }
    } catch DeleteValidationError.malformed {
        throw HelperError.invalidRequest("Every delete item requires an identifier and expected state.")
    } catch DeleteValidationError.duplicateIdentifier {
        throw HelperError.invalidRequest("Delete identifiers must be unique.")
    } catch DeleteValidationError.missingAsset {
        throw HelperError.notFound("One or more assets were not found before delete mutation.")
    } catch DeleteValidationError.stale {
        throw HelperError.stale("A delete precondition changed before the native transaction.")
    } catch let error as HelperError {
        throw error
    } catch {
        throw HelperError.transaction(error.localizedDescription)
    }
}

func verifyAssets(_ payload: [String: Any]) throws -> [String: Any] {
    try requestAuthorization()
    let identifiers = try payloadArray(payload, "local_identifiers")
    let albumIdentifier = payload["album_id"] as? String
    var fetched = Dictionary(uniqueKeysWithValues: fetchAssets(identifiers).map { ($0.localIdentifier, $0) })
    var albumMembers = Set<String>()
    if let albumIdentifier {
        let album = try fetchAlbum(albumIdentifier)
        let result = PHAsset.fetchAssets(in: album, options: nil)
        result.enumerateObjects { asset, _, _ in albumMembers.insert(asset.localIdentifier) }
    }
    let results: [[String: Any]] = identifiers.map { identifier in
        let present = fetched.removeValue(forKey: identifier) != nil
        return [
            "local_identifier": identifier,
            "present": present,
            "in_album": albumIdentifier == nil ? NSNull() : albumMembers.contains(identifier)
        ]
    }
    return ["assets": results]
}

func dispatch(_ operation: String, payload: [String: Any]) throws -> Any {
    switch operation {
    case "probe-library": return try probeLibrary()
    case "list-albums": return try listAlbums()
    case "fetch-assets": return try fetchAssetDictionaries(payload)
    case "read-resources": return try readResources(payload)
    case "import-assets": return try importAssets(payload)
    case "add-assets-to-album": return try addAssetsToAlbum(payload)
    case "delete-assets": return try deleteAssets(payload)
    case "verify-assets": return try verifyAssets(payload)
    default: throw HelperError.invalidRequest("Unknown operation: \(operation)")
    }
}

do {
    guard let line = readLine(), let data = line.data(using: .utf8),
          let request = try JSONSerialization.jsonObject(with: data) as? [String: Any],
          request["protocol_version"] as? String == protocolVersion,
          let operation = request["operation"] as? String,
          let payload = request["payload"] as? [String: Any] else {
        throw HelperError.invalidRequest("Expected one versioned JSON request on stdin.")
    }
    writeResponse(ok: true, result: try dispatch(operation, payload: payload))
} catch let error as HelperError {
    writeResponse(ok: false, error: error)
    exit(0)
} catch {
    writeResponse(ok: false, error: .invalidRequest(error.localizedDescription))
    exit(0)
}
