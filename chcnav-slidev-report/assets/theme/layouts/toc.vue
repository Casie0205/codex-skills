<script setup lang="ts">
import background from '../assets/template_toc.png'
import logo from '../assets/chcnav-logo.png'
</script>

<template>
  <div
    class="slidev-layout chcnav-toc"
    :style="{ backgroundImage: `url(${background})` }"
  >
    <img class="chcnav-page-logo" :src="logo" alt="CHCNAV">
    <div class="chcnav-toc-word">
      Contents
    </div>
    <div class="chcnav-toc-body">
      <slot />
    </div>
  </div>
</template>
