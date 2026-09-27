const fs = require("fs");
const vm = require("vm");

const src = fs.readFileSync("web/app.js", "utf8");
const els = {};
const el = (id) => els[id] || (els[id] = {
  textContent: "",
  style: {},
  onclick: null,
  value: "en-IN",
});

const canvasContext = {
  drawImage() {},
  getImageData() {
    return { data: new Uint8ClampedArray(0) };
  },
};

const context = {
  window: {
    speechSynthesis: {
      cancel() {},
      speak() {},
    },
  },
  document: {
    getElementById: el,
    createElement() {
      return { getContext() { return canvasContext; } };
    },
  },
  requestAnimationFrame() {},
  setTimeout,
  clearTimeout,
  Date,
  Math,
  Float32Array,
  Uint8Array,
  Int32Array,
  TextDecoder,
  atob: global.atob,
  console,
};

vm.createContext(context);
vm.runInContext(src, context);

for (const name of [
  "loadNpz",
  "featureFromCanvas",
  "grabCutBox",
  "progress",
  "captureView",
  "viewEvidence",
  "loadModel",
  "start",
  "process",
]) {
  if (typeof context[name] !== "function") {
    throw new Error(name);
  }
}

console.log("browser smoke OK");
