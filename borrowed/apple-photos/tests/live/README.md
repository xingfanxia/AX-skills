# Live Test Gate

Live tests are intentionally not part of the default suite. They require a dedicated macOS account or VM with a disposable System Photo Library, `APPLE_PHOTOS_ENABLE_LIVE_TESTS=1`, and a locally built PhotoKit helper.

Never point future live tests at a person's primary library. Do not automate System Photo Library switching, Photos authorization, or the native delete confirmation dialog.
