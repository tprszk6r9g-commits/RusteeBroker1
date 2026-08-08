# Installing On-Chain Metadata — Rustee Broker #1

**Contract:** `0x4523467C4DDC6D775C7EaD4Dce7656DCe54e7F60`
**Chain:** Robinhood Chain mainnet (4663)
**Token:** #1 (`TOKEN_ID` is a constant in the deployed contract)
**Method:** `setTokenURI(string)` — selector `0xe0df5b6f`, `onlyOwner`
**Tool:** `Rustee_Metadata_Installer_v1.html`

The goal: replace the current metadata pointer with a self-contained `data:` URI that carries the artwork and the deployment binding, so the token renders on OpenSea with no server in the loop.

---

## 0. The one thing that can end this before it starts

The deployed `BrokerNFT` has a `metadataFrozen` flag. If it is `true`, `setTokenURI` reverts with `MetadataIsFrozen()` forever. There is no owner override, no upgrade path, no workaround.

**Check it first.** Section 2 of the installer reads it. If it comes back `TRUE — PERMANENTLY LOCKED`, stop reading; the only remaining path is deploying a new NFT contract, which would change the contract address and therefore every ERC-6551 account address derived from it. That is not worth doing for a picture.

If it reads `false — writable`, continue.

---

## 1. What you need before you start

| Requirement | Why | How to check |
|---|---|---|
| Owner wallet `0x8fC320c8…75B955` | `setTokenURI` is `onlyOwner` | Installer §2, `owner() matches wallet` |
| Wallet browser (MetaMask in-app, Rabby, etc.) | The installer needs an injected provider | Opening the file in Safari/Chrome without a wallet extension will fail at Connect |
| Chain 4663 selected | Calls are chain-specific | Installer §1, or the Switch button |
| ETH for ~11.6M gas | This is a large write | See §2 below |
| Block gas limit above ~12M | The transaction must fit in one block | See §2 below |

### Transaction size

| Item | Value |
|---|---|
| tokenURI string | 18,072 characters |
| Calldata | 18,148 bytes |
| Fresh storage slots | 566 |
| Storage cost | 566 × 20,000 = 11,320,000 gas |
| Calldata cost | ~290,368 gas |
| Base | 21,000 gas |
| **Estimated total** | **~11,631,000 gas** |

This is a genuinely large transaction — roughly 550× a plain ETH transfer. That is the inherent cost of on-chain art; nothing is wrong.

---

## 2. Pre-flight checks the installer does *not* do

Two things to verify manually before you commit.

### Gas price and total cost

Query the chain:

```
eth_gasPrice
```

Then: `cost in ETH = 11,631,000 × gasPrice / 1e18`.

At 0.001 gwei that is ~0.0000116 ETH. At 1 gwei it is ~0.0116 ETH. At 10 gwei it is ~0.116 ETH. Robinhood Chain is an L2 and should sit at the cheap end, but **confirm before signing** — this is the one number that could surprise you, and it scales linearly with a gas price you have not checked.

### Block gas limit

```
eth_getBlockByNumber("latest", false)  →  read .gasLimit
```

Convert from hex. If it is below ~12,000,000, this transaction cannot be included in any block, and you need the smaller build.

You will usually find this out anyway: `eth_estimateGas` fails with *"gas required exceeds allowance"* when a transaction exceeds the block limit, so a failed simulate at step 3 with that message means "too big," not "broken."

**If it is too big:** rebuild with the 192×192 image (`rustee-broker-192.webp`, 9,652 bytes). Regenerate with:

```
python3 build_tokenuri.py IMG_5468.jpeg --size 192 --quality 60
```

That produces roughly 13,700 characters and ~8.8M gas. Then paste the new string into the installer's `<script id="TOKEN_URI" type="text/plain">` block, replacing what is there.

---

## 3. Step-by-step

### §1 Connect

