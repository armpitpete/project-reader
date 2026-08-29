import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

import { buildComprehension } from "../prototype/comprehension.js";
import { correctNetworkServiceReading } from "../prototype/network-corrections.js";
import { polishReading } from "../prototype/polish.js";

const BASELINE = "1332e0a6baab8b3dd03dff30473ac52edda2b52e";
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const EXPECTED_PATH = path.join(ROOT, "research", "unseen-generalisation-v1.3", "expected-readings.json");
const DEFAULT_OUTPUT = path.join(ROOT, "build", "unseen-generalisation-v1.3", "raw-results.json");
const GITHUB_API = "https://api.github.com";

const FROZEN_PRODUCTION_BLOBS = new Map([
  ["prototype/comprehension.js", "2d59801ca8ad30875da7ef51415a1b1844c3a92d"],
  ["prototype/network-corrections.js", "9f1a8788c14732f820c02e9098a5e10e46a014d5"],
  ["prototype/polish.js", "c329de3b0a92ddc8705504e01f6065c66b7440d3"]
]);

function argumentValue(name, fallback = null) {
  const index = process.argv.indexOf(name);
  if (index === -1) return fallback;
  const value = process.argv[index + 1];
  if (!value || value.startsWith("--")) throw new Error(`${name} requires a value.`);
  return value;
}

function gitBlobSha(filePath) {
  return execFileSync("git", ["hash-object", filePath], { cwd: ROOT, encoding: "utf8" }).trim();
}

function assertFrozenProduction() {
  for (const [relativePath, expectedSha] of FROZEN_PRODUCTION_BLOBS) {
    const actualSha = gitBlobSha(relativePath);
    if (actualSha !== expectedSha) {
      throw new Error(
        `Benchmark refused: ${relativePath} is ${actualSha}, expected frozen production blob ${expectedSha}.`
      );
    }
  }
}

async function loadExpectedRecords() {
  const payload = JSON.parse(await readFile(EXPECTED_PATH, "utf8"));
  if (payload.schema_version !== 1) throw new Error("Unsupported expected-reading schema version.");
  if (payload.baseline_project_reader_main !== BASELINE) throw new Error("Expected readings target the wrong Project Reader baseline.");
  if (!Array.isArray(payload.records) || payload.records.length !== 30) {
    throw new Error("Expected readings must contain exactly 30 active benchmark records.");
  }

  const ids = new Set();
  const repositories = new Set();
  for (const record of payload.records) {
    if (!record.id || !record.repository) throw new Error("Every benchmark record needs id and repository.");
    if (ids.has(record.id)) throw new Error(`Duplicate benchmark id: ${record.id}`);
    if (repositories.has(record.repository.toLowerCase())) throw new Error(`Duplicate benchmark repository: ${record.repository}`);
    ids.add(record.id);
    repositories.add(record.repository.toLowerCase());
  }
  return payload.records;
}

function githubHeaders() {
  const headers = {
    Accept: "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "project-reader-unseen-generalisation-v1.3"
  };
  const token = process.env.PROJECT_READER_GITHUB_TOKEN || process.env.GITHUB_TOKEN;
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

async function githubJson(url, { allow404 = false } = {}) {
  const response = await fetch(url, { headers: githubHeaders(), cache: "no-store" });
  if (allow404 && response.status === 404) return null;
  if (!response.ok) {
    throw new Error(`GitHub ${response.status} for ${url}`);
  }
  return response.json();
}

function decodeGitHubContent(payload) {
  if (!payload || payload.type !== "file" || payload.encoding !== "base64" || typeof payload.content !== "string") {
    return null;
  }
  return Buffer.from(payload.content.replace(/\s/g, ""), "base64").toString("utf8");
}

async function readOne(record) {
  const [owner, repoName] = record.repository.split("/", 2);
  const encodedOwner = encodeURIComponent(owner);
  const encodedRepo = encodeURIComponent(repoName);
  const repoUrl = `${GITHUB_API}/repos/${encodedOwner}/${encodedRepo}`;

  try {
    const repo = await githubJson(repoUrl);
    if (repo.private) throw new Error("Benchmark repository is private.");

    const branch = encodeURIComponent(repo.default_branch);
    const base = `${GITHUB_API}/repos/${encodeURIComponent(repo.owner.login)}/${encodeURIComponent(repo.name)}`;
    const [readmePayload, progressPayload, languages] = await Promise.all([
      githubJson(`${base}/readme?ref=${branch}`),
      githubJson(`${base}/contents/.project/progress.json?ref=${branch}`, { allow404: true }),
      githubJson(`${base}/languages`, { allow404: true })
    ]);

    const readme = decodeGitHubContent(readmePayload);
    if (!readme) throw new Error("Repository does not provide a readable README through GitHub's public API.");

    let progress = null;
    const progressText = decodeGitHubContent(progressPayload);
    if (progressText) {
      try {
        progress = JSON.parse(progressText);
      } catch {
        progress = null;
      }
    }

    const baseReading = polishReading(
      buildComprehension(repo, readme, progress, languages || {}),
      repo,
      readme
    );
    const reading = correctNetworkServiceReading(baseReading, repo, readme);

    return {
      id: record.id,
      repository: record.repository,
      status: "READ",
      observed_repository: {
        full_name: repo.full_name,
        html_url: repo.html_url,
        default_branch: repo.default_branch,
        description: repo.description,
        archived: Boolean(repo.archived),
        fork: Boolean(repo.fork)
      },
      readme_sha256: createHash("sha256").update(readme, "utf8").digest("hex"),
      reading,
      error: null
    };
  } catch (error) {
    return {
      id: record.id,
      repository: record.repository,
      status: "UNAVAILABLE",
      observed_repository: null,
      readme_sha256: null,
      reading: null,
      error: error instanceof Error ? error.message : String(error)
    };
  }
}

async function main() {
  assertFrozenProduction();
  const records = await loadExpectedRecords();

  if (process.argv.includes("--validate-only")) {
    console.log(`Validated frozen Project Reader production blobs and ${records.length} pre-evaluation expectation records.`);
    return;
  }

  const outputPath = path.resolve(argumentValue("--output", DEFAULT_OUTPUT));
  const results = [];
  for (const record of records) {
    process.stderr.write(`[${record.id}] ${record.repository}\n`);
    results.push(await readOne(record));
  }

  const payload = {
    schema_version: 1,
    baseline_project_reader_main: BASELINE,
    generated_at: new Date().toISOString().replace(/\.\d{3}Z$/, "Z"),
    records: results
  };

  await mkdir(path.dirname(outputPath), { recursive: true });
  await writeFile(outputPath, `${JSON.stringify(payload, null, 2)}\n`, "utf8");

  const readCount = results.filter(item => item.status === "READ").length;
  const unavailableCount = results.length - readCount;
  console.log(`Wrote ${results.length} frozen-baseline results: ${readCount} READ, ${unavailableCount} UNAVAILABLE.`);
  console.log(outputPath);

  if (unavailableCount) process.exitCode = 2;
}

await main();
