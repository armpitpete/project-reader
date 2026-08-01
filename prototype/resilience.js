const RAW_ORIGIN = "https://raw.githubusercontent.com";
const MAX_README_CHARS = 180_000;

export class GitHubApiError extends Error {
  constructor(message, { status = 0, unavailable = false, rateLimited = false } = {}) {
    super(message);
    this.name = "GitHubApiError";
    this.status = status;
    this.unavailable = unavailable;
    this.rateLimited = rateLimited;
  }
}

export function repositoryReference(value) {
  const text = String(value || "").trim();
  let match = text.match(/^([A-Za-z0-9_.-]+)\/([A-Za-z0-9_.-]+)$/);
  if (!match) {
    try {
      const url = new URL(text);
      if (url.protocol !== "https:" || url.hostname !== "github.com" || url.search || url.hash) throw new Error();
      const parts = url.pathname.split("/").filter(Boolean);
      if (parts.length !== 2) throw new Error();
      match = [text, parts[0], parts[1].replace(/\.git$/i, "")];
    } catch {
      throw new Error("Enter owner/name or a root public GitHub repository address.");
    }
  }
  const owner = match[1];
  const repo = match[2].replace(/\.git$/i, "");
  if (!owner || !repo || owner.length > 100 || repo.length > 100 || owner.startsWith(".") || repo.startsWith(".")) {
    throw new Error("That repository address is not supported.");
  }
  return { owner, repo, fullName: `${owner}/${repo}` };
}

function rawCandidates(reference) {
  const owner = encodeURIComponent(reference.owner);
  const repo = encodeURIComponent(reference.repo);
  const refs = ["HEAD", "main", "master"];
  const paths = ["README.md", "readme.md", "Readme.md", "README"];
  const candidates = [];
  for (const ref of refs) {
    for (const path of paths) {
      candidates.push({
        ref,
        path,
        url: `${RAW_ORIGIN}/${owner}/${repo}/${ref}/${path}`
      });
    }
  }
  return candidates;
}

export async function fetchRawReadme(reference, fetchImpl = fetch) {
  let lastStatus = 0;
  for (const candidate of rawCandidates(reference)) {
    try {
      const response = await fetchImpl(candidate.url, {
        method: "GET",
        headers: { Accept: "text/plain" },
        cache: "no-store"
      });
      lastStatus = response.status;
      if (!response.ok) continue;
      const text = (await response.text()).slice(0, MAX_README_CHARS);
      if (!text.trim()) continue;
      return { ...candidate, text };
    } catch {
      lastStatus = 0;
    }
  }
  throw new GitHubApiError(
    "The public README could not be loaded from GitHub's raw-content service.",
    { status: lastStatus, unavailable: true }
  );
}

export function fallbackRepository(reference, readmeRef = "HEAD") {
  const htmlUrl = `https://github.com/${encodeURIComponent(reference.owner)}/${encodeURIComponent(reference.repo)}`;
  return {
    name: reference.repo,
    full_name: reference.fullName,
    html_url: htmlUrl,
    homepage: null,
    description: null,
    default_branch: readmeRef,
    archived: null,
    fork: null,
    private: false,
    license: null,
    owner: {
      login: reference.owner,
      html_url: `https://github.com/${encodeURIComponent(reference.owner)}`
    }
  };
}

export function fallbackNotice(rateLimited = false) {
  return rateLimited
    ? "GitHub's anonymous API allowance was unavailable, so this reading uses the public README directly. Licence, default-branch, language and owner-progress metadata could not be checked."
    : "GitHub's metadata API was unavailable, so this reading uses the public README directly. Licence, default-branch, language and owner-progress metadata could not be checked.";
}
