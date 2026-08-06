// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "PhotoKitHelper",
    platforms: [.macOS(.v13)],
    products: [
        .executable(name: "PhotoKitHelper", targets: ["PhotoKitHelper"])
    ],
    targets: [
        .target(name: "PhotoKitCore"),
        .executableTarget(name: "PhotoKitHelper", dependencies: ["PhotoKitCore"]),
        .testTarget(name: "PhotoKitCoreTests", dependencies: ["PhotoKitCore"])
    ]
)
