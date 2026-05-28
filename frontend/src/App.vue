<script setup>
import { ref, onMounted } from 'vue'
import DealForm from './components/DealForm.vue'
import SowOutput from './components/SowOutput.vue'
import SourcesPanel from './components/SourcesPanel.vue'

const useRag = ref(true)
const busy = ref(false)
const error = ref('')
const health = ref(null)

const mode = ref('single')        // 'single' | 'compare'
const single = ref(null)
const compare = ref(null)         // { with_rag, without_rag }

async function api(path, body) {
  const res = await fetch(`/api${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`)
  return res.json()
}

async function onGenerate({ deal, useRag: rag }) {
  busy.value = true; error.value = ''; compare.value = null
  try {
    mode.value = 'single'
    single.value = await api('/generate', { deal, use_rag: rag })
  } catch (e) { error.value = String(e) } finally { busy.value = false }
}

async function onCompare(deal) {
  busy.value = true; error.value = ''; single.value = null
  try {
    mode.value = 'compare'
    compare.value = await api('/compare', deal)
  } catch (e) { error.value = String(e) } finally { busy.value = false }
}

onMounted(async () => {
  try { health.value = await (await fetch('/api/health')).json() }
  catch { error.value = 'Backend not reachable on :8000. Start it with `python run.py`.' }
})
</script>

<template>
  <header>
    <div class="brand">
      <div class="mark">◆</div>
      <div>
        <h1>AI Presales Agent</h1>
        <p class="tag">Deal data → retrieved knowledge → grounded Statement of Work</p>
      </div>
    </div>
    <div class="status" v-if="health">
      <span class="dot" />
      <span class="mono">{{ health.llm_provider }} · {{ health.embedding_backend }} · {{ health.kb_chunks }} chunks</span>
    </div>
  </header>

  <DealForm :busy="busy" v-model:useRag="useRag" @generate="onGenerate" @compare="onCompare" />

  <p v-if="error" class="error">{{ error }}</p>

  <!-- Single mode -->
  <div v-if="mode === 'single' && single" class="results">
    <SowOutput :result="single" />
    <SourcesPanel :sources="single.sources" />
  </div>

  <!-- Compare mode -->
  <div v-if="mode === 'compare' && compare" class="compare">
    <div class="compare-note card">
      <strong>Side-by-side comparison.</strong>
      <span class="dim"> The left SOW is grounded in {{ compare.with_rag.sources.length }} retrieved
      knowledge-base chunks; the right SOW is generated from the input alone. Compare Scope,
      Deliverables and Assumptions to see the grounding effect.</span>
    </div>
    <div class="compare-grid">
      <SowOutput :result="compare.with_rag" title="WITH RAG (grounded)" />
      <SowOutput :result="compare.without_rag" title="WITHOUT RAG (input only)" />
    </div>
    <SourcesPanel :sources="compare.with_rag.sources" />
  </div>
</template>

<style scoped>
header { display: flex; justify-content: space-between; align-items: flex-end; padding: 40px 0 28px; flex-wrap: wrap; gap: 16px; }
.brand { display: flex; gap: 14px; align-items: center; }
.mark { font-size: 26px; color: var(--accent); }
h1 { font-family: var(--display); font-weight: 600; font-size: 30px; margin: 0; letter-spacing: -0.01em; }
.tag { margin: 2px 0 0; color: var(--text-dim); font-size: 14px; }
.status { display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--text-faint); }
.dot { width: 8px; height: 8px; border-radius: 50%; background: var(--teal); box-shadow: 0 0 8px var(--teal); }
.error { color: var(--danger); background: #2a1714; border: 1px solid #3d2019; border-radius: 8px; padding: 12px 14px; margin-top: 18px; font-size: 14px; }
.results { display: grid; grid-template-columns: 1.6fr 1fr; gap: 18px; margin-top: 22px; align-items: start; }
.compare { margin-top: 22px; }
.compare-note { margin-bottom: 16px; font-size: 13.5px; }
.compare-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; margin-bottom: 18px; align-items: start; }
@media (max-width: 900px) { .results, .compare-grid { grid-template-columns: 1fr; } }
</style>
