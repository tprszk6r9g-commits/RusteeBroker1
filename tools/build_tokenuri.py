#!/usr/bin/env python3
"""
Build a fully on-chain tokenURI for Rustee Broker #1.

Encodes the artwork as WebP, embeds it as a data URI inside the ERC-721
metadata JSON, and emits the complete string to pass to
BrokerNFT.setTokenURI(string calldata).

Usage:
    python3 build_tokenuri.py SOURCE.jpeg [--size 224] [--quality 60] [--base64]

Requires Pillow with WebP support (PIL.features.check('webp') is True).
"""
import argparse, base64, io, json, math, pathlib, sys
from PIL import Image, features

# Deployed binding — chain 4663, Robinhood Chain mainnet.
BINDING = [
    ("Chain",          "Robinhood Chain (4663)"),
    ("Vault TBA",      "0x8ad8bd35d33dd7b4d0de81f809f5b7f92623956d"),
    ("Trading TBA",    "0x522f5637f2c556aad9b2245f3b8e6bf4dfd9a654"),
    ("Rewards TBA",    "0xfd0d881d73ec1476f5da0ab78283149ea21c3b32"),
    ("Identity TBA",   "0x496d7d47ae69d65d714413f0dc78c712ed92158d"),
    ("Registry",       "0xa36a28f160d9cf0bb924c2ed5a1263dd11e54199"),
    ("Max Trade",      "$5"),
    ("Max Daily",      "$10"),
    ("Trades Per Day", "1"),
    ("Metadata",       "Fully on-chain"),
]

NAME = "Rustee Broker #1"
DESCRIPTION = (
    "NFT-rooted authority for an ERC-6551 broker system on Robinhood Chain. "
    "Ownership of this token is the root authority over four token-bound "
    "accounts. Image and metadata are stored fully on-chain."
)


def encode_image(path, size, quality):
    im = Image.open(path).convert("RGB").resize((size, size), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=quality, method=6)  # method=6 = slowest, smallest
    return buf.getvalue()


def build_metadata(image_bytes):
    img_uri = "data:image/webp;base64," + base64.b64encode(image_bytes).decode()
    meta = {
        "name": NAME,
        "description": DESCRIPTION,
        "image": img_uri,
        "attributes": [{"trait_type": k, "value": v} for k, v in BINDING],
    }
    # Compact separators matter: every saved byte is 16 gas of calldata
    # plus a share of a 20,000-gas storage slot.
    return json.dumps(meta, separators=(",", ":"))


def estimate_gas(token_uri):
    """Rough cost of one setTokenURI call writing into previously-zero slots."""
    n = len(token_uri.encode())
    slots = math.ceil(n / 32) + 1        # +1 for the string length slot
    sstore = slots * 20_000              # zero -> nonzero
    calldata = n * 16                    # base64/JSON is all nonzero bytes
    return n, slots, sstore + calldata + 21_000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("--size", type=int, default=224)
    ap.add_argument("--quality", type=int, default=60)
    ap.add_argument("--base64", action="store_true",
                    help="wrap JSON as data:application/json;base64 "
                         "(safer parsing, ~33%% more gas)")
    ap.add_argument("--out", default=".")
    args = ap.parse_args()

    if not features.check("webp"):
        sys.exit("Pillow lacks WebP support; install pillow with libwebp.")

    raw = encode_image(args.source, args.size, args.quality)
    meta_json = build_metadata(raw)

    if args.base64:
        token_uri = ("data:application/json;base64,"
                     + base64.b64encode(meta_json.encode()).decode())
    else:
        token_uri = "data:application/json;utf8," + meta_json

    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"rustee-broker-{args.size}.webp").write_bytes(raw)
    (out / "tokenURI.txt").write_text(token_uri)

    n, slots, gas = estimate_gas(token_uri)
    print(f"image      : {args.size}x{args.size} WebP q{args.quality} — {len(raw):,} bytes")
    print(f"tokenURI   : {n:,} chars")
    print(f"storage    : {slots:,} slots")
    print(f"est. gas   : ~{gas:,}")
    print(f"written to : {out.resolve()}")


if __name__ == "__main__":
    main()
