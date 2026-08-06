import CryptoKit
import Foundation
import XCTest
@testable import PhotoKitCore

final class ValidationTests: XCTestCase {
    private let descriptors: [[String: Any]] = [[
        "role": "photo", "uti": "public.jpeg", "original_filename": "photo.jpg"
    ]]

    private func deleteItem(digest: String) -> [String: Any] {
        let expected: [String: Any] = [
            "original_filename": "photo.jpg",
            "media_type": "image",
            "date_taken": NSNull(),
            "date_modified": NSNull(),
            "width": 8,
            "height": 8,
            "resource_descriptor_digest": digest,
            "in_trash": false
        ]
        return [
            "local_identifier": "asset-id",
            "expected": expected,
            "planned_action": "move_to_recently_deleted",
            "pixel_similarity_proof": [
                "pair_id": "pair-id",
                "keeper_local_identifier": "keeper-id",
                "keeper_expected": expected,
                "candidate_source_sha256": "sha256:" + String(repeating: "a", count: 64),
                "keeper_source_sha256": "sha256:" + String(repeating: "b", count: 64),
                "bytes_different": true,
                "dimensions": ["width": 8, "height": 8],
                "metrics": [
                    "rgb_mean_absolute_error": 0.005,
                    "luma_mean_absolute_error": 0.005,
                    "rgb_p99_absolute_error": 0.04,
                    "rgb_max_absolute_error": 0.1
                ]
            ]
        ]
    }

    private func actualDeleteAsset() -> [String: Any] {
        [
            "local_identifier": "asset-id",
            "original_filename": "photo.jpg",
            "media_type": "image",
            "date_taken": NSNull(),
            "date_modified": NSNull(),
            "width": 8,
            "height": 8,
            "in_trash": false,
            "resource_descriptors": descriptors
        ]
    }

    func testDeleteBoundaryRejectsDriftBeforeMutation() throws {
        let data = try JSONSerialization.data(
            withJSONObject: descriptors, options: [.sortedKeys, .withoutEscapingSlashes]
        )
        let digest = SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
        var mutationCalls = 0
        XCTAssertThrowsError(try executeValidatedDelete(
            [deleteItem(digest: "sha256:\(digest)")],
            actualByIdentifier: [
                "asset-id": actualDeleteAsset().merging(
                    ["original_filename": "changed.jpg"], uniquingKeysWith: { _, new in new }
                ),
                "keeper-id": actualDeleteAsset()
            ]
        ) { _ in mutationCalls += 1 })
        XCTAssertEqual(mutationCalls, 0)
    }

    func testDeleteBoundaryAcceptsExactExpectedState() throws {
        let data = try JSONSerialization.data(
            withJSONObject: descriptors, options: [.sortedKeys, .withoutEscapingSlashes]
        )
        let digest = SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
        var mutationCalls = 0
        try executeValidatedDelete(
            [deleteItem(digest: "sha256:\(digest)")],
            actualByIdentifier: [
                "asset-id": actualDeleteAsset(), "keeper-id": actualDeleteAsset()
            ]
        ) { identifiers in
            mutationCalls += 1
            XCTAssertEqual(identifiers, ["asset-id"])
        }
        XCTAssertEqual(mutationCalls, 1)
    }

    func testDeleteBoundaryRejectsMalformedNullableExpectedField() throws {
        var item = deleteItem(digest: "sha256:" + String(repeating: "0", count: 64))
        var expected = item["expected"] as! [String: Any]
        expected["date_taken"] = 7
        item["expected"] = expected
        var mutationCalls = 0

        XCTAssertThrowsError(try executeValidatedDelete(
            [item], actualByIdentifier: [
                "asset-id": actualDeleteAsset(), "keeper-id": actualDeleteAsset()
            ]
        ) { _ in mutationCalls += 1 }) { error in
            XCTAssertEqual(error as? DeleteValidationError, .malformed)
        }
        XCTAssertEqual(mutationCalls, 0)
    }

