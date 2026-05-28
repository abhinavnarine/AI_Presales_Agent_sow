<script setup>
defineProps({
  sources: { type: Array, default: () => [] },
})
</script>

<template>
  <div class="card sources">
    <h3>Retrieved Sources <span class="count">{{ sources.length }}</span></h3>
    <p v-if="!sources.length" class="faint empty">
      No sources — generated without retrieval.
    </p>
    <ul v-else>
      <li v-for="(s, i) in sources" :key="i">
        <div class="src-head">
          <span class="src-name mono">{{ s.source }}</span>
          <span class="score" :style="{ '--w': Math.min(s.score, 1) * 100 + '%' }">
            {{ s.score.toFixed(3) }}
          </span>
        </div>
        <p class="snippet">{{ s.snippet.slice(0, 220) }}{{ s.snippet.length > 220 ? '…' : '' }}</p>
      </li>
    </ul>
  </div>
</template>

<style scoped>
h3 { font-family: var(--display); font-weight: 500; font-size: 16px; margin: 0 0 14px; display: flex; align-items: center; gap: 8px; }
.count { font-family: var(--mono); font-size: 12px; background: var(--accent-soft); color: var(--accent); border-radius: 20px; padding: 2px 9px; }
.empty { font-size: 13px; }
ul { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 12px; }
li { border-left: 2px solid var(--line); padding-left: 12px; }
.src-head { display: flex; justify-content: space-between; align-items: baseline; gap: 10px; }
.src-name { font-size: 12px; color: var(--teal); }
.score { font-family: var(--mono); font-size: 11px; color: var(--text-faint); position: relative; }
.snippet { font-size: 12.5px; color: var(--text-dim); margin: 6px 0 0; line-height: 1.5; }
</style>
