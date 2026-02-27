#!/usr/bin/env node
// Reads all .md files in zettelkasten/, parses YAML frontmatter,
// and writes zettelkasten-graph.json for the network visualisation.

const fs = require('fs');
const path = require('path');
const matter = require('gray-matter');

const notesDir = path.join(__dirname, '..', 'zettelkasten');
const outputFile = path.join(__dirname, '..', 'zettelkasten-graph.json');

if (!fs.existsSync(notesDir)) {
  console.log('No zettelkasten/ directory found. Writing empty graph.');
  fs.writeFileSync(outputFile, JSON.stringify({ nodes: [], edges: [] }, null, 2));
  process.exit(0);
}

const files = fs.readdirSync(notesDir).filter(f => f.endsWith('.md'));
const nodes = [];
const seen = new Set();
const edges = [];

for (const file of files) {
  const id = path.basename(file, '.md');
  const raw = fs.readFileSync(path.join(notesDir, file), 'utf8');
  const { data, content } = matter(raw);

  // Normalise date — gray-matter may parse YAML dates as Date objects
  let date = null;
  if (data.date) {
    date = data.date instanceof Date
      ? data.date.toISOString().split('T')[0]
      : String(data.date).split('T')[0];
  }

  nodes.push({
    id,
    title:  data.title  || id,
    tags:   Array.isArray(data.tags)  ? data.tags  : [],
    links:  Array.isArray(data.links) ? data.links : [],
    date,
    source: data.source || null,
    author: data.author || null,
    body:   content.trim(),
  });
}

// Build edges after all nodes are known so we can validate targets
const nodeIds = new Set(nodes.map(n => n.id));

for (const node of nodes) {
  for (const target of node.links) {
    if (!nodeIds.has(target)) {
      console.warn(`  Warning: "${node.id}" links to unknown note "${target}"`);
      continue;
    }
    const key = [node.id, target].sort().join('||');
    if (!seen.has(key)) {
      seen.add(key);
      edges.push({ source: node.id, target });
    }
  }
}

fs.writeFileSync(outputFile, JSON.stringify({ nodes, edges }, null, 2));
console.log(`Built graph: ${nodes.length} nodes, ${edges.length} edges → zettelkasten-graph.json`);
