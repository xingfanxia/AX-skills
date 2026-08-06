import CryptoKit
import Foundation

public struct ValidatedImportFields: Equatable {
    public let itemID: String
    public let stagedPath: String
    public let role: String
    public let uti: String
}

public enum ImportFieldError: Error, Equatable {
    case malformed
    case unsupportedType
}

public enum ImportTransactionPlanError: Error, Equatable {
    case albumChangeUnavailable
}

public enum DeleteValidationError: Error, Equatable {
    case malformed
    case duplicateIdentifier
    case missingAsset
    case stale
}

public func deleteAuthorizationIsValid(expiresAt: Date, now: Date = Date()) -> Bool {
    expiresAt > now
}

public func deletePreconditionMatches(
    actual: [String: Any], expected: [String: Any]
) -> Bool {
    guard nullableStringMatches(expected["original_filename"], actual["original_filename"]),
          (expected["media_type"] as? String) == (actual["media_type"] as? String),
          nullableStringMatches(expected["date_taken"], actual["date_taken"]),
          nullableStringMatches(expected["date_modified"], actual["date_modified"]),
          (expected["width"] as? Int) == (actual["width"] as? Int),
          (expected["height"] as? Int) == (actual["height"] as? Int),
          let expectedDigest = expected["resource_descriptor_digest"] as? String,
          let descriptors = actual["resource_descriptors"] as? [[String: Any]],
          let data = try? JSONSerialization.data(
            withJSONObject: descriptors, options: [.sortedKeys, .withoutEscapingSlashes]
          ) else { return false }
    let digest = SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
    return expectedDigest == "sha256:\(digest)"
}

private func nullableStringMatches(_ expected: Any?, _ actual: Any?) -> Bool {
    if expected is NSNull { return actual is NSNull }
    guard let expectedString = expected as? String else { return false }
    return expectedString == (actual as? String)
}

public func executeValidatedDelete<Result>(
    _ items: [[String: Any]],
    actualByIdentifier: [String: [String: Any]],
    mutation: ([String]) throws -> Result
) throws -> Result {
    let identifiers = try items.map { item -> String in
        guard let identifier = item["local_identifier"] as? String,
              !identifier.isEmpty,
              item["expected"] is [String: Any],
              item["planned_action"] as? String == "move_to_recently_deleted" else {
            throw DeleteValidationError.malformed
        }
        return identifier
    }
    guard Set(identifiers).count == identifiers.count else {
        throw DeleteValidationError.duplicateIdentifier
    }
    let keeperIdentifiers = try items.map { item -> String in
        guard let proof = item["pixel_similarity_proof"] as? [String: Any],
              let keeperIdentifier = proof["keeper_local_identifier"] as? String,
              !keeperIdentifier.isEmpty,
              proof["keeper_expected"] is [String: Any] else {
            throw DeleteValidationError.malformed
        }
        return keeperIdentifier
    }
    guard Set(identifiers).isDisjoint(with: Set(keeperIdentifiers)) else {
        throw DeleteValidationError.duplicateIdentifier
    }
    for item in items {
        let identifier = item["local_identifier"] as! String
        let expected = item["expected"] as! [String: Any]
        let proof = item["pixel_similarity_proof"] as! [String: Any]
        let keeperIdentifier = proof["keeper_local_identifier"] as! String
        let keeperExpected = proof["keeper_expected"] as! [String: Any]
        guard pixelProofIsWellFormed(proof),
              deleteExpectedIsWellFormed(expected),
              deleteExpectedIsWellFormed(keeperExpected) else {
            throw DeleteValidationError.malformed
        }
        guard let actual = actualByIdentifier[identifier] else {
            throw DeleteValidationError.missingAsset
        }
        guard let keeperActual = actualByIdentifier[keeperIdentifier] else {
            throw DeleteValidationError.missingAsset
        }
        guard deletePreconditionMatches(actual: actual, expected: expected) else {
            throw DeleteValidationError.stale
        }
        guard deletePreconditionMatches(actual: keeperActual, expected: keeperExpected) else {
            throw DeleteValidationError.stale
        }
        guard let dimensions = proof["dimensions"] as? [String: Any],
              let width = dimensions["width"] as? Int,
              let height = dimensions["height"] as? Int,
              actual["width"] as? Int == width,
              actual["height"] as? Int == height,
              keeperActual["width"] as? Int == width,
              keeperActual["height"] as? Int == height else {
            throw DeleteValidationError.stale
        }
    }
    return try mutation(identifiers)
}

private func pixelProofIsWellFormed(_ proof: [String: Any]) -> Bool {
    guard let pairID = proof["pair_id"] as? String, !pairID.isEmpty,
          proof["bytes_different"] as? Bool == true,
          let candidateSHA = proof["candidate_source_sha256"] as? String,
          let keeperSHA = proof["keeper_source_sha256"] as? String,
          isSHA256Digest(candidateSHA), isSHA256Digest(keeperSHA),
          candidateSHA != keeperSHA,
          let dimensions = proof["dimensions"] as? [String: Any],
          let width = dimensions["width"] as? Int, width > 0,
          let height = dimensions["height"] as? Int, height > 0,
          let metrics = proof["metrics"] as? [String: Any],
          let rgbMAE = metrics["rgb_mean_absolute_error"] as? Double,
          let lumaMAE = metrics["luma_mean_absolute_error"] as? Double,
          let rgbP99 = metrics["rgb_p99_absolute_error"] as? Double else {
        return false
    }
    return rgbMAE >= 0 && rgbMAE <= 0.01
        && lumaMAE >= 0 && lumaMAE <= 0.01
        && rgbP99 >= 0 && rgbP99 <= 0.05
}

