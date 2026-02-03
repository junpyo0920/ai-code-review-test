const fs = require('fs');
const input = fs.readFileSync('/dev/stdin').toString().trim();

const lines = input.split('\n');

function getAnswer(data) {
    const stack = [];

    for (const b of data) {
        if (b === '(') stack.push(b);
        else if (stack.pop() === undefined) return 'NO';
    }

    return stack.length ? 'NO' : 'YES';
}

for (let i = 1; i < lines.length; i++) {
    const isVPS = getAnswer(lines[i]);
    console.log(isVPS);
}