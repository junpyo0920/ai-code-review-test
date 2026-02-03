const fs = require('fs');
const input = fs.readFileSync('/dev/stdin').toString().trim();
const lines = input.split('\n').map(e => +e);
const T = lines[0];

const dp = Array(11).fill(0)

dp[1] = 1;
dp[2] = 2;
dp[3] = 4;

function getWays(i) {
    if (dp[i]) return dp[i];

    dp[i] = getWays(i - 1) + getWays(i - 2) + getWays(i - 3);

    return dp[i];
}

for (let i = 1; i <= T; i++) {
    if (lines[i] < 4) {
        console.log(dp[lines[i]]);
        continue;
    }
    
    console.log(getWays(lines[i]));
}
