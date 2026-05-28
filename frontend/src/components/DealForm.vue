<script setup>
import { reactive, watch } from 'vue'

const props = defineProps({
  busy: Boolean,
  useRag: Boolean,
})
const emit = defineEmits(['generate', 'compare', 'update:useRag'])

const form = reactive({
  client_name: '',
  industry: '',
  project_type: '',
  objectivesText: '',
  timeline: '',
  budget_range: '',
})

const samples = {
  complete: {
    client_name: 'Acme Health',
    industry: 'Healthcare',
    project_type: 'Cloud Migration',
    objectivesText: 'Migrate legacy systems to AWS\nImprove scalability\nEnsure HIPAA compliance',
    timeline: '6 months',
    budget_range: '$250k-$500k',
  },
  messy: {
    client_name: 'Unknown',
    industry: '',
    project_type: 'Modernization',
    objectivesText: 'Improve systems',
    timeline: '',
    budget_range: '',
  },
}

function loadSample(name) {
  Object.assign(form, samples[name])
}

function buildDeal() {
  const objectives = form.objectivesText
    .split('\n')
    .map((s) => s.trim())
    .filter(Boolean)
  return {
    client_name: form.client_name || null,
    industry: form.industry || null,
    project_type: form.project_type || null,
    objectives: objectives.length ? objectives : null,
    timeline: form.timeline || null,
    budget_range: form.budget_range || null,
  }
}
</script>

<template>
  <div class="card form">
    <div class="form-head">
      <h2>Deal Input</h2>
      <div class="samples">
        <button @click="loadSample('complete')">Load complete sample</button>
        <button @click="loadSample('messy')">Load messy sample</button>
      </div>
    </div>

    <div class="grid">
      <div>
        <label class="label">Client name</label>
        <input v-model="form.client_name" placeholder="Acme Health (or leave blank)" />
      </div>
      <div>
        <label class="label">Industry</label>
        <input v-model="form.industry" placeholder="Healthcare" />
      </div>
      <div>
        <label class="label">Project type</label>
        <input v-model="form.project_type" placeholder="Cloud Migration" />
      </div>
      <div>
        <label class="label">Timeline</label>
        <input v-model="form.timeline" placeholder="6 months (or leave blank to infer)" />
      </div>
      <div class="span-2">
        <label class="label">Budget range</label>
        <input v-model="form.budget_range" placeholder="$250k-$500k (or leave blank)" />
      </div>
      <div class="span-2">
        <label class="label">Objectives (one per line)</label>
        <textarea v-model="form.objectivesText" rows="4"
          placeholder="Migrate legacy systems to AWS&#10;Improve scalability&#10;Ensure HIPAA compliance"></textarea>
      </div>
    </div>

    <div class="controls">
      <label class="toggle">
        <input type="checkbox" class="cb" :checked="useRag"
          @change="$emit('update:useRag', $event.target.checked)" />
        <span>Use RAG retrieval</span>
      </label>
      <div class="actions">
        <button :disabled="busy" @click="$emit('generate', { deal: buildDeal(), useRag })">
          {{ busy ? 'Working…' : 'Generate SOW' }}
        </button>
        <button class="primary" :disabled="busy" @click="$emit('compare', buildDeal())">
          Compare WITH vs WITHOUT RAG
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.form-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; gap: 12px; flex-wrap: wrap; }
h2 { font-family: var(--display); font-weight: 500; font-size: 20px; margin: 0; }
.samples { display: flex; gap: 8px; }
.samples button { font-size: 12px; padding: 6px 10px; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.span-2 { grid-column: 1 / -1; }
textarea { resize: vertical; font-family: var(--mono); font-size: 13px; }
.controls { display: flex; justify-content: space-between; align-items: center; margin-top: 18px; gap: 12px; flex-wrap: wrap; }
.toggle { display: flex; align-items: center; gap: 8px; font-size: 14px; color: var(--text-dim); cursor: pointer; }
.cb { width: auto; accent-color: var(--accent); }
.actions { display: flex; gap: 10px; }
@media (max-width: 620px) { .grid { grid-template-columns: 1fr; } }
</style>
