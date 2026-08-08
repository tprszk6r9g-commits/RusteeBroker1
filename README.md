# Rustee Broker — On-Chain Metadata Installer

A single-page tool that writes fully on-chain metadata to **Rustee Broker #1**
via `setTokenURI(string)`.

- **Contract:** `0x4523467C4DDC6D775C7EaD4Dce7656DCe54e7F60`
- **Chain:** Robinhood Chain mainnet (4663)
- **Method:** `setTokenURI(string)` — selector `0xe0df5b6f`, `onlyOwner`

No private key or seed phrase is ever requested. Every write is gated behind a
read-only preflight, a live `eth_estimateGas` + `eth_call` simulation, and a
separate wallet confirmation.

Full walkthrough: [`docs/METADATA_INSTALL_GUIDE.md`](docs/METADATA_INSTALL_GUIDE.md)

---

## Why you got a 404

GitHub Pages serves the repository root. Visiting your Pages URL loads
`index.html` from that root — **and nothing else**. A file named
`Rustee_Metadata_Installer_v1.html` is only reachable at its literal path:

```
https://<user>.github.io/<repo>/Rustee_Metadata_Installer_v1.html
```

Hitting `https://<user>.github.io/<repo>/` with no `index.html` present
returns 404. That is the whole bug.

This package fixes it by shipping the installer **as `index.html` at the repo
root**, so the bare Pages URL works.

Three other causes worth ruling out if you still 404:

| Cause | Check | Fix |
|---|---|---|
| Pages not enabled, or wrong source | Settings → Pages | Set source to **GitHub Actions** |
| First deploy hasn't finished | Actions tab | Wait for the workflow to go green |
| Filename case mismatch | Pages URLs are case-sensitive | Use exactly `index.html`, lowercase |

`.nojekyll` is included so Jekyll doesn't process the site or drop files.

---

## Deploy

1. Create a new repository (public or private — Pages works with private on
   paid plans).
2. Copy every file in this package to the repo root, preserving structure:

   ```
   index.html
   .nojekyll
   README.md
   .github/workflows/pages.yml
   docs/METADATA_INSTALL_GUIDE.md
   assets/tokenURI_utf8.txt
   assets/tokenURI_base64.txt
   assets/rustee-broker-224.webp
   assets/rustee-broker-192.webp
   tools/build_tokenuri.py
   ```

3. Commit and push to `main`.
4. **Settings → Pages → Source → GitHub Actions.**
5. Watch the Actions tab. The workflow verifies the entry point, the contract
   address, the selectors, and that the embedded tokenURI matches
   `assets/tokenURI_utf8.txt` — then deploys.
6. Open the Pages URL **in your wallet's built-in browser** (MetaMask, Rabby,
   etc.). A normal mobile browser has no injected provider and will fail at
   Connect.

HTTPS matters here: wallet injection generally requires a secure context, so
GitHub Pages works where a locally-opened `file://` copy may not.

---

## What the workflow checks

| Gate | Why |
|---|---|
| `index.html` and `.nojekyll` exist at root | Prevents the 404 this package fixes |
| Contract address present | Catches a truncated or wrong-file commit |
| `setTokenURI` / `metadataFrozen` selectors intact | Catches an edited or corrupted script block |
| Embedded tokenURI matches `assets/tokenURI_utf8.txt` | The 18,072-char blob is easy to mangle on copy/paste |
| No key material | Fails the build on anything resembling a private key |

These are presence and equality checks, not proof of correctness. The real
gate is the installer's own on-chain preflight and simulation.

---

## Swapping the metadata payload

Two prebuilt payloads ship in `assets/`:

| File | Chars | Est. gas | Notes |
|---|---|---|---|
| `tokenURI_utf8.txt` | 18,072 | ~11.6M | **Default** — embedded in `index.html` |
| `tokenURI_base64.txt` | 24,089 | ~15.5M | Fallback if OpenSea won't parse the utf8 form |

To swap, replace the contents of the `<script id="TOKEN_URI" type="text/plain">`
block in `index.html` with the new string, and update
`assets/tokenURI_utf8.txt` to match — otherwise the workflow's equality check
fails the build, which is the point.

To rebuild from source art at a different size:

```bash
python3 tools/build_tokenuri.py IMG_5468.jpeg --size 224 --quality 60
python3 tools/build_tokenuri.py IMG_5468.jpeg --size 192 --quality 60   # ~8.8M gas
python3 tools/build_tokenuri.py IMG_5468.jpeg --base64                  # safer parsing
```

---

## Before you run it

**Check `metadataFrozen()` first.** If it returns `true`, `setTokenURI`
reverts permanently and there is no workaround. The installer's preflight
reads it — that is the go/no-go gate, and everything else is downstream of it.

Also confirm gas price (`eth_gasPrice`) and block gas limit before signing.
~11.6M gas is a large write, and its ETH cost scales linearly with a gas price
you have not looked at yet.

---

## Security notes

- Read-only until every gate passes; the wallet confirmation is the final
  authorization boundary.
- No private key, seed phrase, or API credential appears anywhere in this
  package.
- The installer performs exactly two possible writes: `setTokenURI(string)`
  and, only after byte-for-byte verification and two confirmations,
  `freezeMetadata()`.
- `freezeMetadata()` is irreversible. The guide's §5 checklist exists for a
  reason — don't run it on day one.
