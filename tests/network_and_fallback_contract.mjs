import assert from "node:assert/strict";
import { buildComprehension } from "../prototype/comprehension.js";
import {
  correctNetworkServiceReading,
  isCommandLineNetworkService
} from "../prototype/network-corrections.js";
import { polishReading } from "../prototype/polish.js";
import {
  fallbackRepository,
  fetchRawReadme,
  repositoryReference
} from "../prototype/resilience.js";

const repo = {
  name: "cloudflared",
  full_name: "cloudflare/cloudflared",
  html_url: "https://github.com/cloudflare/cloudflared",
  homepage: "",
  description: "A tunneling daemon that proxies traffic from the Cloudflare network to your origins.",
  default_branch: "master",
  archived: false,
  fork: false,
  license: { spdx_id: "Apache-2.0" },
  owner: { login: "cloudflare", html_url: "https://github.com/cloudflare" }
};

const readme = `# cloudflared

cloudflared contains the command-line client for Cloudflare Tunnel, a tunneling daemon that proxies traffic from the Cloudflare network to your origins. This daemon sits between Cloudflare's network and your origin, creating outbound-only connections.

## Installing cloudflared

Download a release from [GitHub releases](https://github.com/cloudflare/cloudflared/releases/latest).

User documentation for Cloudflare Tunnel can be found in the [Cloudflare Tunnel documentation](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/).

Available on [DockerHub](https://hub.docker.com/r/cloudflare/cloudflared).

See [Deprecated versions](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/previous-versions/) only for old systems.

## Requirements

[Cap'n Proto](https://capnproto.org/) is needed for some development tasks.

## Usage

Run cloudflared and configure a tunnel for your origin service.
`;

assert.equal(isCommandLineNetworkService(repo, readme), true);
const base = polishReading(buildComprehension(repo, readme, null, { Go: 900, Shell: 100 }), repo, readme);
const reading = correctNetworkServiceReading(base, repo, readme);

assert.equal(reading.classification.id, "network-service");
assert.equal(reading.classification.label, "Command-line network client or service");
assert.notEqual(reading.classification.id, "website");
assert.match(reading.purpose, /command-line client/i);
assert.match(reading.purpose, /background service/i);
assert.match(reading.purpose, /Cloudflare Tunnel/i);
assert.match(reading.purpose, /outbound connections/i);
assert.match(reading.audience, /run or develop services/i);
assert.ok(reading.actions.some(action => /install or download/i.test(action.label)));
assert.ok(reading.actions.some(action => /Tunnel documentation/i.test(action.label)));
assert.ok(reading.actions.some(action => /container image/i.test(action.label)));
assert.ok(reading.actions.every(action => !/deprecated|cap.?n proto|requirements/i.test(`${action.label} ${action.source}`)));
assert.ok(reading.capabilities.some(item => /implemented Cloudflare Tunnel client and daemon/i.test(item)));
assert.ok(reading.capabilities.some(item => /outbound tunnel connections/i.test(item)));
assert.equal(reading.progress.completion, null);
assert.ok(reading.evidence.some(record => /command-line client/i.test(record.excerpt)));

const reference = repositoryReference("https://github.com/cloudflare/cloudflared");
assert.deepEqual(reference, {
  owner: "cloudflare",
  repo: "cloudflared",
  fullName: "cloudflare/cloudflared"
});

const calls = [];
const fakeFetch = async url => {
  calls.push(url);
  if (url === "https://raw.githubusercontent.com/cloudflare/cloudflared/HEAD/README.md") {
    return {
      ok: true,
      status: 200,
      text: async () => readme
    };
  }
  return { ok: false, status: 404, text: async () => "" };
};
const raw = await fetchRawReadme(reference, fakeFetch);
assert.equal(raw.ref, "HEAD");
assert.match(raw.text, /command-line client/i);
assert.equal(calls.length, 1);

const fallback = fallbackRepository(reference, raw.ref);
assert.equal(fallback.full_name, "cloudflare/cloudflared");
assert.equal(fallback.default_branch, "HEAD");
assert.equal(fallback.archived, null);
assert.equal(fallback.license, null);
assert.equal(fallback.html_url, "https://github.com/cloudflare/cloudflared");

console.log("network-and-fallback-contract=pass");