1. Open `Rustee_Metadata_Installer_v1.html` in your wallet's built-in browser.
2. Tap **Connect owner wallet**. Approve the connection prompt.
3. Confirm the wallet readout is green. Red means you are connected as a different account — switch accounts in the wallet, then reconnect.
4. Confirm **Chain** reads `4663` in green. If not, tap **Switch to Robinhood Chain**.

### §2 Preflight

Tap **Run read-only preflight**. Four gates, all read-only — nothing is signed and nothing is written.

| Row | Expected | If it fails |
|---|---|---|
| Contract has code | PASS | Wrong address or wrong chain |
| `owner()` matches wallet | PASS | You are not connected as the owner |
| `metadataFrozen()` | `false — writable` | See §0. Stop. |
| Current `tokenURI(1)` | some length | Informational — this is what you're replacing |
| New tokenURI length | 18,072 chars | Informational |

The log pane prints the on-chain owner address, the current URI's first 120 characters, and the new URI's first 120 characters. **Read them.** This is your last chance to notice you are about to overwrite something you did not expect.

Simulate stays disabled unless the owner check and the frozen check both pass.

### §3 Simulate

Tap **Simulate setTokenURI**. Two independent checks run:

- `eth_estimateGas` — would this transaction succeed, and what does it cost?
- `eth_call` — execute it against current state without broadcasting

Both must pass before Execute unlocks. The log shows the destination, the selector, calldata size, and gas.

**The simulation expires after 120 seconds.** If you walk away, simulate again — do not try to execute against a stale simulation.

### §4 Execute

1. Tap **Write metadata on-chain**.
2. A browser confirm appears summarizing the write. Read it.
3. Your wallet then asks for a **separate** signature. This is the real authorization boundary.
4. In the wallet prompt, verify: destination is `0x4523467C…54e7F60`, value is **0**, gas is roughly 12–14M (the installer pads the estimate by 20%).
5. Confirm.

The page polls for the receipt for up to 6 minutes and prints the transaction hash, block number, and actual gas used.

> Your wallet may render the calldata as an unreadable hex blob or warn about an "unknown" method. That is normal for an 18KB argument. What matters is the destination address, zero value, and the fact that your own simulation passed.

### §5 Verify

Tap **Re-read tokenURI(1) and compare**.

This reads back what actually landed on-chain and compares it character-for-character against what you sent. You want `MATCH ✓`.

This step exists because "the transaction confirmed" and "the right bytes are stored" are different claims. Do not treat the receipt as proof of the second one.

**Extra confidence:** copy the on-chain string from the log and paste it into a browser address bar. A correct `data:application/json;utf8,{...}` URI renders as JSON; copy the `image` field value into the address bar and the artwork should display.

### §6 OpenSea

1. Open the item page for token #1 on Robinhood Chain.
2. Tap **… → Refresh metadata**.
3. Wait. Indexing commonly takes 2–15 minutes and occasionally longer on newer chains.

The item currently shows *"Content not available yet"* because the existing metadata pointer does not resolve to an image. That message should clear on its own once OpenSea re-fetches.

**Do not re-send the transaction because the image has not appeared.** Verify at step 5 instead — if the on-chain string matches, the write is done and everything remaining is OpenSea's indexer.

---

## 4. Troubleshooting

| Symptom | Cause | Action |
|---|---|---|
| `execution reverted` on simulate | Frozen, or not the owner | Re-run §2; the failing gate tells you which |
| `gas required exceeds allowance` | Exceeds block gas limit | Rebuild at 192px (§2) |
| `intrinsic gas too low` | Wallet overrode the gas field | Reset gas to the simulated value +20% |
| Connect does nothing | No injected provider | Open in the wallet's own browser, not Safari |
| Receipt timeout after 6 min | Chain congestion or dropped tx | Look up the hash on the explorer; do **not** re-send blind |
| Verify shows MISMATCH | Truncated or corrupted write | Do **not** freeze. Re-run §3–§5 |
| OpenSea still blank after an hour | Indexer lag or unsupported data URI form | Confirm §5 passed, then try the base64 variant (see §5 below) |