private func isSHA256Digest(_ value: String) -> Bool {
    let hex = value.hasPrefix("sha256:") ? String(value.dropFirst(7)) : ""
    return hex.count == 64 && hex.allSatisfy { $0.isHexDigit && !$0.isUppercase }
}

private func deleteExpectedIsWellFormed(_ expected: [String: Any]) -> Bool {
    expected["media_type"] as? String == "image"
        && expected["resource_descriptor_digest"] is String
        && expected["in_trash"] as? Bool == false
        && (expected["original_filename"] is String || expected["original_filename"] is NSNull)
        && (expected["date_taken"] is String || expected["date_taken"] is NSNull)
        && (expected["date_modified"] is String || expected["date_modified"] is NSNull)
        && (expected["width"] as? Int ?? 0) > 0
        && (expected["height"] as? Int ?? 0) > 0
}

public enum ImportMutationEvidenceStatus: String, Equatable {
    case createdIdentifierKnown = "created_identifier_known"
    case outcomeUnknown = "outcome_unknown"
    case notAttempted = "not_attempted"
    case notAttemptedAfterUnknown = "not_attempted_after_unknown"
}

public struct ImportMutationEvidence: Equatable {
    public let itemID: String
    public let localIdentifier: String?
    public let status: ImportMutationEvidenceStatus
    public let evidence: String
}

private let canonicalTypes: [String: (role: String, uti: String)] = [
    "jpg": ("photo", "public.jpeg"),
    "jpeg": ("photo", "public.jpeg"),
    "png": ("photo", "public.png"),
    "heic": ("photo", "public.heic"),
    "heif": ("photo", "public.heif"),
    "tif": ("photo", "public.tiff"),
    "tiff": ("photo", "public.tiff"),
    "gif": ("photo", "com.compuserve.gif"),
    "mov": ("video", "com.apple.quicktime-movie"),
    "mp4": ("video", "public.mpeg-4"),
    "m4v": ("video", "com.apple.m4v-video")
]

public func validateImportFields(_ item: [String: Any]) throws -> ValidatedImportFields {
    guard let itemID = item["item_id"] as? String, !itemID.isEmpty,
          let stagedPath = item["staged_path"] as? String, !stagedPath.isEmpty,
          let role = item["role"] as? String,
          let uti = item["uti"] as? String else {
        throw ImportFieldError.malformed
    }
    let ext = URL(fileURLWithPath: stagedPath).pathExtension.lowercased()
    guard let expected = canonicalTypes[ext], expected.role == role, expected.uti == uti else {
        throw ImportFieldError.unsupportedType
    }
    return ValidatedImportFields(itemID: itemID, stagedPath: stagedPath, role: role, uti: uti)
}

public func validateImportBatch(_ items: [[String: Any]]) throws -> [ValidatedImportFields] {
    guard !items.isEmpty else { throw ImportFieldError.malformed }
    return try items.map(validateImportFields)
}

public func executeValidatedImport<Result>(
    _ items: [[String: Any]],
    mutation: ([ValidatedImportFields]) throws -> Result
) throws -> Result {
    let validated = try validateImportBatch(items)
    return try mutation(validated)
}

public func dispatchImportPayload<Result>(
    _ payload: [String: Any],
    mutation: ([ValidatedImportFields], String) throws -> Result
) throws -> Result {
    guard let items = payload["items"] as? [[String: Any]],
          let albumIdentifier = payload["album_id"] as? String,
          !albumIdentifier.isEmpty else {
        throw ImportFieldError.malformed
    }
    return try executeValidatedImport(items) { validated in
        try mutation(validated, albumIdentifier)
    }
}

public func executeOrderedAlbumMutation<AlbumChange>(
    acquireAlbumChange: () -> AlbumChange?,
    registerCreations: (AlbumChange) -> Void
) throws {
    guard let albumChange = acquireAlbumChange() else {
        throw ImportTransactionPlanError.albumChangeUnavailable
    }
    registerCreations(albumChange)
}

public func executePerItemImport(
    _ items: [ValidatedImportFields],
    transaction: (ValidatedImportFields) throws -> String?
) -> [ImportMutationEvidence] {
    var results: [ImportMutationEvidence] = []
    var stoppedAfterUnknown = false
    var stoppedKnown = false
    for item in items {
        if stoppedAfterUnknown {
            results.append(ImportMutationEvidence(
                itemID: item.itemID,
                localIdentifier: nil,
                status: .notAttemptedAfterUnknown,
                evidence: "not_attempted_after_unknown"
            ))
            continue
        }
        if stoppedKnown {
            results.append(ImportMutationEvidence(
                itemID: item.itemID,
                localIdentifier: nil,
                status: .notAttempted,
                evidence: "not_attempted"
            ))
            continue
        }
        do {
            if let identifier = try transaction(item) {
                results.append(ImportMutationEvidence(
                    itemID: item.itemID,
                    localIdentifier: identifier,
                    status: .createdIdentifierKnown,
                    evidence: "photokit_placeholder"
                ))
                continue
            }
            results.append(ImportMutationEvidence(
                itemID: item.itemID,
                localIdentifier: nil,
                status: .outcomeUnknown,
                evidence: "placeholder_missing_after_creation_registered"
            ))
            stoppedAfterUnknown = true
        } catch is ImportTransactionPlanError {
            results.append(ImportMutationEvidence(
                itemID: item.itemID,
                localIdentifier: nil,
                status: .notAttempted,
                evidence: "transaction_not_started"
            ))
            stoppedKnown = true
        } catch {
            results.append(ImportMutationEvidence(
                itemID: item.itemID,
                localIdentifier: nil,
                status: .outcomeUnknown,
                evidence: "transaction_outcome_unknown"
            ))
            stoppedAfterUnknown = true
        }
    }
    return results
}
