import { cleanMarkdown, safePublicUrl } from "./comprehension.js";

const NETWORK_SERVICE_SIGNAL = /\b(?:command[- ]line client|tunnell?ing daemon|tunnel client|proxy daemon|network connector|cloudflare tunnel|proxies? traffic from|creates? outbound connections?)\b/i;
const BROWSER_PRODUCT_SIGNAL = /\b(?:browser-facing|web application|web app|live website|website builder|open in (?:a|your) browser|deployed (?:at|website))\b/i;

function corpusFor(repo, readme) {
  return `${repo?.name || ""} ${repo?.description || ""} ${String(readme || "").slice(0, 45_000)}`;
}

export function isCommandLineNetworkService(repo, readme) {
  const corpus = corpusFor(repo, readme);
  if (!NETWORK_SERVICE_SIGNAL.test(corpus)) return false;
  if (/\b(?:command[- ]line client|tunnell?ing daemon|cloudflare tunnel)\b/i.test(corpus)) return true;
  return !BROWSER_PRODUCT_SIGNAL.test(corpus);
}

function firstUsefulParagraph(readme) {
  const paragraphs = String(readme || "")
    .replace(/\r\n?/g, "\n")
    .replace(/\[!\[[^\]]*\]\([^)]*\)\]\([^)]*\)/g, " ")
    .replace(/```[\s\S]*?```/g, " ")
    .split(/\n\s*\n/)
    .map(cleanMarkdown)
    .filter(item => item.length >= 45)
    .filter(item => !/^github |^build status|^table of contents/i.test(item));
  return paragraphs.find(item => NETWORK_SERVICE_SIGNAL.test(item)) || paragraphs[0] || "";
}

function sectionBefore(readme, index) {
  const headings = [...String(readme || "").slice(0, index).matchAll(/^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$/gm)];
  return headings.length ? cleanMarkdown(headings.at(-1)[1]) : "README overview";
}

function resolveLink(repo, href) {
  try {
    if (/^https?:\/\//i.test(href)) {
      const url = new URL(href);
      if (url.protocol === "http:") url.protocol = "https:";
      return safePublicUrl(url.href);
    }
    const repository = safePublicUrl(repo?.html_url);
    if (href.startsWith("#")) return repository ? `${repository.replace(/\/$/, "")}${href}` : null;
    if (href.startsWith("/")) return safePublicUrl(`https://github.com${href}`);
    if (!repo?.full_name || !repo?.default_branch) return null;
    return safePublicUrl(new URL(
      href,
      `https://github.com/${repo.full_name}/blob/${encodeURIComponent(repo.default_branch)}/`
    ).href);
  } catch {
    return null;
  }
}

function readmeLinks(repo, readme) {
  const text = String(readme || "");
  const pattern = /(?<!!)\[([^\]]{1,180})\]\(([^)\s]+)(?:\s+["'][^"']*["'])?\)/g;
  const links = [];
  let match;
  while ((match = pattern.exec(text)) && links.length < 260) {
    const label = cleanMarkdown(match[1]);
    const url = resolveLink(repo, match[2].trim().replace(/^<|>$/g, ""));
    if (label && url) links.push({ label, url, source: sectionBefore(text, match.index) });
  }
  return links;
}