    func testDeleteBoundaryRejectsNonImageExpectedState() throws {
        let data = try JSONSerialization.data(
            withJSONObject: descriptors, options: [.sortedKeys, .withoutEscapingSlashes]
        )
        let digest = SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
        var item = deleteItem(digest: "sha256:\(digest)")
        var expected = item["expected"] as! [String: Any]
        expected["media_type"] = "video"
        item["expected"] = expected
        var mutationCalls = 0

        XCTAssertThrowsError(try executeValidatedDelete(
            [item], actualByIdentifier: [
                "asset-id": actualDeleteAsset(), "keeper-id": actualDeleteAsset()
            ]
        ) { _ in mutationCalls += 1 }) { error in
            XCTAssertEqual(error as? DeleteValidationError, .malformed)
        }
        XCTAssertEqual(mutationCalls, 0)
    }

    func testDeleteBoundaryRejectsKeeperDriftBeforeMutation() throws {
        let data = try JSONSerialization.data(
            withJSONObject: descriptors, options: [.sortedKeys, .withoutEscapingSlashes]
        )
        let digest = SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
        var mutationCalls = 0

        XCTAssertThrowsError(try executeValidatedDelete(
            [deleteItem(digest: "sha256:\(digest)")],
            actualByIdentifier: [
                "asset-id": actualDeleteAsset(),
                "keeper-id": actualDeleteAsset().merging(
                    ["original_filename": "changed.jpg"], uniquingKeysWith: { _, new in new }
                )
            ]
        ) { _ in mutationCalls += 1 }) { error in
            XCTAssertEqual(error as? DeleteValidationError, .stale)
        }
        XCTAssertEqual(mutationCalls, 0)
    }

    func testDeleteAuthorizationMustRemainValidAtNativeBoundary() {
        let now = Date(timeIntervalSince1970: 100)
        XCTAssertTrue(deleteAuthorizationIsValid(
            expiresAt: Date(timeIntervalSince1970: 101), now: now
        ))
        XCTAssertFalse(deleteAuthorizationIsValid(expiresAt: now, now: now))
    }

    func testAcceptsCanonicalJPEG() throws {
        let value = try validateImportFields([
            "item_id": "src_1", "staged_path": "/tmp/photo.jpg",
            "role": "photo", "uti": "public.jpeg"
        ])
        XCTAssertEqual(value.uti, "public.jpeg")
    }

    func testRejectsMIMETypeInUTIField() {
        XCTAssertThrowsError(try validateImportFields([
            "item_id": "src_1", "staged_path": "/tmp/photo.jpg",
            "role": "photo", "uti": "image/jpeg"
        ]))
    }

    func testRejectsMissingField() {
        XCTAssertThrowsError(try validateImportFields(["item_id": "src_1"]))
    }

    func testRejectsMixedValidAndInvalidBatchBeforeMutation() {
        XCTAssertThrowsError(try validateImportBatch([
            [
                "item_id": "src_1", "staged_path": "/tmp/photo.jpg",
                "role": "photo", "uti": "public.jpeg"
            ],
            ["item_id": "src_2"]
        ]))
    }

    func testRejectsWrongRoleAndFieldType() {
        XCTAssertThrowsError(try validateImportFields([
            "item_id": "src_1", "staged_path": "/tmp/photo.jpg",
            "role": "video", "uti": "public.jpeg"
        ]))
        XCTAssertThrowsError(try validateImportFields([
            "item_id": 1, "staged_path": "/tmp/photo.jpg",
            "role": "photo", "uti": "public.jpeg"
        ]))
    }

    func testRejectsEmptyBatch() {
        XCTAssertThrowsError(try validateImportBatch([]))
    }

    func testMixedInvalidBatchNeverEntersProductionMutationSeam() {
        var mutationCalls = 0
        let payload: [String: Any] = [
            "album_id": "album-id",
            "items": [
                [
                    "item_id": "src_1", "staged_path": "/tmp/photo.jpg",
                    "role": "photo", "uti": "public.jpeg"
                ],
                ["item_id": "src_2"]
            ]
        ]
        XCTAssertThrowsError(try dispatchImportPayload(payload) { _, _ in
            mutationCalls += 1
        })
        XCTAssertEqual(mutationCalls, 0)
    }

