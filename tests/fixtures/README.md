`bread.jpg` is a real Food-11 image copied byte-for-byte from
`data/food11_processed_mini/training/Bread/0_0.jpg` after DVC restoration.

- Format: JPEG, RGB, 128×128.
- Size: 5,087 bytes.
- SHA-256: `43a8d524fa9befcb74a761d82c59fb38e5052ac3915a6d650da81a1aa83d46d7`.

The API test uses this checked-in fixture with a fake model. A separate API test
uses an explicitly generated image. Neither test needs MLflow or DVC downloads.