function badPrimaryAction(link) {
  const text = `${link.label} ${link.source} ${link.url}`.toLowerCase();
  return /deprecated|previous-versions|update-cloudflared|cap(?:'n|n)p|capnproto|requirements?|optional sdk|badge|twitter|discord|locali[sz]ation|sign up|status page/.test(text);
}

function firstLink(links, predicate) {
  return links.find(link => !badPrimaryAction(link) && predicate(`${link.label} ${link.source} ${link.url}`.toLowerCase(), link)) || null;
}

function unique(items, key) {
  const seen = new Set();
  return items.filter(item => {
    const value = key(item);
    if (!value || seen.has(value)) return false;
    seen.add(value);
    return true;
  });
}

function networkActions(repo, readme) {
  const links = readmeLinks(repo, readme);
  const corpus = corpusFor(repo, readme);
  const repository = safePublicUrl(repo?.html_url);
  const actions = [];

  if (repository && /\b(?:installing|installation|downloads?|standalone binaries|packages?|releases?)\b/i.test(corpus)) {
    actions.push({
      label: "Install or download the command-line client",
      url: `${repository.replace(/\/$/, "")}/releases/latest`,
      source: "README installation section"
    });
  }

  const documentation = firstLink(links, text =>
    /developers\.cloudflare\.com\/cloudflare-one\/networks\/connectors\/cloudflare-tunnel\/?(?:\s|$)/.test(text) ||
    /cloudflare tunnel (?:section|documentation)|user documentation for cloudflare tunnel/.test(text)
  );
  if (documentation) {
    actions.push({
      label: "Read the Cloudflare Tunnel documentation",
      url: documentation.url,
      source: documentation.source
    });
  }

  const setup = firstLink(links, text =>
    /get-started\/create-remote-tunnel|create a tunnel|trycloudflare|getting started|quick start/.test(text)
  );
  if (setup) {
    actions.push({
      label: "Configure and run a tunnel",
      url: setup.url,
      source: setup.source
    });
  } else if (repository && /^cloudflared$/i.test(String(repo?.name || ""))) {
    actions.push({
      label: "Read the setup and command guide",
      url: `${repository.replace(/\/$/, "")}#creating-tunnels-and-routing-traffic`,
      source: "README setup section"
    });
  }

  const container = firstLink(links, text => /hub\.docker\.com|dockerhub|container image|docker image/.test(text));
  if (container) {
    actions.push({
      label: "Get the container image",
      url: container.url,
      source: container.source
    });
  }

  if (repository) actions.push({ label: "Open the source repository", url: repository, source: "Repository" });

  if (actions.length < 3) {
    const fallbackLinks = links
      .filter(link => !badPrimaryAction(link))
      .filter(link => /install|download|documentation|\bdocs\b|usage|guide|contribut/i.test(`${link.label} ${link.source}`))
      .map(link => ({ label: cleanMarkdown(link.label), url: link.url, source: link.source }));
    actions.push(...fallbackLinks);
  }

  return unique(actions, action => action.label).slice(0, 4);
}

function networkPurpose(repo, readme) {
  const corpus = corpusFor(repo, readme);
  const name = cleanMarkdown(repo?.name || "This project").replace(/[-_]+/g, " ");
  if (/\bcloudflared\b/i.test(corpus) && /\bcloudflare tunnel\b/i.test(corpus)) {
    return "cloudflared is the command-line client and background service for Cloudflare Tunnel. It opens outbound connections between a local service or origin and Cloudflare's network so traffic can reach that service without exposing an inbound port.";
  }
  if (/\btunnel\b/i.test(corpus)) {
    return `${name} is a command-line network client and background service. It creates and maintains tunnel connections between a local service and another network.`;
  }
  return `${name} is a command-line network client or background service used to connect, proxy or route traffic between systems.`;
}

function networkAudience(repo, readme) {
  const corpus = corpusFor(repo, readme);
  if (/\b(?:operators?|administrators?|developers?|origin|services?)\b/i.test(corpus)) {
    return "It is mainly for people who run or develop services and need to connect them through a tunnel, proxy or managed network.";
  }
  return "The README appears to address people who configure and operate networked services.";
}

function networkCapabilities(repo, readme) {
  const corpus = corpusFor(repo, readme);
  const items = [];
  if (/\bcloudflared\b/i.test(corpus) && /\bcloudflare tunnel\b/i.test(corpus)) {
    items.push("The repository contains the implemented Cloudflare Tunnel client and daemon.");
  }
  if (/\b(?:outbound connection|proxies? traffic|tunnel)\b/i.test(corpus)) {
    items.push("It can carry traffic between a local origin or service and a remote network through outbound tunnel connections.");
  }
  if (/without requiring you to (?:poke|open).*firewall|without.*inbound port/i.test(corpus)) {
    items.push("The tunnel design avoids requiring a publicly exposed inbound port on the origin network.");
  }
  if (/dockerhub|container image|docker image/i.test(corpus)) {
    items.push("The README links to a container image for running the client in a container environment.");
  }
  if (/\b(?:installing|installation|package manager|binary releases?|standalone binaries)\b/i.test(corpus)) {
    items.push("The project provides installation or release routes for running the command-line client.");
  }
  if (!items.length) {
    items.push("The README describes an implemented command-line network client or service, although it does not provide a concise feature list.");
  }
  return unique(items, item => item).slice(0, 5);
}

function networkEvidence(readme, reading) {
  const excerpt = firstUsefulParagraph(readme);
  if (!excerpt) return reading.evidence;
  const records = [
    { statement: reading.purpose, source: "README overview", excerpt: excerpt.slice(0, 320) },
    { statement: reading.audience, source: "README overview and installation guidance", excerpt: excerpt.slice(0, 320) }
  ];
  return unique([...records, ...(reading.evidence || [])], record => `${record.statement}|${record.excerpt}`).slice(0, 10);
}

export function correctNetworkServiceReading(reading, repo, readme) {
  if (!isCommandLineNetworkService(repo, readme)) return reading;

  const actions = networkActions(repo, readme);
  const purpose = networkPurpose(repo, readme);
  const audience = networkAudience(repo, readme);
  let unfinished = (reading.unfinished || []).filter(item => !/README does not provide a complete plan of remaining work/i.test(item));
  if (!unfinished.some(item => /completion remains unknown/i.test(item))) {
    unfinished.push("Overall completion remains unknown because no recognised owner-defined completion measure is available.");
  }
  if (!unfinished.some(item => /roadmap|remaining work/i.test(item))) {
    unfinished.unshift("The public README does not provide an owner-defined roadmap that measures all remaining work.");
  }

  const corrected = {
    ...reading,
    classification: {
      ...reading.classification,
      id: "network-service",
      label: "Command-line network client or service",
      confidence: "high"
    },
    purpose,
    audience,
    actions,
    capabilities: networkCapabilities(repo, readme),
    unfinished: unique(unfinished, item => item).slice(0, 5),
    start: actions[0] || reading.start
  };
  corrected.evidence = networkEvidence(readme, corrected);
  return corrected;
}
