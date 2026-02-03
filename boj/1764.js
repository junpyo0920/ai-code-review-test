const fs = require('fs');
const input = fs.readFileSync('/dev/stdin').toString().trim();
const lines = input.split('\n');
const [N, M] = lines[0].split(' ').map((e) => +e);

const neverHeardMap = new Map();
const neverHeardSeenMap = new Map();

for (let i = 1; i <= N; i++) {
    neverHeardMap.set(lines[i], true);
}

for (let i = N + 1; i <= N + M; i++) {
    if (neverHeardMap.get(lines[i])) neverHeardSeenMap.set(lines[i], true);
}

console.log(neverHeardSeenMap.size);
[...neverHeardSeenMap.keys()].sort().forEach((e) => console.log(e));