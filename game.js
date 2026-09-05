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