### If the utf8 form does not render

You have two builds:

- `tokenURI_utf8.txt` — 18,072 chars, ~11.6M gas *(what the installer ships with)*
- `tokenURI_base64.txt` — 24,089 chars, ~15.5M gas *(more universally parsed)*

If OpenSea will not parse the utf8 version after a genuine refresh and a wait, swap the base64 string into the installer's `TOKEN_URI` script block and run §3–§5 again.

**A second write is much cheaper than the first.** Those 566 storage slots are already non-zero, so overwriting costs roughly 5,000 gas per slot instead of 20,000 — call it ~3.5M gas rather than 11.3M. Getting this wrong once is not expensive. That is a good reason not to rush to freeze.

---

## 5. The freeze decision

`freezeMetadata()` permanently disables `setTokenURI`. Section 6 of the installer stays locked until step 5 returns MATCH, and then double-confirms.

**Do not freeze the same day.** Work this checklist first:

- [ ] Step 5 returned MATCH
- [ ] The artwork renders on OpenSea
- [ ] You have looked at it on a phone **and** a desktop
- [ ] You are satisfied with 224×224 at quality 60 — freezing locks that compromise in permanently
- [ ] The attribute values are correct (all four TBA addresses, registry, policy limits)
- [ ] You have checked whether Robinhood Chain gas is cheap enough that a larger image is affordable — if so, redo it *before* freezing
- [ ] Nothing in the description will read as wrong in a year

The value of freezing is real: it converts "the art is on-chain" into "the art is on-chain and provably immutable," which is the strongest version of the claim. But it is one-way, and there is no cost to waiting a week.

---

## 6. Fallback: Blockscout

If the installer will not run in your wallet browser:

1. Open the contract on `robinhoodchain.blockscout.com`.
2. Go to **Contract → Write Contract**. This requires the source to be verified there — if it isn't, verify it first or use the installer.
3. Connect the owner wallet.
4. Find `setTokenURI` and paste the full contents of `tokenURI_utf8.txt` into the `newURI` field.
5. Write, then confirm in the wallet.

This works but is strictly worse: no owner pre-check, no `metadataFrozen` pre-check, no simulation gate, no read-back verification, and pasting 18,072 characters into a mobile form field is its own adventure. Use it only if the installer cannot run.

---

## 7. What is actually being stored

```json
{
  "name": "Rustee Broker #1",
  "description": "NFT-rooted authority for an ERC-6551 broker system on
                  Robinhood Chain...",
  "image": "data:image/webp;base64,<12,838 bytes of WebP>",
  "attributes": [
    { "trait_type": "Chain",          "value": "Robinhood Chain (4663)" },
    { "trait_type": "Vault TBA",      "value": "0x8ad8bd35…23956d" },
    { "trait_type": "Trading TBA",    "value": "0x522f5637…d9a654" },
    { "trait_type": "Rewards TBA",    "value": "0xfd0d881d…1c3b32" },
    { "trait_type": "Identity TBA",   "value": "0x496d7d47…92158d" },
    { "trait_type": "Registry",       "value": "0xa36a28f1…e54199" },
    { "trait_type": "Max Trade",      "value": "$5" },
    { "trait_type": "Max Daily",      "value": "$10" },
    { "trait_type": "Trades Per Day", "value": "1" },
    { "trait_type": "Metadata",       "value": "Fully on-chain" }
  ]
}
```

The attributes are a deliberate choice: the token describes its own deployed architecture, so anyone looking at it on OpenSea can read the binding without trusting a server, a README, or an infographic. That is the same standard the rest of the project holds to — the artifact carries its own evidence.

**One caution.** These trait values are a snapshot of the policy as deployed today (`$5` / `$10` / 1 trade per day, registry at `0xa36a28f1…`). If Registry V2 ever migrates to a new address or the limits change, frozen metadata will still assert the old values with no way to correct them. Either accept that the traits describe the token's original configuration rather than its live state, or drop the mutable ones before freezing.
