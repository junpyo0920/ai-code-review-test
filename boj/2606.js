const fs = require('fs');
const input = fs.readFileSync('/dev/stdin').toString().trim();
const lines = input.split('\n');

const n = +lines[0];

const mat = Array.from({ length: n + 1 }, () => Array(n + 1).fill(0));

for (let i = 2; i < lines.length; i++) {
    const [s, e] = lines[i].split(' ').map(e => +e);
    mat[s][e] = 1;
    mat[e][s] = 1;
}

const connectedCount = checkConnections(n + 1);

console.log(connectedCount);

function checkConnections(n) {
    const visited = Array(n + 1).fill(0);
    const queue = [1];

    while (queue.length) {
        const now = queue.pop();
        visited[now] = 1;

        for (let i = 1; i < n; i++) {
            if (mat[now][i] && !visited[i]) queue.push(i);
        }
    }

    return visited.filter(e => e).length - 1;
}