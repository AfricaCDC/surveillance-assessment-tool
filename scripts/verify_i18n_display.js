// Focused DOM contract check: translated option text must retain its English value.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const catalog = JSON.parse(fs.readFileSync(path.join(root, 'static', 'question-translations.json'), 'utf8'));
const choices = JSON.parse(fs.readFileSync(path.join(root, 'static', 'choice-translations.json'), 'utf8'));
const question = 'Which surveillance approaches does the system support?';
const callbacks = {};
const selector = {value: '', addEventListener: (name, callback) => {callbacks[name] = callback}};
function parent(tagName, explicitValue = true) {
  const attributes = new Set(explicitValue ? ['value'] : []);
  return {
    tagName,
    value: undefined,
    hasAttribute: name => attributes.has(name),
    closest: selector => selector.includes('script') ? null : {},
  };
}
const questionNode = {nodeValue: question, parentElement: parent('P')};
const optionNode = {nodeValue: 'Yes', parentElement: parent('OPTION', false)};
const choiceNode = {nodeValue: 'Ministry of Health', parentElement: parent('OPTION', false)};
const nodes = [questionNode, optionNode, choiceNode];
const field = {
  attributes: {placeholder: 'Search countries'},
  hasAttribute(name) {return Object.hasOwn(this.attributes, name)},
  getAttribute(name) {return this.attributes[name]},
  setAttribute(name, value) {this.attributes[name] = value},
};
const document = {
  body: {},
  documentElement: {lang: 'en', dir: 'ltr'},
  addEventListener: (name, callback) => {callbacks[name] = callback},
  getElementById: id => id === 'app-language' ? selector : null,
  createTreeWalker: () => {let i = 0; return {nextNode: () => nodes[i++] || null}},
  querySelectorAll: () => [field],
};
const context = {
  document,
  NodeFilter: {SHOW_TEXT: 4},
  MutationObserver: class {observe() {}},
  localStorage: {getItem: () => 'fr', setItem() {}},
  requestAnimationFrame: callback => callback(),
  fetch: async path => ({ok: true, json: async () => path.includes('question-translations') ? catalog : path.includes('choice-translations') ? choices : {}}),
};
vm.runInNewContext(fs.readFileSync(path.join(root, 'static', 'i18n.js'), 'utf8'), context);
callbacks.DOMContentLoaded();
setImmediate(() => {
  assert.equal(questionNode.nodeValue, catalog.fr[question]);
  assert.equal(optionNode.nodeValue, 'Oui');
  assert.equal(optionNode.parentElement.value, 'Yes');
  assert.equal(choiceNode.nodeValue, choices.fr['Ministry of Health']);
  assert.equal(choiceNode.parentElement.value, 'Ministry of Health');
  assert.equal(field.attributes.placeholder, 'Rechercher un pays');
  selector.value = 'ar';
  callbacks.change();
  assert.equal(questionNode.nodeValue, catalog.ar[question]);
  assert.equal(optionNode.parentElement.value, 'Yes');
  assert.equal(choiceNode.parentElement.value, 'Ministry of Health');
  assert.equal(document.documentElement.dir, 'rtl');
  selector.value = 'en';
  callbacks.change();
  assert.equal(questionNode.nodeValue, question);
  assert.equal(optionNode.nodeValue, 'Yes');
  assert.equal(choiceNode.nodeValue, 'Ministry of Health');
  assert.equal(field.attributes.placeholder, 'Search countries');
  console.log('Question display, option value, and language switching passed.');
});