    func testAlbumChangeIsAcquiredBeforeCreationRegistration() throws {
        var events: [String] = []
        try executeOrderedAlbumMutation(
            acquireAlbumChange: {
                events.append("album-change")
                return "change"
            },
            registerCreations: { _ in events.append("creations") }
        )
        XCTAssertEqual(events, ["album-change", "creations"])
    }

    func testMissingAlbumChangeNeverRegistersCreations() {
        var creationCalls = 0
        XCTAssertThrowsError(try executeOrderedAlbumMutation(
            acquireAlbumChange: { nil as String? },
            registerCreations: { _ in creationCalls += 1 }
        ))
        XCTAssertEqual(creationCalls, 0)
    }

    func testMissingPlaceholderStopsLaterTransactionsAndPreservesPriorEvidence() throws {
        let validated = try validateImportBatch([
            [
                "item_id": "src_1", "staged_path": "/tmp/one.jpg",
                "role": "photo", "uti": "public.jpeg"
            ],
            [
                "item_id": "src_2", "staged_path": "/tmp/two.jpg",
                "role": "photo", "uti": "public.jpeg"
            ],
            [
                "item_id": "src_3", "staged_path": "/tmp/three.jpg",
                "role": "photo", "uti": "public.jpeg"
            ]
        ])
        var transactionItemIDs: [String] = []
        let evidence = executePerItemImport(validated) { item in
            transactionItemIDs.append(item.itemID)
            return item.itemID == "src_2" ? nil : "local-\(item.itemID)"
        }

        XCTAssertEqual(evidence.map(\.status), [
            .createdIdentifierKnown, .outcomeUnknown, .notAttemptedAfterUnknown
        ])
        XCTAssertEqual(evidence.map(\.localIdentifier), [
            "local-src_1", nil, nil
        ])
        XCTAssertEqual(transactionItemIDs, ["src_1", "src_2"])
        XCTAssertEqual(
            evidence[1].evidence,
            "placeholder_missing_after_creation_registered"
        )
        XCTAssertEqual(evidence[2].evidence, "not_attempted_after_unknown")
    }

    func testPerItemTransactionErrorStopsLaterTransactions() throws {
        struct SyntheticError: Error {}
        let validated = try validateImportBatch([
            [
                "item_id": "src_1", "staged_path": "/tmp/one.jpg",
                "role": "photo", "uti": "public.jpeg"
            ],
            [
                "item_id": "src_2", "staged_path": "/tmp/two.jpg",
                "role": "photo", "uti": "public.jpeg"
            ]
        ])
        var transactionItemIDs: [String] = []
        let evidence = executePerItemImport(validated) { item in
            transactionItemIDs.append(item.itemID)
            if item.itemID == "src_1" { throw SyntheticError() }
            return "local-src_2"
        }

        XCTAssertEqual(evidence[0].status, .outcomeUnknown)
        XCTAssertEqual(evidence[0].evidence, "transaction_outcome_unknown")
        XCTAssertEqual(evidence[1].status, .notAttemptedAfterUnknown)
        XCTAssertNil(evidence[1].localIdentifier)
        XCTAssertEqual(transactionItemIDs, ["src_1"])
    }

    func testKnownImportPlanErrorPreservesPriorEvidence() throws {
        let validated = try validateImportBatch([
            [
                "item_id": "src_1", "staged_path": "/tmp/one.jpg",
                "role": "photo", "uti": "public.jpeg"
            ],
            [
                "item_id": "src_2", "staged_path": "/tmp/two.jpg",
                "role": "photo", "uti": "public.jpeg"
            ],
            [
                "item_id": "src_3", "staged_path": "/tmp/three.jpg",
                "role": "photo", "uti": "public.jpeg"
            ]
        ])

        let evidence = executePerItemImport(validated) { item in
            if item.itemID == "src_2" {
                throw ImportTransactionPlanError.albumChangeUnavailable
            }
            return "local-\(item.itemID)"
        }
        XCTAssertEqual(evidence.map(\.status), [
            .createdIdentifierKnown, .notAttempted, .notAttempted
        ])
        XCTAssertEqual(evidence.map(\.localIdentifier), ["local-src_1", nil, nil])
        XCTAssertEqual(evidence[1].evidence, "transaction_not_started")
        XCTAssertEqual(evidence[2].evidence, "not_attempted")
    }
}
