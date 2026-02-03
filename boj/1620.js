const fs = require('fs');
const input = fs.readFileSync('/dev/stdin').toString().trim();
const lines = input.split('\n');
const [N, M] = lines[0].split(' ').map((e) => +e);

const map = new Map();

for (let i = 1; i <= N; i++) {
    map.set(i, lines[i]);
    map.set(lines[i], i);
}

for (let i = N + 1; i <= N + M; i++) {
    const numOrName = Number.isNaN(+lines[i]) ? lines[i] : +lines[i];
    console.log(map.get(numOrName));
}