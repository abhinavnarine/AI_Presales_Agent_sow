<script setup>
defineProps({
  result: { type: Object, default: null },
  title: { type: String, default: 'Statement of Work' },
})

const sections = [
  ['project_overview', 'Project Overview'],
  ['scope_of_work', 'Scope of Work'],
  ['deliverables', 'Deliverables'],
  ['timeline', 'Timeline'],
  ['assumptions', 'Assumptions'],
]
</script>

<template>
  <div class="card sow" v-if="result">
    <div class="sow-head">
      <h3>{{ title }}</h3>
      <span class="badge" :class="result.used_rag ? 'on' : 'off'">
        {{ result.used_rag ? 'RAG ON' : 'RAG OFF' }}
      </span>
    </div>

    <div class="meta" v-if="result.normalized_deal">
      <span class="pill">{{ result.normalized_deal.client_name }}</span>
      <span class="pill">{{ result.normalized_deal.industry }}</span>
      <span class="pill">{{ result.normalized_deal.project_type }}</span>
      <span class="pill">{{ result.normalized_deal.timeline }}</span>
    </div>

    <div class="warns" v-if="result.normalized_deal && result.normalized_deal.warnings.length">
      <div v-for="(w, i) in result.normalized_deal.warnings" :key="i" class="warn">⚠ {{ w }}</div>
    </div>

    <div class="section" v-for="[key, heading] in sections" :key="key">
      <h4>{{ heading }}</h4>
      <pre>{{ result.sow[key] }}</pre>
    </div>
  </div>
</template>

<style scoped>
.sow-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
h3 { font-family: var(--display); font-weight: 500; font-size: 18px; margin: 0; }
.badge { font-family: var(--mono); font-size: 11px; padding: 3px 9px; border-radius: 6px; letter-spacing: .03em; }
.badge.on { background: var(--teal-soft); color: var(--teal); }
.badge.off { background: #2a1f1a; color: var(--danger); }
.meta { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px; }
.pill { font-size: 11.5px; background: var(--bg-elev-2); border: 1px solid var(--line-soft); color: var(--text-dim); border-radius: 20px; padding: 3px 11px; }
.warns { margin-bottom: 14px; }
.warn { font-size: 12.5px; color: var(--accent); background: var(--accent-soft); border-radius: 6px; padding: 6px 10px; margin-bottom: 6px; }
.section { margin-top: 16px; }
h4 { font-size: 12px; letter-spacing: .05em; text-transform: uppercase; color: var(--text-faint); margin: 0 0 6px; border-bottom: 1px solid var(--line-soft); padding-bottom: 5px; }
pre { font-family: var(--sans); font-size: 13.5px; color: var(--text); white-space: pre-wrap; margin: 0; line-height: 1.6; }
</style>
