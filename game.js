const REWARDS = [
  { name: 'Golden Lucky Cat', prob: 3.33, icon: '🐱', cssClass: 'gold' },
  { name: 'Pink Lucky Cat', prob: 6.67, icon: '🐱', cssClass: 'pink' },
  { name: 'Blue Lucky Cat', prob: 13.33, icon: '🐱', cssClass: 'blue' },
  { name: 'Cat Sticker', prob: 26.67, icon: '🏷️', cssClass: 'sticker' },
  { name: 'Thank You for Participating', prob: 50, icon: '💝', cssClass: 'thanks' },
];

const INITIAL_CHANCES = 5;
const DRAW_ANIMATION_MS = 1000;

let chances = INITIAL_CHANCES;
let isDrawing = false;
let drawHistory = [];

const rewardsListEl = document.getElementById('rewards-list');
const historyListEl = document.getElementById('history-list');
const chancesCountEl = document.getElementById('chances-count');
const gachaMachineEl = document.getElementById('gacha-machine');
const resultDisplayEl = document.getElementById('result-display');
const btnDrawEl = document.getElementById('btn-draw');
const btnResetEl = document.getElementById('btn-reset');

function renderRewardsList() {
  rewardsListEl.innerHTML = REWARDS.map(
    (r) => `
      <li class="reward-item">
        <div class="reward-icon ${r.cssClass}">${r.icon}</div>
        <div class="reward-info">
          <div class="reward-name">${r.name}</div>
          <div class="reward-prob">${r.prob.toFixed(2)}%</div>
        </div>
      </li>`
  ).join('');
}

function renderHistory() {
  if (drawHistory.length === 0) {
    historyListEl.innerHTML = '<li class="history-empty">No draws yet</li>';
    return;
  }

  historyListEl.innerHTML = drawHistory
    .map(
      (entry, i) => `
      <li class="history-item">
        <span class="history-num">Draw ${i + 1}</span>
        <span class="history-icon">${entry.icon}</span>
        <span class="history-name">${entry.name}</span>
      </li>`
    )
    .join('');
}

function updateChancesDisplay() {
  chancesCountEl.textContent = chances;
}

function updateDrawButton() {
  btnDrawEl.disabled = isDrawing || chances <= 0;
}

function clearResult() {
  resultDisplayEl.innerHTML = '<p class="result-placeholder">Press "Draw Once" to start!</p>';
}

function showResult(reward) {
  const message =
    reward.cssClass === 'thanks' ? 'Better luck next time!' : 'Congratulations!';
  resultDisplayEl.innerHTML = `
    <div class="result-content">
      <div class="result-icon">${reward.icon}</div>
      <div class="result-name">${reward.name}</div>
      <div class="result-message">${message}</div>
    </div>`;
}

function selectReward() {
  const roll = Math.random() * 100;
  let cumulative = 0;
  for (const reward of REWARDS) {
    cumulative += reward.prob;
